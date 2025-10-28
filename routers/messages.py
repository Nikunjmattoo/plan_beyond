# app/routers/messages.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, cast
from sqlalchemy.dialects.postgresql import JSONB
from typing import List
from datetime import datetime, timedelta
import base64, secrets, smtplib
from email.mime.text import MIMEText
import threading, time as _time
from contextlib import contextmanager

from app.database import SessionLocal
from app.dependencies import get_current_user, get_current_admin
from app.models.enums import (
    EventType, AssignmentRole, FolderStatus, BranchInviteStatus,
    ApprovalStatus
)
from app.models.message import (
    MessageCollection, MessageFile, MessageCollectionAssignment
)
from app.models.user import User, UserStatus
from app.models.contact import Contact
from app.models.trustee import Trustee
from app.models.death_approval import DeathApproval
from app.models.death import DeathLock, DeathLockType
from app.schemas.message import (
    MsgCreate, MsgUpdate, MsgOut, MsgAssignmentOut, MsgFileOut
)

from app.config import settings

router = APIRouter(prefix="/messages", tags=["Messages"])

# ---------- DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- helpers: text <-> data URL ----------
def _data_url_from_text(text: str) -> str:
    b = text.encode("utf-8")
    b64 = base64.b64encode(b).decode("ascii")
    return f"data:text/plain;charset=utf-8;base64,{b64}"

def _extract_text_from_files(files: List[MessageFile]) -> str:
    for f in files or []:
        if f.app_url and f.app_url.startswith("data:text/plain"):
            try:
                comma = f.app_url.index(",")
                raw = base64.b64decode(f.app_url[comma+1:])
                return raw.decode("utf-8")
            except Exception:
                continue
        if (f.mime_type or "").startswith("text/") and f.app_url and f.app_url.startswith("data:"):
            try:
                comma = f.app_url.index(",")
                raw = base64.b64decode(f.app_url[comma+1:])
                return raw.decode("utf-8")
            except Exception:
                continue
    return ""

# ---------- uniqueness & status ----------
def _ensure_unique_name(db: Session, *, user_id: int, name: str, exclude_id: int | None = None):
    if not (name and str(name).strip()):
        return
    q = db.query(MessageCollection.id).filter(
        MessageCollection.user_id == user_id,
        MessageCollection.name.ilike(name)
    )
    if exclude_id:
        q = q.filter(MessageCollection.id != exclude_id)
    if db.query(q.exists()).scalar():
        raise HTTPException(status_code=409, detail="A message with this name already exists.")

def _trigger_present(m: MessageCollection) -> bool:
    if m.event_type == EventType.time:
        return m.scheduled_at is not None
    if m.event_type == EventType.event:
        return bool(m.event_label and str(m.event_label).strip())
    return False

def _recompute_status(db: Session, m: MessageCollection):
    branch = db.query(MessageCollectionAssignment).filter(
        MessageCollectionAssignment.collection_id == m.id,
        MessageCollectionAssignment.role == AssignmentRole.branch
    ).count()
    leaf = db.query(MessageCollectionAssignment).filter(
        MessageCollectionAssignment.collection_id == m.id,
        MessageCollectionAssignment.role == AssignmentRole.leaf
    ).count()
    m.status = (
        FolderStatus.complete
        if branch >= 1 and leaf >= 1 and _trigger_present(m)
        else FolderStatus.incomplete
    )

# ---------- contacts & linking ----------
def _ensure_user_contact(db: Session, user_id: int, contact_id: int):
    q = db.query(Contact.id).filter(Contact.id == contact_id)
    if hasattr(Contact, "owner_user_id") and hasattr(Contact, "linked_user_id"):
        q = q.filter(or_(Contact.owner_user_id == user_id, Contact.linked_user_id == user_id))
    elif hasattr(Contact, "owner_user_id"):
        q = q.filter(Contact.owner_user_id == user_id)
    elif hasattr(Contact, "user_id"):
        q = q.filter(Contact.user_id == user_id)
    if not q.first():
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found for this user")

def _link_contacts_for_user(db: Session, user: User) -> int:
    filters = []
    if user.email:
        filters.append(cast(Contact.emails, JSONB).contains([user.email.strip().lower()]))
    if user.phone:
        filters.append(cast(Contact.phone_numbers, JSONB).contains([user.country_code + user.phone.strip()]))
    if not filters:
        return 0
    contacts = db.query(Contact).filter(or_(*filters)).all()
    changed = 0
    for c in contacts:
        if not getattr(c, "linked_user_id", None):
            c.linked_user_id = user.id
            changed += 1
    if changed:
        db.commit()
        for c in contacts:
            db.refresh(c)
    return changed

# ---------- death lock ----------
def _legacy_death_declared(db: Session, user_id: int) -> bool:
    from app.models.enums import TrusteeStatus
    trustees = db.query(Trustee).filter(Trustee.user_id == user_id, Trustee.status == TrusteeStatus.accepted).count()
    approvals = db.query(DeathApproval).filter(DeathApproval.user_id == user_id, DeathApproval.status == ApprovalStatus.approved).count()
    return trustees >= 2 and approvals >= 2

def _is_hard_death_finalized_for_owner(db: Session, owner_user_id: int) -> bool:
    hard = db.query(DeathLock).filter(
        DeathLock.root_user_id == owner_user_id,
        DeathLock.lock == DeathLockType.hard_finalized
    ).first()
    if hard:
        return True
    return _legacy_death_declared(db, owner_user_id)

def _enforce_vault_open(db: Session, owner_user_id: int):
    if _is_hard_death_finalized_for_owner(db, owner_user_id):
        raise HTTPException(status_code=403, detail="Vault is locked (hard-death finalized).")

# ---------- email (branch invites) ----------
def _send_plain_email(to_addr: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_EMAIL
    msg["To"] = to_addr
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
        server.send_message(msg)

def _compose_signup_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/register"

def _compose_otp_start_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/otp/start"

def _compose_profile_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/profile"

def _accept_branch_url(aid: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/messages/assignments/a/{aid}/{token}"

def _reject_branch_url(aid: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/messages/assignments/r/{aid}/{token}"

def _accept_leaf_url(aid: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/messages/leaves/a/{aid}/{token}"

def _reject_leaf_url(aid: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/messages/leaves/r/{aid}/{token}"

def _ensure_assignment_token(db: Session, a: MessageCollectionAssignment) -> str:
    changed = False
    if not getattr(a, "invite_token", None):
        a.invite_token = secrets.token_urlsafe(24)
        changed = True
    if not getattr(a, "invite_expires_at", None):
        a.invite_expires_at = datetime.utcnow() + timedelta(days=30)
        changed = True
    if changed:
        db.add(a); db.commit(); db.refresh(a)
    return a.invite_token

def _pb_blurb() -> str:
    return (
        "—\n"
        "Plan Beyond helps families handle important tasks when it matters most.\n"
        "As a Branch, you’re a trusted contact who can act when asked.\n"
        "Your privacy is respected — nothing is shared without the owner’s intent.\n"
    )

def _send_branch_invite_email(db: Session, a: MessageCollectionAssignment):
    if a.role != AssignmentRole.branch:
        return
    contact: Contact = db.query(Contact).filter(Contact.id == a.contact_id).first()
    if not contact or not contact.emails: return
    to_email = contact.emails[0]

    linked_user: User | None = None
    if getattr(contact, "linked_user_id", None):
        linked_user = db.query(User).filter(User.id == contact.linked_user_id).first()
    else:
        linked_user = db.query(User).filter(User.email == to_email).first()

    subject = "You were added as a Branch in Plan Beyond"
    body = f"Hello,\n\nYou were added as a Branch in Plan Beyond.\n\n{_pb_blurb()}"

    if not linked_user:
        subject = "You've been invited as a Branch — Create your account"
        body = (
            "Hello,\n\n"
            "To view and respond to your Branch invitation, create your account:\n"
            f"{_compose_signup_url()}\n\n{_pb_blurb()}"
        )
    elif not linked_user.otp_verified:
        subject = "Verify your account to respond to the Branch invitation"
        body = (
            "Hello,\n\n"
            "Verify your account to respond to your Branch invitation:\n"
            f"{_compose_otp_start_url()}\n\n{_pb_blurb()}"
        )
    elif linked_user.status in (UserStatus.unknown, UserStatus.guest):
        subject = "Complete your profile to respond to the Branch invitation"
        body = (
            "Hello,\n\n"
            "Complete your profile to respond to your Branch invitation:\n"
            f"{_compose_profile_url()}\n\n{_pb_blurb()}"
        )
    else:
        token = _ensure_assignment_token(db, a)
        subject = "Branch Invitation — Respond with Accept or Decline"
        body = (
            "Hello,\n\n"
            "You can respond to your Branch invitation below:\n\n"
            f"Accept:  {_accept_branch_url(a.id, token)}\n"
            f"Decline: {_reject_branch_url(a.id, token)}\n\n"
            f"{_pb_blurb()}"
        )
    try:
        _send_plain_email(to_email, subject, body)
    except Exception:
        pass

# ---------- assignment helpers ----------
def _add_assignments_and_invites(db: Session, m: MessageCollection, assignments: List[dict]):
    for a in assignments or []:
        _ensure_user_contact(db, m.user_id, a["contact_id"])
        row = MessageCollectionAssignment(
            collection_id=m.id,
            contact_id=a["contact_id"],
            role=a["role"],
        )
        if a["role"] == AssignmentRole.branch:
            row.invite_status = BranchInviteStatus.sent
            row.invited_at = datetime.utcnow()
        db.add(row)
        db.flush()
        if a["role"] == AssignmentRole.branch:
            _send_branch_invite_email(db, row)

def _reconcile_assignments(db: Session, m: MessageCollection, desired: List[dict]):
    existing = db.query(MessageCollectionAssignment).filter(
        MessageCollectionAssignment.collection_id == m.id
    ).all()
    existing_map = {(e.contact_id, e.role): e for e in existing}
    desired_keys = {(d["contact_id"], d["role"]) for d in desired}

    for key, row in list(existing_map.items()):
        if key not in desired_keys:
            db.delete(row)

    for d in desired:
        key = (d["contact_id"], d["role"])
        if key in existing_map:
            continue
        _ensure_user_contact(db, m.user_id, d["contact_id"])
        row = MessageCollectionAssignment(collection_id=m.id, contact_id=d["contact_id"], role=d["role"])
        if d["role"] == AssignmentRole.branch:
            row.invite_status = BranchInviteStatus.sent
            row.invited_at = datetime.utcnow()
        db.add(row)
        db.flush()
        if d["role"] == AssignmentRole.branch:
            _send_branch_invite_email(db, row)

# ---------- CRUD ----------
@router.post("/", response_model=MsgOut, status_code=status.HTTP_201_CREATED)
def create_message(payload: MsgCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _enforce_vault_open(db, user.id)
    _ensure_unique_name(db, user_id=user.id, name=payload.name)

    m = MessageCollection(
        user_id=user.id,
        name=payload.name.strip(),
        description=None,
        event_type=payload.event_type,
        scheduled_at=payload.scheduled_at if payload.event_type == EventType.time else None,
        event_label=payload.event_label if payload.event_type == EventType.event else None,
        is_armed=False,
    )
    db.add(m); db.flush()

    desired = [{"contact_id": a.contact_id, "role": a.role} for a in payload.assignments]
    _add_assignments_and_invites(db, m, desired)

    data_url = _data_url_from_text(payload.message_text or "")
    db.add(MessageFile(
        collection_id=m.id,
        app_url=data_url,
        title="Message.txt",
        mime_type="text/plain",
        size=len(payload.message_text.encode("utf-8")) if payload.message_text else 0,
    ))

    db.flush()
    _recompute_status(db, m)
    db.commit()

    m = db.query(MessageCollection)\
        .options(joinedload(MessageCollection.files), joinedload(MessageCollection.assignments))\
        .filter(MessageCollection.id == m.id).first()

    base = MsgOut.model_validate(m, from_attributes=True)
    return base.model_copy(update={
        "assignments": [MsgAssignmentOut.model_validate(a, from_attributes=True) for a in m.assignments],
        "files": [MsgFileOut.model_validate(f, from_attributes=True) for f in m.files],
        "message_text": _extract_text_from_files(m.files),
    })

@router.get("/", response_model=List[MsgOut])
def list_messages(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(MessageCollection)\
        .options(joinedload(MessageCollection.files), joinedload(MessageCollection.assignments))\
        .filter(MessageCollection.user_id == user.id)\
        .order_by(MessageCollection.created_at.desc())\
        .all()

    changed = False
    for m in rows:
        prev = getattr(m, "status", None)
        _recompute_status(db, m)
        if m.status != prev: changed = True
    if changed: db.commit()

    out: List[MsgOut] = []
    for m in rows:
        base = MsgOut.model_validate(m, from_attributes=True)
        out.append(base.model_copy(update={
            "assignments": [MsgAssignmentOut.model_validate(a, from_attributes=True) for a in m.assignments],
            "files": [MsgFileOut.model_validate(f, from_attributes=True) for f in m.files],
            "message_text": None,  # keep list lightweight
        }))
    return out

@router.get("/{message_id}", response_model=MsgOut)
def get_message(message_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.query(MessageCollection)\
        .options(joinedload(MessageCollection.files), joinedload(MessageCollection.assignments))\
        .filter(MessageCollection.id == message_id, MessageCollection.user_id == user.id)\
        .first()
    if not m:
        raise HTTPException(status_code=404, detail="Message not found")
    _recompute_status(db, m); db.commit()

    base = MsgOut.model_validate(m, from_attributes=True)
    return base.model_copy(update={
        "assignments": [MsgAssignmentOut.model_validate(a, from_attributes=True) for a in m.assignments],
        "files": [MsgFileOut.model_validate(f, from_attributes=True) for f in m.files],
        "message_text": _extract_text_from_files(m.files),
    })

@router.put("/{message_id}", response_model=MsgOut)
def put_message(message_id: int, payload: MsgCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _enforce_vault_open(db, user.id)
    m = db.query(MessageCollection)\
        .options(joinedload(MessageCollection.files), joinedload(MessageCollection.assignments))\
        .filter(MessageCollection.id == message_id, MessageCollection.user_id == user.id)\
        .first()
    if not m: raise HTTPException(status_code=404, detail="Message not found")

    _ensure_unique_name(db, user_id=user.id, name=payload.name, exclude_id=message_id)

    m.name = payload.name.strip()
    new_type = payload.event_type or m.event_type
    if new_type == EventType.time:
        if payload.scheduled_at is None:
            raise HTTPException(status_code=422, detail="scheduled_at is required when event_type is 'time'")
        m.scheduled_at = payload.scheduled_at
        m.event_label = None
    else:
        m.event_label = (payload.event_label or "").strip() or None
        m.scheduled_at = None
    m.event_type = new_type

    if payload.assignments is not None:
        desired = [{"contact_id": a.contact_id, "role": a.role} for a in payload.assignments]
        _reconcile_assignments(db, m, desired)

    db.query(MessageFile).filter(MessageFile.collection_id == m.id).delete(synchronize_session=False)
    data_url = _data_url_from_text(payload.message_text or "")
    db.add(MessageFile(
        collection_id=m.id,
        app_url=data_url,
        title="Message.txt",
        mime_type="text/plain",
        size=len(payload.message_text.encode("utf-8")) if payload.message_text else 0,
    ))

    db.flush()
    _recompute_status(db, m)
    db.commit()

    m = db.query(MessageCollection)\
        .options(joinedload(MessageCollection.files), joinedload(MessageCollection.assignments))\
        .filter(MessageCollection.id == message_id).first()
    base = MsgOut.model_validate(m, from_attributes=True)
    return base.model_copy(update={
        "assignments": [MsgAssignmentOut.model_validate(a, from_attributes=True) for a in m.assignments],
        "files": [MsgFileOut.model_validate(f, from_attributes=True) for f in m.files],
        "message_text": _extract_text_from_files(m.files),
    })

@router.patch("/{message_id}", response_model=MsgOut)
def patch_message(message_id: int, payload: MsgUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _enforce_vault_open(db, user.id)
    m = db.query(MessageCollection)\
        .options(joinedload(MessageCollection.files), joinedload(MessageCollection.assignments))\
        .filter(MessageCollection.id == message_id, MessageCollection.user_id == user.id)\
        .first()
    if not m: raise HTTPException(status_code=404, detail="Message not found")

    if payload.name is not None:
        _ensure_unique_name(db, user_id=user.id, name=payload.name, exclude_id=message_id)
        m.name = payload.name.strip()

    if payload.event_type is not None:
        try:
            m.event_type = EventType(payload.event_type)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid event_type")

    if m.event_type == EventType.time:
        if payload.scheduled_at is not None:
            m.scheduled_at = payload.scheduled_at
        if m.scheduled_at is None:
            raise HTTPException(status_code=422, detail="scheduled_at is required when event_type is 'time'")
        m.event_label = None
    else:
        if payload.event_label is not None:
            raw = payload.event_label
            m.event_label = (str(raw).strip() if raw is not None else None)
        m.scheduled_at = None

    if payload.assignments is not None:
        desired = [{"contact_id": a.contact_id, "role": a.role} for a in payload.assignments]
        _reconcile_assignments(db, m, desired)

    if payload.message_text is not None:
        db.query(MessageFile).filter(MessageFile.collection_id == m.id).delete(synchronize_session=False)
        data_url = _data_url_from_text(payload.message_text or "")
        db.add(MessageFile(
            collection_id=m.id,
            app_url=data_url,
            title="Message.txt",
            mime_type="text/plain",
            size=len(payload.message_text.encode("utf-8")) if payload.message_text else 0,
        ))

    db.flush()
    _recompute_status(db, m)
    db.commit()

    m = db.query(MessageCollection)\
        .options(joinedload(MessageCollection.files), joinedload(MessageCollection.assignments))\
        .filter(MessageCollection.id == m.id).first()
    base = MsgOut.model_validate(m, from_attributes=True)
    return base.model_copy(update={
        "assignments": [MsgAssignmentOut.model_validate(a, from_attributes=True) for a in m.assignments],
        "files": [MsgFileOut.model_validate(f, from_attributes=True) for f in m.files],
        "message_text": _extract_text_from_files(m.files),
    })

@router.delete("/{message_id}", status_code=204)
def delete_message(message_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _enforce_vault_open(db, user.id)
    m = db.query(MessageCollection).filter(
        MessageCollection.id == message_id,
        MessageCollection.user_id == user.id
    ).first()
    if not m: raise HTTPException(status_code=404, detail="Message not found")
    db.delete(m); db.commit()
    return

# ---------- Public accept/decline (branch) ----------
@router.get("/assignments/a/{assignment_id}/{token}")
def public_accept_branch(assignment_id: int, token: str, db: Session = Depends(get_db)):
    a = db.query(MessageCollectionAssignment).filter(MessageCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.branch:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not a.invite_token or a.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if a.invite_status != BranchInviteStatus.sent:
        raise HTTPException(status_code=409, detail=f"Invite already {getattr(a.invite_status,'value',a.invite_status)}")
    a.invite_status = BranchInviteStatus.accepted
    a.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Branch invitation accepted"}

@router.get("/assignments/r/{assignment_id}/{token}")
def public_reject_branch(assignment_id: int, token: str, db: Session = Depends(get_db)):
    a = db.query(MessageCollectionAssignment).filter(MessageCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.branch:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not a.invite_token or a.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if a.invite_status != BranchInviteStatus.sent:
        raise HTTPException(status_code=409, detail=f"Invite already {getattr(a.invite_status,'value',a.invite_status)}")
    a.invite_status = BranchInviteStatus.declined
    a.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Branch invitation declined"}

# ---------- Public accept/decline (leaf) ----------
@router.get("/leaves/a/{assignment_id}/{token}")
def public_accept_leaf(assignment_id: int, token: str, db: Session = Depends(get_db)):
    a = db.query(MessageCollectionAssignment).filter(MessageCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.leaf:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not a.invite_token or a.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    a.invite_status = BranchInviteStatus.accepted
    a.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Leaf assignment accepted"}

@router.get("/leaves/r/{assignment_id}/{token}")
def public_reject_leaf(assignment_id: int, token: str, db: Session = Depends(get_db)):
    a = db.query(MessageCollectionAssignment).filter(MessageCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.leaf:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not a.invite_token or a.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    a.invite_status = BranchInviteStatus.declined
    a.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Leaf assignment declined"}

# ---------- Invitee-side “to-do” views ----------
@router.get("/branches/todo")
def my_branch_todo(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        _link_contacts_for_user(db, user)
    except Exception:
        pass

    contact_ids = [cid for (cid,) in db.query(Contact.id).filter(Contact.linked_user_id == user.id).all()]
    if not contact_ids:
        return []

    rows = (
        db.query(MessageCollectionAssignment, MessageCollection, User)
        .join(MessageCollection, MessageCollectionAssignment.collection_id == MessageCollection.id)
        .join(User, MessageCollection.user_id == User.id, isouter=True)
        .filter(
            MessageCollectionAssignment.contact_id.in_(contact_ids),
            MessageCollectionAssignment.role == AssignmentRole.branch,
        )
        .all()
    )
    out = []
    for a, coll, inviter in rows:
        status_val = a.invite_status.value if hasattr(a.invite_status, "value") else a.invite_status
        out.append({
            "id": a.id,
            "contact_id": a.contact_id,
            "status": status_val,
            "invited_at": a.invited_at,
            "collection_id": coll.id if coll else None,
            "collection_name": coll.name if coll else None,
            "inviter_user_id": inviter.id if inviter else None,
            "inviter_display_name": (inviter.display_name if inviter and inviter.display_name else "A Plan Beyond member"),
            "event_type": (coll.event_type.value if hasattr(coll.event_type, "value") else coll.event_type),
            "event_label": (coll.event_label if coll else None),
            "scheduled_at": (coll.scheduled_at if coll else None),
        })
    out.sort(key=lambda x: (0 if x["status"] == "sent" else 1, -(x["invited_at"].timestamp() if x["invited_at"] else 0.0)))
    return out

@router.get("/leaves/todo")
def my_leaf_todo(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        _link_contacts_for_user(db, user)
    except Exception:
        pass

    contact_ids = [cid for (cid,) in db.query(Contact.id).filter(Contact.linked_user_id == user.id).all()]
    if not contact_ids:
        return []

    rows = (
        db.query(MessageCollectionAssignment, MessageCollection, User)
        .join(MessageCollection, MessageCollectionAssignment.collection_id == MessageCollection.id)
        .join(User, MessageCollection.user_id == User.id, isouter=True)
        .filter(
            MessageCollectionAssignment.contact_id.in_(contact_ids),
            MessageCollectionAssignment.role == AssignmentRole.leaf,
        )
        .all()
    )
    out = []
    for a, coll, inviter in rows:
        raw_status = getattr(a.invite_status, "value", None) or a.invite_status
        accept_url = reject_url = None
        hard_final = bool(inviter and _is_hard_death_finalized_for_owner(db, inviter.id))
        if hard_final and a.invite_token:
            s = (str(raw_status).lower() if raw_status else None)
            if s in {"sent", "accepted", "declined"}:
                accept_url = _accept_leaf_url(a.id, a.invite_token)
                reject_url = _reject_leaf_url(a.id, a.invite_token)
        past_due_notice = None
        if coll and coll.event_type == EventType.time and coll.scheduled_at:
            if coll.scheduled_at < datetime.utcnow() and not a.invite_status:
                past_due_notice = f"This was scheduled for {coll.scheduled_at.isoformat()}."
        out.append({
            "id": a.id,
            "contact_id": a.contact_id,
            "status": raw_status,
            "invited_at": a.invited_at,
            "collection_id": coll.id if coll else None,
            "collection_name": coll.name if coll else None,
            "inviter_user_id": inviter.id if inviter else None,
            "inviter_display_name": (inviter.display_name if inviter and inviter.display_name else "A Plan Beyond member"),
            "accept_url": accept_url,
            "reject_url": reject_url,
            "event_type": (coll.event_type.value if hasattr(coll.event_type, "value") else coll.event_type),
            "event_label": (coll.event_label if coll else None),
            "scheduled_at": (coll.scheduled_at if coll else None),
            "past_due_notice": past_due_notice,
        })
    out.sort(key=lambda x: (0 if x["status"] == "sent" else 1, -(x["invited_at"].timestamp() if x["invited_at"] else 0.0)))
    return out

# ---------- time-based auto send (no warmups; send once when due) ----------
def _now_utc() -> datetime:
    return datetime.utcnow()

def _send_time_based_leaf_links_once(db: Session, *, collection_id: int) -> dict:
    coll = db.query(MessageCollection).filter(MessageCollection.id == collection_id).first()
    if not coll or coll.event_type != EventType.time or not coll.scheduled_at:
        return {"ok": True, "sent": 0}
    if not _is_hard_death_finalized_for_owner(db, coll.user_id):
        return {"ok": True, "sent": 0, "skipped": "hard-death not finalized"}

    now = _now_utc()
    if coll.scheduled_at > now:
        return {"ok": True, "sent": 0, "skipped": "not due yet"}

    leaf_asgs = db.query(MessageCollectionAssignment).filter(
        MessageCollectionAssignment.collection_id == collection_id,
        MessageCollectionAssignment.role == AssignmentRole.leaf,
    ).all()
    if not leaf_asgs:
        return {"ok": True, "sent": 0}

    sent = 0
    changed = False
    for a in leaf_asgs:
        status_lower = (a.invite_status.value if hasattr(a.invite_status, "value") else a.invite_status)
        if status_lower in {"sent", "accepted", "declined"}:
            continue
        contact = db.query(Contact).filter(Contact.id == a.contact_id).first()
        if not contact or not contact.emails or not contact.emails[0]:
            continue
        to_email = contact.emails[0]
        linked_user: User | None = None
        if getattr(contact, "linked_user_id", None):
            linked_user = db.query(User).filter(User.id == contact.linked_user_id).first()
        else:
            linked_user = db.query(User).filter(User.email == to_email).first()
        if not linked_user or not linked_user.otp_verified or linked_user.status in (UserStatus.unknown, UserStatus.guest):
            # no warmups; skip until they’re ready
            continue

        if getattr(a, "invite_status", None) is None:
            a.invite_status = BranchInviteStatus.sent
            a.invited_at = now
            a.invite_expires_at = now + timedelta(days=30)
            changed = True

        token = _ensure_assignment_token(db, a)
        subject = "Items assigned to you — confirm to proceed"
        body = (
            "Hello,\n\n"
            "A scheduled message is now due and was assigned to you. Please choose:\n\n"
            f"Accept:  {_accept_leaf_url(a.id, token)}\n"
            f"Decline: {_reject_leaf_url(a.id, token)}\n\n"
            "— Plan Beyond"
        )
        try:
            _send_plain_email(to_email, subject, body)
            sent += 1
        except Exception:
            pass

    if changed: db.commit()
    return {"ok": True, "sent": sent, "due": True}

@router.post("/collections/{collection_id}/auto-time-check")
def auto_time_check(collection_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    coll = db.query(MessageCollection).filter(MessageCollection.id == collection_id).first()
    if not coll: raise HTTPException(status_code=404, detail="Message not found")
    # owner or accepted-branch can run this; to keep simple, allow owner only here:
    if coll.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this message")
    res = _send_time_based_leaf_links_once(db, collection_id=collection_id)
    return {"ok": True, **res}

@router.post("/collections/auto-time-scan")
def auto_time_scan_all(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    cols = db.query(MessageCollection).filter(
        MessageCollection.event_type == EventType.time,
        MessageCollection.scheduled_at.isnot(None),
    ).all()
    totals = {"sent": 0, "scanned": 0}
    for c in cols:
        if not _is_hard_death_finalized_for_owner(db, c.user_id):
            continue
        res = _send_time_based_leaf_links_once(db, collection_id=c.id)
        totals["sent"] += res.get("sent", 0)
        totals["scanned"] += 1
    return {"ok": True, **totals}

# ---------- light cron (optional) ----------
_CRON_STARTED = False
def _cron_tick_once():
    with SessionLocal() as db:
        cols = db.query(MessageCollection).filter(
            MessageCollection.event_type == EventType.time,
            MessageCollection.scheduled_at.isnot(None),
        ).all()
        for c in cols:
            try:
                if _is_hard_death_finalized_for_owner(db, c.user_id):
                    _send_time_based_leaf_links_once(db, collection_id=c.id)
            except Exception:
                pass

def _cron_loop(interval_seconds: int = 7200):
    _time.sleep(2.0)
    while True:
        start = _time.time()
        try:
            _cron_tick_once()
        except Exception:
            pass
        elapsed = _time.time() - start
        _time.sleep(max(10.0, interval_seconds - elapsed))

def _start_messages_cron_if_needed():
    global _CRON_STARTED
    if _CRON_STARTED:
        return
    _CRON_STARTED = True
    t = threading.Thread(target=_cron_loop, args=(7200,), daemon=True)
    t.start()

_start_messages_cron_if_needed()
