# app/models/user_forms.py
from uuid import uuid4
from sqlalchemy import Boolean, Column, Integer, TIMESTAMP, ForeignKey, String, func, Enum, UniqueConstraint, JSON
from app.database import Base
import enum

class SectionProgressStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"

class UserSectionProgress(Base):
    __tablename__ = "user_section_progress"
    
    id = Column(Integer, primary_key=True)
    section_photo_url = Column(String(512), nullable=True) 
    display_name = Column(String(255), nullable=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id = Column(ForeignKey("categories_master.id", ondelete="CASCADE"), index=True, nullable=False)
    section_id = Column(ForeignKey("category_sections_master.id", ondelete="CASCADE"), index=True, nullable=False)
    record_key = Column(String(64), nullable=False, default=lambda: uuid4().hex, index=True)
    
    # IMPORTANT: same named DB enum everywhere
    status = Column(
        Enum(SectionProgressStatus, name="sectionprogressstatus"),
        nullable=False,
        default=SectionProgressStatus.draft,
    )
    saved_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    submitted_at = Column(TIMESTAMP, nullable=True)

class UserStepAnswer(Base):
    __tablename__ = "user_step_answers"
    __table_args__ = (UniqueConstraint("progress_id","step_id", name="uq_answer_once"),)

    id = Column(Integer, primary_key=True)
    progress_id = Column(ForeignKey("user_section_progress.id", ondelete="CASCADE"), index=True, nullable=False)
    step_id = Column(ForeignKey("form_steps.id", ondelete="CASCADE"), index=True, nullable=False)
    value = Column(JSON, nullable=True)

class UserStepReminder(Base):
    __tablename__ = "user_step_reminders"
    __table_args__ = (UniqueConstraint("progress_id", "step_id", name="uq_reminder_once"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    wants_reminder = Column(Boolean, nullable=False, server_default="false")

    category_id = Column(ForeignKey("categories_master.id", ondelete="CASCADE"), index=True, nullable=False)
    section_id  = Column(ForeignKey("category_sections_master.id", ondelete="CASCADE"), index=True, nullable=False)
    progress_id = Column(ForeignKey("user_section_progress.id", ondelete="CASCADE"), index=True, nullable=False)
    step_id     = Column(ForeignKey("form_steps.id", ondelete="CASCADE"), index=True, nullable=False)

    enabled   = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
