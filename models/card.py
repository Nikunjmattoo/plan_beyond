from sqlalchemy import (
    Column, Integer, Text, Boolean, ForeignKey, TIMESTAMP, func, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

class SectionItemTemplate(Base):
    """
    Admin-managed template for a default 'card' that appears under a Section.
    One template belongs to a SectionMaster (category_sections_master).
    """
    __tablename__ = "section_item_templates"
    __table_args__ = (
        UniqueConstraint("section_master_id", "code", name="uq_template_code_per_section"),
        UniqueConstraint("section_master_id", "sort_index", name="uq_template_order_per_section"),
    )

    id = Column(Integer, primary_key=True)
    section_master_id = Column(ForeignKey("category_sections_master.id", ondelete="CASCADE"),
                               index=True, nullable=False)

    # short code so you can reference/update easily (e.g. "new_home", "new_vehicle")
    code = Column(Text, nullable=False)
    name = Column(Text, nullable=False)        # text shown on the card
    icon = Column(Text, nullable=True)         # frontend icon key (string)
    sort_index = Column(Integer, default=0)    # order within the section

    # flags to help the UI
    is_recommended = Column(Boolean, nullable=False, default=False)
    is_pre_populated = Column(Boolean, nullable=False, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class UserSectionItem(Base):
    """
    The actual card row a user sees inside a Section.
    Usually copied from a SectionItemTemplate on first init.
    Users can later create their own ad-hoc cards too (template_id = NULL).
    """
    __tablename__ = "user_section_items"
    __table_args__ = (
        UniqueConstraint("user_category_section_id", "template_id",
                         name="uq_user_section_item_template_once"),
    )

    id = Column(Integer, primary_key=True)
    user_category_section_id = Column(ForeignKey("user_category_sections.id", ondelete="CASCADE"),
                                      index=True, nullable=False)

    template_id = Column(ForeignKey("section_item_templates.id", ondelete="SET NULL"),
                         index=True, nullable=True)

    title = Column(Text, nullable=False)       # card title shown to user
    icon = Column(Text, nullable=True)
    sort_index = Column(Integer, default=0)
    is_pre_populated = Column(Boolean, nullable=False, default=False)
    is_recommended = Column(Boolean, nullable=False, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
