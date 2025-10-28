# app/controller/relationship.py
from __future__ import annotations
from typing import List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, timezone as dt_timezone
import secrets
import smtplib
from email.mime.text import MIMEText
import logging

from app.config import settings
from app.models.relationship import RelationshipRequest, RequestStatus
from app.models.folder import (
    Folder, FolderBranch, FolderTrigger,
    TriggerType, TriggerState, AssignmentStatus,
)
from app.models.contact import Contact
from app.models.user import User
from app.schemas.relationship import (
    RelationshipRequestCreate, RelationshipRequestResponse,
    RelationshipRequestAccept, RelationshipRequestReject, BranchResponsibilityItem,
    BranchTodoItem, BranchTodoSummary, TodoStatus,
)

logger = logging.getLogger(__name__)

# ---------- tiny helpers for enums/None ----------

def _to_str(val: Optional[Any], default: str = "none") -> str:
    """Convert SA/Python Enum or str to plain str; coalesce None to `default`."""
    if val is None:
        return default
    try:
        return val.value  # Enum
    except AttributeError:
        return str(val)

# ---------- Email helpers ----------

def _send_email(to_addr: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_EMAIL
    msg["To"] = to_addr
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
        server.send_message(msg)

def _signup_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/register"

def _verify_profile_url() -> str:
    return f"{settings.APP_URL.rstrip('/')}/profile"

def _accept_url(request_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/rr/a/{request_id}/{token}"

def _reject_url(request_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/rr/r/{request_id}/{token}"

def _pb_blurb() -> str:
    return (
        "—\n"
        "Plan Beyond helps families handle important tasks when it matters most.\n"
        "As a Branch, you’re a trusted contact who can act when asked.\n"
        "Your privacy is respected—nothing is shared without the owner’s intent.\n"
    )

# ---------- Internal helpers ----------

def _assert_folder_owner(db: Session, folder_id: int, owner_user_id: int) -> Folder | None:
    return (
        db.query(Folder)
        .filter(Folder.id == folder_id, Folder.user_id == owner_user_id)
        .first()
    )

def _get_active_branch_row(db: Session, folder_id: int, linked_user_id: int) -> FolderBranch | None:
    return (
        db.query(FolderBranch)
        .join(Contact, Contact.id == FolderBranch.contact_id)
        .filter(
            FolderBranch.folder_id == folder_id,
            FolderBranch.status == AssignmentStatus.active,
            Contact.linked_user_id == linked_user_id,
        )
        .first()
    )

def _send_relationship_email_for_status(
    *,
    contact: Contact,
    request: RelationshipRequest,
    inviter_name: str,
    user_status: str | None,
    otp_verified: bool | None,
) -> None:
    to_email = contact.emails[0] if contact.emails and len(contact.emails) > 0 else None
    if not to_email:
        logger.info(f"Contact {contact.id} has no email; skipping relationship email")
        return

    try:
        if not user_status or user_status == "no_user":
            subject = f"{inviter_name} invited you to join Plan Beyond"
            body = (
                f"Hello,\n\n"
                f"{inviter_name} added you as a Branch in Plan Beyond and would like you to be able to help when needed.\n"
                f"Create your account to get started:\n{_signup_url()}\n\n"
                f"{_pb_blurb()}"
            )
        elif user_status in ("unknown",) or otp_verified is False:
            subject = f"Verify your account to view {inviter_name}'s invitation"
            body = (
                f"Hello,\n\n"
                f"{inviter_name} added you as a Branch in Plan Beyond. Before you can view details or respond,\n"
                f"please verify your account using the OTP we sent to your email/phone.\n\n"
                f"{_pb_blurb()}"
            )
        elif user_status in ("guest",):
            subject = f"Complete your profile to respond to {inviter_name}'s invitation"
            body = (
                f"Hello,\n\n"
                f"{inviter_name} added you as a Branch in Plan Beyond. To respond, please complete your profile verification:\n"
                f"{_verify_profile_url()}\n\n"
                f"{_pb_blurb()}"
            )
        else:  # verified or member
            subject = f"{inviter_name} invited you to be a Branch"
            body = (
                f"Hello,\n\n"
                f"{inviter_name} added you as a Branch in Plan Beyond. You can respond below:\n\n"
                f"Accept:  {_accept_url(request.id, request.token)}\n"
                f"Decline: {_reject_url(request.id, request.token)}\n\n"
                f"{_pb_blurb()}"
            )

        _send_email(to_email, subject, body)
        logger.info(f"Relationship email sent to {to_email} for request {request.id} (status {user_status})")
    except Exception as e:
        logger.error(f"Failed to send relationship email to {to_email}: {e}")

def _find_user_for_contact(db: Session, contact: Contact) -> Optional[User]:
    """
    Resolve a User for a Contact by:
      1) linked_user_id if present
      2) OR match by email OR phone (any one match is enough)
    Returns the first match found.
    """
    # 1) linked_user_id shortcut
    if contact.linked_user_id:
        u = db.query(User).filter(User.id == contact.linked_user_id).first()
        if u:
            return u

    # 2) fallback by email/phone match (OR)
    emails = [e for e in (contact.emails or []) if e]
    phones = [p for p in (contact.phone_numbers or []) if p]

    if not emails and not phones:
        return None

    clause = []
    if emails:
        clause.append(User.email.in_(emails))
    if phones:
        clause.append(User.phone.in_(phones))

    # If both present, OR logic applies (any match is sufficient)
    q = db.query(User)
    if clause:
        q = q.filter(or_(*clause))

    # Any one match is okay; pick the first deterministically
    return q.first()

# ---------- Owner: send or resend requests ----------

def send_relationship_requests(
    db: Session,
    owner_user_id: int,
    folder_id: int,
    creates: list[RelationshipRequestCreate],
) -> list[RelationshipRequest]:
    folder = _assert_folder_owner(db, folder_id, owner_user_id)
    if not folder:
        return []

    inviter = db.query(User).filter(User.id == folder.user_id).first()
    inviter_name = (inviter.display_name or "A Plan Beyond member") if inviter else "A Plan Beyond member"

    branch_rows = db.query(FolderBranch).filter(FolderBranch.folder_id == folder_id).all()
    allowed_contact_ids = {b.contact_id for b in branch_rows}
    create_map = {c.contact_id: c for c in creates if c.contact_id in allowed_contact_ids}

    out: list[RelationshipRequest] = []
    now = datetime.utcnow()

    for contact_id, payload in create_map.items():
        existing_sent = (
            db.query(RelationshipRequest)
            .filter(
                RelationshipRequest.folder_id == folder_id,
                RelationshipRequest.contact_id == contact_id,
                RelationshipRequest.status == RequestStatus.sent,
            )
            .first()
        )
        if existing_sent:
            out.append(existing_sent)
            continue

        token = secrets.token_urlsafe(24)
        expires_at = payload.expires_at or (now + timedelta(days=7))

        rr = RelationshipRequest(
            folder_id=folder_id,
            contact_id=contact_id,
            token=token,
            status=RequestStatus.sent,
            sent_via=payload.sent_via,
            message=payload.message,
            expires_at=expires_at,
        )
        db.add(rr)
        db.flush()  # ensure rr.id for links

        out.append(rr)

        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if contact:
            # 🔁 NEW: resolve user by linked_user_id OR email/phone (OR match)
            user: Optional[User] = _find_user_for_contact(db, contact)

            if not user:
                _send_relationship_email_for_status(
                    contact=contact,
                    request=rr,
                    inviter_name=inviter_name,
                    user_status="no_user",
                    otp_verified=None,
                )
            else:
                status_str = getattr(user.status, "value", str(user.status))
                _send_relationship_email_for_status(
                    contact=contact,
                    request=rr,
                    inviter_name=inviter_name,
                    user_status=status_str,
                    otp_verified=bool(user.otp_verified),
                )

    db.commit()
    for rr in out:
        db.refresh(rr)
    return out

# ---------- Owner: revoke ----------

def revoke_request(db: Session, owner_user_id: int, request_id: int) -> RelationshipRequest | None:
    rr = (
        db.query(RelationshipRequest)
        .join(Folder, Folder.id == RelationshipRequest.folder_id)
        .filter(RelationshipRequest.id == request_id, Folder.user_id == owner_user_id)
        .first()
    )
    if not rr or rr.status != RequestStatus.sent:
        return None
    rr.status = RequestStatus.revoked
    rr.revoked_at = datetime.utcnow()
    db.commit()
    db.refresh(rr)
    return rr

# ---------- Branch: list my requests (auth) ----------

def list_my_requests(db: Session, branch_user_id: int) -> list[RelationshipRequest]:
    return (
        db.query(RelationshipRequest)
        .join(Contact, Contact.id == RelationshipRequest.contact_id)
        .filter(Contact.linked_user_id == branch_user_id)
        .order_by(RelationshipRequest.created_at.desc())
        .all()
    )

# ---------- Branch: accept / reject (auth) ----------

def accept_request(db: Session, branch_user_id: int, request_id: int, body: RelationshipRequestAccept) -> RelationshipRequest | None:
    rr = (
        db.query(RelationshipRequest)
        .join(Contact, Contact.id == RelationshipRequest.contact_id)
        .filter(RelationshipRequest.id == request_id, Contact.linked_user_id == branch_user_id)
        .first()
    )
    if not rr or rr.status != RequestStatus.sent or rr.token != body.token:
        return None
    if rr.expires_at and rr.expires_at < datetime.utcnow():
        rr.status = RequestStatus.expired
        db.commit()
        return None

    fb = (
        db.query(FolderBranch)
        .filter(FolderBranch.folder_id == rr.folder_id, FolderBranch.contact_id == rr.contact_id)
        .first()
    )
    if not fb:
        return None

    fb.status = AssignmentStatus.active
    fb.accepted_at = datetime.utcnow()

    rr.status = RequestStatus.accepted
    rr.accepted_at = datetime.utcnow()

    db.commit()
    db.refresh(rr)
    return rr

def reject_request(db: Session, branch_user_id: int, request_id: int, body: RelationshipRequestReject) -> RelationshipRequest | None:
    rr = (
        db.query(RelationshipRequest)
        .join(Contact, Contact.id == RelationshipRequest.contact_id)
        .filter(RelationshipRequest.id == request_id, Contact.linked_user_id == branch_user_id)
        .first()
    )
    if not rr or rr.status != RequestStatus.sent or rr.token != body.token:
        return None
    if rr.expires_at and rr.expires_at < datetime.utcnow():
        rr.status = RequestStatus.expired
        db.commit()
        return None

    fb = (
        db.query(FolderBranch)
        .filter(FolderBranch.folder_id == rr.folder_id, FolderBranch.contact_id == rr.contact_id)
        .first()
    )
    if fb:
        fb.status = AssignmentStatus.declined

    rr.status = RequestStatus.rejected
    rr.rejected_at = datetime.utcnow()
    db.commit()
    db.refresh(rr)
    return rr

# ---------- PUBLIC helpers ----------

def public_request_status(db: Session, request_id: int, token: str) -> str:
    """
    Returns one of:
      'sent', 'revoked', 'expired', 'already_accepted', 'already_rejected', 'invalid'
    """
    rr = db.query(RelationshipRequest).filter(RelationshipRequest.id == request_id).first()
    if not rr or rr.token != token:
        return "invalid"

    if rr.expires_at and rr.expires_at < datetime.utcnow():
        if rr.status == RequestStatus.sent:
            rr.status = RequestStatus.expired
            db.commit()
        return "expired"

    if rr.status == RequestStatus.sent:
        return "sent"
    if rr.status == RequestStatus.revoked:
        return "revoked"
    if rr.status == RequestStatus.accepted:
        return "already_accepted"
    if rr.status == RequestStatus.rejected:
        return "already_rejected"
    if rr.status == RequestStatus.expired:
        return "expired"

    return "invalid"

def _validate_rr_for_token_flow(db: Session, request_id: int, token: str) -> RelationshipRequest | None:
    rr = db.query(RelationshipRequest).filter(RelationshipRequest.id == request_id).first()
    if not rr or rr.status != RequestStatus.sent or rr.token != token:
        return None
    if rr.expires_at and rr.expires_at < datetime.utcnow():
        rr.status = RequestStatus.expired
        db.commit()
        return None
    return rr

def accept_request_by_token(db: Session, request_id: int, token: str) -> bool:
    rr = _validate_rr_for_token_flow(db, request_id, token)
    if not rr:
        return False

    fb = (
        db.query(FolderBranch)
        .filter(FolderBranch.folder_id == rr.folder_id, FolderBranch.contact_id == rr.contact_id)
        .first()
    )
    if not fb:
        return False

    fb.status = AssignmentStatus.active
    fb.accepted_at = datetime.utcnow()

    rr.status = RequestStatus.accepted
    rr.accepted_at = datetime.utcnow()

    db.commit()
    return True

def reject_request_by_token(db: Session, request_id: int, token: str) -> bool:
    rr = _validate_rr_for_token_flow(db, request_id, token)
    if not rr:
        return False

    fb = (
        db.query(FolderBranch)
        .filter(FolderBranch.folder_id == rr.folder_id, FolderBranch.contact_id == rr.contact_id)
        .first()
    )
    if fb:
        fb.status = AssignmentStatus.declined

    rr.status = RequestStatus.rejected
    rr.rejected_at = datetime.utcnow()

    db.commit()
    return True

# ---------- Branch: responsibilities ----------

def list_branch_responsibilities(db: Session, branch_user_id: int) -> list[BranchResponsibilityItem]:
    from app.models.user import User as UserModel
    q = (
        db.query(
            Folder.id.label("folder_id"),
            Folder.name.label("folder_name"),
            UserModel.display_name.label("root_user_display_name"),
            FolderTrigger.type.label("trigger_type"),
            FolderTrigger.state.label("trigger_state"),
            FolderTrigger.time_at.label("time_at"),
            FolderTrigger.timezone.label("timezone"),
            FolderTrigger.event_label.label("event_label"),
        )
        .join(FolderBranch, FolderBranch.folder_id == Folder.id)
        .join(Contact, Contact.id == FolderBranch.contact_id)
        .join(UserModel, UserModel.id == Folder.user_id)
        .outerjoin(FolderTrigger, FolderTrigger.folder_id == Folder.id)
        .filter(
            Contact.linked_user_id == branch_user_id,
            FolderBranch.status == AssignmentStatus.active,
        )
        .order_by(Folder.id.desc())
    )

    items: list[BranchResponsibilityItem] = []
    for r in q.all():
        # booleans for actionability based on actual enums (may be None)
        is_event = (r.trigger_type == TriggerType.event_based)
        is_sched = (r.trigger_type == TriggerType.time_based)
        is_actionable = is_event and (r.trigger_state in (TriggerState.configured, TriggerState.scheduled))

        items.append(
            BranchResponsibilityItem(
                folder_id=r.folder_id,
                folder_name=r.folder_name,
                root_user_display_name=r.root_user_display_name or "Root",
                trigger_type=_to_str(r.trigger_type, "none"),
                trigger_state=_to_str(r.trigger_state, "none"),
                time_at=r.time_at if is_sched else None,
                timezone=r.timezone if is_sched else None,
                event_label=r.event_label if is_event else None,
                is_actionable=bool(is_actionable),
            )
        )
    return items

# ---------- Branch: mark event happened ----------

def mark_trigger_happened(db: Session, branch_user_id: int, folder_id: int) -> bool:
    fb = _get_active_branch_row(db, folder_id, branch_user_id)
    if not fb:
        return False

    trig = db.query(FolderTrigger).filter(FolderTrigger.folder_id == folder_id).first()
    if not trig or trig.type != TriggerType.event_based:
        return False
    if trig.state in (TriggerState.fired, TriggerState.cancelled):
        return False

    trig.state = TriggerState.fired
    db.commit()
    return True

# ---------- Branch: to-dos (safe against NULL triggers) ----------

def list_branch_todos(
    db: Session,
    branch_user_id: int,
) -> List[BranchTodoItem]:
    """
    Consolidated To-Do list for a Branch:
      - Event-based triggers → actionable (CTA = 'Mark happened') until fired/cancelled
      - Time-based triggers → informational (visibility / audit)
      - No trigger → informational (not actionable)
    """
    from app.models.user import User as UserModel

    q = (
        db.query(
            Folder.id.label("folder_id"),
            Folder.name.label("folder_name"),
            UserModel.display_name.label("root_user_display_name"),
            FolderTrigger.id.label("trigger_id"),
            FolderTrigger.type.label("trigger_type"),
            FolderTrigger.state.label("trigger_state"),
            FolderTrigger.time_at.label("time_at"),
            FolderTrigger.timezone.label("timezone"),
            FolderTrigger.event_label.label("event_label"),
        )
        .join(FolderBranch, FolderBranch.folder_id == Folder.id)
        .join(Contact, Contact.id == FolderBranch.contact_id)
        .join(UserModel, UserModel.id == Folder.user_id)
        .outerjoin(FolderTrigger, FolderTrigger.folder_id == Folder.id)
        .filter(
            Contact.linked_user_id == branch_user_id,
            FolderBranch.status == AssignmentStatus.active,
        )
        .order_by(Folder.id.desc())
    )

    items: List[BranchTodoItem] = []
    for r in q.all():
        is_event = (r.trigger_type == TriggerType.event_based)
        is_sched = (r.trigger_type == TriggerType.time_based)

        # Derive status
        if is_event:
            if r.trigger_state in (TriggerState.configured, TriggerState.scheduled):
                status = TodoStatus.actionable
            elif r.trigger_state == TriggerState.fired:
                status = TodoStatus.done
            elif r.trigger_state == TriggerState.cancelled:
                status = TodoStatus.cancelled
            else:
                status = TodoStatus.informational  # unexpected/missing state
        elif is_sched:
            if r.trigger_state == TriggerState.fired:
                status = TodoStatus.done
            elif r.trigger_state == TriggerState.cancelled:
                status = TodoStatus.cancelled
            else:
                status = TodoStatus.informational
        else:
            # No trigger configured
            status = TodoStatus.informational

        can_mark = is_event and (status == TodoStatus.actionable)

        title = (
            (r.event_label or "Event") if is_event
            else ("Scheduled release" if is_sched else "No trigger configured")
        )
        subtitle = f"{(r.root_user_display_name or 'Root')} • {(r.folder_name or 'Folder')}"

        todo_id = f"folder:{r.folder_id}-trigger:{r.trigger_id or 'none'}"

        items.append(
            BranchTodoItem(
                todo_id=todo_id,
                folder_id=r.folder_id,
                folder_name=r.folder_name or "",
                root_user_display_name=r.root_user_display_name or "Root",
                trigger_type=_to_str(r.trigger_type, "none"),
                trigger_state=_to_str(r.trigger_state, "none"),
                title=title,
                subtitle=subtitle,
                next_at=r.time_at if is_sched else None,
                timezone=r.timezone if is_sched else None,
                status=status,
                cta_label="Mark happened" if can_mark else None,
                can_mark_happened=bool(can_mark),
            )
        )
    return items

def list_branch_todos_summary(
    db: Session,
    branch_user_id: int,
) -> BranchTodoSummary:
    items = list_branch_todos(db, branch_user_id=branch_user_id)
    actionable = sum(1 for i in items if i.status == TodoStatus.actionable)
    informational = sum(1 for i in items if i.status == TodoStatus.informational)
    done = sum(1 for i in items if i.status == TodoStatus.done)
    cancelled = sum(1 for i in items if i.status == TodoStatus.cancelled)
    return BranchTodoSummary(
        actionable_count=actionable,
        informational_count=informational,
        done_count=done,
        cancelled_count=cancelled,
    )
