from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum

class VerificationMethod(enum.Enum):
    document = "document"
    referral = "referral"
    other = "other"

class VerificationStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class IdentityVerification(Base):
    __tablename__ = "identity_verifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    method = Column(Enum(VerificationMethod), nullable=False)
    document_type = Column(String, nullable=True)
    document_ref = Column(String, nullable=True)
    status = Column(Enum(VerificationStatus), default=VerificationStatus.pending, nullable=False)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="verifications")

class UserStatusHistory(Base):
    __tablename__ = "user_status_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="status_history")