from sqlalchemy import (
    Column, Integer, ForeignKey, TIMESTAMP, func, Text, Enum, Boolean,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import EventType, AssignmentRole, FolderStatus, BranchInviteStatus

class MemoryCollection(Base):
    __tablename__ = "memory_collections"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)

    event_type = Column(Enum(EventType), default=EventType.event, nullable=False)
    scheduled_at = Column(TIMESTAMP)                 # time-based trigger
    event_label = Column(Text)                       # event-based trigger label

    is_armed = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(FolderStatus), default=FolderStatus.incomplete, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    files = relationship("MemoryFile", cascade="all, delete-orphan", backref="collection")
    folder_assignments = relationship("MemoryCollectionAssignment", cascade="all, delete-orphan", backref="collection")

class MemoryFile(Base):
    __tablename__ = "memory_files"
    id = Column(Integer, primary_key=True)
    collection_id = Column(ForeignKey("memory_collections.id", ondelete="CASCADE"), index=True, nullable=False)

    file_id = Column(ForeignKey("files.id", ondelete="SET NULL"), index=True, nullable=True)

    app_url = Column(Text, nullable=True)
    mime_type = Column(Text, nullable=True)
    size = Column(Integer, nullable=True)
    title = Column(Text)

    __table_args__ = (
        UniqueConstraint("collection_id", "app_url", name="uq_collection_app_url"),
    )

class MemoryFileAssignment(Base):
    __tablename__ = "memory_file_assignments"
    __table_args__ = (UniqueConstraint("memory_file_id","contact_id","role", name="uq_mf_assignment"),)
    id = Column(Integer, primary_key=True)
    memory_file_id = Column(ForeignKey("memory_files.id", ondelete="CASCADE"), index=True, nullable=False)
    contact_id = Column(ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(Enum(AssignmentRole), nullable=False)

class MemoryCollectionAssignment(Base):
    __tablename__ = "memory_collection_assignments"
    __table_args__ = (UniqueConstraint("collection_id", "contact_id", "role", name="uq_collection_assignment"),)
    id = Column(Integer, primary_key=True)
    collection_id = Column(ForeignKey("memory_collections.id", ondelete="CASCADE"), index=True, nullable=False)
    contact_id = Column(ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(Enum(AssignmentRole), nullable=False)

    # ✅ NEW: only used for role == branch (email invite lifecycle)
    invite_status = Column(Enum(BranchInviteStatus), nullable=True)  # sent | accepted | declined
    invited_at = Column(TIMESTAMP)
    responded_at = Column(TIMESTAMP)
    invite_token = Column(Text)          # short token for public accept/decline
    invite_expires_at = Column(TIMESTAMP)
