# routers/user.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field

from app.schemas.user import UserProfileResponse, UserUpdate
from app.controller import user as user_crud
from app.database import SessionLocal
from app.dependencies import get_current_user, get_current_admin
from app.models.user import User, UserProfile, UserStatus
from app.models.contact import Contact
from app.models.admin import Admin

# ✅ Reuse mailers from routers.auth (single, correct import line)
from app.routers.auth import (
    send_relationship_emails_for_pending_requests,
    send_trustee_emails_for_pending_invites,
    send_memory_branch_emails_for_pending_invites,
    send_leaf_stage_emails_for_user,
    send_memories_leaf_emails_for_user,
    send_message_branch_emails_for_pending_invites,
    send_messages_leaf_emails_for_user,
)



router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- helpers for merge/split ---

USER_FIELDS = {
    "display_name", "email", "phone", "communication_channel", "password"
}
PROFILE_FIELDS = {
    "title", "first_name", "middle_name", "last_name", "date_of_birth", "anniversary",
    "gender", "address_line_1", "address_line_2", "city", "state", "zip_code",
    "country", "profile_image"
}

class StatusToggle(BaseModel):
    verified: int = Field(..., ge=0, le=1, description="0=guest, 1=verified")

def ensure_profile(db: Session, user: User) -> User:
    """Guarantee a profile row exists for the user."""
    if user.profile is None:
        user.profile = UserProfile(user_id=user.id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def combine_user_and_profile(u: User) -> dict:
    p = u.profile
    out = {
        "id": u.id,
        "display_name": u.display_name,
        "email": u.email,
        "phone": u.phone,
        "country_code": getattr(u, "country_code", None),  # <— NEW
        "communication_channel": u.communication_channel,
        "status": u.status.value if hasattr(u.status, "value") else u.status,
        "created_at": u.created_at,
        "otp_verified": u.otp_verified,
    }
    if p:
        out.update({
            "title": p.title,
            "first_name": p.first_name,
            "middle_name": p.middle_name,
            "last_name": p.last_name,
            "date_of_birth": p.date_of_birth,
            "anniversary": p.anniversary, 
            "gender": p.gender,
            "address_line_1": p.address_line_1,
            "address_line_2": p.address_line_2,
            "city": p.city,
            "state": p.state,
            "zip_code": p.zip_code,
            "country": p.country,
            "profile_image": p.profile_image,
        })
    return out


# --- /users/me ---

@router.get("/me", response_model=UserProfileResponse)
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = ensure_profile(db, user)
    return combine_user_and_profile(user)

@router.put("/me", response_model=UserProfileResponse)
def update_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = ensure_profile(db, user)

    payload = user_update.dict(exclude_unset=True)

    if "communication_channel" in payload and payload["communication_channel"] is not None:
        cc = payload["communication_channel"]
        payload["communication_channel"] = getattr(cc, "value", cc)

    for k, v in payload.items():
        if k in USER_FIELDS:
            if k == "password" and v:
                user.password = v
            else:
                setattr(user, k, v)
        elif k in PROFILE_FIELDS:
            setattr(user.profile, k, v)

    user.updated_at = datetime.utcnow()
    user.profile.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)

    return combine_user_and_profile(user)

@router.delete("/me")
def delete_my_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted_user = user_crud.delete_user(db, user_id=current_user.id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}

# --- Admin endpoints ---

@router.get("", response_model=List[UserProfileResponse])
def get_users_admin_only(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    users_with_counts = user_crud.get_all_users_with_contact_counts(db)
    out: List[dict] = []
    for user, contact_count in users_with_counts:
        user = ensure_profile(db, user)
        merged = combine_user_and_profile(user)
        merged["contact_count"] = contact_count
        out.append(merged)
    return out

@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = ensure_profile(db, user)
    merged = combine_user_and_profile(user)

    contact_count = db.query(Contact).filter(Contact.owner_user_id == user_id).count()
    merged["contact_count"] = contact_count
    return merged

@router.get("/admin/me")
def get_admin_me(current_admin: Admin = Depends(get_current_admin)):
    return {"id": current_admin.id, "username": current_admin.username, "email": current_admin.email}

@router.put("/me/status-verify", response_model=UserProfileResponse)
def set_my_status_toggle(
    toggle: StatusToggle,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.status == UserStatus.member:
        raise HTTPException(status_code=400, detail="Members cannot change status with this toggle.")

    target_status = UserStatus.verified if toggle.verified == 1 else UserStatus.guest
    if user.status == target_status:
        user = ensure_profile(db, user)
        return combine_user_and_profile(user)

    prev_status = user.status
    if user.status in (UserStatus.unknown, UserStatus.guest, UserStatus.verified):
        user.status = target_status
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)

        # When transitioning TO verified, send follow-ups once.
        if prev_status != UserStatus.verified and target_status == UserStatus.verified:
            try:
                send_relationship_emails_for_pending_requests(db, user)
                send_trustee_emails_for_pending_invites(db, user)
                send_memory_branch_emails_for_pending_invites(db, user)
                send_leaf_stage_emails_for_user(db, user)  # ✅ new
                send_memories_leaf_emails_for_user(db, user)
                send_message_branch_emails_for_pending_invites(db, user)
                send_messages_leaf_emails_for_user(db, user)


            except Exception:
                # Never block the toggle on email failures
                pass

        user = ensure_profile(db, user)
        return combine_user_and_profile(user)

    raise HTTPException(status_code=400, detail="Unsupported status transition.")
