from sqlalchemy import Column, Integer, Text, String, Enum, Boolean, ForeignKey, TIMESTAMP, func, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class StepType(str, enum.Enum):
    list = "list"
    hierarchical = "hierarchical"
    single_select = "single_select"
    checklist = "checklist"
    open = "open"
    date_mm_yyyy = "date_mm_yyyy"
    date_dd_mm_yyyy = "date_dd_mm_yyyy"
    google_location = "google_location"
    photo = "photo"
    file_upload = "file_upload"

class FormStep(Base):
    __tablename__ = "form_steps"
    __table_args__ = (
        UniqueConstraint("section_master_id", "display_order", name="uq_section_step_order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    # NOTE: this points to the *master* section definition
    section_master_id = Column(Integer, ForeignKey("category_sections_master.id", ondelete="CASCADE"), nullable=False)

    step_name = Column(Text, nullable=False)
    question_id = Column(String, nullable=True)
    title = Column(Text, nullable=False)
    top_one_liner = Column(Text, nullable=True)
    bottom_one_line = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=False, default=1)

    type = Column(Enum(StepType), nullable=False)
    nested = Column(Boolean, nullable=False, default=False)

    validation = Column(Boolean, nullable=False, default=False)
    mandatory = Column(Boolean, nullable=False, default=False)
    skippable = Column(Boolean, nullable=False, default=True)
    eligible_reminder = Column(Boolean, nullable=False, default=False)
    privacy_nudge = Column(Boolean, nullable=False, default=False)
    privacy_liner = Column(Text, nullable=True)

    # free-form config bucket (child_list, parent_step_id, reference_object, etc.)
    config = Column(JSON, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    options = relationship("StepOption", back_populates="step", cascade="all, delete-orphan", order_by="StepOption.display_order")

class StepOption(Base):
    __tablename__ = "step_options"
    __table_args__ = (
        UniqueConstraint("step_id", "value", name="uq_step_option_value"),
    )

    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("form_steps.id", ondelete="CASCADE"), nullable=False)

    label = Column(Text, nullable=False)
    value = Column(Text, nullable=False)
    display_order = Column(Integer, nullable=False, default=1)

    parent_option_id = Column(Integer, ForeignKey("step_options.id", ondelete="CASCADE"), nullable=True)
    meta = Column(JSON, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    step = relationship("FormStep", back_populates="options")
    parent_option = relationship("StepOption", remote_side=[id], uselist=False)
