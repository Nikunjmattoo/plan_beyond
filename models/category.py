# app/models/category.py
from sqlalchemy import Column, Integer, ForeignKey, Text, Enum, UniqueConstraint, TIMESTAMP, func, Boolean
from app.database import Base
from app.models.enums import EventType
import enum

class CategoryMaster(Base):
    __tablename__ = "categories_master"

    id = Column(Integer, primary_key=True)
    code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    sort_index = Column(Integer, default=0)
    # optional icon name (e.g., "Banknote", "Shield", etc.)
    icon = Column(Text, nullable=True)

class CategorySectionMaster(Base):
    __tablename__ = "category_sections_master"
    __table_args__ = (
        UniqueConstraint("category_id", "code", name="uq_category_section_code_per_category"),
    )

    id = Column(Integer, primary_key=True)
    category_id = Column(ForeignKey("categories_master.id", ondelete="CASCADE"), index=True, nullable=False)
    code = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    sort_index = Column(Integer, default=0)
    # NEW: file import flag for the section
    file_import = Column(Boolean, nullable=False, default=False)

class UserCategory(Base):
    __tablename__ = "user_categories"
    __table_args__ = (UniqueConstraint("user_id","category_id", name="uq_user_category_once"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id = Column(ForeignKey("categories_master.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type = Column(Enum(EventType), nullable=False, default=EventType.after_death)

class UserCategorySection(Base):
    __tablename__ = "user_category_sections"
    __table_args__ = (UniqueConstraint("user_category_id","section_master_id", name="uq_user_category_section_once"),)

    id = Column(Integer, primary_key=True)
    user_category_id = Column(ForeignKey("user_categories.id", ondelete="CASCADE"), index=True, nullable=False)
    section_master_id = Column(ForeignKey("category_sections_master.id", ondelete="CASCADE"), index=True, nullable=False)

class CategoryFile(Base):
    __tablename__ = "category_files"

    id = Column(Integer, primary_key=True)
    user_category_section_id = Column(ForeignKey("user_category_sections.id", ondelete="CASCADE"), index=True, nullable=False)
    file_id = Column(ForeignKey("files.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(Text)

class CategoryLeafAssignment(Base):
    __tablename__ = "category_leaf_assignments"
    __table_args__ = (UniqueConstraint("user_category_section_id","contact_id", name="uq_category_leaf"),)

    id = Column(Integer, primary_key=True)
    user_category_section_id = Column(ForeignKey("user_category_sections.id", ondelete="CASCADE"), index=True, nullable=False)
    contact_id = Column(ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)

class ProgressLeafStatus(str, enum.Enum):
    active   = "active"
    accepted = "accepted"
    removed  = "removed"

class CategoryProgressLeaf(Base):
    __tablename__ = "category_progress_leaf"
    __table_args__ = (UniqueConstraint("progress_id", "contact_id", name="uq_progress_leaf_once"),)

    id = Column(Integer, primary_key=True)
    user_id     = Column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id = Column(ForeignKey("categories_master.id", ondelete="CASCADE"), index=True, nullable=False)
    section_id  = Column(ForeignKey("category_sections_master.id", ondelete="CASCADE"), index=True, nullable=False)
    progress_id = Column(ForeignKey("user_section_progress.id", ondelete="CASCADE"), index=True, nullable=False)
    contact_id  = Column(ForeignKey("contacts.id", ondelete="CASCADE"), index=True, nullable=False)

    status = Column(
        Enum(
            ProgressLeafStatus,
            name="categoryprogressleafstatus",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=ProgressLeafStatus.active,
    )

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
