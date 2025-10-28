from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.card import SectionItemTemplate, UserSectionItem
from app.models.category import CategorySectionMaster, UserCategorySection, UserCategory

# -------------------- Admin: Template CRUD --------------------

def create_template(db: Session, data) -> SectionItemTemplate:
    # verify section exists
    sec = db.query(CategorySectionMaster).filter(
        CategorySectionMaster.id == data.section_master_id
    ).first()
    if not sec:
        raise ValueError("Section master not found")

    t = SectionItemTemplate(**data.dict())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def update_template(db: Session, template_id: int, data) -> Optional[SectionItemTemplate]:
    t = db.query(SectionItemTemplate).filter(SectionItemTemplate.id == template_id).first()
    if not t:
        return None
    for k, v in data.dict(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t

def delete_template(db: Session, template_id: int) -> bool:
    t = db.query(SectionItemTemplate).filter(SectionItemTemplate.id == template_id).first()
    if not t:
        return False
    db.delete(t)
    db.commit()
    return True

def list_templates(db: Session, section_master_id: Optional[int] = None) -> List[SectionItemTemplate]:
    q = db.query(SectionItemTemplate)
    if section_master_id:
        q = q.filter(SectionItemTemplate.section_master_id == section_master_id)
    return q.order_by(SectionItemTemplate.sort_index.asc(), SectionItemTemplate.id.asc()).all()

# -------------------- User init / copy defaults --------------------

def ensure_default_items_for_user_section(db: Session, user_section: UserCategorySection):
    """
    Copy templates under this section to concrete user cards (if not already copied).
    """
    templates = db.query(SectionItemTemplate).filter(
        SectionItemTemplate.section_master_id == user_section.section_master_id
    ).order_by(SectionItemTemplate.sort_index.asc()).all()

    existing = {
        row.template_id for row in db.query(UserSectionItem)
        .filter(UserSectionItem.user_category_section_id == user_section.id).all()
        if row.template_id is not None
    }

    created = 0
    for t in templates:
        if t.id in existing:
            continue
        db.add(
            UserSectionItem(
                user_category_section_id=user_section.id,
                template_id=t.id,
                title=t.name,
                icon=t.icon,
                sort_index=t.sort_index,
                is_pre_populated=t.is_pre_populated,
                is_recommended=t.is_recommended,
            )
        )
        created += 1

    if created:
        db.commit()

def ensure_default_items_for_user(db: Session, user_id: int) -> int:
    """
    Copy templates for ALL sections of this user.
    Returns number of sections that received at least one new default card.
    """
    sections = (
        db.query(UserCategorySection)
        .join(UserCategory, UserCategorySection.user_category_id == UserCategory.id)
        .filter(UserCategory.user_id == user_id)
        .all()
    )

    touched = 0
    for s in sections:
        before = db.query(UserSectionItem).filter(
            UserSectionItem.user_category_section_id == s.id
        ).count()
        ensure_default_items_for_user_section(db, s)
        after = db.query(UserSectionItem).filter(
            UserSectionItem.user_category_section_id == s.id
        ).count()
        if after > before:
            touched += 1
    return touched

def list_user_items(db: Session, user_section_id: int) -> List[UserSectionItem]:
    return (
        db.query(UserSectionItem)
        .filter(UserSectionItem.user_category_section_id == user_section_id)
        .order_by(UserSectionItem.sort_index.asc(), UserSectionItem.id.asc())
        .all()
    )
