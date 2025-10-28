from sqlalchemy import (
    Column, Integer, Text, TIMESTAMP, ForeignKey, func, Enum, String,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base

# -------------------- Enums --------------------

class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    declined = "declined"
    removed = "removed"

class LeafRole(str, enum.Enum):
    leaf = "leaf"
    fallback_leaf = "fallback_leaf"

class TriggerType(str, enum.Enum):
    time_based = "time_based"
    event_based = "event_based"

class TriggerState(str, enum.Enum):
    configured = "configured"
    scheduled = "scheduled"
    fired = "fired"
    cancelled = "cancelled"

class FolderComputedStatus(str, enum.Enum):
    complete = "complete"
    incomplete = "incomplete"

# -------------------- Core Models --------------------

class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    files = relationship("File", back_populates="folder", cascade="all, delete-orphan")
    branches = relationship("FolderBranch", back_populates="folder", cascade="all, delete-orphan")
    leaves = relationship("FolderLeaf", back_populates="folder", cascade="all, delete-orphan")
    trigger = relationship(
        "FolderTrigger",
        back_populates="folder",
        uselist=False,
        cascade="all, delete-orphan"
    )

class FolderBranch(Base):
    __tablename__ = "folder_branches"
    __table_args__ = (
        UniqueConstraint("folder_id", "contact_id", name="uq_folder_branch"),
    )

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)

    status = Column(Enum(AssignmentStatus), nullable=False, default=AssignmentStatus.pending)
    accepted_at = Column(TIMESTAMP, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    folder = relationship("Folder", back_populates="branches")

class FolderLeaf(Base):
    __tablename__ = "folder_leaves"
    __table_args__ = (
        UniqueConstraint("folder_id", "contact_id", "role", name="uq_folder_leaf"),
    )

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)

    role = Column(Enum(LeafRole), nullable=False, default=LeafRole.leaf)
    status = Column(Enum(AssignmentStatus), nullable=False, default=AssignmentStatus.pending)
    accepted_at = Column(TIMESTAMP, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    folder = relationship("Folder", back_populates="leaves")

class FolderTrigger(Base):
    __tablename__ = "folder_triggers"
    __table_args__ = (
        UniqueConstraint("folder_id", name="uq_folder_trigger_singleton"),
    )

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)

    type = Column(Enum(TriggerType), nullable=False)

    time_at = Column(TIMESTAMP, nullable=True)
    timezone = Column(String, nullable=True)

    event_label = Column(Text, nullable=True)

    state = Column(Enum(TriggerState), nullable=False, default=TriggerState.configured)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    folder = relationship("Folder", back_populates="trigger")