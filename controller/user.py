# controller/user.py
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import user as models
from app.schemas import user as schemas
from app.core.security import hash_password
from app.models.contact import Contact
from datetime import datetime
from typing import Optional
def create_user(db: Session, user: schemas.UserCreate):
    hashed_pw = hash_password(user.password) if user.password else None
    db_user = models.User(
        display_name=user.display_name,
        email=user.email,
        phone=user.phone,
        country_code=user.country_code, 
        password=hashed_pw,
        communication_channel=user.communication_channel.value if user.communication_channel else None,
        status=models.UserStatus.unknown,
        otp=None,
        otp_expires_at=None,
        otp_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_display_name(db: Session, display_name: str):
    return db.query(models.User).filter(models.User.display_name == display_name).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(models.User).filter(models.User.phone == phone).first()

def update_user(db: Session, user_id: int, updates: schemas.UserUpdate):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None

    if updates.display_name is not None:
        user.display_name = updates.display_name
    if updates.email is not None:
        user.email = updates.email
    if updates.phone is not None:
        user.phone = updates.phone
    if updates.country_code is not None:          
        # normalize leading +
        cc = updates.country_code.strip() if isinstance(updates.country_code, str) else updates.country_code
        if cc and not cc.startswith("+"):
            cc = f"+{cc}"
        user.country_code = cc
    if updates.communication_channel is not None:
        user.communication_channel = updates.communication_channel.value
    if updates.password:
        user.password = hash_password(updates.password)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user

def get_all_users_with_contact_counts(db: Session):
    return db.query(
        models.User,
        func.count(Contact.id).label('contact_count')
    ).outerjoin(
        Contact, models.User.id == Contact.owner_user_id  
    ).group_by(
        models.User.id
    ).all()

def get_user_by_phone_and_cc(db: Session, phone: str, country_code: Optional[str]):
    q = db.query(models.User).filter(models.User.phone == phone)
    if country_code:
        q = q.filter(models.User.country_code == (country_code if country_code.startswith("+") else f"+{country_code}"))
    return q.first()
