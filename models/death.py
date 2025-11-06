from sqlalchemy import (
    Column, Integer, String, Enum, Text, TIMESTAMP, ForeignKey, func, Boolean, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY
import enum
from app.database import Base

class DeathAck(Base):
    __tablename__ = "death_ack"
    __table_args__ = (UniqueConstraint("declaration_id", "trustee_user_id", name="uq_ack_decl_trustee"),)
    id = Column(Integer, primary_key=True)
    declaration_id = Column(Integer, ForeignKey("death_declarations.id", ondelete="CASCADE"), index=True, nullable=False)
    trustee_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

# -------- Enums --------
class DeathType(str, enum.Enum):
    soft = "soft"
    hard = "hard"

class DeclarationState(str, enum.Enum):
    pending_review = "pending_review"
    accepted = "accepted"
    rejected = "rejected"
    retracted = "retracted"

class LLMSafetyCheck(str, enum.Enum):
    pending = "pending"
    passed = "passed"
    flagged = "flagged"

class ReviewAutomated(str, enum.Enum):
    match = "match"
    mismatch = "mismatch"
    inconclusive = "inconclusive"

class ReviewDecision(str, enum.Enum):
    accepted = "accepted"
    rejected = "rejected"

class LifecycleState(str, enum.Enum):
    alive = "alive"
    soft_announced = "soft_announced"
    hard_review = "hard_review"
    legend = "legend"
    retired = "retired"

class ContestStatus(str, enum.Enum):
    pending = "pending"
    upheld_rollback = "upheld_rollback"
    dismissed = "dismissed"

class BroadcastType(str, enum.Enum):
    soft_death_announce = "soft_death_announce"
    retraction = "retraction"

class BroadcastState(str, enum.Enum):
    queued = "queued"
    sent = "sent"
    failed = "failed"

class DeathLockType(str, enum.Enum):
    hard_finalized = "hard_finalized"

# -------- Tables --------

class DeathDeclaration(Base):
    __tablename__ = "death_declarations"

    id = Column(Integer, primary_key=True)
    root_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    type = Column(Enum(DeathType), nullable=False)
    declared_by_contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)

    message = Column(Text, nullable=True)
    media_ids = Column(ARRAY(Integer), nullable=True)
    evidence_file_id = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)

    llm_safety_check = Column(Enum(LLMSafetyCheck), default=LLMSafetyCheck.pending, nullable=False)
    state = Column(Enum(DeclarationState), default=DeclarationState.pending_review, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

class DeathReview(Base):
    __tablename__ = "death_reviews"

    id = Column(Integer, primary_key=True)
    declaration_id = Column(Integer, ForeignKey("death_declarations.id", ondelete="CASCADE"), index=True, nullable=False)
    automated_result = Column(Enum(ReviewAutomated), default=ReviewAutomated.inconclusive, nullable=False)
    human_reviewer_id = Column(Integer, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    final_decision = Column(Enum(ReviewDecision), nullable=True)
    notes = Column(Text, nullable=True)
    reviewed_at = Column(TIMESTAMP, nullable=True)

class LegendLifecycle(Base):
    __tablename__ = "legend_lifecycle"

    id = Column(Integer, primary_key=True)
    root_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    state = Column(Enum(LifecycleState), default=LifecycleState.alive, nullable=False)
    entered_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    exited_at = Column(TIMESTAMP, nullable=True)

class Contest(Base):
    __tablename__ = "death_contests"

    id = Column(Integer, primary_key=True)
    declaration_id = Column(Integer, ForeignKey("death_declarations.id", ondelete="CASCADE"), index=True, nullable=False)
    raised_by = Column(String(16), nullable=False)  # "root" | "trustee"
    raised_by_id = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    evidence_file_id = Column(Integer, nullable=True)
    status = Column(Enum(ContestStatus), default=ContestStatus.pending, nullable=False)
    decided_at = Column(TIMESTAMP, nullable=True)

class Broadcast(Base):
    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True)
    type = Column(Enum(BroadcastType), nullable=False)
    root_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    audience_config_json = Column(Text, nullable=True)
    channels = Column(ARRAY(String), nullable=False)  # e.g. ["email","sms","inapp"]
    content = Column(Text, nullable=False)
    llm_safety_result = Column(Enum(LLMSafetyCheck), default=LLMSafetyCheck.pending, nullable=False)
    state = Column(Enum(BroadcastState), default=BroadcastState.queued, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

class Config(Base):
    __tablename__ = "death_config"

    root_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    soft_death_enabled = Column(Boolean, default=True, nullable=False)
    hard_death_allowed_for_branches = Column(Boolean, default=True, nullable=False)
    soft_broadcast_on_hard_enabled = Column(Boolean, default=True, nullable=False)
    contest_window_days = Column(Integer, default=7, nullable=False)

class DeathLock(Base):
    __tablename__ = "death_lock"

    root_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    lock = Column(Enum(DeathLockType), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    actor_type = Column(String(16), nullable=False)   # "root" | "trustee" | "admin" | "system"
    actor_id = Column(Integer, nullable=False)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(Integer, nullable=False)
    data_json = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
