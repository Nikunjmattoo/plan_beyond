# app/controller/step.py
from __future__ import annotations
from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from app.models.step import FormStep, StepOption
from app.schemas.step import StepCreate, StepUpdate, StepOptionCreate

# ---------- helpers ----------
def _next_free_display_order(
    db: Session,
    section_master_id: int,
    desired: Optional[int],
    *,
    exclude_step_id: Optional[int] = None,
) -> int:
    """
    Returns the first available display_order >= desired (or max+1 if desired is None).
    Excludes a given step id (useful during updates to ignore the row being updated).
    """
    # If not provided, default to max+1
    if desired is None:
        max_order = db.execute(
            select(func.coalesce(func.max(FormStep.display_order), 0)).where(
                FormStep.section_master_id == section_master_id
            )
        ).scalar_one()
        return int(max_order) + 1

    # Normalize to >= 1
    desired = int(desired)
    if desired < 1:
        desired = 1

    q = select(FormStep.display_order).where(
        FormStep.section_master_id == section_master_id
    )
    if exclude_step_id:
        q = q.where(FormStep.id != exclude_step_id)

    taken = set(db.execute(q).scalars().all())

    # Find first free >= desired
    candidate = desired
    while candidate in taken:
        candidate += 1
    return candidate

# ---------- Steps ----------
def create_step(db: Session, section_master_id: int, data: StepCreate) -> FormStep:
    # resolve display_order (auto-increment if collides)
    display_order = _next_free_display_order(
        db,
        section_master_id=section_master_id,
        desired=data.display_order,
        exclude_step_id=None,
    )

    step = FormStep(
        section_master_id=section_master_id,
        step_name=data.step_name,
        question_id=data.question_id,
        title=data.title,
        top_one_liner=data.top_one_liner,
        bottom_one_line=data.bottom_one_line,
        display_order=display_order,
        type=data.type,
        nested=data.nested,
        validation=data.validation,
        mandatory=data.mandatory,
        skippable=data.skippable,
        eligible_reminder=data.eligible_reminder,
        privacy_nudge=data.privacy_nudge,
        privacy_liner=data.privacy_liner,
        config=data.config or {},
    )
    db.add(step)
    db.flush()  # step.id available

    if data.options:
        _bulk_create_options(db, step, data.options)

    db.commit()
    db.refresh(step)
    _ = step.options  # eager load for response
    return step

def bulk_create_steps(db: Session, section_id: int, rows: List[StepCreate]) -> List[FormStep]:
    created: List[FormStep] = []
    for row in rows:
        created.append(create_step(db, section_id, row))
    return created

def update_step(db: Session, step_id: int, data: StepUpdate) -> Optional[FormStep]:
    step = db.get(FormStep, step_id)
    if not step:
        return None

    payload = data.model_dump(exclude_unset=True)

    # If display_order is requested, resolve collisions before commit
    if "display_order" in payload:
        payload["display_order"] = _next_free_display_order(
            db,
            section_master_id=step.section_master_id,
            desired=payload["display_order"],
            exclude_step_id=step.id,
        )

    for k, v in payload.items():
        setattr(step, k, v)

    db.commit()
    db.refresh(step)
    _ = step.options
    return step

def delete_step(db: Session, step_id: int) -> bool:
    step = db.get(FormStep, step_id)
    if not step:
        return False
    db.delete(step)
    db.commit()
    return True

def list_steps_for_section(db: Session, section_id: int) -> List[FormStep]:
    # use section_master_id
    return (
        db.query(FormStep)
        .options(joinedload(FormStep.options))
        .filter(FormStep.section_master_id == section_id)
        .order_by(FormStep.display_order.asc(), FormStep.id.asc())
        .all()
    )

# ---------- Options ----------
def _bulk_create_options(db: Session, step: FormStep, opts: List[StepOptionCreate]) -> None:
    """
    Parent mapping behavior:
    1) If parent_value refers to an option created in the *same request* (value_to_option), use that.
    2) Otherwise, look up an *existing* StepOption for this step by value and use its id.
       This allows adding children under already-existing parents during EDIT.
    """
    value_to_option: Dict[str, StepOption] = {}
    current_order = (
        db.query(func.coalesce(func.max(StepOption.display_order), 0))
        .filter(StepOption.step_id == step.id)
        .scalar()
        or 0
    )

    for row in opts:
        current_order += 1
        parent_id = None

        pv = getattr(row, "parent_value", None)
        if pv:
            # 1) parent in this batch?
            parent = value_to_option.get(pv)

            # 2) or an existing parent in DB?
            if not parent:
                parent = db.execute(
                    select(StepOption).where(
                        StepOption.step_id == step.id,
                        StepOption.value == pv,
                    )
                ).scalar_one_or_none()

            parent_id = parent.id if parent else None

        opt = StepOption(
            step_id=step.id,
            label=row.label,
            value=row.value,
            display_order=row.display_order or current_order,
            parent_option_id=parent_id,
            meta=getattr(row, "meta", None) or {},
        )
        db.add(opt)
        db.flush()  # get opt.id
        value_to_option[row.value] = opt  # enable chaining

def add_options(db: Session, step_id: int, opts: List[StepOptionCreate]):
    step = db.get(FormStep, step_id)
    if not step:
        return None
    _bulk_create_options(db, step, opts)
    db.commit()
    db.refresh(step)
    _ = step.options
    return step

def list_options(db: Session, step_id: int) -> List[StepOption]:
    return (
        db.query(StepOption)
        .filter(StepOption.step_id == step_id)
        .order_by(StepOption.display_order.asc(), StepOption.id.asc())
        .all()
    )

def delete_option(db: Session, option_id: int) -> bool:
    opt = db.get(StepOption, option_id)
    if not opt:
        return False
    db.delete(opt)
    db.commit()
    return True
