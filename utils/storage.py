from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.models.user import User, UserPlan
from app.models.file import File

def get_storage_limit_bytes(plan: UserPlan) -> int:
    """Returns storage limit in bytes based on user plan"""
    if plan == UserPlan.basic:
        return 5 * 1024 * 1024 * 1024  # 5GB
    elif plan == UserPlan.pro:
        return 10 * 1024 * 1024 * 1024  # 10GB
    elif plan == UserPlan.professional:
        return 15 * 1024 * 1024 * 1024  # 15GB
    return 0

def get_user_used_storage(db: Session, user_id: int) -> int:
    """Returns total storage used by user in bytes"""
    total_size = db.query(func.sum(File.size)).filter(File.user_id == user_id).scalar()
    return total_size or 0

def check_storage_available(db: Session, user_id: int, file_size: int) -> bool:
    """Check if user has enough storage space for new file"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    used_storage = get_user_used_storage(db, user_id)
    storage_limit = get_storage_limit_bytes(user.plan)
    
    return (used_storage + file_size) <= storage_limit