from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, func, Enum, UniqueConstraint, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import TrusteeStatus

class Trustee(Base):
    __tablename__ = "trustees"
    __table_args__ = (
        UniqueConstraint("user_id", "contact_id", name="uq_trustee_one_per_contact"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    contact_id = Column(ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)

    status = Column(Enum(TrusteeStatus), default=TrusteeStatus.invited, nullable=False)

    invited_at = Column(TIMESTAMP, server_default=func.now())
    responded_at = Column(TIMESTAMP)

    is_primary = Column(Boolean, default=False, nullable=False)
    version = Column(Integer, default=0, nullable=False)

    # NEW: public invite token & expiry (for email Accept/Decline links)
    invite_token = Column(Text)               # random token sent by email
    invite_expires_at = Column(TIMESTAMP)     # optional expiry for the token
