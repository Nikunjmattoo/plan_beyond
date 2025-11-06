from __future__ import annotations
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import base64
import hmac
import hashlib
import time as _time
import os
from typing import Tuple, Dict, Any, List, Optional, Set
from fastapi import HTTPException, UploadFile

from app.models.death import (
    DeathDeclaration, DeathReview, LegendLifecycle, Contest, Broadcast, Config, DeathLock,
    DeathType, DeclarationState, LLMSafetyCheck, ReviewAutomated, ReviewDecision,
    LifecycleState, ContestStatus, BroadcastType, BroadcastState, DeathLockType,
    AuditLog, DeathAck
)
from app.models.contact import Contact
from app.models.user import User
from app.models.trustee import Trustee
from app.models.enums import TrusteeStatus, ApprovalStatus
from app.models.death_approval import DeathApproval

import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# ==== NEW: S3 imports & config (for evidence storage) ====
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import mimetypes
from uuid import uuid4
import re
from app.config import settings
from app.models.category import CategoryProgressLeaf, ProgressLeafStatus

AWS_REGION = settings.AWS_REGION
S3_BUCKET = settings.S3_BUCKET
S3_PUBLIC_BASE_URL = settings.S3_PUBLIC_BASE_URL  # same base used by /s3 routes

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

def _safe_filename(name: str) -> str:
    n = (name or "file").strip().replace(" ", "_")
    return SAFE_NAME_RE.sub("", n) or "file"
# =========================================================

logger = logging.getLogger(__name__)

# ==============================
# Audit & Authorization Helpers
# ==============================

def _audit(
    db: Session, *,
    actor_type: str, actor_id: int, action: str,
    entity_type: str, entity_id: int, data: dict | None = None
):
    db.add(AuditLog(
        actor_type=actor_type, actor_id=actor_id, action=action,
        entity_type=entity_type, entity_id=entity_id, data_json=json.dumps(data or {})
    ))

# ==============================
# Small helpers
# ==============================

def _has_hard_finalized(db: Session, root_user_id: int) -> bool:
    return db.query(DeathLock).filter(
        DeathLock.root_user_id == root_user_id,
        DeathLock.lock == DeathLockType.hard_finalized
    ).first() is not None

def _get_or_default_config(db: Session, root_user_id: int) -> Config:
    cfg = db.query(Config).filter(Config.root_user_id == root_user_id).first()
    if cfg:
        return cfg
    cfg = Config(root_user_id=root_user_id)  # defaults apply
    db.add(cfg)
    db.flush()
    return cfg

def _update_lifecycle(db: Session, root_user_id: int, new_state: LifecycleState):
    cur = (
        db.query(LegendLifecycle)
        .filter(LegendLifecycle.root_user_id == root_user_id)
        .order_by(LegendLifecycle.id.desc())
        .first()
    )
    now = datetime.utcnow()
    if cur and cur.exited_at is None:
        cur.exited_at = now
    db.add(LegendLifecycle(root_user_id=root_user_id, state=new_state, entered_at=now))

def _has_soft_accepted(db: Session, root_user_id: int) -> bool:
    return db.query(DeathDeclaration).filter(
        DeathDeclaration.root_user_id == root_user_id,
        DeathDeclaration.type == DeathType.soft,
        DeathDeclaration.state == DeclarationState.accepted
    ).first() is not None

def _no_lock(db: Session, root_user_id: int) -> bool:
    return db.query(DeathLock).filter(DeathLock.root_user_id == root_user_id).first() is None

# ==============================
# Misc helpers
# ==============================

def _llm_safety_check(text: str) -> LLMSafetyCheck:
    if not text:
        return LLMSafetyCheck.passed
    return LLMSafetyCheck.passed

def _resolve_root_user_id(db: Session, owner: str | int) -> int | None:
    try:
        s = str(owner).strip()
        if s.isdigit():
            uid = int(s)
            u = db.query(User).filter(User.id == uid).first()
            return uid if u else None
        u = db.query(User).filter(User.display_name == s).first()
        return u.id if u else None
    except Exception:
        return None

# ==============================
# Active banners
# ==============================

def get_active_soft_info(db: Session, *, viewer_user_id: int, owner: str) -> dict:
    root_user_id = _resolve_root_user_id(db, owner)
    if not root_user_id:
        return {"active": False, "root_user_id": None}

    if _has_hard_finalized(db, root_user_id):
        return {
            "active": False,
            "root_user_id": root_user_id,
            "finalized_by_hard": True
        }

    cfg = _get_or_default_config(db, root_user_id)
    decl = (
        db.query(DeathDeclaration)
        .filter(
            DeathDeclaration.root_user_id == root_user_id,
            DeathDeclaration.type == DeathType.soft,
            DeathDeclaration.state == DeclarationState.accepted
        )
        .order_by(DeathDeclaration.created_at.desc())
        .first()
    )
    if not decl:
        return {"active": False, "root_user_id": root_user_id}

    window_days = cfg.contest_window_days or 7
    window_ends_at = decl.created_at + timedelta(days=window_days)

    ok, viewer_contact_id = _actor_contact_if_authorized_for_root(
        db, actor_user_id=viewer_user_id, root_user_id=root_user_id
    )
    declared_by_me = bool(ok and viewer_contact_id and viewer_contact_id == decl.declared_by_contact_id)
    acknowledged_by_me = (
        db.query(DeathAck)
        .filter(DeathAck.declaration_id == decl.id, DeathAck.trustee_user_id == viewer_user_id)
        .first()
        is not None
    )
    return {
        "active": True,
        "root_user_id": root_user_id,
        "declaration_id": decl.id,
        "message": decl.message,
        "declared_by_contact_id": decl.declared_by_contact_id,
        "declared_by_me": declared_by_me,
        "acknowledged_by_me": acknowledged_by_me,
        "window_ends_at": (window_ends_at.isoformat() + "Z"),
    }

def get_active_hard_info(db: Session, *, viewer_user_id: int, owner: str) -> dict:
    root_user_id = _resolve_root_user_id(db, owner)
    if not root_user_id:
        return {"active": False, "root_user_id": None}

    decl = (
        db.query(DeathDeclaration)
        .filter(
            DeathDeclaration.root_user_id == root_user_id,
            DeathDeclaration.type == DeathType.hard,
            DeathDeclaration.state == DeclarationState.accepted
        )
        .order_by(DeathDeclaration.created_at.desc())
        .first()
    )
    if not decl:
        return {"active": False, "root_user_id": root_user_id}

    ok, viewer_contact_id = _actor_contact_if_authorized_for_root(
        db, actor_user_id=viewer_user_id, root_user_id=root_user_id
    )
    declared_by_me = bool(ok and viewer_contact_id and viewer_contact_id == decl.declared_by_contact_id)

    return {
        "active": True,
        "root_user_id": root_user_id,
        "declaration_id": decl.id,
        "message": decl.note,
        "declared_by_contact_id": decl.declared_by_contact_id,
        "declared_by_me": declared_by_me,
        "final": True,
    }

# ==============================
# URL & Token helpers
# ==============================

def _get_app_base_url() -> str:
    try:
        from app.config import settings
        return (
            getattr(settings, "APP_BASE_URL", None)
            or getattr(settings, "FRONTEND_BASE_URL", None)
            or getattr(settings, "APP_URL", None)
            or "https://app.example.com"
        ).rstrip("/")
    except Exception:
        return "https://app.example.com"

def _get_api_base_url() -> str:
    try:
        from app.config import settings
        return (
            getattr(settings, "API_BASE_URL", None)
            or getattr(settings, "BACKEND_BASE_URL", None)
            or getattr(settings, "PUBLIC_API_BASE_URL", None)
            or getattr(settings, "BACKEND_URL", None)
            or "http://127.0.0.1:8000"
        ).rstrip("/")
    except Exception:
        return "http://127.0.0.1:8000"

def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def _b64urldec(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _gen_quick_token(contest_id: int, decision: str, expires_at_ts: int) -> str:
    from app.config import settings
    secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
    payload = {"cid": contest_id, "dec": decision, "exp": int(expires_at_ts)}
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(secret, data, hashlib.sha256).digest()
    return f"{_b64url(data)}.{_b64url(sig)}"

def _verify_quick_token(token: str, contest_id: int, decision: str) -> bool:
    try:
        from app.config import settings
        secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
        parts = token.split(".")
        if len(parts) != 2:
            return False
        data_b = _b64urldec(parts[0])
        sig_b = _b64urldec(parts[1])
        exp_sig = hmac.new(secret, data_b, hashlib.sha256).digest()
        if not hmac.compare_digest(sig_b, exp_sig):
            return False
        payload = json.loads(data_b.decode())
        if int(payload.get("cid")) != int(contest_id):
            return False
        if str(payload.get("dec")) != str(decision):
            return False
        if int(payload.get("exp", 0)) < int(_time.time()):
            return False
        return True
    except Exception:
        return False

def _gen_quick_token_hard(declaration_id: int, decision: str, expires_at_ts: int) -> str:
    from app.config import settings
    secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
    payload = {"did": declaration_id, "dec": decision, "exp": int(expires_at_ts)}
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(secret, data, hashlib.sha256).digest()
    return f"{_b64url(data)}.{_b64url(sig)}"

def _verify_quick_token_hard(token: str, declaration_id: int, decision: str) -> bool:
    try:
        from app.config import settings
        secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
        parts = token.split(".")
        if len(parts) != 2:
            return False
        data_b = _b64urldec(parts[0])
        sig_b = _b64urldec(parts[1])
        exp_sig = hmac.new(secret, data_b, hashlib.sha256).digest()
        if not hmac.compare_digest(sig_b, exp_sig):
            return False
        payload = json.loads(data_b.decode())
        if int(payload.get("did")) != int(declaration_id):
            return False
        if str(payload.get("dec")) != str(decision):
            return False
        if int(payload.get("exp", 0)) < int(_time.time()):
            return False
        return True
    except Exception:
        return False

# ==============================
# Email helpers
# ==============================

def _send_email_now(to_addr: str, subject: str, body: str, html: bool = False) -> None:
    try:
        from app.config import settings
        if html:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "html"))
        else:
            msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_EMAIL
        msg["To"] = to_addr
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent to {to_addr}")
    except Exception as e:
        logger.error(f"Email FAILED to {to_addr}: {e}")

def _send_bulk_emails_async(
    recipients: list[str],
    subject: str,
    body: str,
    delay_days: int = 0,
    batch_size: int = 100,
    html: bool = False,
) -> None:
    def worker():
        if delay_days and delay_days > 0:
            time.sleep(delay_days * 86400)
        recips = [r for r in set(recipients) if r]
        for addr in recips:
            _send_email_now(addr, subject, body, html=html)
            time.sleep(0.2)
    threading.Thread(target=worker, daemon=True).start()

# ==============================
# File storage (HARD evidence) — NOW USING S3
# ==============================

def _get_unique_filename(_storage_path: str, filename: str) -> str:
    # kept for compatibility; no local FS use in S3 flow
    base, ext = os.path.splitext(filename or "evidence")
    return f"{base}{ext}"

async def _store_evidence_file_for_root(root_user_id: int, upload: UploadFile) -> Tuple[str, str]:
    """
    Upload evidence to S3 (instead of local disk).
    Returns (key, public_url) — same tuple shape as before.
    """
    if not upload:
        raise HTTPException(status_code=400, detail="evidence_file is required")

    content = await upload.read()
    if not content:
        raise HTTPException(status_code=400, detail="evidence_file is empty")
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="evidence_file must be <= 25MB")

    # Determine content type
    inferred_ct = upload.content_type or mimetypes.guess_type(upload.filename or "")[0] or "application/octet-stream"

    safe = _safe_filename(upload.filename or "evidence.bin")
    key = f"evidence/{root_user_id}/{uuid4().hex}_{safe}"

    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=content,
            ContentType=inferred_ct,
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")

    public_url = f"{S3_PUBLIC_BASE_URL}/{key}"  # consistent with Memories app_url
    return key, public_url

# ==============================
# Audience & Email resolution
# ==============================

def _contact_opted_in(c: Contact) -> bool:
    try:
        return bool(getattr(c, "share_after_death", False))
    except Exception:
        return False

def _yield_opted_in_emails(c: Contact) -> list[str]:
    if not _contact_opted_in(c):
        return []
    emails = []
    if c.emails:
        for e in c.emails:
            if e:
                emails.append(str(e).lower())
    return emails

def _resolve_all_contact_emails(db: Session, *, root_user_id: int) -> list[str]:
    emails: set[str] = set()
    for c in db.query(Contact).filter(Contact.owner_user_id == root_user_id).all():
        for e in _yield_opted_in_emails(c):
            emails.add(e)
    return list(emails)

def _resolve_trustee_emails(db: Session, *, root_user_id: int, exclude_contact_id: int | None = None) -> list[str]:
    emails: set[str] = set()
    q = (
        db.query(Trustee, Contact)
        .join(Contact, Contact.id == Trustee.contact_id)
        .filter(Trustee.user_id == root_user_id, Trustee.status == TrusteeStatus.accepted)
    )
    for _t, c in q.all():
        if exclude_contact_id and c.id == exclude_contact_id:
            continue
        for e in _yield_opted_in_emails(c):
            emails.add(e)
    return list(emails)

def _resolve_audience_emails(db: Session, *, root_user_id: int, audience_config: dict | None) -> list[str]:
    emails: set[str] = set()
    cfg = audience_config or {}

    if cfg.get("include_all_contacts", True):
        for c in db.query(Contact).filter(Contact.owner_user_id == root_user_id).all():
            for e in _yield_opted_in_emails(c):
                emails.add(e)

    contact_ids = set(cfg.get("contact_ids", []) or [])
    if contact_ids:
        for c in db.query(Contact).filter(Contact.id.in_(contact_ids)).all():
            for e in _yield_opted_in_emails(c):
                emails.add(e)

    for e in (cfg.get("extra_emails") or []):
        if e:
            emails.add(str(e).lower())

    return list(emails)

# ==============================
# SOFT flow utilities (emails)
# ==============================

def _email_soft_initiated(db: Session, *, decl: DeathDeclaration, initiator_contact_id: int):
    root = db.query(User).filter(User.id == decl.root_user_id).first()
    root_email = (getattr(root, "email", None) or "").strip().lower()
    root_name = getattr(root, "display_name", None) or "your contact"

    trustee_emails = set(_resolve_trustee_emails(
        db, root_user_id=decl.root_user_id, exclude_contact_id=initiator_contact_id
    ))

    review_url = f"{_get_app_base_url()}/death-message/{decl.root_user_id}"
    subject = f"Review request: death message initiated for {root_name}"
    body = (
        f"A trustee has initiated a death message for {root_name}.\n\n"
        f"If this is true, please approve. If not, decline and attach a valid document.\n"
        f"Review link: {review_url}\n\n— Plan Beyond"
    )
    recipients = set(trustee_emails)
    if root_email:
        recipients.add(root_email)
    if recipients:
        _send_bulk_emails_async(list(recipients), subject, body, delay_days=0, html=False)

def _broadcast_soft_contacts(db: Session, *, decl: DeathDeclaration, message_text: str, audience_config: dict | None):
    root = db.query(User).filter(User.id == decl.root_user_id).first()
    root_name = getattr(root, "display_name", None) or "your contact"
    subject = f"Soft-death announcement for {root_name}"
    body = (message_text or "A soft-death has been declared.") + "\n\n— Plan Beyond"

    recipients = _resolve_all_contact_emails(db, root_user_id=decl.root_user_id)
    if recipients:
        _send_bulk_emails_async(
            recipients,
            subject,
            body,
            delay_days=int((audience_config or {}).get("delay_days", 0)),
            html=False
        )

    db.add(Broadcast(
        type=BroadcastType.soft_death_announce,
        root_user_id=decl.root_user_id,
        audience_config_json=json.dumps(audience_config or {}),
        channels=["email", "inapp"],
        content=(message_text or "A soft-death has been declared."),
        llm_safety_result=LLMSafetyCheck.passed,
        state=BroadcastState.queued,
    ))

# ==============================
# Trustee-only APIs
# ==============================

def declare_soft_death(
    db: Session, *, trustee_user_id: int, root_user_id: int, message: str | None,
    media_ids: list[int] | None, audience_config: dict | None
) -> DeathDeclaration | None:
    cfg = _get_or_default_config(db, root_user_id)
    if not cfg.soft_death_enabled:
        return None
    if not _no_lock(db, root_user_id):
        return None

    ok, contact_id = _actor_contact_if_authorized_for_root(
        db, actor_user_id=trustee_user_id, root_user_id=root_user_id
    )
    if not ok:
        return None

    existing_pending = db.query(DeathDeclaration).filter(
        DeathDeclaration.root_user_id == root_user_id,
        DeathDeclaration.type == DeathType.soft,
        DeathDeclaration.state == DeclarationState.pending_review
    ).first()
    if existing_pending:
        return existing_pending

    decl = DeathDeclaration(
        root_user_id=root_user_id,
        type=DeathType.soft,
        declared_by_contact_id=contact_id,
        message=message,
        media_ids=media_ids or None,
        llm_safety_check=_llm_safety_check(message or ""),
        state=DeclarationState.pending_review,
    )
    db.add(decl)
    db.flush()

    _update_lifecycle(db, root_user_id, LifecycleState.soft_announced)
    _audit(
        db, actor_type="trustee", actor_id=trustee_user_id, action="declare_soft_pending",
        entity_type="DeathDeclaration", entity_id=decl.id, data={"root_user_id": root_user_id}
    )
    db.commit()
    db.refresh(decl)

    try:
        _email_soft_initiated(db, decl=decl, initiator_contact_id=contact_id)
    except Exception as e:
        logger.error(f"Soft-death initial email error: {e}")

    return decl

async def declare_hard_death(
    db: Session, *, trustee_user_id: int, root_user_id: int, evidence_file: UploadFile, note: str | None,
    also_broadcast: bool
) -> DeathDeclaration | None:
    cfg = _get_or_default_config(db, root_user_id)
    if not cfg.hard_death_allowed_for_branches:
        return None
    if not _no_lock(db, root_user_id):
        return None

    ok, contact_id = _actor_contact_if_authorized_for_root(
        db, actor_user_id=trustee_user_id, root_user_id=root_user_id
    )
    if not ok:
        return None

    decl = DeathDeclaration(
        root_user_id=root_user_id,
        type=DeathType.hard,
        declared_by_contact_id=contact_id,
        evidence_file_id=None,
        note=note,
        state=DeclarationState.pending_review,
    )
    db.add(decl)
    db.flush()

    # S3 upload (returns key, public_url)
    _, public_url = await _store_evidence_file_for_root(root_user_id=root_user_id, upload=evidence_file)

    rev = DeathReview(declaration_id=decl.id, automated_result=ReviewAutomated.inconclusive)
    rev.notes = f"[evidence] {public_url}"
    db.add(rev)

    _update_lifecycle(db, root_user_id, LifecycleState.hard_review)
    _audit(db, actor_type="trustee", actor_id=trustee_user_id, action="declare_hard",
           entity_type="DeathDeclaration", entity_id=decl.id, data={"root_user_id": root_user_id})

    db.commit()
    db.refresh(decl)

    try:
        notify_admin_on_hard_request(db, declaration_id=decl.id, evidence_url=public_url)
    except Exception as e:
        logger.error(f"Failed to email admin for hard request #{decl.id}: {e}")

    return decl

# ==============================
# Trustee approvals/declines (guard if hard finalized)
# ==============================

def _resolve_trustee_row_for_actor(db: Session, *, root_user_id: int, actor_user_id: int) -> Optional[Trustee]:
    row = (
        db.query(Trustee, Contact)
        .join(Contact, Contact.id == Trustee.contact_id)
        .filter(
            Trustee.user_id == root_user_id,
            Trustee.status == TrusteeStatus.accepted,
            Contact.linked_user_id == actor_user_id
        )
        .first()
    )
    if not row:
        return None
    t, _c = row
    return t

def approve_soft_by_trustee(db: Session, *, declaration_id: int, actor_user_id: int) -> bool:
    decl = db.query(DeathDeclaration).filter(DeathDeclaration.id == declaration_id).first()
    if not decl or decl.type != DeathType.soft or decl.state != DeclarationState.pending_review:
        raise HTTPException(status_code=400, detail="Not reviewable")

    if _has_hard_finalized(db, decl.root_user_id):
        raise HTTPException(status_code=400, detail="Hard-death finalized; soft approvals are closed.")

    trustee = _resolve_trustee_row_for_actor(db, root_user_id=decl.root_user_id, actor_user_id=actor_user_id)
    if not trustee:
        raise HTTPException(status_code=403, detail="Not authorized")
    if decl.declared_by_contact_id == trustee.contact_id:
        raise HTTPException(status_code=400, detail="Initiator cannot approve their own initiation")

    existing = db.query(DeathApproval).filter(
        DeathApproval.declaration_id == declaration_id,
        DeathApproval.trustee_id == trustee.id,
    ).first()
    if existing:
        existing.status = ApprovalStatus.approved
    else:
        db.add(DeathApproval(
            user_id=decl.root_user_id,
            declaration_id=declaration_id,
            trustee_id=trustee.id,
            status=ApprovalStatus.approved
        ))
    db.flush()

    approvals_count = db.query(DeathApproval).filter(
        DeathApproval.declaration_id == declaration_id,
        DeathApproval.status == ApprovalStatus.approved
    ).count()

    if approvals_count >= 1:
        decl.state = DeclarationState.accepted
        db.flush()
        msg = decl.message or "A soft-death has been declared."
        try:
            _broadcast_soft_contacts(db, decl=decl, message_text=msg, audience_config={})
        except Exception as e:
            logger.error(f"Soft broadcast error decl #{decl.id}: {e}")
        _update_lifecycle(db, decl.root_user_id, LifecycleState.soft_announced)
        _audit(db, actor_type="trustee", actor_id=actor_user_id, action="soft_approved_and_broadcast",
               entity_type="DeathDeclaration", entity_id=decl.id, data={})

    db.commit()
    return True

async def decline_soft_by_trustee(
    db: Session, *, declaration_id: int, actor_user_id: int, reason: str, evidence_file: UploadFile | None
) -> Contest:
    decl = db.query(DeathDeclaration).filter(DeathDeclaration.id == declaration_id).first()
    if not decl or decl.type != DeathType.soft:
        raise HTTPException(status_code=400, detail="Not declinable")

    if _has_hard_finalized(db, decl.root_user_id):
        raise HTTPException(status_code=400, detail="Hard-death finalized; soft disputes are closed.")

    trustee = _resolve_trustee_row_for_actor(db, root_user_id=decl.root_user_id, actor_user_id=actor_user_id)
    is_owner = actor_user_id == decl.root_user_id  # Owner can also contest

    if not trustee and not is_owner:
        raise HTTPException(status_code=403, detail="Not authorized")

    c = Contest(
        declaration_id=declaration_id,
        raised_by=("root" if is_owner else "trustee"),
        raised_by_id=(decl.root_user_id if is_owner else actor_user_id),
        reason=(reason or "").strip() or "Declined",
        evidence_file_id=None,
        status=ContestStatus.pending
    )
    db.add(c)
    db.flush()

    if evidence_file:
        # S3 upload for contest evidence too
        _, public_url = await _store_evidence_file_for_root(decl.root_user_id, evidence_file)
        c.reason = (c.reason + f"\n[evidence] {public_url}").strip()

    db.commit()

    try:
        notify_admin_on_contest(db, c.id)
    except Exception as e:
        logger.error(f"notify_admin_on_contest failed for contest #{c.id}: {e}")

    return c

# ==============================
# Admin notifications & actions
# ==============================

def notify_admin_on_contest(db: Session, contest_id: int) -> None:
    try:
        admin_email = "nisha@theplanbeyond.com"
        c = db.query(Contest).filter(Contest.id == contest_id).first()
        if not c:
            return
        decl = db.query(DeathDeclaration).filter(DeathDeclaration.id == c.declaration_id).first()
        if not decl:
            return

        if decl.type == DeathType.hard or _has_hard_finalized(db, decl.root_user_id):
            logger.info(f"Ignoring contest #{c.id} (hard-finalized or hard type) for decl #{getattr(decl,'id','?')}")
            return

        root = db.query(User).filter(User.id == decl.root_user_id).first()
        cfg = _get_or_default_config(db, decl.root_user_id)

        window_end = decl.created_at + timedelta(days=cfg.contest_window_days or 7)
        exp_ts = int(window_end.timestamp())

        token_approve = _gen_quick_token(c.id, "approve", exp_ts)
        token_decline = _gen_quick_token(c.id, "decline", exp_ts)
        api_base = _get_api_base_url()

        approve_url = f"{api_base}/v1/death/contest/{c.id}/quick?decision=approve&token={token_approve}"
        decline_url = f"{api_base}/v1/death/contest/{c.id}/quick?decision=decline&token={token_decline}"

        root_name = getattr(root, "display_name", None) or "the contact"
        subject = f"Contest raised for soft-death announcement of {root_name} (Decl #{decl.id}, Contest #{c.id})"
        body_html = f"""
        <div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.5;">
          <p>A dispute was raised for the soft-death announcement of <strong>{root_name}</strong>.</p>
          <p>
            <a href="{approve_url}" style="background:#2e7d32;color:#fff;padding:8px 12px;border-radius:6px;text-decoration:none;">Approve</a>
            &nbsp;&nbsp;
            <a href="{decline_url}" style="background:#c62828;color:#fff;padding:8px 12px;border-radius:6px;text-decoration:none;">Decline</a>
          </p>
          <p style="color:#666;margin-top:8px;">
            Note: If no announcement was broadcast yet, approving the contest will not send a retraction.
          </p>
        </div>
        """.strip()

        _send_email_now(admin_email, subject, body_html, html=True)
    except Exception as e:
        logger.error(f"Failed to notify admin on contest #{contest_id}: {e}")

def notify_admin_on_hard_request(db: Session, declaration_id: int, evidence_url: Optional[str] = None) -> None:
    try:
        admin_email = "nisha@theplanbeyond.com"
        decl = db.query(DeathDeclaration).filter(DeathDeclaration.id == declaration_id).first()
        if not decl or decl.type != DeathType.hard:
            return
        root = db.query(User).filter(User.id == decl.root_user_id).first()
        root_name = getattr(root, "display_name", None) or "the contact"

        exp_ts = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        api_base = _get_api_base_url()

        token_accept = _gen_quick_token_hard(decl.id, "accept", exp_ts)
        token_reject = _gen_quick_token_hard(decl.id, "reject", exp_ts)

        accept_url = f"{api_base}/v1/death/hard/{decl.id}/quick?decision=accept&token={token_accept}"
        reject_url = f"{api_base}/v1/death/hard/{decl.id}/quick?decision=reject&token={token_reject}"

        evidence_html = f'<p><strong>Evidence:</strong> <a href="{evidence_url}">{evidence_url}</a></p>' if evidence_url else ""

        subject = f"Hard-death request for {root_name} requires verification (Decl #{decl.id})"
        body_html = f"""
        <div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;">
          <p>A hard-death request was submitted for <strong>{root_name}</strong>.</p>
          <p>Note from submitter: <em>{(decl.note or '—').strip()}</em></p>
          {evidence_html}
          <p>
            <a href="{accept_url}" style="background:#1e40af;color:#fff;padding:8px 12px;border-radius:6px;text-decoration:none;">Verify (Accept)</a>
            &nbsp;&nbsp;
            <a href="{reject_url}" style="background:#b91c1c;color:#fff;padding:8px 12px;border-radius:6px;text-decoration:none;">Reject</a>
          </p>
          <p style="color:#666;">These links are signed and will expire automatically.</p>
        </div>
        """.strip()

        _send_email_now(admin_email, subject, body_html, html=True)
    except Exception as e:
        logger.error(f"Failed to notify admin on hard request #{declaration_id}: {e}")

# ==============================
# Quick actions (email links)
# ==============================

def quick_decide_dispute(db: Session, *, contest_id: int, decision: str) -> tuple[bool, str]:
    c = db.query(Contest).filter(Contest.id == contest_id).first()
    if not c:
        return False, "Contest not found."

    decl = db.query(DeathDeclaration).filter(DeathDeclaration.id == c.declaration_id).first()
    if not decl:
        db.delete(c)
        db.commit()
        return True, "Contest removed (no declaration)."

    if decl.type == DeathType.hard or _has_hard_finalized(db, decl.root_user_id):
        db.delete(c)
        db.commit()
        return True, "Final hard-death recorded; contest closed."

    # SOFT flow
    if decision == "approve":
        was_broadcast = (decl.type == DeathType.soft and decl.state == DeclarationState.accepted)

        if was_broadcast:
            admin_retract_soft_death(db, admin_id=0, declaration_id=decl.id, reason="Contest approved (quick link)")
            db.query(Contest).filter(Contest.declaration_id == decl.id).delete(synchronize_session=False)
            db.commit()
            return True, "Approved: prior announcement retracted and records updated."
        else:
            db.query(Contest).filter(Contest.declaration_id == decl.id).delete(synchronize_session=False)
            try:
                db.delete(decl)
            except Exception:
                pass
            _update_lifecycle(db, decl.root_user_id, LifecycleState.alive)
            _audit(db, actor_type="system", actor_id=0, action="contest_approved_removed_pending",
                   entity_type="User", entity_id=decl.root_user_id, data={"contest_id": contest_id})
            db.commit()
            return True, "Approved: pending declaration removed (no broadcast was sent)."

    db.delete(c)
    db.flush()
    _audit(db, actor_type="system", actor_id=0, action="contest_declined_deleted",
           entity_type="Contest", entity_id=contest_id, data={})
    db.commit()
    return True, "Declined: contest deleted."

def _get_soft_broadcast_cfg(db: Session, *, root_user_id: int, created_at: datetime) -> dict:
    b = (
        db.query(Broadcast)
        .filter(
            Broadcast.root_user_id == root_user_id,
            Broadcast.type == BroadcastType.soft_death_announce,
            Broadcast.created_at >= created_at - timedelta(seconds=1),
        )
        .order_by(Broadcast.id.desc())
        .first()
    )
    try:
        return json.loads(b.audience_config_json) if (b and b.audience_config_json) else {}
    except Exception:
        return {}

# ==============================
# Admin: retraction / hard decisions / disputes
# ==============================

def admin_retract_soft_death(
    db: Session, *, admin_id: int, declaration_id: int, reason: str | None = None
) -> DeathDeclaration | None:
    decl = (
        db.query(DeathDeclaration)
        .filter(DeathDeclaration.id == declaration_id)
        .first()
    )
    if not decl or decl.type != DeathType.soft or decl.state != DeclarationState.accepted:
        return None

    cfg = _get_soft_broadcast_cfg(db, root_user_id=decl.root_user_id, created_at=decl.created_at)
    recipients = _resolve_audience_emails(db, root_user_id=decl.root_user_id, audience_config=cfg)

    root = db.query(User).filter(User.id == decl.root_user_id).first()
    root_name = getattr(root, "display_name", None) or "your contact"
    subject = f"Retraction: earlier soft-death announcement for {root_name} was incorrect"
    body = (
        f"Update: The previous soft-death announcement for {root_name} was incorrect.\n"
        f"{root_name} is alive. We apologize for the confusion."
        + (f"\n\nReason: {reason}" if (reason and reason.strip()) else "")
        + "\n\n— Plan Beyond"
    )
    if recipients:
        _send_bulk_emails_async(recipients, subject, body, delay_days=0, html=False)

    decl.state = DeclarationState.retracted
    db.add(Broadcast(
        type=BroadcastType.retraction,
        root_user_id=decl.root_user_id,
        audience_config_json=json.dumps(cfg or {}),
        channels=["email", "sms", "inapp"],
        content="Retraction: previous soft-death announcement has been withdrawn.",
        llm_safety_result=LLMSafetyCheck.passed,
        state=BroadcastState.queued,
    ))
    _update_lifecycle(db, decl.root_user_id, LifecycleState.alive)
    _audit(db, actor_type="admin", actor_id=admin_id, action="admin_retract_soft",
           entity_type="DeathDeclaration", entity_id=declaration_id, data={"reason": reason})

    db.commit()
    db.refresh(decl)
    return decl

def list_pending_hard(db: Session):
    return db.query(DeathDeclaration).filter(
        DeathDeclaration.type == DeathType.hard,
        DeathDeclaration.state == DeclarationState.pending_review
    ).order_by(DeathDeclaration.created_at.asc()).all()

def admin_decide_hard(
    db: Session, *, admin_id: int, declaration_id: int, decision: str, notes: str | None
) -> DeathDeclaration | None:
    decl = db.query(DeathDeclaration).filter(DeathDeclaration.id == declaration_id).first()
    if not decl or decl.type != DeathType.hard or decl.state != DeclarationState.pending_review:
        return None

    rev = db.query(DeathReview).filter(DeathReview.declaration_id == declaration_id).first()
    if not rev:
        rev = DeathReview(declaration_id=declaration_id)
        db.add(rev)

    now = datetime.utcnow()
    if decision == "accepted":
        rev.final_decision = ReviewDecision.accepted
        if notes and notes.strip():
            rev.notes = (rev.notes or "") + (("\n" if rev.notes else "") + notes.strip())
        rev.reviewed_at = now

        decl.state = DeclarationState.accepted
        db.add(DeathLock(root_user_id=decl.root_user_id, lock=DeathLockType.hard_finalized))
        _update_lifecycle(db, decl.root_user_id, LifecycleState.legend)

        soft_decl_ids = [d.id for d in db.query(DeathDeclaration).filter(
            DeathDeclaration.root_user_id == decl.root_user_id,
            DeathDeclaration.type == DeathType.soft
        ).all()]
        if soft_decl_ids:
            db.query(Contest).filter(
                Contest.declaration_id.in_(soft_decl_ids),
                Contest.status == ContestStatus.pending
            ).delete(synchronize_session=False)

        db.flush()
        _audit(db, actor_type="admin", actor_id=admin_id, action="decide_hard",
               entity_type="DeathDeclaration", entity_id=declaration_id, data={"decision": decision, "notes": notes})
        db.commit()
        db.refresh(decl)

        try:
            _notify_reviewers_on_hard_verified(db, decl)
        except Exception as e:
            logger.error(f"Failed to notify reviewers on hard verify decl #{decl.id}: {e}")

        try:
            _send_leaf_emails_after_hard_final(db, root_user_id=decl.root_user_id)
        except Exception as e:
            logger.error(f"Failed sending leaf emails for root_user_id={decl.root_user_id}: {e}")

        return decl

    # Rejected
    rev.final_decision = ReviewDecision.rejected
    if notes and notes.strip():
        rev.notes = (rev.notes or "") + (("\n" if rev.notes else "") + notes.strip())
    rev.reviewed_at = now

    decl.state = DeclarationState.rejected
    _update_lifecycle(
        db, decl.root_user_id,
        LifecycleState.soft_announced if _has_soft_accepted(db, decl.root_user_id) else LifecycleState.alive
    )

    db.flush()
    _audit(db, actor_type="admin", actor_id=admin_id, action="decide_hard",
           entity_type="DeathDeclaration", entity_id=declaration_id, data={"decision": decision, "notes": notes})
    db.commit()
    db.refresh(decl)
    return decl

def _notify_reviewers_on_hard_verified(db: Session, decl: DeathDeclaration) -> None:
    root = db.query(User).filter(User.id == decl.root_user_id).first()
    root_name = getattr(root, "display_name", None) or "the contact"

    trustees = set(_resolve_trustee_emails(db, root_user_id=decl.root_user_id, exclude_contact_id=decl.declared_by_contact_id))
    recipients = list(trustees)
    if not recipients:
        logger.info(f"No trustee recipients for hard-verified root_user_id={decl.root_user_id}")
        return

    subject = f"Hard-death verified for {root_name}"
    body = (
        f"An admin has verified a hard-death for {root_name}.\n"
        f"This decision is final. Soft-death contest windows are now closed.\n\n— Plan Beyond"
    )
    _send_bulk_emails_async(recipients, subject, body, delay_days=0, html=False)

def list_disputes(db: Session):
    return db.query(Contest).order_by(Contest.id.desc()).all()

# ---- Helper: build a safe response payload even if ORM row gets deleted later
def _contest_payload(c: Contest) -> dict:
    return {
        "id": c.id,
        "declaration_id": c.declaration_id,
        "status": getattr(c.status, "value", c.status),
        "decided_at": c.decided_at,
        "reason": c.reason,
    }

def admin_decide_dispute(
    db: Session, *, admin_id: int, contest_id: int, decision: str, notes: str | None
) -> dict | Contest | None:
    c = db.query(Contest).filter(Contest.id == contest_id).first()
    if not c or c.status != ContestStatus.pending:
        return None

    # Cache anything we will need later BEFORE we possibly delete the row
    contest_id_cached = c.id
    decl = db.query(DeathDeclaration).filter(DeathDeclaration.id == c.declaration_id).first()
    now = datetime.utcnow()

    # If the declaration is already gone, just mark/deliver and return a payload
    if not decl:
        c.status = ContestStatus.dismissed
        c.decided_at = now
        db.commit()
        return _contest_payload(c)

    # Hard finalized / hard type -> dismiss (keep contest row)
    if _has_hard_finalized(db, decl.root_user_id) or decl.type == DeathType.hard:
        c.status = ContestStatus.dismissed
        c.decided_at = now
        db.flush()
        _audit(
            db,
            actor_type="admin",
            actor_id=admin_id,
            action="dispute_dismissed_hard_final",
            entity_type="Contest",
            entity_id=contest_id_cached,
            data={"notes": notes},
        )
        db.commit()
        return _contest_payload(c)

    # ---- SOFT ----
    if decision == "uphold_rollback":
        # Build response now (safe values only)
        resp = {
            "id": contest_id_cached,
            "declaration_id": c.declaration_id,
            "status": ContestStatus.upheld_rollback.value,
            "decided_at": now,
            "reason": c.reason,
        }

        was_broadcast = (decl.state == DeclarationState.accepted)

        if was_broadcast:
            # Retract previously broadcast soft-death
            admin_retract_soft_death(db, admin_id=admin_id, declaration_id=decl.id, reason=notes)

            # Delete *all* contests for this declaration, including c
            db.query(Contest).filter(Contest.declaration_id == decl.id).delete(synchronize_session=False)

            # Use cached contest_id; do not access `c` after delete
            _audit(
                db,
                actor_type="admin",
                actor_id=admin_id,
                action="dispute_upheld_soft_retracted",
                entity_type="DeathDeclaration",
                entity_id=decl.id,
                data={"contest_id": contest_id_cached, "notes": notes},
            )
            db.commit()

            # Notify trustees about retraction
            try:
                _notify_trustees_on_contest_approved(db, decl, was_broadcast=True)
            except Exception as e:
                logger.error(f"notify trustees (retracted) failed for decl #{decl.id}: {e}")

            return resp

        else:
            # No broadcast yet: notify trustees first while decl still exists
            try:
                _notify_trustees_on_contest_approved(db, decl, was_broadcast=False)
            except Exception as e:
                logger.error(f"notify trustees (pending-removed) failed for decl #{decl.id}: {e}")

            # Remove all contests and the pending declaration
            db.query(Contest).filter(Contest.declaration_id == decl.id).delete(synchronize_session=False)
            try:
                db.delete(decl)
            except Exception:
                pass

            _update_lifecycle(db, decl.root_user_id, LifecycleState.alive)
            _audit(
                db,
                actor_type="admin",
                actor_id=admin_id,
                action="dispute_upheld_soft_removed_pending",
                entity_type="DeathDeclaration",
                entity_id=decl.id,
                data={"contest_id": contest_id_cached, "notes": notes},
            )
            db.commit()
            return resp
    if decision == "dismiss":
        # Mark the contest dismissed
        c.status = ContestStatus.dismissed
        c.decided_at = now
        db.flush()

        if decl.type == DeathType.soft and decl.state == DeclarationState.pending_review:
            decl.state = DeclarationState.accepted
            db.flush()
            # Broadcast the soft message now (only once)
            try:
                msg = decl.message or "A soft-death has been declared."
                _broadcast_soft_contacts(db, decl=decl, message_text=msg, audience_config={})
            except Exception as e:
                logger.error(f"Soft broadcast error on dismiss decl #{decl.id}: {e}")

            _update_lifecycle(db, decl.root_user_id, LifecycleState.soft_announced)
            _audit(
                db,
                actor_type="admin",
                actor_id=admin_id,
                action="dispute_dismissed_soft_promoted",
                entity_type="DeathDeclaration",
                entity_id=decl.id,
                data={"contest_id": contest_id_cached, "notes": notes},
            )

        else:
            # Already accepted or not a soft decl (shouldn't reach here) — just audit dismissal
            _audit(
                db,
                actor_type="admin",
                actor_id=admin_id,
                action="dispute_dismissed",
                entity_type="Contest",
                entity_id=contest_id_cached,
                data={"notes": notes},
            )

        db.commit()
        return _contest_payload(c)

    # ---------------- Default fallback (kept for safety) ----------------
    c.status = ContestStatus.dismissed
    c.decided_at = now
    db.flush()
    _audit(
        db,
        actor_type="admin",
        actor_id=admin_id,
        action="dispute_dismissed",
        entity_type="Contest",
        entity_id=contest_id_cached,
        data={"notes": notes},
    )
    db.commit()
    return _contest_payload(c)



# ==============================
# Acknowledge (no-op gate for soft accepted)
# ==============================

def acknowledge_soft_death(db: Session, *, trustee_user_id: int, declaration_id: int) -> bool:
    decl = db.query(DeathDeclaration).filter(DeathDeclaration.id == declaration_id).first()
    if not decl or decl.type != DeathType.soft or decl.state != DeclarationState.accepted:
        return False

    if _has_hard_finalized(db, decl.root_user_id):
        return False

    ok, _ = _actor_contact_if_authorized_for_root(
        db, actor_user_id=trustee_user_id, root_user_id=decl.root_user_id
    )
    if not ok:
        return False

    exists = (
        db.query(DeathAck)
        .filter(DeathAck.declaration_id == declaration_id, DeathAck.trustee_user_id == trustee_user_id)
        .first()
    )
    if exists:
        return True

    db.add(DeathAck(declaration_id=declaration_id, trustee_user_id=trustee_user_id))
    _audit(db, actor_type="trustee", actor_id=trustee_user_id, action="soft_ack",
           entity_type="DeathDeclaration", entity_id=declaration_id, data={})
    db.commit()
    return True

# ==============================
# Contests: creation gate
# ==============================

def create_contest(db: Session, *, actor_type: str, actor_id: int, declaration_id: int) -> Contest | None:
    decl = db.query(DeathDeclaration).filter(DeathDeclaration.id == declaration_id).first()
    if not decl:
        return None

    if decl.type == DeathType.hard or _has_hard_finalized(db, decl.root_user_id):
        return None

    cfg = _get_or_default_config(db, decl.root_user_id)
    window_end = decl.created_at + timedelta(days=cfg.contest_window_days or 7)
    if datetime.utcnow() > window_end:
        return None

    c = Contest(
        declaration_id=declaration_id,
        raised_by=actor_type,  # "root" | "trustee"
        raised_by_id=actor_id,
        reason="",
        evidence_file_id=None,
        status=ContestStatus.pending,
    )
    db.add(c)
    db.flush()
    return c

# ==============================
# Actor auth (trustees only)
# ==============================

def _actor_contact_if_authorized_for_root(
    db: Session, *, actor_user_id: int, root_user_id: int
) -> tuple[bool, int | None]:
    row_tr = (
        db.query(Trustee, Contact)
        .join(Contact, Contact.id == Trustee.contact_id)
        .filter(
            Trustee.user_id == root_user_id,
            Trustee.status == TrusteeStatus.accepted,
            Contact.linked_user_id == actor_user_id
        )
        .first()
    )
    if row_tr:
        _t, c = row_tr
        return True, c.id
    return False, None

# ==============================
# Pending soft banner helper
# ==============================

def get_pending_soft_info(db: Session, *, viewer_user_id: int, owner: str) -> dict:
    root_user_id = _resolve_root_user_id(db, owner)
    if not root_user_id:
        return {"pending": False, "root_user_id": None}

    if _has_hard_finalized(db, root_user_id):
        return {"pending": False, "root_user_id": root_user_id, "finalized_by_hard": True}

    decl = (
        db.query(DeathDeclaration)
        .filter(
            DeathDeclaration.root_user_id == root_user_id,
            DeathDeclaration.type == DeathType.soft,
            DeathDeclaration.state == DeclarationState.pending_review,
        )
        .order_by(DeathDeclaration.created_at.desc())
        .first()
    )
    if not decl:
        return {"pending": False, "root_user_id": root_user_id}

    ok, viewer_contact_id = _actor_contact_if_authorized_for_root(
        db, actor_user_id=viewer_user_id, root_user_id=root_user_id
    )
    declared_by_me = bool(ok and viewer_contact_id and viewer_contact_id == decl.declared_by_contact_id)

    return {
        "pending": True,
        "root_user_id": root_user_id,
        "declaration_id": decl.id,
        "message": decl.message,
        "declared_by_contact_id": decl.declared_by_contact_id,
        "declared_by_me": declared_by_me,
        "created_at": (decl.created_at.isoformat() + "Z"),
    }

def get_pending_soft_multi_info(
    db: Session, *, viewer_user_id: int
) -> dict:
    """
    Build pending-soft info for ALL root users reachable from viewer_user_id via contacts
    where Contact.linked_user_id == viewer_user_id.

    Returns:
      {"results": [SoftPendingRecord, ...]} 
      Each record includes:
        - declared_by_name (from Contact)
        - root_user_display_name (from User)
    """

    def _build_for_root(root_user_id: int) -> Dict[str, Any]:
        # Skip if hard-death finalized
        if _has_hard_finalized(db, root_user_id):
            # fetch root display_name even for finalized record
            user_display = (
                db.query(User.display_name)
                .filter(User.id == root_user_id)
                .scalar()
            )
            return {
                "pending": False,
                "root_user_id": root_user_id,
                "root_user_display_name": user_display,
                "finalized_by_hard": True,
            }

        # Fetch latest pending soft declaration
        decl = (
            db.query(DeathDeclaration)
            .filter(
                DeathDeclaration.root_user_id == root_user_id,
                DeathDeclaration.type == DeathType.soft,
                DeathDeclaration.state == DeclarationState.pending_review,
            )
            .order_by(DeathDeclaration.created_at.desc())
            .first()
        )

        # Always fetch root user display name
        root_user_display_name = (
            db.query(User.display_name)
            .filter(User.id == root_user_id)
            .scalar()
        )

        if not decl:
            return {
                "pending": False,
                "root_user_id": root_user_id,
                "root_user_display_name": root_user_display_name,
            }

        # Fetch declared_by contact info
        contact = (
            db.query(Contact.first_name, Contact.last_name)
            .filter(Contact.id == decl.declared_by_contact_id)
            .first()
        )

        declared_by_name = None
        if contact:
            declared_by_name = " ".join(
                filter(None, [contact.first_name, contact.last_name])
            ).strip() or None

        # Check if viewer declared it
        ok, viewer_contact_id = _actor_contact_if_authorized_for_root(
            db, actor_user_id=viewer_user_id, root_user_id=root_user_id
        )
        declared_by_me = bool(
            ok and viewer_contact_id and viewer_contact_id == decl.declared_by_contact_id
        )
        
        if declared_by_me:
            return None

        return {
            "pending": True,
            "root_user_id": root_user_id,
            "root_user_display_name": root_user_display_name,
            "declaration_id": decl.id,
            "message": decl.message,
            "declared_by_contact_id": decl.declared_by_contact_id,
            "declared_by_name": declared_by_name,
            "declared_by_me": declared_by_me,
            "created_at": (decl.created_at.isoformat() + "Z"),
        }

    # Find all owners whose contacts are linked to the viewer
    owner_ids_rows = (
        db.query(Contact.owner_user_id)
        .filter(Contact.linked_user_id == viewer_user_id)
        .distinct()
        .all()
    )
    root_user_ids = {row[0] for row in owner_ids_rows if row[0] is not None}

    if not root_user_ids:
        return {"results": []}

    results = [_build_for_root(ru_id) for ru_id in sorted(root_user_ids)]
    return {"results": results}

# ==============================
# Soft: notify on contest approved (trustees only)
# ==============================

def _notify_trustees_on_contest_approved(db: Session, decl: DeathDeclaration, *, was_broadcast: bool) -> None:
    try:
        root = db.query(User).filter(User.id == decl.root_user_id).first()
        root_name = getattr(root, "display_name", None) or "the contact"
        review_url = f"{_get_app_base_url()}/death-message/{decl.root_user_id}"

        recipients = _resolve_trustee_emails(db, root_user_id=decl.root_user_id, exclude_contact_id=None)
        if not recipients:
            return

        if was_broadcast:
            subject = f"Contest approved: soft-death retracted for {root_name}"
            body = (
                f"An admin approved a contest regarding the soft-death announcement for {root_name}.\n"
                f"The earlier announcement has been retracted and contacts have been notified.\n\n"
                f"Review: {review_url}\n\n— Plan Beyond"
            )
        else:
            subject = f"Contest approved: soft-death request removed for {root_name}"
            body = (
                f"An admin approved a contest while the soft-death was still pending review for {root_name}.\n"
                f"No broadcast went out. The pending declaration has been removed.\n\n"
                f"Review: {review_url}\n\n— Plan Beyond"
            )

        _send_bulk_emails_async(recipients, subject, body, delay_days=0, html=False)
    except Exception as e:
        logger.error(f"Failed to notify trustees on contest approval for decl #{getattr(decl, 'id', 'unknown')}: {e}")

# ==============================
# Pending hard banner helper
# ==============================
def get_pending_hard_info(db: Session, *, viewer_user_id: int, owner: str) -> dict:
    root_user_id = _resolve_root_user_id(db, owner)
    if not root_user_id:
        return {"pending": False, "root_user_id": None}

    if _has_hard_finalized(db, root_user_id):
        return {"pending": False, "root_user_id": root_user_id, "finalized_by_hard": True}

    decl = (
        db.query(DeathDeclaration)
        .filter(
            DeathDeclaration.root_user_id == root_user_id,
            DeathDeclaration.type == DeathType.hard,
            DeathDeclaration.state == DeclarationState.pending_review,
        )
        .order_by(DeathDeclaration.created_at.desc())
        .first()
    )
    if not decl:
        return {"pending": False, "root_user_id": root_user_id}

    ok, viewer_contact_id = _actor_contact_if_authorized_for_root(
        db, actor_user_id=viewer_user_id, root_user_id=root_user_id
    )
    declared_by_me = bool(ok and viewer_contact_id and viewer_contact_id == decl.declared_by_contact_id)

    return {
        "pending": True,
        "root_user_id": root_user_id,
        "declaration_id": decl.id,
        "note": decl.note,
        "declared_by_contact_id": decl.declared_by_contact_id,
        "declared_by_me": declared_by_me,
        "created_at": (decl.created_at.isoformat() + "Z"),
    }


# --- replace these helpers (no exp) ---
def _gen_quick_token_leaf(leaf_id: int, decision: str) -> str:
    from app.config import settings
    secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
    payload = {"lid": int(leaf_id), "dec": str(decision)}
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(secret, data, hashlib.sha256).digest()
    return f"{_b64url(data)}.{_b64url(sig)}"

def _verify_quick_token_leaf(token: str, leaf_id: int, decision: str) -> bool:
    try:
        from app.config import settings
        secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
        parts = token.split(".")
        if len(parts) != 2:
            return False
        data_b = _b64urldec(parts[0])
        sig_b  = _b64urldec(parts[1])
        exp_sig = hmac.new(secret, data_b, hashlib.sha256).digest()
        if not hmac.compare_digest(sig_b, exp_sig):
            return False
        payload = json.loads(data_b.decode())
        if int(payload.get("lid")) != int(leaf_id):
            return False
        if str(payload.get("dec")) != str(decision):
            return False
        # no expiry check
        return True
    except Exception:
        return False

def _gen_quick_token_leaf_bulk(root_user_id: int, contact_id: int, decision: str) -> str:
    """
    decision: "accept_all" | "reject_all"
    """
    from app.config import settings
    secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
    payload = {"rid": int(root_user_id), "cid": int(contact_id), "dec": str(decision)}
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(secret, data, hashlib.sha256).digest()
    return f"{_b64url(data)}.{_b64url(sig)}"


def _compose_leaf_accept_url(leaf_id: int, token: str) -> str:
    api = _get_api_base_url()
    return f"{api}/catalog/leaves/a/{leaf_id}/{token}"

def _compose_leaf_reject_url(leaf_id: int, token: str) -> str:
    api = _get_api_base_url()
    return f"{api}/catalog/leaves/r/{leaf_id}/{token}"


def _compose_leaf_bulk_accept_url(root_user_id: int, contact_id: int, token: str) -> str:
    api = _get_api_base_url()
    return f"{api}/catalog/leaves/a/bulk/{root_user_id}/{contact_id}/{token}"

def _compose_leaf_bulk_reject_url(root_user_id: int, contact_id: int, token: str) -> str:
    api = _get_api_base_url()
    return f"{api}/catalog/leaves/r/bulk/{root_user_id}/{contact_id}/{token}"


def _send_leaf_emails_after_hard_final(db: Session, *, root_user_id: int) -> None:
    """
    After hard-finalization, email assignees. If an assignee (contact) has multiple
    active leaves under the same root, send one BULK pair (Accept All / Decline All).
    Otherwise send single-leaf links.

    NOTE: Also triggers the Memories (time-based) kickoff ONCE after we finish the category emails.
    """
    q = (
        db.query(CategoryProgressLeaf, Contact, User)
        .join(Contact, Contact.id == CategoryProgressLeaf.contact_id)
        .outerjoin(User, User.id == Contact.linked_user_id)
        .filter(
            CategoryProgressLeaf.user_id == root_user_id,
            CategoryProgressLeaf.status == ProgressLeafStatus.active,
        )
    )
    rows = q.all()
    if not rows:
        logger.info(f"No active leaves for root_user_id={root_user_id}")
        # Still run the memories kickoff so time-based shares go out automatically
        try:
            from app.routers.memories import run_memories_on_hard_finalized
            res = run_memories_on_hard_finalized(db, owner_user_id=root_user_id)
            logger.info(f"Memories kickoff after hard-finalized (no category rows): {res}")
        except Exception:
            logger.exception("Failed to kickoff memories after hard-finalization")
        return

    from app.config import settings
    app_base = getattr(settings, "APP_URL", "https://app.example.com").rstrip("/")
    otp_start_url = f"{app_base}/otp/start"
    guest_verify_url = f"{app_base}/profile"
    signup_url = f"{app_base}/register"

    # Group by contact_id
    by_contact: dict[int, list[tuple[CategoryProgressLeaf, Contact, User | None]]] = {}
    for row in rows:
        leaf, contact, u = row
        if not contact:
            continue
        by_contact.setdefault(contact.id, []).append(row)

    # --- local helpers (no expiry in tokens) ---
    def _accept_url_for(leaf_id: int) -> str:
        tok_a = _gen_quick_token_leaf(leaf_id, "accept")
        return _compose_leaf_accept_url(leaf_id, tok_a)

    def _reject_url_for(leaf_id: int) -> str:
        tok_r = _gen_quick_token_leaf(leaf_id, "reject")
        return _compose_leaf_reject_url(leaf_id, tok_r)

    def _bulk_urls(contact_id: int) -> tuple[str, str]:
        tok_accept = _gen_quick_token_leaf_bulk(root_user_id, contact_id, "accept_all")
        tok_reject = _gen_quick_token_leaf_bulk(root_user_id, contact_id, "reject_all")
        accept_url = _compose_leaf_bulk_accept_url(root_user_id, contact_id, tok_accept)
        reject_url = _compose_leaf_bulk_reject_url(root_user_id, contact_id, tok_reject)
        return accept_url, reject_url

    # Send per-contact
    for contact_id, items in by_contact.items():
        # choose recipient email
        contact = items[0][1]
        to_email = contact.emails[0] if (contact and contact.emails) else None
        if not to_email:
            continue

        # auth stage routing based on linked user
        linked_user = items[0][2]
        if linked_user is None:
            _send_email_now(
                to_email,
                "Create your account to view items assigned to you",
                "Hello,\n\nA passing has been verified. You were designated to receive certain items in Plan Beyond. "
                f"Please create your account to continue:\n{signup_url}\n\n— Plan Beyond",
                html=False,
            )
            continue

        if not getattr(linked_user, "otp_verified", False):
            _send_email_now(
                to_email,
                "Verify your account (OTP) to view items assigned to you",
                "Hello,\n\nA passing has been verified. You were designated to receive certain items. "
                f"Please verify your account to continue:\n{otp_start_url}\n\n— Plan Beyond",
                html=False,
            )
            continue

        from app.models import user as user_models
        if getattr(linked_user, "status", None) in (user_models.UserStatus.unknown, user_models.UserStatus.guest):
            _send_email_now(
                to_email,
                "Complete your profile to view items assigned to you",
                "Hello,\n\nA passing has been verified. You were designated to receive certain items. "
                f"Please complete your profile verification to continue:\n{guest_verify_url}\n\n— Plan Beyond",
                html=False,
            )
            continue

        # fully verified/member:
        if len(items) == 1:
            leaf = items[0][0]
            accept_url = _accept_url_for(leaf.id)
            reject_url = _reject_url_for(leaf.id)
            _send_email_now(
                to_email,
                "Items assigned to you — confirm to proceed",
                "Hello,\n\nA passing has been verified, and items in selected categories/sections were assigned to you. "
                f"Please choose:\n\nAccept:  {accept_url}\nDecline: {reject_url}\n\n— Plan Beyond",
                html=False,
            )
        else:
            accept_url, reject_url = _bulk_urls(contact_id)
            _send_email_now(
                to_email,
                "Multiple items assigned to you — confirm once",
                "Hello,\n\nA passing has been verified, and multiple items were assigned to you. "
                f"Use one link below to apply to all of them:\n\nAccept All:  {accept_url}\nDecline All: {reject_url}\n\n— Plan Beyond",
                html=False,
            )

    # ---- Kick off Memories (time-based) once, after we finish category emails ----
    try:
        from app.routers.memories import run_memories_on_hard_finalized
        res = run_memories_on_hard_finalized(db, owner_user_id=root_user_id)  # correct kw + in-scope vars
        logger.info(f"Memories kickoff after hard-finalized: {res}")
    except Exception:
        # don't block if memories kickoff fails
        logger.exception("Failed to kickoff memories after hard-finalization")
