from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Tuple, Dict
from sqlalchemy import or_, func, cast  
from sqlalchemy.dialects.postgresql import JSONB 
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText

from app.database import SessionLocal
from app.dependencies import get_current_user
from app.models.memory import (
    MemoryCollection, MemoryFile, MemoryFileAssignment, MemoryCollectionAssignment
)
from app.models.trustee import Trustee
from app.models.death_approval import DeathApproval
from app.models.enums import (
    EventType, AssignmentRole, ApprovalStatus, ReleaseScope, ReleaseReason, FolderStatus,
    BranchInviteStatus
)
from app.schemas.memory import (
    MemoryCreate, MemoryOut, MemoryFileAttach, MemoryAssignmentIn, MemoryUpdate, TriggerIn,
    MemoryFileOut, MemoryAssignmentOut
)
from fastapi.responses import HTMLResponse

from app.models.release import Release
from app.models.contact import Contact
from app.models.user import User, UserStatus
from app.config import settings
from app.models.death import DeathLock, DeathLockType 
from app.schemas.releases import ReleaseItemOut
from app.dependencies import get_current_admin


from datetime import timezone as _dt_tz

import threading
import time as _time
from contextlib import contextmanager

_CRON_STARTED = False 

router = APIRouter(prefix="/memories", tags=["Memories"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------ Helpers ------------------------

def _ensure_unique_collection_name(db: Session, *, user_id: int, name: str, exclude_id: int | None = None):
    if not (name and str(name).strip()):
        return
    q = db.query(MemoryCollection.id).filter(
        MemoryCollection.user_id == user_id,
        func.lower(MemoryCollection.name) == func.lower(name)
    )
    if exclude_id:
        q = q.filter(MemoryCollection.id != exclude_id)
    if db.query(q.exists()).scalar():
        raise HTTPException(status_code=409, detail="A folder with this name already exists.")
    
def is_death_declared(db: Session, user_id: int) -> bool:
    from app.models.enums import TrusteeStatus
    trustees = db.query(Trustee).filter(
        Trustee.user_id == user_id,
        Trustee.status == TrusteeStatus.accepted
    ).count()
    approvals = db.query(DeathApproval).filter(
        DeathApproval.user_id == user_id,
        DeathApproval.status == ApprovalStatus.approved
    ).count()
    return trustees >= 2 and approvals >= 2

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

def _trigger_present(m: MemoryCollection) -> bool:
    if m.event_type == EventType.time:
        return m.scheduled_at is not None
    if m.event_type == EventType.event:
        return bool(m.event_label and str(m.event_label).strip())
    return False

def _recompute_folder_status(db: Session, collection: MemoryCollection):
    branch_count = db.query(func.count(MemoryCollectionAssignment.id)).filter(
        MemoryCollectionAssignment.collection_id == collection.id,
        MemoryCollectionAssignment.role == AssignmentRole.branch
    ).scalar() or 0
    leaf_count = db.query(func.count(MemoryCollectionAssignment.id)).filter(
        MemoryCollectionAssignment.collection_id == collection.id,
        MemoryCollectionAssignment.role == AssignmentRole.leaf
    ).scalar() or 0

    collection.status = (
        FolderStatus.complete
        if branch_count >= 1 and leaf_count >= 1 and _trigger_present(collection)
        else FolderStatus.incomplete
    )

# ------------------------ Email helpers (branch invites only) ------------------------
def _send_plain_email(to_addr: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_EMAIL
    msg["To"] = to_addr
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
        server.send_message(msg)

def _pb_blurb() -> str:
    return (
        "—\n"
        "Plan Beyond helps families handle important tasks when it matters most.\n"
        "As a Branch, you’re a trusted contact who can act when asked.\n"
        "Your privacy is respected — nothing is shared without the owner’s intent.\n"
    )

def _compose_signup_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/register"

def _compose_otp_start_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/otp/start"

def _compose_profile_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/profile"

def _compose_assignment_accept_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/memories/assignments/a/{assignment_id}/{token}"

def _compose_assignment_reject_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/memories/assignments/r/{assignment_id}/{token}"

def _ensure_assignment_token(db: Session, a: MemoryCollectionAssignment) -> str:
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

def _send_branch_invite_email(db: Session, a: MemoryCollectionAssignment):
    """
    Stage-aware email to the contact for branch assignments:
      - No linked user (and none matches email) -> Register
      - user.otp_verified == False -> OTP flow
      - user.status in (unknown/guest) -> Profile page
      - verified/member -> Accept/Decline links
    """
    if a.role != AssignmentRole.branch:
        return

    contact: Contact = db.query(Contact).filter(Contact.id == a.contact_id).first()
    if not contact or not contact.emails:
        return
    to_email = contact.emails[0]

    linked_user: User | None = None
    if getattr(contact, "linked_user_id", None):
        linked_user = db.query(User).filter(User.id == contact.linked_user_id).first()
    else:
        candidate = db.query(User).filter(User.email == to_email).first()
        if candidate:
            linked_user = candidate

    # default subject/body
    subject = "You were added as a Branch in Plan Beyond"
    body = f"Hello,\n\nYou were added as a Branch in Plan Beyond.\n\n{_pb_blurb()}"

    if not linked_user:
        subject = "You've been invited as a Branch — Create your account"
        body = (
            f"Hello,\n\n"
            f"You were added as a Branch in Plan Beyond. To view and respond to the invitation, please create your account:\n"
            f"{_compose_signup_url()}\n\n"
            f"{_pb_blurb()}"
        )
    elif not linked_user.otp_verified:
        subject = "Verify your account to respond to the Branch invitation"
        body = (
            f"Hello,\n\n"
            f"You were added as a Branch in Plan Beyond. To respond, please verify your account using the OTP flow:\n"
            f"{_compose_otp_start_url()}\n\n"
            f"{_pb_blurb()}"
        )
    elif linked_user.status in (UserStatus.unknown, UserStatus.guest):
        subject = "Complete your profile to respond to the Branch invitation"
        body = (
            f"Hello,\n\n"
            f"You were added as a Branch in Plan Beyond. To respond, please complete your profile verification:\n"
            f"{_compose_profile_url()}\n\n"
            f"{_pb_blurb()}"
        )
    else:
        token = _ensure_assignment_token(db, a)
        accept_link = _compose_assignment_accept_url(a.id, token)
        reject_link = _compose_assignment_reject_url(a.id, token)
        subject = "Branch Invitation — Respond with Accept or Decline"
        body = (
            f"Hello,\n\n"
            f"You were added as a Branch in Plan Beyond. You can respond below:\n\n"
            f"Accept:  {accept_link}\n"
            f"Decline: {reject_link}\n\n"
            f"{_pb_blurb()}"
        )

    _send_plain_email(to_email, subject, body)

# ------------------------ Create ------------------------
@router.post("/", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
def create_memory(payload: MemoryCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ensure_unique_collection_name(db, user_id=user.id, name=payload.name)
    m = MemoryCollection(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        event_type=payload.event_type,
        scheduled_at=payload.scheduled_at if payload.event_type == EventType.time else None,
        event_label=payload.event_label if payload.event_type == EventType.event else None,
        is_armed=False,
    )
    db.add(m)
    db.flush()  # m.id

    # Add assignments; send invite for branches only
    for a in payload.assignments:
        _ensure_user_contact(db, user.id, a.contact_id)
        row = MemoryCollectionAssignment(
            collection_id=m.id,
            contact_id=a.contact_id,
            role=a.role,
        )
        # branch invite metadata
        if a.role == AssignmentRole.branch:
            row.invite_status = BranchInviteStatus.sent
            row.invited_at = datetime.utcnow()
        db.add(row)
        db.flush()
        if a.role == AssignmentRole.branch:
            _send_branch_invite_email(db, row)

    db.flush()
    _recompute_folder_status(db, m)
    db.commit()
    db.refresh(m)

    m = db.query(MemoryCollection)\
        .options(joinedload(MemoryCollection.files), joinedload(MemoryCollection.folder_assignments))\
        .filter(MemoryCollection.id == m.id).first()

    base = MemoryOut.model_validate(m, from_attributes=True)
    return base.model_copy(update={
        "assignments": [MemoryAssignmentOut.model_validate(a, from_attributes=True) for a in m.folder_assignments],
        "files": [MemoryFileOut.model_validate(f, from_attributes=True) for f in m.files],
    })

# ------------------------ List ------------------------
@router.get("/", response_model=List[MemoryOut])
def list_memories(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(MemoryCollection)\
        .options(joinedload(MemoryCollection.files), joinedload(MemoryCollection.folder_assignments))\
        .filter(MemoryCollection.user_id == user.id)\
        .order_by(MemoryCollection.created_at.desc())\
        .all()

    changed = False
    for m in rows:
        old = getattr(m, "status", None)
        _recompute_folder_status(db, m)
        if m.status != old: changed = True
    if changed: db.commit()

    out: List[MemoryOut] = []
    for m in rows:
        base = MemoryOut.model_validate(m, from_attributes=True)
        out.append(base.model_copy(update={
            "assignments": [MemoryAssignmentOut.model_validate(a, from_attributes=True) for a in m.folder_assignments],
            "files": [MemoryFileOut.model_validate(f, from_attributes=True) for f in m.files],
        }))
    return out

# ------------------------ Attach file ------------------------
@router.post("/{memory_id}/files", status_code=status.HTTP_201_CREATED)
def attach_file(
    memory_id: int,
    payload: MemoryFileAttach,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    m = db.query(MemoryCollection).filter(MemoryCollection.id == memory_id, MemoryCollection.user_id == user.id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Folder not found")

    if payload.file_id is not None:
        mf = MemoryFile(collection_id=m.id, file_id=payload.file_id, title=(payload.title or "").strip() or None)
    elif payload.app_url:
        mf = MemoryFile(
            collection_id=m.id,
            title=(payload.title or "").strip() or None,
            app_url=str(payload.app_url),
            mime_type=payload.mime_type,
            size=payload.size,
        )
    else:
        raise HTTPException(status_code=422, detail="Provide file_id or app_url")
    db.add(mf); db.commit(); db.refresh(mf)
    return {"id": mf.id}

# ------------------------ Assign / Unassign (collection) ------------------------
@router.post("/{memory_id}/assign", status_code=status.HTTP_201_CREATED)
def assign_to_folder(memory_id: int, data: MemoryAssignmentIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.query(MemoryCollection).filter(MemoryCollection.id == memory_id, MemoryCollection.user_id == user.id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Folder not found")

    _ensure_user_contact(db, user.id, data.contact_id)

    a = MemoryCollectionAssignment(collection_id=memory_id, contact_id=data.contact_id, role=data.role)
    if data.role == AssignmentRole.branch:
        a.invite_status = BranchInviteStatus.sent
        a.invited_at = datetime.utcnow()
    db.add(a)
    db.flush()

    if data.role == AssignmentRole.branch:
        _send_branch_invite_email(db, a)

    _recompute_folder_status(db, m)
    db.commit()
    db.refresh(a); db.refresh(m)
    return {"id": a.id, "status": m.status}

@router.delete("/{memory_id}/assign/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_from_folder(memory_id: int, assignment_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.query(MemoryCollection).filter(MemoryCollection.id == memory_id, MemoryCollection.user_id == user.id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Folder not found")

    a = db.query(MemoryCollectionAssignment)\
        .filter(MemoryCollectionAssignment.id == assignment_id, MemoryCollectionAssignment.collection_id == memory_id)\
        .first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(a)
    db.flush()
    _recompute_folder_status(db, m)
    db.commit()
    return

# ------------------------ Assign (file) – unchanged, no emails ------------------------
@router.post("/files/{memory_file_id}/assign", status_code=status.HTTP_201_CREATED)
def assign_file(memory_file_id: int, data: MemoryAssignmentIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    mf = db.query(MemoryFile)\
        .join(MemoryCollection, MemoryFile.collection_id == MemoryCollection.id)\
        .filter(MemoryFile.id == memory_file_id, MemoryCollection.user_id == user.id).first()
    if not mf:
        raise HTTPException(status_code=404, detail="Memory file not found")

    _ensure_user_contact(db, user.id, data.contact_id)

    a = MemoryFileAssignment(memory_file_id=memory_file_id, contact_id=data.contact_id, role=data.role)
    db.add(a); db.commit(); db.refresh(a)
    return {"id": a.id}

# ------------------------ Manual trigger (unchanged) ------------------------
@router.post("/files/trigger")
def trigger(data: TriggerIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not is_death_declared(db, user.id):
        raise HTTPException(status_code=400, detail="Death not declared. Trustees must approve first.")
    mf = db.query(MemoryFile)\
        .join(MemoryCollection, MemoryFile.collection_id == MemoryCollection.id)\
        .filter(MemoryFile.id == data.memory_file_id, MemoryCollection.user_id == user.id).first()
    if not mf:
        raise HTTPException(status_code=404, detail="Memory file not found")

    r = Release(user_id=user.id, scope=ReleaseScope.memory_file, scope_id=mf.id, reason=ReleaseReason.manual_trigger)
    db.add(r); db.commit(); db.refresh(r)
    return {"release_id": r.id}

# ------------------------ Read one ------------------------
@router.get("/{memory_id}", response_model=MemoryOut, status_code=status.HTTP_200_OK)
def get_memory(memory_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.query(MemoryCollection)\
        .options(joinedload(MemoryCollection.files), joinedload(MemoryCollection.folder_assignments))\
        .filter(MemoryCollection.id == memory_id, MemoryCollection.user_id == user.id)\
        .first()
    if not m:
        raise HTTPException(status_code=404, detail="Folder not found")

    _recompute_folder_status(db, m)
    db.commit()

    base = MemoryOut.model_validate(m, from_attributes=True)
    return base.model_copy(update={
        "assignments": [MemoryAssignmentOut.model_validate(a, from_attributes=True) for a in m.folder_assignments],
        "files": [MemoryFileOut.model_validate(f, from_attributes=True) for f in m.files],
    })

# ------------------------ Update / Patch (preserve branch invite status) ------------------------
def _reconcile_assignments(
    db: Session,
    m: MemoryCollection,
    desired: List[MemoryAssignmentIn],
):
    existing: List[MemoryCollectionAssignment] = db.query(MemoryCollectionAssignment)\
        .filter(MemoryCollectionAssignment.collection_id == m.id).all()

    existing_map: Dict[Tuple[int, AssignmentRole], MemoryCollectionAssignment] = {
        (e.contact_id, e.role): e for e in existing
    }
    desired_keys = {(d.contact_id, d.role) for d in desired}

    # Delete removed
    for key, row in list(existing_map.items()):
        if key not in desired_keys:
            db.delete(row)

    # Add new
    for d in desired:
        key = (d.contact_id, d.role)
        if key in existing_map:
            continue
        _ensure_user_contact(db, m.user_id, d.contact_id)
        row = MemoryCollectionAssignment(
            collection_id=m.id, contact_id=d.contact_id, role=d.role
        )
        if d.role == AssignmentRole.branch:
            row.invite_status = BranchInviteStatus.sent
            row.invited_at = datetime.utcnow()
        db.add(row)
        db.flush()
        if d.role == AssignmentRole.branch:
            _send_branch_invite_email(db, row)

@router.put("/{memory_id}", response_model=MemoryOut, status_code=status.HTTP_200_OK)
def update_memory(memory_id: int, payload: MemoryUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.query(MemoryCollection)\
        .options(joinedload(MemoryCollection.files), joinedload(MemoryCollection.folder_assignments))\
        .filter(MemoryCollection.id == memory_id, MemoryCollection.user_id == user.id)\
        .first()
    if not m:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if payload.name is not None:
        _ensure_unique_collection_name(db, user_id=user.id, name=payload.name, exclude_id=memory_id)  # ← add
        m.name = payload.name

    if payload.name is not None: m.name = payload.name
    if payload.description is not None: m.description = payload.description

    new_event_type = payload.event_type or m.event_type
    if new_event_type == EventType.time:
        if payload.scheduled_at is not None:
            m.scheduled_at = payload.scheduled_at
        if m.scheduled_at is None:
            raise HTTPException(status_code=422, detail="scheduled_at is required when event_type is 'time'")
        m.event_label = None
    else:
        if payload.event_label is not None:
            m.event_label = payload.event_label.strip() if payload.event_label else None
        # if not (m.event_label and m.event_label.strip()):
        #     raise HTTPException(status_code=422, detail="event_label is required when event_type is 'event'")
        m.scheduled_at = None
    m.event_type = new_event_type

    if payload.assignments is not None:
        _reconcile_assignments(db, m, payload.assignments)

    if payload.files is not None:
        db.query(MemoryFile).filter(MemoryFile.collection_id == m.id).delete(synchronize_session=False)
        for f in payload.files:
            db.add(MemoryFile(
                collection_id=m.id, file_id=None, app_url=f.app_url,
                title=f.title, mime_type=f.mime_type, size=f.size,
            ))

    db.flush()
    _recompute_folder_status(db, m)
    db.commit()

    m = db.query(MemoryCollection)\
        .options(joinedload(MemoryCollection.files), joinedload(MemoryCollection.folder_assignments))\
        .filter(MemoryCollection.id == memory_id).first()

    base = MemoryOut.model_validate(m, from_attributes=True)
    return base.model_copy(update={
        "assignments": [MemoryAssignmentOut.model_validate(a, from_attributes=True) for a in m.folder_assignments],
        "files": [MemoryFileOut.model_validate(f, from_attributes=True) for f in m.files],
    })

@router.patch("/{memory_id}", response_model=MemoryOut, status_code=status.HTTP_200_OK)
def patch_memory(memory_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.query(MemoryCollection)\
        .options(joinedload(MemoryCollection.folder_assignments), joinedload(MemoryCollection.files))\
        .filter(MemoryCollection.id == memory_id, MemoryCollection.user_id == user.id)\
        .first()
    if not m:
        raise HTTPException(status_code=404, detail="Folder not found")

    if "name" in payload:
        _ensure_unique_collection_name(db, user_id=user.id, name=payload["name"], exclude_id=memory_id)  # ← add
        m.name = payload["name"]
    if "description" in payload: m.description = payload["description"]

    if "event_type" in payload:
        try:
            m.event_type = EventType(payload["event_type"])
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid event_type")

    if m.event_type == EventType.time:
        if "scheduled_at" in payload: m.scheduled_at = payload["scheduled_at"]
        if m.scheduled_at is None:
            raise HTTPException(status_code=422, detail="scheduled_at is required when event_type is 'time'")
        m.event_label = None
    else:
        if "event_label" in payload:
            raw = payload["event_label"]
            m.event_label = (str(raw).strip() if raw is not None else None)
        # if not (m.event_label and m.event_label.strip()):
        #     raise HTTPException(status_code=422, detail="event_label is required when event_type is 'event'")
        m.scheduled_at = None

    if "assignments" in payload and payload["assignments"] is not None:
        desired = [MemoryAssignmentIn(**a) for a in payload["assignments"]]
        _reconcile_assignments(db, m, desired)

    db.flush()
    _recompute_folder_status(db, m)
    db.commit()

    m = db.query(MemoryCollection)\
        .options(joinedload(MemoryCollection.files), joinedload(MemoryCollection.folder_assignments))\
        .filter(MemoryCollection.id == m.id).first()

    base = MemoryOut.model_validate(m, from_attributes=True)
    return base.model_copy(update={
        "assignments": [MemoryAssignmentOut.model_validate(a, from_attributes=True) for a in m.folder_assignments],
        "files": [MemoryFileOut.model_validate(f, from_attributes=True) for f in m.files],
    })

# ------------------------ Public accept/decline links for branch ------------------------
@router.get("/assignments/a/{assignment_id}/{token}")
def public_accept_branch(assignment_id: int, token: str, db: Session = Depends(get_db)):
    a = db.query(MemoryCollectionAssignment).filter(MemoryCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.branch:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not a.invite_token or a.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if a.invite_status != BranchInviteStatus.sent:
        raise HTTPException(status_code=409, detail=f"Invite already {a.invite_status.value}")

    a.invite_status = BranchInviteStatus.accepted
    a.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Branch invitation accepted"}

@router.get("/assignments/r/{assignment_id}/{token}")
def public_reject_branch(assignment_id: int, token: str, db: Session = Depends(get_db)):
    a = db.query(MemoryCollectionAssignment).filter(MemoryCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.branch:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not a.invite_token or a.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if a.invite_status != BranchInviteStatus.sent:
        raise HTTPException(status_code=409, detail=f"Invite already {a.invite_status.value}")

    a.invite_status = BranchInviteStatus.declined
    a.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Branch invitation declined"}

# ------------------------ Invitee-side accept/decline (logged in) ------------------------
@router.post("/assignments/accept-as-invitee/{assignment_id}")
def accept_branch_as_invitee(assignment_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    a = db.query(MemoryCollectionAssignment).filter(MemoryCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.branch:
        raise HTTPException(status_code=404, detail="Invite not found")
    contact = db.query(Contact).filter(Contact.id == a.contact_id).first()
    if not contact or contact.linked_user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to act on this invite")

    # Require verified/member to accept (same as trustee)
    if user.status not in (UserStatus.verified, UserStatus.member):
        raise HTTPException(status_code=400, detail="Please verify your profile to accept branch invites")

    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if a.invite_status != BranchInviteStatus.sent:
        raise HTTPException(status_code=409, detail=f"Invite already {a.invite_status.value}")

    a.invite_status = BranchInviteStatus.accepted
    a.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True}

@router.post("/assignments/reject-as-invitee/{assignment_id}")
def reject_branch_as_invitee(assignment_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    a = db.query(MemoryCollectionAssignment).filter(MemoryCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.branch:
        raise HTTPException(status_code=404, detail="Invite not found")
    contact = db.query(Contact).filter(Contact.id == a.contact_id).first()
    if not contact or contact.linked_user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to act on this invite")

    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if a.invite_status != BranchInviteStatus.sent:
        raise HTTPException(status_code=409, detail=f"Invite already {a.invite_status.value}")

    a.invite_status = BranchInviteStatus.declined
    a.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.query(MemoryCollection).filter(
        MemoryCollection.id == memory_id,
        MemoryCollection.user_id == user.id
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Folder not found")
    db.delete(m)
    db.commit()
    return


def _link_contacts_for_user(db: Session, user: User) -> int:
    """
    Link any contacts whose emails/phones match the current user's details.
    Safe no-op if nothing to link. Mirrors the helper in trustees router.
    """
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


@router.get("/branches/todo")
def my_branch_todo(
    db: Session = Depends(get_db),
    user: Depends(get_current_user) = Depends(get_current_user),
):
    # Link any matching contacts for this user (do not fail the request if this errors)
    try:
        _link_contacts_for_user(db, user)
    except Exception:
        pass

    # All contacts that are linked to me
    contact_rows = db.query(Contact.id).filter(Contact.linked_user_id == user.id).all()
    contact_ids = [cid for (cid,) in contact_rows]
    if not contact_ids:
        return []

    # Branch assignments for me, joined to the collection & inviter user
    rows = (
        db.query(MemoryCollectionAssignment, MemoryCollection, User)
        .join(MemoryCollection, MemoryCollectionAssignment.collection_id == MemoryCollection.id)
        .join(User, MemoryCollection.user_id == User.id, isouter=True)
        .filter(
            MemoryCollectionAssignment.contact_id.in_(contact_ids),
            MemoryCollectionAssignment.role == AssignmentRole.branch,
        )
        .all()
    )

    # Collect all collection_ids present in these rows (avoid N+1 checks)
    collection_ids = [coll.id for (_, coll, _) in rows if coll is not None]
    triggered_collection_ids = set()
    release_map = {}

    if collection_ids:
        # Fetch all releases in one go (scope_id == collection_id)
        release_rows = (
            db.query(Release.scope_id, Release.released_at)
            .filter(Release.scope_id.in_(collection_ids))
            .all()
        )

        # Map collection_id -> released_at
        for scope_id, released_at in release_rows:
            release_map[scope_id] = released_at
            triggered_collection_ids.add(scope_id)

    out = []
    for a, coll, inviter in rows:
        status_val = a.invite_status.value if hasattr(a.invite_status, "value") else a.invite_status

        # Determine event_status and release date
        if coll and coll.id in triggered_collection_ids:
            event_status = "triggered"
            event_released_date = release_map.get(coll.id)
        else:
            event_status = "pending triggered"
            event_released_date = None

        out.append({
            "id": a.id,
            "contact_id": a.contact_id,
            "status": status_val,
            "invited_at": a.invited_at,
            "collection_id": coll.id if coll else None,
            "collection_name": coll.name if coll else None,
            "inviter_user_id": inviter.id if inviter else None,
            "inviter_display_name": (
                inviter.display_name
                if inviter and inviter.display_name
                else "A Plan Beyond member"
            ),
            "event_type": (
                coll.event_type.value
                if hasattr(coll.event_type, "value")
                else (coll.event_type if coll else None)
            ),
            "event_label": (coll.event_label if coll else None),
            "scheduled_at": (coll.scheduled_at if coll else None),

            # Added fields
            "event_status": event_status,
            "event_released_date": event_released_date,
        })

    # Sort: pending ("sent") first, then most-recent invited_at
    def _sort_key(item):
        invited_first = 0 if item["status"] == "sent" else 1
        ts = item["invited_at"].timestamp() if item["invited_at"] else 0.0
        return (invited_first, -ts)

    out.sort(key=_sort_key)
    return out








def is_hard_death_finalized_for_owner(db: Session, owner_user_id: int) -> bool:
    """
    True if the owner's passing is finalized by your hard lock, OR by the
    legacy '2 trustees + 2 approvals' rule.
    """
    # Preferred: hard lock (what your /v1/death/hard/active endpoint uses)
    hard = (
        db.query(DeathLock)
        .filter(
            DeathLock.root_user_id == owner_user_id,
            DeathLock.lock == DeathLockType.hard_finalized
        )
        .first()
    )
    if hard:
        return True

    # Fallback to old rule
    return is_death_declared(db, owner_user_id)

# --- Authorization helper: is current user an accepted Branch on this collection? ---
def _is_current_user_accepted_branch_for_collection(db: Session, *, collection_id: int, current_user: User) -> tuple[bool, MemoryCollection | None]:
    # fetch the collection
    coll = db.query(MemoryCollection).filter(MemoryCollection.id == collection_id).first()
    if not coll:
        return (False, None)

    # if owner, it's allowed
    if coll.user_id == current_user.id:
        return (True, coll)

    # else: check if current_user is linked to any Contact that is an accepted Branch assignment on this collection
    contact_ids = [cid for (cid,) in db.query(Contact.id).filter(Contact.linked_user_id == current_user.id).all()]
    if not contact_ids:
        return (False, coll)

    assignment = (
        db.query(MemoryCollectionAssignment)
        .filter(
            MemoryCollectionAssignment.collection_id == collection_id,
            MemoryCollectionAssignment.contact_id.in_(contact_ids),
            MemoryCollectionAssignment.role == AssignmentRole.branch,
            MemoryCollectionAssignment.invite_status == BranchInviteStatus.accepted,
        )
        .first()
    )
    return (assignment is not None, coll)


# ------------------------ LEAF nudging helpers (collection-scoped) ------------------------
def _compose_profile_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/profile"

def _compose_signup_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/register"

def _compose_otp_start_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/otp/start"


# add with the other helpers at the top of memories.py
def _compose_mem_leaf_accept_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/memories/leaves/a/{assignment_id}/{token}"

def _compose_mem_leaf_reject_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/memories/leaves/r/{assignment_id}/{token}"


def _leaf_stage_email_for_contact(linked_user: User | None) -> tuple[str, str]:
    """
    Return (subject, body) for the leaf recipient’s current stage.
    This mirrors your existing style used elsewhere.
    """
    if linked_user is None:
        return (
            "Create your account to receive items assigned to you",
            "Hello,\n\n"
            "You were designated to receive certain items in Plan Beyond. "
            "Please create your account to continue:\n"
            f"{_compose_signup_url()}\n\n— Plan Beyond"
        )

    if not linked_user.otp_verified:
        return (
            "Verify your account (OTP) to receive items assigned to you",
            "Hello,\n\n"
            "You were designated to receive certain items. Please verify your account to continue:\n"
            f"{_compose_otp_start_url()}\n\n— Plan Beyond"
        )

    if linked_user.status in (UserStatus.unknown, UserStatus.guest):
        return (
            "Complete your profile to receive items assigned to you",
            "Hello,\n\n"
            "You were designated to receive certain items. "
            "Please complete your profile verification to continue:\n"
            f"{_compose_profile_url()}\n\n— Plan Beyond"
        )

    # Verified / member
    return (
        "You’re set to receive items assigned to you",
        "Hello,\n\n"
        "A passing has been verified and you’re all set to receive items assigned to you. "
        "We’ll proceed with the release.\n\n— Plan Beyond"
    )


def _send_leaf_nudges_for_collection(db: Session, *, collection_id: int) -> dict:
    """
    For a given MemoryCollection, email all LEAF assignees according to their stage.
    """
    # Fetch collection with owner
    coll = db.query(MemoryCollection).filter(MemoryCollection.id == collection_id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Folder not found")

    # All leaf assignments on this collection
    leaf_asgs = db.query(MemoryCollectionAssignment).filter(
        MemoryCollectionAssignment.collection_id == collection_id,
        MemoryCollectionAssignment.role == AssignmentRole.leaf,
    ).all()

    if not leaf_asgs:
        return {"nudged": 0}

    sent = 0
    for a in leaf_asgs:
        contact: Contact | None = db.query(Contact).filter(Contact.id == a.contact_id).first()
        if not contact or not contact.emails:
            continue

        # Resolve linked user (or by email match)
        linked_user: User | None = None
        if getattr(contact, "linked_user_id", None):
            linked_user = db.query(User).filter(User.id == contact.linked_user_id).first()
        else:
            # opportunistic match by primary email
            primary = contact.emails[0]
            linked_user = db.query(User).filter(User.email == primary).first()

        subject, body = _leaf_stage_email_for_contact(linked_user)
        try:
            _send_plain_email(contact.emails[0], subject, body)
            sent += 1
        except Exception:
            # never block the flow on email errors
            pass

    return {"nudged": sent}

def _send_memories_leaf_emails_for_collection(db: Session, *, collection_id: int) -> dict:
    """
    If the collection is time-based:
      - BEFORE scheduled_at -> only stage nudges (signup/otp/profile/headsup)
      - AT/AFTER scheduled_at -> send accept/decline links, set invite_status=sent if NULL
    Non-time-based -> same as before (send based on auth stage).
    """
    coll = db.query(MemoryCollection).filter(MemoryCollection.id == collection_id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Folder not found")

    # If time-based, delegate to the auto helper which already does the right thing
    if coll.event_type == EventType.time and coll.scheduled_at:
        # Require hard-death finalized for OWNER (same gate everywhere for consistency)
        if not is_hard_death_finalized_for_owner(db, coll.user_id):
            return {"nudged": 0, "skipped": "hard-death not finalized"}

        # Use the existing logic that warms up before time and sends links when due/past
        res = _send_time_based_leaf_emails_auto(db, collection_id=collection_id)
        # Normalize shape: report total emails sent (links or warmups) under 'nudged'
        return {"nudged": res.get("warmups", 0) + res.get("sent", 0), **res}

    # ---- Non-time-based: keep existing behavior ----
    leaf_asgs = db.query(MemoryCollectionAssignment).filter(
        MemoryCollectionAssignment.collection_id == collection_id,
        MemoryCollectionAssignment.role == AssignmentRole.leaf,
    ).all()
    if not leaf_asgs:
        return {"nudged": 0}

    sent = 0
    changed = False

    for a in leaf_asgs:
        contact: Contact | None = db.query(Contact).filter(Contact.id == a.contact_id).first()
        if not contact or not contact.emails or not contact.emails[0]:
            continue
        to_email = contact.emails[0]

        linked_user: User | None = None
        if getattr(contact, "linked_user_id", None):
            linked_user = db.query(User).filter(User.id == contact.linked_user_id).first()
        else:
            linked_user = db.query(User).filter(User.email == to_email).first()

        if not linked_user:
            subject = "Create your account to receive items assigned to you"
            body = (
                "Hello,\n\n"
                "You were designated to receive certain items in Plan Beyond. "
                "Please create your account to continue:\n"
                f"{_compose_signup_url()}\n\n— Plan Beyond"
            )
        elif not linked_user.otp_verified:
            subject = "Verify your account (OTP) to receive items assigned to you"
            body = (
                "Hello,\n\n"
                "You were designated to receive certain items. Please verify your account to continue:\n"
                f"{_compose_otp_start_url()}\n\n— Plan Beyond"
            )
        elif linked_user.status in (UserStatus.unknown, UserStatus.guest):
            subject = "Complete your profile to receive items assigned to you"
            body = (
                "Hello,\n\n"
                "You were designated to receive certain items. "
                "Please complete your profile verification to continue:\n"
                f"{_compose_profile_url()}\n\n— Plan Beyond"
            )
        else:
            if getattr(a, "invite_status", None) is None:
                a.invite_status = BranchInviteStatus.sent
                a.invited_at = datetime.utcnow()
                a.invite_expires_at = datetime.utcnow() + timedelta(days=30)
                changed = True

            token = _ensure_assignment_token(db, a)
            accept_link = _compose_mem_leaf_accept_url(a.id, token)
            reject_link = _compose_mem_leaf_reject_url(a.id, token)
            subject = "Items assigned to you — confirm to proceed"
            body = (
                "Hello,\n\n"
                "A passing has been verified, and items in a folder were assigned to you. "
                "Please choose:\n\n"
                f"Accept:  {accept_link}\n"
                f"Decline: {reject_link}\n\n"
                "— Plan Beyond"
            )

        try:
            _send_plain_email(to_email, subject, body)
            sent += 1
        except Exception:
            pass

    if changed:
        db.commit()

    return {"nudged": sent}


def _now_utc() -> datetime:
    # keep naive UTC comparisons consistent with existing code that uses utcnow()
    return datetime.utcnow()

def _within(dt: datetime | None, *, ahead_hours: int) -> bool:
    """
    True if dt is in (now, now + ahead_hours], used to warm up before the time hits.
    """
    if not dt:
        return False
    now = _now_utc()
    return now < dt <= (now + timedelta(hours=ahead_hours))

def _is_past(dt: datetime | None) -> bool:
    return bool(dt and dt < _now_utc())

def _send_time_based_leaf_emails_auto(
    db: Session,
    *,
    collection_id: int,
) -> dict:
    """
    Time-based memories:
      - NO warmups.
      - At/after scheduled time: send accept/decline links ONCE per assignee.
      - Do not send again if invite_status is sent/accepted/declined.
    """
    coll: MemoryCollection | None = db.query(MemoryCollection).filter(MemoryCollection.id == collection_id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Folder not found")
    if coll.event_type != EventType.time or not coll.scheduled_at:
        return {"ok": True, "warmups": 0, "sent": 0}

    # Require hard-death finalized for OWNER
    if not is_hard_death_finalized_for_owner(db, coll.user_id):
        return {"ok": True, "warmups": 0, "sent": 0, "skipped": "hard-death not finalized"}

    # Only act at/after scheduled time
    now = _now_utc()
    if coll.scheduled_at > now:
        return {"ok": True, "warmups": 0, "sent": 0, "skipped": "not due yet"}

    leaf_asgs: list[MemoryCollectionAssignment] = db.query(MemoryCollectionAssignment).filter(
        MemoryCollectionAssignment.collection_id == collection_id,
        MemoryCollectionAssignment.role == AssignmentRole.leaf,
    ).all()
    if not leaf_asgs:
        return {"ok": True, "warmups": 0, "sent": 0}

    sent = 0
    changed = False

    for a in leaf_asgs:
        # Skip if we already sent (or if recipient already accepted/declined)
        status_lower = (a.invite_status.value if hasattr(a.invite_status, "value") else a.invite_status)
        if status_lower in {"sent", "accepted", "declined"}:
            continue

        contact: Contact | None = db.query(Contact).filter(Contact.id == a.contact_id).first()
        if not contact or not contact.emails or not contact.emails[0]:
            continue
        to_email = contact.emails[0]

        # Resolve linked user (or opportunistic email match)
        linked_user: User | None = None
        if getattr(contact, "linked_user_id", None):
            linked_user = db.query(User).filter(User.id == contact.linked_user_id).first()
        else:
            linked_user = db.query(User).filter(User.email == to_email).first()

        # Require fully verified/member to send links (otherwise do nothing now)
        if not linked_user or not linked_user.otp_verified or linked_user.status in (UserStatus.unknown, UserStatus.guest):
            # You asked for a single send exactly at time; no warmups, so skip.
            continue

        # Mark as sent (if previously NULL) and send links
        if getattr(a, "invite_status", None) is None:
            a.invite_status = BranchInviteStatus.sent
            a.invited_at = now
            a.invite_expires_at = now + timedelta(days=30)
            changed = True

        token = _ensure_assignment_token(db, a)
        accept_link = _compose_mem_leaf_accept_url(a.id, token)
        reject_link = _compose_mem_leaf_reject_url(a.id, token)

        subject = "Items assigned to you — confirm to proceed"
        body = (
            "Hello,\n\n"
            "An item has reached its scheduled time and was assigned to you. "
            "Please choose:\n\n"
            f"Accept:  {accept_link}\n"
            f"Decline: {reject_link}\n\n"
            "— Plan Beyond"
        )
        try:
            _send_plain_email(to_email, subject, body)
            sent += 1
        except Exception:
            # Don't crash; just move on
            pass

    if changed:
        db.commit()

    return {"ok": True, "warmups": 0, "sent": sent, "due": True}



def run_memories_on_hard_finalized(db: Session, owner_user_id: int) -> dict:
    """
    Called once when hard-death is finalized.
    - NO warmups.
    - If any time-based collection is already due/past, send accept/decline ONCE.
    """
    totals = {"nudges": 0, "due_sends": 0, "collections": 0}
    cols = (
        db.query(MemoryCollection)
        .filter(
            MemoryCollection.user_id == owner_user_id,
            MemoryCollection.event_type == EventType.time,
            MemoryCollection.scheduled_at.isnot(None),
        )
        .all()
    )

    now = _now_utc()
    for c in cols:
        totals["collections"] += 1

        # Only send if due/past
        if c.scheduled_at and c.scheduled_at <= now:
            try:
                res = _send_time_based_leaf_emails_auto(db, collection_id=c.id)
                totals["due_sends"] += res.get("sent", 0)
            except Exception:
                pass

    return totals


# ------------------------ NEW: Nudge leaves (collection-scoped) ------------------------
@router.post("/collections/{collection_id}/nudge-leaves")
def nudge_leaves_for_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    allowed, coll = _is_current_user_accepted_branch_for_collection(
        db, collection_id=collection_id, current_user=user
    )
    if not coll:
        raise HTTPException(status_code=404, detail="Folder not found")
    if not allowed:
        raise HTTPException(status_code=403, detail="Not allowed for this folder")

    if not is_hard_death_finalized_for_owner(db, coll.user_id):
        raise HTTPException(status_code=400, detail="Hard-death not finalized. Try again after verification.")

    # Time-based: use the unified helper (warmups before time, links when due/past)
    if coll.event_type == EventType.time and coll.scheduled_at:
        res = _send_memories_leaf_emails_for_collection(db, collection_id=collection_id)
        return {"ok": True, **res}

    # Non-time-based: existing behavior
    result = _send_memories_leaf_emails_for_collection(db, collection_id=collection_id)
    return {"ok": True, **result}



# ------------------------ NEW: Auto-run time-based flow for a collection ------------------------
@router.post("/collections/{collection_id}/auto-time-check")
def auto_time_check_for_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # same authorization model as your other collection-scoped branch actions
    allowed, coll = _is_current_user_accepted_branch_for_collection(
        db, collection_id=collection_id, current_user=user
    )
    if not coll:
        raise HTTPException(status_code=404, detail="Folder not found")
    # Owner is also allowed (parity with your helper’s “owner allowed” behavior)
    if not allowed and coll.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this folder")

    # Require hard-death finalized for OWNER
    if not is_hard_death_finalized_for_owner(db, coll.user_id):
        raise HTTPException(status_code=400, detail="Hard-death not finalized. Try again after verification.")

    # Run auto flow for time-based collections
    result = _send_time_based_leaf_emails_auto(db, collection_id=collection_id)
    return {"ok": True, **result}

# ------------------------ OPTIONAL: Admin-wide scan for time-based memories ------------------------
@router.post("/collections/auto-time-scan")
def auto_time_scan_all(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    # Find time-based collections that have a schedule (simple broad scan).
    cols = db.query(MemoryCollection).filter(
        MemoryCollection.event_type == EventType.time,
        MemoryCollection.scheduled_at.isnot(None),
    ).all()

    totals = {"warmups": 0, "sent": 0, "scanned": 0}
    for c in cols:
        # Respect the same hard-death check here to keep parity.
        if not is_hard_death_finalized_for_owner(db, c.user_id):
            continue
        res = _send_time_based_leaf_emails_auto(db, collection_id=c.id)
        totals["warmups"] += res.get("warmups", 0)
        totals["sent"] += res.get("sent", 0)
        totals["scanned"] += 1

    return {"ok": True, **totals}


@router.post("/collections/{collection_id}/trigger")
def trigger_collection_release(
    collection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    allowed, coll = _is_current_user_accepted_branch_for_collection(db, collection_id=collection_id, current_user=user)
    if not coll:
        raise HTTPException(status_code=404, detail="Folder not found")
    if not allowed:
        raise HTTPException(status_code=403, detail="Not allowed for this folder")

    if not is_hard_death_finalized_for_owner(db, coll.user_id):
        raise HTTPException(status_code=400, detail="Hard-death not finalized. Try again after verification.")

    if coll.event_type == EventType.time and coll.scheduled_at and coll.scheduled_at > _now_utc():
        raise HTTPException(status_code=400, detail="This folder is scheduled; releases and confirmation links will be available at the scheduled time.")

    files = db.query(MemoryFile).filter(MemoryFile.collection_id == collection_id).all()
    if not files:
        return {"ok": True, "released": 0}

    contact = (
        db.query(Contact.id)
        .filter(Contact.linked_user_id == user.id)
        .first()
    )
     
    db.add(Release(
        user_id=coll.user_id,
        scope=ReleaseScope.memory_collection,
        scope_id=collection_id,
        reason=ReleaseReason.manual_trigger,
        triggered_by_contact_id=contact.id
    ))

    db.commit()
    
    # released = 0
    # for mf in files:
    #     db.add(Release(
    #         user_id=coll.user_id,
    #         scope=ReleaseScope.memory_file,
    #         scope_id=mf.id,
    #         reason=ReleaseReason.manual_trigger,
    #     ))
    #     released += 1

    # db.commit()
    return {"ok": True, "released": True}



# ------------------------ Public accept/decline links for MEMORIES LEAF ------------------------
@router.get("/leaves/a/{assignment_id}/{token}")
def public_accept_mem_leaf(assignment_id: int, token: str, db: Session = Depends(get_db)):
    a = db.query(MemoryCollectionAssignment).filter(MemoryCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.leaf:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not a.invite_token or a.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")

    a.invite_status = BranchInviteStatus.accepted
    a.responded_at = datetime.utcnow()
    db.commit()

    return HTMLResponse("<h3>Thanks!</h3><p>You've accepted the assignment.</p>", status_code=200)

@router.get("/leaves/r/{assignment_id}/{token}")
def public_reject_mem_leaf(assignment_id: int, token: str, db: Session = Depends(get_db)):
    a = db.query(MemoryCollectionAssignment).filter(MemoryCollectionAssignment.id == assignment_id).first()
    if not a or a.role != AssignmentRole.leaf:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not a.invite_token or a.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if a.invite_expires_at and a.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")

    a.invite_status = BranchInviteStatus.declined
    a.responded_at = datetime.utcnow()
    db.commit()

    return HTMLResponse("<h3>Done</h3><p>You declined the assignment.</p>", status_code=200)



@router.get("/leaves/todo")
def my_leaf_todo(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Return LEAF assignments for the current user (invitee) across all memory collections.

    ADJUSTMENT:
    - Do NOT auto-promote invite_status from NULL -> 'sent' just because hard-death is finalized.
    - Only promote to 'sent' during the Trigger flow (via /memories/collections/{id}/nudge-leaves).
    - Here, expose public links ONLY if:
        (a) the owner's hard-death is finalized AND
        (b) the assignment already has an invite_token AND
        (c) invite_status is one of sent/accepted/declined (i.e., was nudged/triggered).
    """
    # Opportunistically link Contacts to this user (email/phone match).
    try:
        _link_contacts_for_user(db, user)
    except Exception:
        pass

    # All my linked Contact ids
    contact_ids = [cid for (cid,) in db.query(Contact.id).filter(Contact.linked_user_id == user.id).all()]
    if not contact_ids:
        return []

    # Pull LEAF assignments for me, with the owning collection and inviter (owner).
    rows = (
        db.query(MemoryCollectionAssignment, MemoryCollection, User)
        .join(MemoryCollection, MemoryCollectionAssignment.collection_id == MemoryCollection.id)
        .join(User, MemoryCollection.user_id == User.id, isouter=True)
        .filter(
            MemoryCollectionAssignment.contact_id.in_(contact_ids),
            MemoryCollectionAssignment.role == AssignmentRole.leaf,
        )
        .all()
    )

    out = []
    # NOTE: we no longer mutate/commit anything in this read endpoint
    for a, coll, inviter in rows:
        # status may be None initially (pre-trigger)
        enum_val = getattr(a.invite_status, "value", None)
        raw_status = enum_val if enum_val is not None else a.invite_status  # str | None

        accept_url = None
        reject_url = None

        # Only surface actionable links once the OWNER's hard-death is finalized
        owner_id = inviter.id if inviter else None
        hard_final = (owner_id is not None) and is_hard_death_finalized_for_owner(db, owner_id)

        # Build links ONLY if already nudged/triggered (status in sent/accepted/declined) AND token exists.
        if hard_final and a.invite_token:
            status_lower = (str(raw_status).lower() if raw_status else None)
            if status_lower in {"sent", "accepted", "declined"}:
                accept_url = _compose_mem_leaf_accept_url(a.id, a.invite_token)
                reject_url = _compose_mem_leaf_reject_url(a.id, a.invite_token)

        inviter_display_name = (
            inviter.display_name if (inviter and inviter.display_name) else "A Plan Beyond member"
        )

        past_due_notice = None
        if coll and coll.event_type == EventType.time and coll.scheduled_at:
            if coll.scheduled_at < datetime.utcnow() and not a.invite_status:
                past_due_notice = (
                    f"This was scheduled for {coll.scheduled_at.isoformat()}. "
                    "Sorry for the delay — you can act now once links arrive."
                )

        out.append({
            "id": a.id,
            "contact_id": a.contact_id,
            "status": raw_status,
            "invited_at": a.invited_at,
            "collection_id": coll.id if coll else None,
            "collection_name": coll.name if coll else None,
            "inviter_user_id": inviter.id if inviter else None,
            "inviter_display_name": inviter_display_name,
            "accept_url": accept_url,
            "reject_url": reject_url,
            "event_type": (coll.event_type.value if hasattr(coll.event_type, "value") else (coll.event_type if coll else None)),
            "event_label": (coll.event_label if coll else None),
            "scheduled_at": (coll.scheduled_at if coll else None),

            # <<< ADD THIS LINE >>>
            "past_due_notice": past_due_notice,
        })

    def _sort_key(item):
        invited_first = 0 if item["status"] == "sent" else 1
        ts = item["invited_at"].timestamp() if item["invited_at"] else 0.0
        return (invited_first, -ts)

    out.sort(key=_sort_key)
    return out




def _mf_to_url(db: Session, mf: MemoryFile) -> str | None:
    # If you have a real file server, convert file_id to URL.
    if mf.app_url:
        return mf.app_url
    if getattr(mf, "file_id", None):
        base = settings.BACKEND_URL.rstrip("/")
        return f"{base}/files/{mf.file_id}"
    return None

@router.get("/releases/{owner_user_id}", response_model=List[ReleaseItemOut])
def list_memories_releases_for_invitee(
    owner_user_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Items in the owner's Memory Collections that are assigned to *this* viewer as LEAF.
    We normalize to the same shape as Category releases.
    """
    # my linked contacts
    contact_ids = [cid for (cid,) in db.query(Contact.id).filter(Contact.linked_user_id == user.id).all()]
    if not contact_ids:
        return []

    # Collections owned by owner_user_id where any of my contacts are assigned as LEAF
    asg = (
        db.query(MemoryCollectionAssignment, MemoryCollection)
        .join(MemoryCollection, MemoryCollectionAssignment.collection_id == MemoryCollection.id)
        .filter(
            MemoryCollection.user_id == owner_user_id,
            MemoryCollectionAssignment.contact_id.in_(contact_ids),
            MemoryCollectionAssignment.role == AssignmentRole.leaf,
        )
        .all()
    )
    if not asg:
        return []

    coll_ids = list({c.id for (_, c) in asg if c})
    files = db.query(MemoryFile).filter(MemoryFile.collection_id.in_(coll_ids)).all()
    files_by_coll: Dict[int, List[MemoryFile]] = {}
    for f in files:
        files_by_coll.setdefault(f.collection_id, []).append(f)

    out: List[ReleaseItemOut] = []
    for _, coll in asg:
        if not coll:
            continue
        file_urls = []
        for mf in files_by_coll.get(coll.id, []):
            u = _mf_to_url(db, mf)
            if u:
                file_urls.append(u)

        meta = {
            "category_name": "Memories",
            "section_name": coll.name,
            "notes": coll.description,
            "collection_id": coll.id,
            "answers": {},     # memories has no Q&A; keep shape consistent
            "display": [
                {"label": "Event", "value": (coll.event_label or coll.event_type.value if hasattr(coll.event_type, "value") else coll.event_type), "raw": None},
                {"label": "Scheduled At", "value": (coll.scheduled_at.isoformat() if coll.scheduled_at else None), "raw": None},
            ],
        }

        out.append(ReleaseItemOut(
            id=coll.id,
            title=coll.name or f"Collection #{coll.id}",
            urls=file_urls,
            meta=meta,
            updated_at=(coll.updated_at or coll.created_at).isoformat() if (coll.updated_at or coll.created_at) else None,
        ))

    # newest first
    out.sort(key=lambda x: x.updated_at or "", reverse=True)
    return out



@contextmanager
def _cron_db_session():
    """Short-lived DB session per cron iteration."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _cron_tick_once():
    """
    One pass:
      - Find time-based collections with a schedule.
      - Only process if OWNER is hard-finalized.
      - Call _send_time_based_leaf_emails_auto(...) which now:
          * sends ONCE at/after scheduled time,
          * never resends if status is sent/accepted/declined,
          * does no warmups.
    """
    with _cron_db_session() as db:
        cols = db.query(MemoryCollection).filter(
            MemoryCollection.event_type == EventType.time,
            MemoryCollection.scheduled_at.isnot(None),
        ).all()

        if not cols:
            return

        for c in cols:
            if not is_hard_death_finalized_for_owner(db, c.user_id):
                continue
            try:
                _send_time_based_leaf_emails_auto(db, collection_id=c.id)
            except Exception:
                # Never let the scheduler die
                pass

def _memories_cron_loop(interval_seconds: int = 7200):
    """
    Daemon loop. Ticks every ~interval_seconds (default 2 hours).
    """
    _time.sleep(2.0)  # let the app boot
    while True:
        start = _time.time()
        try:
            _cron_tick_once()
        except Exception:
            pass
        elapsed = _time.time() - start
        wait = max(10.0, interval_seconds - elapsed)
        _time.sleep(wait)

def _start_memories_cron_if_needed():
    global _CRON_STARTED
    if _CRON_STARTED:
        return
    _CRON_STARTED = True
    t = threading.Thread(target=_memories_cron_loop, args=(7200,), daemon=True)  # every 2 hours
    t.start()

# Start the cron when this module is imported by FastAPI
_start_memories_cron_if_needed()
