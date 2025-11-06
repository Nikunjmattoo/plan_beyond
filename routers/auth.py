from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal

from sqlalchemy import or_, cast
from sqlalchemy.dialects.postgresql import JSONB

from app.schemas.user import (
    UserCreate, UserProfileResponse, LoginCredentials, OTPStart, OTPVerify,
    VerificationSubmit, IdentityVerification,
    AdminOTPStart, AdminOTPVerify
)
from app.controller.user import (
    get_user_by_display_name,
    get_user_by_email,
    get_user_by_phone,
    get_user_by_phone_and_cc,  
    create_user,
    update_user,
)

from app.controller.verification import submit_verification
from app.core.security import verify_password, hash_password
from app.core.jwt import create_access_token
from app.config import settings
from app.models import user as models
from app.models.verification import UserStatusHistory
from app.models.admin import Admin
from app.dependencies import get_current_user
from app.controller.folder import create_default_folders_for_user
from app.models.relationship import RelationshipRequest, RequestStatus
from app.models.contact import Contact
from app.models.folder import Folder
from app.models.trustee import Trustee
from app.models.enums import TrusteeStatus  # <-- needed for filtering invites
import secrets
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import logging
import re

from app.models.memory import MemoryCollection, MemoryCollectionAssignment
from app.models.message import MessageCollection, MessageCollectionAssignment
from app.models.enums import EventType, AssignmentRole, BranchInviteStatus
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from app.models.category import CategoryProgressLeaf, ProgressLeafStatus
from app.models.death import DeathLock, DeathLockType
from app.controller.death import (
    _gen_quick_token_leaf,
    _compose_leaf_accept_url,
    _compose_leaf_reject_url,
)
# NEW imports for bulk token helpers
import hmac, hashlib, json, time as _time, base64
from app.models.enums import EventType  # ← add

from twilio.rest import Client
import secrets

def generate_numeric_otp(length: int = 6) -> str:
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))



account_sid = "AC886d5ba3138a1ed761cd4af8d4be67fe"
auth_token  = "126aa9bdd9aa36946674bee493ded6e6"
client = Client(account_sid, auth_token)

def send_otp_via_twilio(to_phone, message_body, from_phone='+14786666810'):
    msg = client.messages.create(
        body=message_body,
        from_=from_phone,
        to=to_phone
    )
    return msg.sid, msg.status

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------ Email/Link helpers ------------------------------

def _send_plain_email(to_addr: str, subject: str, body: str):
    """Send a plain text email via Gmail SMTP (same setup you already use)."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_EMAIL
    msg["To"] = to_addr
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
        server.send_message(msg)

def _compose_guest_verification_url() -> str:
    base = settings.APP_URL.rstrip("/")
    return f"{base}/profile"

def _compose_signup_url() -> str:
    base = settings.APP_URL.rstrip("/")
    return f"{base}/register"

def _compose_otp_start_url() -> str:
    return f"{settings.APP_URL}/otp/start"

# ✅ Short public backend URLs (no login required)
def _compose_accept_url(request_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/rr/a/{request_id}/{token}"

def _compose_reject_url(request_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/rr/r/{request_id}/{token}"

def _compose_trustee_accept_url(trustee_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/trustees/a/{trustee_id}/{token}"

def _compose_trustee_reject_url(trustee_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/trustees/r/{trustee_id}/{token}"




# ========= BULK leaf link helpers (scoped to (root_user_id, contact_id)) =========

def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def _gen_quick_token_leaf_bulk(root_user_id: int, contact_id: int, decision: str) -> str:
    """
    decision: "accept_all" | "reject_all"
    """
    secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
    payload = {"rid": int(root_user_id), "cid": int(contact_id), "dec": str(decision)}
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(secret, data, hashlib.sha256).digest()
    return f"{_b64url(data)}.{_b64url(sig)}"


def _compose_leaf_bulk_accept_url(root_user_id: int, contact_id: int, token: str) -> str:
    # Same public router shape you added in categories.py -> public_leaf_router
    return f"{settings.BACKEND_URL}/catalog/leaves/a/bulk/{root_user_id}/{contact_id}/{token}"

def _compose_leaf_bulk_reject_url(root_user_id: int, contact_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/catalog/leaves/r/bulk/{root_user_id}/{contact_id}/{token}"


def _pb_blurb() -> str:
    return (
        "—\n"
        "Plan Beyond helps families handle important tasks when it matters most.\n"
        "As a Branch, you’re a trusted contact who can act when asked.\n"
        "Your privacy is respected — nothing is shared without the owner’s intent.\n"
    )

# ------------------------------ Contact linking ------------------------------

def _link_user_to_matching_contacts(db: Session, user: models.User) -> list[Contact]:
    filters = []
    if user.email:
        filters.append(cast(Contact.emails, JSONB).contains([user.email]))
    if user.phone:
        filters.append(cast(Contact.phone_numbers, JSONB).contains([user.country_code + user.phone]))

    if not filters:
        return []

    contacts = db.query(Contact).filter(or_(*filters)).all()
    changed = False
    for c in contacts:
        if not getattr(c, "linked_user_id", None):
            c.linked_user_id = user.id
            changed = True
    if changed:
        db.commit()
        for c in contacts:
            db.refresh(c)
    return contacts

def _pending_requests_for_contact(db: Session, contact_id: int) -> list[RelationshipRequest]:
    return (
        db.query(RelationshipRequest)
        .filter(
            RelationshipRequest.contact_id == contact_id,
            RelationshipRequest.status == RequestStatus.sent,
            RelationshipRequest.expires_at > datetime.utcnow()
        )
        .all()
    )

# ------------------------------ Branch (relationship) follow-ups ------------------------------

def _send_followup_mails_for_user_status(
    db: Session,
    user: models.User,
    contacts: list[Contact],
):
    for contact in contacts:
        to_email = contact.emails[0] if contact.emails and len(contact.emails) > 0 else None
        if not to_email:
            logger.info(f"Contact {contact.id} has no email; skipping notification.")
            continue

        reqs = _pending_requests_for_contact(db, contact.id)
        if not reqs:
            continue

        for rr in reqs:
            folder = db.query(Folder).filter(Folder.id == rr.folder_id).first()
            if not folder:
                continue

            inviter = db.query(models.User).filter(models.User.id == folder.user_id).first()
            inviter_name = (inviter.display_name or "A Plan Beyond member") if inviter else "A Plan Beyond member"

            if (not user.otp_verified) or (user.status == models.UserStatus.unknown):
                subject = f"Verify your account to view {inviter_name}'s invitation"
                body = (
                    f"Hello,\n\n"
                    f"{inviter_name} added you as a Branch in Plan Beyond. Please verify your account using the OTP we sent to your email/phone.\n"
                    f"If you didn’t request this, you can safely ignore the OTP.\n\n"
                    f"{_pb_blurb()}"
                )
            elif user.status == models.UserStatus.guest:
                subject = f"Complete your profile to respond to {inviter_name}'s invitation"
                body = (
                    f"Hello,\n\n"
                    f"{inviter_name} added you as a Branch in Plan Beyond. To respond, please complete your profile verification:\n"
                    f"{_compose_guest_verification_url()}\n\n"
                    f"{_pb_blurb()}"
                )
            else:
                subject = f"{inviter_name} invited you to be a Branch"
                body = (
                    f"Hello,\n\n"
                    f"{inviter_name} added you as a Branch in Plan Beyond. You can respond below:\n\n"
                    f"Accept:  {_compose_accept_url(rr.id, rr.token)}\n"
                    f"Decline: {_compose_reject_url(rr.id, rr.token)}\n\n"
                    f"{_pb_blurb()}"
                )

            try:
                _send_plain_email(to_email, subject, body)
                logger.info(f"Follow-up sent to {to_email} for request {rr.id} (stage: {user.status.name})")
            except Exception as e:
                logger.error(f"Failed sending follow-up to {to_email} for request {rr.id}: {e}")

def send_otp(contact: str, channel: str, otp: str):
    logger.info(f"Attempting to send OTP to {contact} via {channel}")
    if channel == "email":
        msg = MIMEText(f"Your OTP is {otp}")
        msg["Subject"] = "Plan Beyond OTP Verification"
        msg["From"] = settings.SMTP_EMAIL
        msg["To"] = contact
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
                server.send_message(msg)
                logger.info(f"OTP sent successfully to {contact}")
        except Exception as e:
            logger.error(f"Failed to send OTP to {contact}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")
    elif channel in ["sms", "whatsapp"]:
        logger.info(f"[{channel.upper()} Placeholder] Sending OTP to {contact}: Your OTP is {otp}")
        print(f"[{channel.upper()} Placeholder] Sending OTP to {contact}: Your OTP is {otp}")  # noqa
    else:
        logger.error(f"Invalid communication channel: {channel}")
        raise HTTPException(status_code=400, detail="Invalid communication channel")

def send_relationship_emails_for_pending_requests(db: Session, user: models.User):
    try:
        contacts = _link_user_to_matching_contacts(db, user)
        if not contacts:
            logger.info(f"No matching contacts to link for user {user.id}")
            return
        _send_followup_mails_for_user_status(db, user, contacts)
    except Exception as e:
        logger.error(f"Error sending relationship follow-ups for user {user.id}: {str(e)}")
        pass

# ------------------------------ Trustee follow-ups ------------------------------

def _ensure_trustee_token(db: Session, t: Trustee) -> str:
    token = getattr(t, "invite_token", None)
    if token:
        return token
    if hasattr(t, "invite_token"):
        token = secrets.token_hex(16)
        t.invite_token = token
        db.add(t)
        db.commit()
        db.refresh(t)
        return token
    return ""

def send_trustee_emails_for_pending_invites(db: Session, user: models.User):
    try:
        contacts = _link_user_to_matching_contacts(db, user)
        if not contacts:
            return

        for contact in contacts:
            if not contact.emails or len(contact.emails) == 0:
                continue
            primary_email = contact.emails[0]

            invites = (
                db.query(Trustee)
                .filter(
                    Trustee.contact_id == contact.id,
                    Trustee.status == TrusteeStatus.invited
                )
                .all()
            )
            if not invites:
                continue

            for t in invites:
                inviter = db.query(models.User).filter(models.User.id == t.user_id).first()
                inviter_name = (inviter.display_name or "A Plan Beyond member") if inviter else "A Plan Beyond member"

                if not user.otp_verified:
                    subject = f"Verify your account to view {inviter_name}'s trustee invitation"
                    body = (
                        f"Hello,\n\n"
                        f"{inviter_name} added you as a Trustee in Plan Beyond. To view and respond to the invite, please verify your account using the OTP flow:\n"
                        f"{_compose_otp_start_url()}\n\n"
                        f"{_pb_blurb()}"
                    )

                elif user.status in (models.UserStatus.unknown, models.UserStatus.guest):
                    subject = f"Complete your profile to respond to {inviter_name}'s trustee invitation"
                    body = (
                        f"Hello,\n\n"
                        f"{inviter_name} added you as a Trustee in Plan Beyond. To respond, please complete your profile verification:\n"
                        f"{_compose_guest_verification_url()}\n\n"
                        f"{_pb_blurb()}"
                    )

                else:
                    token = _ensure_trustee_token(db, t)
                    accept_link = _compose_trustee_accept_url(t.id, token)
                    reject_link = _compose_trustee_reject_url(t.id, token)
                    subject = f"{inviter_name} invited you to be a Trustee"
                    body = (
                        f"Hello,\n\n"
                        f"{inviter_name} added you as a Trustee in Plan Beyond. You can respond below:\n\n"
                        f"Accept:  {accept_link}\n"
                        f"Decline: {reject_link}\n\n"
                        f"{_pb_blurb()}"
                    )

                _send_plain_email(primary_email, subject, body)
                logger.info(f"Trustee follow-up sent to {primary_email} for invite {t.id} (stage: {'OTP' if not user.otp_verified else user.status.name})")
    except Exception as e:
        logger.error(f"Error sending trustee follow-ups for user {user.id}: {str(e)}")
        pass


# ------------------------------ Auth flows ------------------------------

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Signup attempt for display_name: {user.display_name}")

    if user.email and user.email.strip() and get_user_by_email(db, user.email.strip()):
        raise HTTPException(status_code=400, detail="Email already registered")
    if user.phone and user.phone.strip() and get_user_by_phone(db, user.phone.strip()):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    db_user = create_user(db, user)
    try:
        created = create_default_folders_for_user(db, db_user.id)
        logger.info(f"Default folders created for user {db_user.id}: {[f.name for f in created]}")
    except Exception as e:
        logger.error(f"Failed to create default folders for user {db_user.id}: {e}")

    if not user.communication_channel:
        raise HTTPException(status_code=400, detail="communication_channel is required to start OTP")
    channel = user.communication_channel.value
    destination = db_user.email if channel == "email" else db_user.phone
    if not destination:
        raise HTTPException(status_code=400, detail=f"{channel} contact not provided")

    otp = generate_numeric_otp(6)
    db_user.otp = otp
    db_user.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    db_user.otp_verified = False
    db.commit()
    db.refresh(db_user)
    send_otp(destination, channel, otp)

    # Link contacts and nudge to OTP verify (if any pending relationship requests exist)
    send_relationship_emails_for_pending_requests(db, db_user)
    # Also send trustee stage emails (unknown stage -> sign up)
    send_trustee_emails_for_pending_invites(db, db_user)
    send_memory_branch_emails_for_pending_invites(db, db_user)
    send_leaf_stage_emails_for_user(db, db_user)
    send_memories_leaf_emails_for_user(db, db_user)
    send_message_branch_emails_for_pending_invites(db, db_user)
    send_messages_leaf_emails_for_user(db, db_user)

    # Log OTP to terminal for debugging
    logger.info(f"User created with ID: {db_user.id}, OTP: {otp} sent to {destination}")
    
    # Return OTP in response (for dev/testing; remove in prod for security)
    return {"detail": "User created, OTP sent", "user_id": db_user.id, "otp": otp}

@router.post("/otp/start")
def otp_start(data: OTPStart, db: Session = Depends(get_db)):
    email = (data.email or "").strip() or None
    phone = (data.phone or "").strip() or None         # EXPECTS NATIONAL number (no +)
    country_code = (data.country_code or "").strip() or None
    if country_code and not country_code.startswith("+"):
        country_code = f"+{country_code}"

    channel = data.communication_channel.value

    # Validate inputs by channel
    if channel == "email" and not email:
        raise HTTPException(status_code=400, detail="Email required for email channel")
    if channel in ["sms", "whatsapp"] and not phone:
        raise HTTPException(status_code=400, detail="Phone required for SMS/WhatsApp channel")

    # Find the user
    if channel == "email":
        user = get_user_by_email(db, email)
    else:
        # Strict match: (phone + country_code) when cc provided, otherwise fallback to phone only
        user = get_user_by_phone_and_cc(db, phone, country_code) if country_code else get_user_by_phone(db, phone)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create OTP
    otp = generate_numeric_otp(6)
    user.otp = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    user.otp_verified = False
    db.commit()
    db.refresh(user)
    
    if channel == "email":
        destination = email
    else:
        # Prefer provided cc; else fall back to user's stored cc
        cc = country_code or (user.country_code or "")
        if cc and not cc.startswith("+"):
            cc = f"+{cc}"
        destination = f"{cc}{phone}" if cc else phone

    send_otp(destination, channel, otp)

    logger.info(f"OTP: {otp} sent to {destination} for user ID: {user.id}")
    # NOTE: `otp` returned only for dev/testing; remove in prod
    return {"detail": "OTP sent", "user_id": user.id, "success": True, "otp": otp}



@router.post("/verify-otp")
def otp_verify(data: OTPVerify, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.otp or user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired or not found")
    if user.otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    from_status = user.status  # capture for history
    user.otp_verified = True
    user.otp = None
    user.otp_expires_at = None
    if user.status == models.UserStatus.unknown:
        db.add(UserStatusHistory(
            user_id=user.id,
            from_status=from_status.value,
            to_status=models.UserStatus.guest.value
        ))
        user.status = models.UserStatus.verified
    db.commit()
    db.refresh(user)

    # Advance emails for both systems at "guest" stage
    send_relationship_emails_for_pending_requests(db, user)
    send_trustee_emails_for_pending_invites(db, user)
    send_memory_branch_emails_for_pending_invites(db, user)
    send_leaf_stage_emails_for_user(db, user)
    send_memories_leaf_emails_for_user(db, user)
    send_message_branch_emails_for_pending_invites(db, user)
    send_messages_leaf_emails_for_user(db, user)

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "userId": user.id, "success": True}

@router.post("/login")
def login(credentials: LoginCredentials, db: Session = Depends(get_db)):
    identifier = (credentials.identifier or "").strip()
    password = credentials.password
    logger.info(f"Login attempt with identifier: {identifier}")

    if not identifier:
        raise HTTPException(status_code=400, detail="Identifier is required")

    user = None
    channel = None
    if "@" in identifier:
        user = get_user_by_email(db, identifier)
        channel = "email"
    elif identifier.isdigit() or identifier.startswith("+"):
        user = get_user_by_phone(db, identifier)
        channel = "sms"
    else:
        user = get_user_by_display_name(db, identifier)
        channel = (user.communication_channel if user and user.communication_channel in ["email", "sms", "whatsapp"] else
                   ("email" if user and user.email else "sms"))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if password:
        if not user.password or not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid password")
        token = create_access_token({"sub": str(user.id)})
        logger.info(f"Password login successful for user ID: {user.id}")
        return {"access_token": token, "token_type": "bearer", "userId": user.id, "success": True}

    destination = user.email if channel == "email" else user.phone
    if not destination:
        raise HTTPException(status_code=400, detail=f"{channel} contact not provided")

    otp = generate_numeric_otp(6)
    user.otp = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    user.otp_verified = False
    db.commit()
    db.refresh(user)

    send_otp(destination, channel, otp)
    logger.info(f"OTP generated and sent to {destination} for user ID: {user.id}")
    return {"detail": "OTP sent", "user_id": user.id, "success": True}

@router.post("/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    identifier = data.get("email")
    otp = data.get("otp")
    new_password = data.get("newPassword")
    confirm_new_password = data.get("confirmNewPassword")
    logger.info(f"Password reset attempt for identifier: {identifier}")

    if not identifier or not otp or not new_password or not confirm_new_password:
        raise HTTPException(status_code=400, detail="Identifier, OTP, new password, and confirm new password are required")

    if new_password != confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,100}$"
    if not re.match(password_regex, new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be 8-100 characters, include uppercase, lowercase, number, and special character"
        )

    if "@" in identifier:
        user = get_user_by_email(db, identifier)
        channel = "email"
    elif identifier.isdigit() or identifier.startswith("+"):
        user = get_user_by_phone(db, identifier)
        channel = "sms"
    else:
        raise HTTPException(status_code=400, detail="Identifier must be an email or phone number")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.otp or user.otp != otp or user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user.password = hash_password(new_password)
    user.otp = None
    user.otp_expires_at = None
    user.otp_verified = True
    user.updated_at = datetime.utcnow()
    db.commit()

    logger.info(f"Password reset successful for user ID: {user.id}")
    return {"detail": "Password updated successfully", "success": True}

@router.post("/reset-password/otp/start")
def reset_password_otp_start(data: OTPStart, db: Session = Depends(get_db)):
    email = (data.email or "").strip() or None
    phone = (data.phone or "").strip() or None
    channel = data.communication_channel.value

    if channel == "email" and not email:
        raise HTTPException(status_code=400, detail="Email required for email channel")
    if channel in ["sms", "whatsapp"] and not phone:
        raise HTTPException(status_code=400, detail="Phone required for SMS/WhatsApp channel")

    user = get_user_by_email(db, email) if channel == "email" else get_user_by_phone(db, phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = generate_numeric_otp(6)
    user.otp = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    user.otp_verified = False
    db.commit()
    db.refresh(user)

    destination = email if channel == "email" else phone
    send_otp(destination, channel, otp)
    return {"detail": "OTP sent", "user_id": user.id, "success": True}

@router.post("/verification/submit", response_model=IdentityVerification)
def submit_verification_request(
    verification: VerificationSubmit,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    prev_status = current_user.status

    identity_verification = submit_verification(db, current_user.id, verification)
    
    if identity_verification.status == "verified":
        current_user.status = models.UserStatus.verified
        current_user.updated_at = datetime.utcnow()
        db.add(UserStatusHistory(
            user_id=current_user.id,
            from_status=prev_status.value,
            to_status=models.UserStatus.verified.value
        ))
        db.commit()
        db.refresh(current_user)

        # At verified stage, send both: relationships and trustees (with accept/decline links)
        send_relationship_emails_for_pending_requests(db, current_user)
        send_trustee_emails_for_pending_invites(db, current_user)
        send_memory_branch_emails_for_pending_invites(db, current_user)
        send_leaf_stage_emails_for_pending_invites = send_leaf_stage_emails_for_user  
        send_leaf_stage_emails_for_user(db, current_user)
        send_memories_leaf_emails_for_user(db, current_user)
        send_message_branch_emails_for_pending_invites(db, current_user)
        send_messages_leaf_emails_for_user(db, current_user)

    return identity_verification

@router.post("/admin/login")
def admin_login(credentials: LoginCredentials, db: Session = Depends(get_db)):
    identifier = (credentials.identifier or "").strip()
    password = credentials.password or ""
    if not identifier or not password:
        raise HTTPException(status_code=400, detail="Identifier and password are required")

    admin = None
    if "@" in identifier:
        admin = db.query(Admin).filter(Admin.email == identifier).first()
    else:
        admin = db.query(Admin).filter(Admin.username == identifier).first()

    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    if not verify_password(password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = create_access_token({"sub": str(admin.id), "adm": True})
    return {"access_token": token, "token_type": "bearer", "success": True}

@router.post("/admin/otp/start")
def admin_otp_start(data: AdminOTPStart, db: Session = Depends(get_db)):
    email = (data.email or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email required for admin OTP")

    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    otp = generate_numeric_otp(6)
    admin.otp = otp
    admin.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
    admin.otp_verified = False
    db.commit()
    db.refresh(admin)

    _send_plain_email(admin.email, "Plan Beyond Admin OTP", f"Your OTP is {otp}")
    return {"detail": "OTP sent", "admin_id": admin.id, "success": True}

@router.post("/admin/verify-otp")
def admin_otp_verify(data: AdminOTPVerify, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.id == data.admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    if not admin.otp or admin.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired or not found")
    if admin.otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    admin.otp_verified = True
    admin.otp = None
    admin.otp_expires_at = None
    db.commit()

    token = create_access_token({"sub": str(admin.id), "adm": True})
    return {"access_token": token, "token_type": "bearer", "adminId": admin.id, "success": True}


def _ensure_assignment_token(db: Session, a: MemoryCollectionAssignment) -> str:
    token = getattr(a, "invite_token", None)
    if token:
        return token
    if hasattr(a, "invite_token"):
        token = secrets.token_hex(16)
        a.invite_token = token
        db.add(a)
        db.commit()
        db.refresh(a)
        return token
    return ""

def _compose_assignment_accept_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/memories/assignments/a/{assignment_id}/{token}"

def _compose_assignment_reject_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/memories/assignments/r/{assignment_id}/{token}"



def _compose_mem_leaf_accept_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/memories/leaves/a/{assignment_id}/{token}"

def _compose_mem_leaf_reject_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/memories/leaves/r/{assignment_id}/{token}"


def send_memory_branch_emails_for_pending_invites(db: Session, user: models.User):
   
    try:
        contacts = _link_user_to_matching_contacts(db, user)
        if not contacts:
            return

        for contact in contacts:
            if not contact.emails or len(contact.emails) == 0:
                continue
            primary_email = contact.emails[0]

            invites = (
                db.query(MemoryCollectionAssignment)
                .filter(
                    MemoryCollectionAssignment.contact_id == contact.id,
                    MemoryCollectionAssignment.role == AssignmentRole.branch,
                    MemoryCollectionAssignment.invite_status == BranchInviteStatus.sent
                )
                .all()
            )
            if not invites:
                continue

            for a in invites:
                if not user.otp_verified:
                    subject = "Verify your account to view a Branch invitation"
                    body = (
                        f"Hello,\n\n"
                        f"You were added as a Branch in Plan Beyond. To view and respond to the invite, please verify your account using the OTP flow:\n"
                        f"{_compose_otp_start_url()}\n\n"
                        f"{_pb_blurb()}"
                    )
                elif user.status in (models.UserStatus.unknown, models.UserStatus.guest):
                    subject = "Complete your profile to respond to a Branch invitation"
                    body = (
                        f"Hello,\n\n"
                        f"You were added as a Branch in Plan Beyond. To respond, please complete your profile verification:\n"
                        f"{_compose_guest_verification_url()}\n\n"
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

                _send_plain_email(primary_email, subject, body)
                logger.info(f"Memory-branch follow-up sent to {primary_email} for assignment {a.id} (stage: {'OTP' if not user.otp_verified else user.status.name})")
    except Exception as e:
        logger.error(f"Error sending memory-branch follow-ups for user {user.id}: {str(e)}")
        pass





def send_leaf_stage_emails_for_user(db: Session, user: models.User):
    
    # Link any matching contacts so we can find their leaves
    contacts = _link_user_to_matching_contacts(db, user)
    if not contacts:
        return

    contact_ids = [c.id for c in contacts]
    if not contact_ids:
        return

    # Find active leaves for these contacts where owner's hard death is finalized
    q = (
        db.query(CategoryProgressLeaf)
        .filter(
            CategoryProgressLeaf.contact_id.in_(contact_ids),
            CategoryProgressLeaf.status == ProgressLeafStatus.active,
        )
    )

    leaves: list[CategoryProgressLeaf] = []
    for leaf in q.all():
        hard_lock = (
            db.query(DeathLock)
            .filter(
                DeathLock.root_user_id == leaf.user_id,
                DeathLock.lock == DeathLockType.hard_finalized
            )
            .first()
        )
        if hard_lock:
            leaves.append(leaf)

    if not leaves:
        return

    # Choose a primary email to notify (from *their* linked contact records)
    to_email = None
    chosen_contact_id = None
    for c in contacts:
        if c.emails and c.emails[0]:
            to_email = c.emails[0]
            chosen_contact_id = c.id
            break
    if not to_email or not chosen_contact_id:
        return

    # Stage-aware content
    app_base = settings.APP_URL.rstrip("/")
    otp_start_url = f"{app_base}/otp/start"
    guest_verify_url = f"{app_base}/profile"

    if not user.otp_verified:
        subject = "Verify your account (OTP) to view items assigned to you"
        body = (
            "Hello,\n\n"
            "A passing has been verified. You were designated to receive certain items. "
            "Please verify your account to continue:\n"
            f"{otp_start_url}\n\n"
            "— Plan Beyond"
        )
        _send_plain_email(to_email, subject, body)
        return

    if user.status in (models.UserStatus.unknown, models.UserStatus.guest):
        subject = "Complete your profile to view items assigned to you"
        body = (
            "Hello,\n\n"
            "A passing has been verified. You were designated to receive certain items. "
            "Please complete your profile verification to continue:\n"
            f"{guest_verify_url}\n\n"
            "— Plan Beyond"
        )
        _send_plain_email(to_email, subject, body)
        return

    # ================= Verified / member → group and prefer bulk =================
    # Group active leaves (hard-finalized) by root_user_id but only for THIS chosen contact
    # (We pick the chosen_contact_id to be consistent with the to_email selected.)
    root_groups: dict[int, list[CategoryProgressLeaf]] = {}
    for lf in leaves:
        if lf.contact_id != chosen_contact_id:
            # We only send one mail to one contact email; skip other linked contacts here.
            continue
        root_groups.setdefault(int(lf.user_id), []).append(lf)

    if not root_groups:
        return

    for root_id, items in root_groups.items():
        if len(items) == 1:
            single = items[0]
            accept_url = _compose_leaf_accept_url(single.id, _gen_quick_token_leaf(single.id, "accept"))
            reject_url = _compose_leaf_reject_url(single.id, _gen_quick_token_leaf(single.id, "reject"))
           
            subject = "Item assigned to you — confirm to proceed"
            body = (
                "Hello,\n\n"
                "A passing has been verified, and one item was assigned to you. Please choose:\n\n"
                f"Accept:  {accept_url}\n"
                f"Decline: {reject_url}\n\n"
                "— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)
        else:
            # NEW: Bulk pair for multiple leaves under the same root owner
            tok_accept = _gen_quick_token_leaf_bulk(root_id, chosen_contact_id, "accept_all")
            tok_reject = _gen_quick_token_leaf_bulk(root_id, chosen_contact_id, "reject_all")
            accept_url = _compose_leaf_bulk_accept_url(root_id, chosen_contact_id, tok_accept)
            reject_url = _compose_leaf_bulk_reject_url(root_id, chosen_contact_id, tok_reject)
           
            subject = "Multiple items assigned to you — confirm once"
            body = (
                "Hello,\n\n"
                "A passing has been verified, and multiple items were assigned to you. "
                "Use one link below to apply to all of them:\n\n"
                f"Accept All:  {accept_url}\n"
                f"Decline All: {reject_url}\n\n"
                "— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)


def send_memories_leaf_emails_for_user(db: Session, user: models.User):
    # Link their contacts first so we can find assignments reliably
    contacts = _link_user_to_matching_contacts(db, user)
    if not contacts:
        return

    contact_ids = [c.id for c in contacts]
    if not contact_ids:
        return

    assignments = (
        db.query(MemoryCollectionAssignment, MemoryCollection, Contact)
        .join(MemoryCollection, MemoryCollectionAssignment.collection_id == MemoryCollection.id)
        .join(Contact, MemoryCollectionAssignment.contact_id == Contact.id)
        .filter(
            MemoryCollectionAssignment.contact_id.in_(contact_ids),
            MemoryCollectionAssignment.role == AssignmentRole.leaf,
        )
        .all()
    )
    if not assignments:
        return

    now = datetime.utcnow()
    changed = False  # track invite_status updates

    for a, coll, contact in assignments:
        # Require hard-death finalized for the owner
        hard_lock = (
            db.query(DeathLock)
            .filter(
                DeathLock.root_user_id == coll.user_id,
                DeathLock.lock == DeathLockType.hard_finalized
            )
            .first()
        )
        if not hard_lock:
            continue

        to_email = (contact.emails or [None])[0]
        if not to_email:
            continue

        # Helper: send a simple warm-up message for the current user stage
        def _send_stage_warmup(prefix: str = "An item is scheduled to be shared with you."):
            nonlocal to_email
            if not user.otp_verified:
                subject = "Verify your account (OTP) to receive a scheduled item"
                body = (
                    "Hello,\n\n"
                    f"{prefix} Please verify your account to continue:\n"
                    f"{_compose_otp_start_url()}\n\n— Plan Beyond"
                )
                _send_plain_email(to_email, subject, body)
                return True
            if user.status in (models.UserStatus.unknown, models.UserStatus.guest):
                subject = "Complete your profile to receive a scheduled item"
                body = (
                    "Hello,\n\n"
                    f"{prefix} Please complete your profile verification to continue:\n"
                    f"{_compose_guest_verification_url()}\n\n— Plan Beyond"
                )
                _send_plain_email(to_email, subject, body)
                return True
            # Verified/member warm-up (no links yet)
            subject = "Heads up: a scheduled item will be shared soon"
            body = (
                "Hello,\n\n"
                "A time-based item will be shared with you at its scheduled time. "
                "We’ll send a confirm link once it’s ready.\n\n— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)
            return True

        is_time_based = (coll.event_type == EventType.time and bool(coll.scheduled_at))

        # -------- BEFORE scheduled_at: warm-ups only --------
        if is_time_based and now < coll.scheduled_at:
            _send_stage_warmup()
            continue

        # -------- AT/AFTER scheduled_at (or non-time-based): stage → links when verified --------
        if not user.otp_verified:
            subject = "Verify your account (OTP) to view items assigned to you"
            body = (
                "Hello,\n\n"
                "A passing has been verified. You were designated to receive certain items. "
                f"Please verify your account to continue:\n{_compose_otp_start_url()}\n\n— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)
            continue

        if user.status in (models.UserStatus.unknown, models.UserStatus.guest):
            subject = "Complete your profile to view items assigned to you"
            body = (
                "Hello,\n\n"
                "A passing has been verified. You were designated to receive certain items. "
                f"Please complete your profile verification to continue:\n{_compose_guest_verification_url()}\n\n— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)
            continue

        # Verified / member:
        if is_time_based:
            # Now due/past → send links and mark as sent if not already
            if getattr(a, "invite_status", None) is None:
                a.invite_status = BranchInviteStatus.sent
                a.invited_at = now
                a.invite_expires_at = now + timedelta(days=30)
                changed = True

            token = _ensure_assignment_token(db, a)
            subject = "Items assigned to you — confirm to proceed"
            body = (
                "Hello,\n\n"
                "A time-based item has reached its scheduled time and was assigned to you. "
                "Please choose:\n\n"
                f"Accept:  {_compose_mem_leaf_accept_url(a.id, token)}\n"
                f"Decline: {_compose_mem_leaf_reject_url(a.id, token)}\n\n"
                "— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)
            continue

        # Non-time-based (original behavior)
        token = _ensure_assignment_token(db, a)
        subject = "Items assigned to you — confirm to proceed"
        body = (
            "Hello,\n\n"
            "A passing has been verified, and items in a folder were assigned to you. "
            "Please choose:\n\n"
            f"Accept:  {_compose_mem_leaf_accept_url(a.id, token)}\n"
            f"Decline: {_compose_mem_leaf_reject_url(a.id, token)}\n\n"
            "— Plan Beyond"
        )
        _send_plain_email(to_email, subject, body)

    if changed:
        db.commit()



# ----- messages: assignment accept/reject (branch) -----
def _compose_msg_assignment_accept_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/messages/assignments/a/{assignment_id}/{token}"

def _compose_msg_assignment_reject_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/messages/assignments/r/{assignment_id}/{token}"

# ----- messages: leaf accept/reject (leaf) -----
def _compose_msg_leaf_accept_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/messages/leaves/a/{assignment_id}/{token}"

def _compose_msg_leaf_reject_url(assignment_id: int, token: str) -> str:
    return f"{settings.BACKEND_URL}/messages/leaves/r/{assignment_id}/{token}"

def _ensure_msg_assignment_token(db: Session, a: MessageCollectionAssignment) -> str:
    token = getattr(a, "invite_token", None)
    if token:
        return token
    if hasattr(a, "invite_token"):
        token = secrets.token_hex(16)
        a.invite_token = token
        db.add(a)
        db.commit()
        db.refresh(a)
        return token
    return ""


def send_message_branch_emails_for_pending_invites(db: Session, user: models.User):

    try:
        contacts = _link_user_to_matching_contacts(db, user)
        if not contacts:
            return

        for contact in contacts:
            if not contact.emails or len(contact.emails) == 0:
                continue
            primary_email = contact.emails[0]

            invites = (
                db.query(MessageCollectionAssignment)
                .filter(
                    MessageCollectionAssignment.contact_id == contact.id,
                    MessageCollectionAssignment.role == AssignmentRole.branch,
                    MessageCollectionAssignment.invite_status == BranchInviteStatus.sent
                )
                .all()
            )
            if not invites:
                continue

            for a in invites:
                # Stage-aware subject/body (same logic as memories)
                if not user.otp_verified:
                    subject = "Verify your account to view a Branch invitation"
                    body = (
                        "Hello,\n\n"
                        "You were added as a Branch in Plan Beyond. To view and respond to the invite, "
                        "please verify your account using the OTP flow:\n"
                        f"{_compose_otp_start_url()}\n\n"
                        f"{_pb_blurb()}"
                    )
                elif user.status in (models.UserStatus.unknown, models.UserStatus.guest):
                    subject = "Complete your profile to respond to a Branch invitation"
                    body = (
                        "Hello,\n\n"
                        "You were added as a Branch in Plan Beyond. To respond, please complete your profile verification:\n"
                        f"{_compose_guest_verification_url()}\n\n"
                        f"{_pb_blurb()}"
                    )
                else:
                    token = _ensure_msg_assignment_token(db, a)
                    accept_link = _compose_msg_assignment_accept_url(a.id, token)
                    reject_link = _compose_msg_assignment_reject_url(a.id, token)
                    subject = "Branch Invitation — Respond with Accept or Decline"
                    body = (
                        "Hello,\n\n"
                        "You were added as a Branch in Plan Beyond. You can respond below:\n\n"
                        f"Accept:  {accept_link}\n"
                        f"Decline: {reject_link}\n\n"
                        f"{_pb_blurb()}"
                    )

                _send_plain_email(primary_email, subject, body)
                logger.info(
                    f"Message-branch follow-up sent to {primary_email} for assignment {a.id} "
                    f"(stage: {'OTP' if not user.otp_verified else user.status.name})"
                )
    except Exception as e:
        logger.error(f"Error sending message-branch follow-ups for user {user.id}: {str(e)}")
        pass



def send_messages_leaf_emails_for_user(db: Session, user: models.User):
    
    contacts = _link_user_to_matching_contacts(db, user)
    if not contacts:
        return

    contact_ids = [c.id for c in contacts]
    if not contact_ids:
        return

    assignments = (
        db.query(MessageCollectionAssignment, MessageCollection, Contact)
        .join(MessageCollection, MessageCollectionAssignment.collection_id == MessageCollection.id)
        .join(Contact, MessageCollectionAssignment.contact_id == Contact.id)
        .filter(
            MessageCollectionAssignment.contact_id.in_(contact_ids),
            MessageCollectionAssignment.role == AssignmentRole.leaf,
        )
        .all()
    )
    if not assignments:
        return

    now = datetime.utcnow()
    changed = False  # track invite_status updates on time-based due

    for a, coll, contact in assignments:
        # Require hard-death finalized for the owner (same policy as memories)
        hard_lock = (
            db.query(DeathLock)
            .filter(
                DeathLock.root_user_id == coll.user_id,
                DeathLock.lock == DeathLockType.hard_finalized
            )
            .first()
        )
        if not hard_lock:
            continue

        to_email = (contact.emails or [None])[0]
        if not to_email:
            continue

        def _warmup(prefix: str = "An item is scheduled to be shared with you."):
            if not user.otp_verified:
                subject = "Verify your account (OTP) to receive a scheduled item"
                body = (
                    "Hello,\n\n"
                    f"{prefix} Please verify your account to continue:\n"
                    f"{_compose_otp_start_url()}\n\n— Plan Beyond"
                )
                _send_plain_email(to_email, subject, body)
                return
            if user.status in (models.UserStatus.unknown, models.UserStatus.guest):
                subject = "Complete your profile to receive a scheduled item"
                body = (
                    "Hello,\n\n"
                    f"{prefix} Please complete your profile verification to continue:\n"
                    f"{_compose_guest_verification_url()}\n\n— Plan Beyond"
                )
                _send_plain_email(to_email, subject, body)
                return
            # Verified/member warm-up (no links yet)
            subject = "Heads up: a scheduled item will be shared soon"
            body = (
                "Hello,\n\n"
                "A time-based item will be shared with you at its scheduled time. "
                "We’ll send a confirm link once it’s ready.\n\n— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)

        is_time_based = (coll.event_type == EventType.time and bool(coll.scheduled_at))

        # BEFORE scheduled_at → warmups only
        if is_time_based and now < coll.scheduled_at:
            _warmup()
            continue

        # Verified/member gating same as memories
        if not user.otp_verified:
            subject = "Verify your account (OTP) to view items assigned to you"
            body = (
                "Hello,\n\n"
                "A passing has been verified. You were designated to receive certain items. "
                f"Please verify your account to continue:\n{_compose_otp_start_url()}\n\n— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)
            continue

        if user.status in (models.UserStatus.unknown, models.UserStatus.guest):
            subject = "Complete your profile to view items assigned to you"
            body = (
                "Hello,\n\n"
                "A passing has been verified. You were designated to receive certain items. "
                f"Please complete your profile verification to continue:\n{_compose_guest_verification_url()}\n\n— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)
            continue

        # Verified / member:
        if is_time_based:
            # Due/past → send links and mark as sent if not already
            if getattr(a, "invite_status", None) is None:
                a.invite_status = BranchInviteStatus.sent
                a.invited_at = now
                a.invite_expires_at = now + timedelta(days=30)
                changed = True

            token = _ensure_msg_assignment_token(db, a)
            subject = "Items assigned to you — confirm to proceed"
            body = (
                "Hello,\n\n"
                "A time-based item has reached its scheduled time and was assigned to you. "
                "Please choose:\n\n"
                f"Accept:  {_compose_msg_leaf_accept_url(a.id, token)}\n"
                f"Decline: {_compose_msg_leaf_reject_url(a.id, token)}\n\n"
                "— Plan Beyond"
            )
            _send_plain_email(to_email, subject, body)
            continue

        # Event-based (non-time): links immediately at verified/member stage
        token = _ensure_msg_assignment_token(db, a)
        subject = "Items assigned to you — confirm to proceed"
        body = (
            "Hello,\n\n"
            "A passing has been verified, and items were assigned to you. "
            "Please choose:\n\n"
            f"Accept:  {_compose_msg_leaf_accept_url(a.id, token)}\n"
            f"Decline: {_compose_msg_leaf_reject_url(a.id, token)}\n\n"
            "— Plan Beyond"
        )
        _send_plain_email(to_email, subject, body)

    if changed:
        db.commit()
