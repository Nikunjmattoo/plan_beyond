from sqlalchemy.orm import Session
from app.models.verification import IdentityVerification, VerificationMethod, VerificationStatus
from app.schemas.user import VerificationSubmit
from datetime import datetime

def submit_verification(db: Session, user_id: int, verification: VerificationSubmit):
    db_verification = IdentityVerification(
        user_id=user_id,
        method=verification.method,
        document_type=verification.document_type,
        document_ref=verification.document_ref,
        status=VerificationStatus.pending,
        created_at=datetime.utcnow()
    )
    db.add(db_verification)
    db.commit()
    db.refresh(db_verification)
    return db_verification