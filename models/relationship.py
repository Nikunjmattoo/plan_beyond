# app/models/relationship.py
from sqlalchemy import (
    Column, Integer, String, Enum, Text, TIMESTAMP, ForeignKey, func, UniqueConstraint
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class RequestStatus(str, enum.Enum):
    sent = "sent"
    accepted = "accepted"
    rejected = "rejected"
    revoked = "revoked"
    expired = "expired"

class RelationshipRequest(Base):
    __tablename__ = "relationship_requests"
    __table_args__ = (
        # one active (sent) invite per (folder, contact)
        UniqueConstraint(
            "folder_id", "contact_id", "status", name="uq_relreq_folder_contact_sent"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)

    token = Column(String(64), nullable=False, index=True)
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.sent)

    # optional metadata
    sent_via = Column(String(32), nullable=True)  # "email" | "sms" | "whatsapp"
    message = Column(Text, nullable=True)
    expires_at = Column(TIMESTAMP, nullable=True)
    accepted_at = Column(TIMESTAMP, nullable=True)
    rejected_at = Column(TIMESTAMP, nullable=True)
    revoked_at = Column(TIMESTAMP, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # soft refs (no back_populates needed)
