
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, func, Enum, JSON
from app.database import Base
from app.models.enums import ReleaseScope, ReleaseReason

class Release(Base):
    __tablename__ = "releases"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    scope = Column(Enum(ReleaseScope), nullable=False)
    scope_id = Column(Integer, nullable=False)
    reason = Column(Enum(ReleaseReason), nullable=False)
    triggered_by_contact_id = Column(ForeignKey("contacts.id"), nullable=True)
    released_at = Column(TIMESTAMP, server_default=func.now())

class ReleaseRecipient(Base):
    __tablename__ = "release_recipients"
    id = Column(Integer, primary_key=True)
    release_id = Column(ForeignKey("releases.id", ondelete="CASCADE"), index=True, nullable=False)
    contact_id = Column(ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)
    delivery_status = Column(Enum("queued","sent","failed","opened", name="delivery_status"), nullable=False, server_default="queued")
    delivery_meta = Column(JSON)
