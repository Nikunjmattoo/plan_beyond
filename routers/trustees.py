from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText

from app.database import SessionLocal
from app.dependencies import get_current_user
from app.config import settings

from app.models.trustee import Trustee
from app.models.death_approval import DeathApproval
from app.models.enums import TrusteeStatus, ApprovalStatus
from app.models.user import User, UserStatus
from app.models.contact import Contact
from sqlalchemy import or_, cast
from sqlalchemy.dialects.postgresql import JSONB

from app.schemas.trustee import TrusteeInvite, TrusteeOut, DeathStatusOut, DeathApproveIn

router = APIRouter(prefix="/trustees", tags=["Trustees"])

# ------------------------ Config ------------------------
MIN_TRUSTEES = 2  

# ------------------------ DB session dep ------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------ Email helpers ------------------------
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
        "As a Trustee, you’re a trusted contact who can act when asked.\n"
        "Your privacy is respected — nothing is shared without the owner’s intent.\n"
    )

def _compose_signup_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/register"

def _compose_guest_verification_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/profile"

# ✅ NEW: direct OTP-start URL (invitee already has an account but hasn't verified OTP)
def _compose_otp_start_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/otp/start"

def _compose_trustee_accept_url(trustee_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/trustees/a/{trustee_id}/{token}"

def _compose_trustee_reject_url(trustee_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/trustees/r/{trustee_id}/{token}"

def _ensure_invite_token(db: Session, t: Trustee) -> str:
    changed = False
    if not getattr(t, "invite_token", None):
        t.invite_token = secrets.token_urlsafe(24)
        changed = True
    if not getattr(t, "invite_expires_at", None):
        t.invite_expires_at = datetime.utcnow() + timedelta(days=30)
        changed = True
    if changed:
        db.add(t)
        db.commit()
        db.refresh(t)
    return t.invite_token

def _send_trustee_invite_email(db: Session, t: Trustee):
    
    contact: Optional[Contact] = db.query(Contact).filter(Contact.id == t.contact_id).first()
    if not contact or not contact.emails:
        return  # nothing to send

    to_email = contact.emails[0]

    # Prefer the explicitly linked user…
    linked_user: Optional[User] = None
    if getattr(contact, "linked_user_id", None):
        linked_user = db.query(User).filter(User.id == contact.linked_user_id).first()
    else:
        # …but if the contact isn't linked yet, try to match by email so we pick the right stage.
        candidate = db.query(User).filter(User.email == to_email).first()
        if candidate:
            linked_user = candidate

    # Compose depending on stage
    if not linked_user:
        # No account we can find → ask to register
        subject = "You've been invited to be a Trustee — Create your account"
        body = (
            f"Hello,\n\n"
            f"You were added as a Trustee in Plan Beyond. To view and respond to the invitation, please create your account:\n"
            f"{_compose_signup_url()}\n\n"
            f"{_pb_blurb()}"
        )

    elif not linked_user.otp_verified:
        # Account exists but OTP not verified yet → nudge to OTP flow
        subject = "Verify your account to respond to the Trustee invitation"
        body = (
            f"Hello,\n\n"
            f"You were added as a Trustee in Plan Beyond. To respond, please verify your account using the OTP flow:\n"
            f"{_compose_otp_start_url()}\n\n"
            f"{_pb_blurb()}"
        )

    elif linked_user.status in (UserStatus.unknown, UserStatus.guest):
        # OTP is verified but profile (KYC) not completed → send to profile page
        subject = "Complete your profile to respond to the Trustee invitation"
        body = (
            f"Hello,\n\n"
            f"You were added as a Trustee in Plan Beyond. To respond, please complete your profile verification:\n"
            f"{_compose_guest_verification_url()}\n\n"
            f"{_pb_blurb()}"
        )

    else:
        # Fully verified (or member) → give Accept / Decline links
        token = _ensure_invite_token(db, t)
        accept_link = _compose_trustee_accept_url(t.id, token)
        reject_link = _compose_trustee_reject_url(t.id, token)
        subject = "Trustee Invitation — Respond with Accept or Decline"
        body = (
            f"Hello,\n\n"
            f"You were added as a Trustee in Plan Beyond. You can respond below:\n\n"
            f"Accept:  {accept_link}\n"
            f"Decline: {reject_link}\n\n"
            f"{_pb_blurb()}"
        )

    _send_plain_email(to_email, subject, body)

# ------------------------ Owner-side routes ------------------------
@router.post("/invite", response_model=TrusteeOut)
def invite_trustee(payload: TrusteeInvite, db: Session = Depends(get_db), user=Depends(get_current_user)):
    existing: Optional[Trustee] = db.query(Trustee).filter(
        Trustee.user_id == user.id,
        Trustee.contact_id == payload.contact_id
    ).first()

    if existing:
        # With hard delete, this will only hit if the row still exists (invited/accepted/rejected/blocked)
        raise HTTPException(status_code=400, detail="Trustee already invited or accepted for this contact.")

    t = Trustee(
        user_id=user.id,
        contact_id=payload.contact_id,
        status=TrusteeStatus.invited,
        is_primary=bool(getattr(payload, "is_primary", False)),
        version=0,
        invited_at=datetime.utcnow(),
        responded_at=None,
    )
    db.add(t)
    try:
        db.commit()
        db.refresh(t)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Trustee already exists for this contact.")

    _ensure_invite_token(db, t)
    _send_trustee_invite_email(db, t)
    return t

@router.get("/", response_model=List[TrusteeOut])
def list_trustees(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Trustee).filter(Trustee.user_id == user.id).all()

@router.post("/accept/{trustee_id}", response_model=TrusteeOut)
def accept_trustee(trustee_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = db.query(Trustee).filter(Trustee.id == trustee_id, Trustee.user_id == user.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trustee not found")
    t.status = TrusteeStatus.accepted
    t.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(t)
    return t

@router.post("/remove/{trustee_id}")
def remove_trustee(trustee_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Hard delete + defensive dependency cleanup
    t = db.query(Trustee).filter(Trustee.id == trustee_id, Trustee.user_id == user.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trustee not found")

    db.query(DeathApproval).filter(
        DeathApproval.user_id == user.id,
        DeathApproval.trustee_id == t.id
    ).delete(synchronize_session=False)

    db.delete(t)
    db.commit()
    return {"ok": True}




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

# ------------------------ Invitee-side routes (To-Do) ------------------------
@router.get("/todo")
def my_trustee_todo(db: Session = Depends(get_db), user: Depends(get_current_user) = Depends(get_current_user)):
    # NEW: make sure any newly-created contacts that match my email/phone are linked to me
    try:
        _link_contacts_for_user(db, user)
    except Exception:
        # Never fail the endpoint because of linking; we'll just show what we can.
        pass

    contact_rows = db.query(Contact.id).filter(Contact.linked_user_id == user.id).all()
    contact_ids = [cid for (cid,) in contact_rows]
    if not contact_ids:
        return []

    rows = (
        db.query(Trustee, User)
        .join(User, Trustee.user_id == User.id, isouter=True)
        .filter(Trustee.contact_id.in_(contact_ids))
        .all()
    )

    out = []
    for t, inviter in rows:
        status_val = t.status.value if hasattr(t.status, "value") else t.status
        out.append({
            "id": t.id,
            "contact_id": t.contact_id,
            "status": status_val,
            "invited_at": t.invited_at,
            "inviter_user_id": inviter.id if inviter else None,
            "inviter_display_name": (inviter.display_name if inviter and inviter.display_name else "A Plan Beyond member"),
        })

    def _sort_key(item):
        invited_first = 0 if item["status"] == "invited" else 1
        ts = item["invited_at"].timestamp() if item["invited_at"] else 0.0
        return (invited_first, -ts)

    out.sort(key=_sort_key)
    return out


@router.post("/accept-as-invitee/{trustee_id}")
def accept_as_invitee(trustee_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = db.query(Trustee).filter(Trustee.id == trustee_id).first()
    if not t:
        # Row removed by owner: treat as revoked
        raise HTTPException(status_code=410, detail="Invite revoked by the user")
    contact = db.query(Contact).filter(Contact.id == t.contact_id).first()
    if not contact or contact.linked_user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to act on this invite")

    # Must be pending and token valid timeframe if present
    if t.invite_expires_at and t.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if (t.status != TrusteeStatus.invited and (getattr(t.status, "value", t.status) != "invited")):
        cur = t.status.value if hasattr(t.status, "value") else t.status
        raise HTTPException(status_code=409, detail=f"Invite already {cur}")

    # Require a real account, but allow accept with verified/member only
    if user.status not in (UserStatus.verified, UserStatus.member):
        raise HTTPException(status_code=400, detail="Please verify your profile to accept trustee invites")

    t.status = TrusteeStatus.accepted
    t.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True}

@router.post("/reject-as-invitee/{trustee_id}")
def reject_as_invitee(trustee_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    
    t = db.query(Trustee).filter(Trustee.id == trustee_id).first()
    if not t:
        # Row removed by owner: treat as revoked
        raise HTTPException(status_code=410, detail="Invite revoked by the user")
    contact = db.query(Contact).filter(Contact.id == t.contact_id).first()
    if not contact or contact.linked_user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to act on this invite")

    # Reject (decline) should be allowed even if the invitee hasn’t verified yet
    if t.invite_expires_at and t.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if (t.status != TrusteeStatus.invited and (getattr(t.status, "value", t.status) != "invited")):
        cur = t.status.value if hasattr(t.status, "value") else t.status
        raise HTTPException(status_code=409, detail=f"Invite already {cur}")

    t.status = TrusteeStatus.rejected
    t.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True}

# ------------------------ Public token endpoints (email links) ------------------------
@router.get("/a/{trustee_id}/{token}")
def public_accept_trustee(trustee_id: int, token: str, db: Session = Depends(get_db)):
    t = db.query(Trustee).filter(Trustee.id == trustee_id).first()
    if not t:
        # Owner removed the invite
        raise HTTPException(status_code=410, detail="Invite revoked by the user")
    if not t.invite_token or t.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if t.invite_expires_at and t.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if t.status != TrusteeStatus.invited:
        cur = t.status.value if hasattr(t.status, "value") else t.status
        raise HTTPException(status_code=409, detail=f"Invite already {cur}")

    t.status = TrusteeStatus.accepted
    t.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Trustee accepted"}

@router.get("/r/{trustee_id}/{token}")
def public_reject_trustee(trustee_id: int, token: str, db: Session = Depends(get_db)):
    t = db.query(Trustee).filter(Trustee.id == trustee_id).first()
    if not t:
        # Owner removed the invite
        raise HTTPException(status_code=410, detail="Invite revoked by the user")
    if not t.invite_token or t.invite_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if t.invite_expires_at and t.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if t.status != TrusteeStatus.invited:
        cur = t.status.value if hasattr(t.status, "value") else t.status
        raise HTTPException(status_code=409, detail=f"Invite already {cur}")

    t.status = TrusteeStatus.rejected
    t.responded_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Trustee declined"}

# ------------------------ Death-approval ------------------------
@router.post("/approve-death")
def approve_death(data: DeathApproveIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = db.query(Trustee).filter(
        Trustee.id == data.trustee_id,
        Trustee.user_id == user.id,
        Trustee.status == TrusteeStatus.accepted
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trustee not found or not accepted")
    existing = db.query(DeathApproval).filter(
        DeathApproval.user_id == user.id,
        DeathApproval.trustee_id == t.id
    ).first()

    if data.action == ApprovalStatus.approved:
        if not existing:
            existing = DeathApproval(user_id=user.id, trustee_id=t.id, status=ApprovalStatus.approved)
            db.add(existing)
        else:
            existing.status = ApprovalStatus.approved
        db.commit()
    else:
        if existing:
            existing.status = ApprovalStatus.retracted
            db.commit()
    return {"ok": True}

@router.get("/death-status", response_model=DeathStatusOut)
def death_status(db: Session = Depends(get_db), user=Depends(get_current_user)):
    trustees = db.query(Trustee).filter(
        Trustee.user_id == user.id,
        Trustee.status == TrusteeStatus.accepted
    ).all()
    approvals = db.query(DeathApproval).filter(
        DeathApproval.user_id == user.id,
        DeathApproval.status == ApprovalStatus.approved
    ).all()
    approved_ids = {a.trustee_id for a in approvals}
    death_declared = len(trustees) >= 2 and len(approved_ids) >= 2
    return DeathStatusOut(death_declared=death_declared, approvals=list(approved_ids))


# ---------------- Invitee-side withdraw (soft end; keep the row visible) ----------------
@router.post("/withdraw-as-invitee/{trustee_id}")
def withdraw_as_invitee(trustee_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
   
    t = db.query(Trustee).filter(Trustee.id == trustee_id).first()
    if not t:
        raise HTTPException(status_code=410, detail="Invite or relationship no longer exists")

    contact = db.query(Contact).filter(Contact.id == t.contact_id).first()
    if not contact or contact.linked_user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to modify this relationship")

    # Was it accepted before? (for UI label)
    prev_status = t.status.value if hasattr(t.status, "value") else str(t.status)

    # Clean approvals, then mark ended
    db.query(DeathApproval).filter(
        DeathApproval.user_id == t.user_id,
        DeathApproval.trustee_id == t.id
    ).delete(synchronize_session=False)

    t.status = TrusteeStatus.rejected
    t.responded_at = datetime.utcnow()
    db.commit()
    return {
        "ok": True,
        "ended": "removed" if prev_status == "accepted" else "declined"
    }