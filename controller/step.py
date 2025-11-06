from __future__ import annotations
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from app.models.step import FormStep, StepOption
from app.schemas.step import StepCreate, StepUpdate, StepOptionCreate

# Keys we will auto-hoist out of config (legacy clients) → first-class fields
PROMOTED_KEYS: Dict[str, tuple[str, type | None]] = {
    "pii": ("pii", bool),
    "pii_note": ("pii_note", str),
    "format": ("format", str),
    "reminder_after_days": ("reminder_after_days", int),
    "reminder_type": ("reminder_type", str),  # pydantic enum will validate on top-level
    "validation_pattern": ("validation_pattern", str),
    "widget": ("widget", str),  # legacy config.widget
    "label": ("label", dict),   # legacy config.label
}

# legacy keys we explicitly remove from config if present anywhere
STRIP_THESE_FROM_CONFIG = {
    "auto_skip",      # no longer used (toggle removed)
    "widget",         # promoted to first-class
    "label",          # promoted to first-class
    "reminder_enabled",  # we store eligible_reminder + reminder_after_days/reminder_type
    "reminder_after_days",
    "reminder_type",
    "validation",     # we keep boolean first-class; regex is validation_pattern
}

def _pop_promoted_from_config(payload: dict) -> dict:
    """
    Back-compat shim:
    - Move known keys from payload['config'] to top-level (in payload['__promoted__'])
    - Also pull legacy config.validation.pattern into 'validation_pattern'
    - Strip unused keys from config.
    """
    cfg: Dict[str, Any] = dict(payload.get("config") or {})
    promoted: Dict[str, object] = {}

    # straight key promotions (if not already provided top-level)
    for cfg_key, (field_name, _caster) in PROMOTED_KEYS.items():
        if cfg_key in cfg and payload.get(field_name) is None:
            promoted[field_name] = cfg.pop(cfg_key)

    # legacy nested path: config.validation.pattern → validation_pattern
    if payload.get("validation_pattern") is None:
        v = cfg.get("validation")
        if isinstance(v, dict) and "pattern" in v:
            promoted["validation_pattern"] = v.pop("pattern")
            # if validation becomes empty dict, keep as empty dict
            cfg["validation"] = v

    # strip legacy/unused noise from config
    for k in list(cfg.keys()):
        if k in STRIP_THESE_FROM_CONFIG:
            cfg.pop(k, None)

    payload["config"] = cfg
    payload["__promoted__"] = promoted
    return promoted

def _next_free_display_order(
    db: Session,
    section_master_id: int,
    desired: Optional[int],
    *,
    exclude_step_id: Optional[int] = None,
) -> int:
    if desired is None:
        max_order = db.execute(
            select(func.coalesce(func.max(FormStep.display_order), 0)).where(
                FormStep.section_master_id == section_master_id
            )
        ).scalar_one()
        return int(max_order) + 1

    desired = int(desired)
    if desired < 1:
        desired = 1

    q = select(FormStep.display_order).where(
        FormStep.section_master_id == section_master_id
    )
    if exclude_step_id:
        q = q.where(FormStep.id != exclude_step_id)

    taken = set(db.execute(q).scalars().all())
    candidate = desired
    while candidate in taken:
        candidate += 1
    return candidate

# ---------- Steps ----------
def create_step(db: Session, section_master_id: int, data: StepCreate) -> FormStep:
    payload = data.model_dump(exclude_unset=True)
    _pop_promoted_from_config(payload)

    display_order = _next_free_display_order(
        db,
        section_master_id=section_master_id,
        desired=payload.get("display_order"),
        exclude_step_id=None,
    )

    step = FormStep(
        section_master_id=section_master_id,
        step_name=payload["step_name"],
        question_id=payload.get("question_id"),
        title=payload["title"],
        top_one_liner=payload.get("top_one_liner"),
        bottom_one_line=payload.get("bottom_one_line"),
        display_order=display_order,
        type=payload["type"],

        # behaviour kept
        validation=payload.get("validation", False),
        mandatory=payload.get("mandatory", False),
        eligible_reminder=payload.get("eligible_reminder", False),

        # privacy kept
        privacy_nudge=payload.get("privacy_nudge", False),
        privacy_liner=payload.get("privacy_liner"),

        # promoted / first-class (top-level takes precedence over promoted)
        widget=payload.get("widget", payload["__promoted__"].get("widget")),
        label=payload.get("label", payload["__promoted__"].get("label")),
        pii=payload.get("pii", payload["__promoted__"].get("pii")),
        pii_note=payload.get("pii_note", payload["__promoted__"].get("pii_note")),
        format=payload.get("format", payload["__promoted__"].get("format")),
        reminder_after_days=payload.get("reminder_after_days", payload["__promoted__"].get("reminder_after_days")),
        reminder_type=payload.get("reminder_type", payload["__promoted__"].get("reminder_type")),
        validation_pattern=payload.get("validation_pattern", payload["__promoted__"].get("validation_pattern")),

        # remaining config (legacy extras only)
        config=payload.get("config") or {},
    )
    db.add(step)
    db.flush()  # step.id

    opts = payload.get("options")
    if opts:
        _bulk_create_options(db, step, [StepOptionCreate(**o) if isinstance(o, dict) else o for o in opts])

    db.commit()
    db.refresh(step)
    _ = step.options
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
    _pop_promoted_from_config(payload)

    if "display_order" in payload:
        payload["display_order"] = _next_free_display_order(
            db,
            section_master_id=step.section_master_id,
            desired=payload["display_order"],
            exclude_step_id=step.id,
        )

    # flatten promoted into payload for setattr loop
    payload.update(payload.pop("__promoted__", {}))

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
    return (
        db.query(FormStep)
        .options(joinedload(FormStep.options))
        .filter(FormStep.section_master_id == section_id)
        .order_by(FormStep.display_order.asc(), FormStep.id.asc())
        .all()
    )

# ---------- Options ----------
def _bulk_create_options(db: Session, step: FormStep, opts: List[StepOptionCreate]) -> None:
    from app.schemas.step import StepOptionCreate as SO  # avoid circular typing at runtime

    value_to_option: Dict[str, StepOption] = {}
    current_order = (
        db.query(func.coalesce(func.max(StepOption.display_order), 0))
        .filter(StepOption.step_id == step.id)
        .scalar()
        or 0
    )

    for raw in opts:
        row: SO = raw if isinstance(raw, SO) else SO(**raw)
        current_order += 1
        parent_id = None

        pv = getattr(row, "parent_value", None)
        if pv:
            parent = value_to_option.get(pv)
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
        db.flush()
        value_to_option[row.value] = opt

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
