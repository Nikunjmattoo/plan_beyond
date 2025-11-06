# app/routers/forms_user.py
from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
from datetime import datetime

# --- Catalog out ---
class StepOptionOut(BaseModel):
    id: int
    label: str
    value: str
    display_order: int
    meta: Optional[Dict[str, Any]] = None
    children: Optional[List["StepOptionOut"]] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

StepOptionOut.model_rebuild()

class FormStepOut(BaseModel):
    id: int
    section_master_id: int
    step_name: str
    question_id: Optional[str]
    title: str
    top_one_liner: Optional[str]
    bottom_one_line: Optional[str]
    display_order: int
    type: str
    nested: bool
    validation: bool
    mandatory: bool
    skippable: bool
    eligible_reminder: bool
    privacy_nudge: bool
    privacy_liner: Optional[str]
    config: Optional[dict]
    options: List[StepOptionOut] = []

    class Config:
        from_attributes = True

class StepsCatalogOut(BaseModel):
    category_id: int
    section_id: int
    section_name: str
    steps: List[FormStepOut]

# --- Save/get answers ---
class AnswerItem(BaseModel):
    step_id: int
    value: Any  # validated server-side based on step.type
    wants_reminder: Optional[bool] = None

class SaveSectionAnswersIn(BaseModel):
    category_id: int
    section_id: int
    progress_id: Optional[int] = None 
    record_key: Optional[str] = None
    answers_kv: Optional[Dict[str, Any]] = None
    answers: Optional[List[AnswerItem]] = None
    section_photo_url: Optional[str] = None
    reminders_kv: Optional[Dict[str, bool]] = None
    display_name: Optional[str] = None

class SavedSectionOut(BaseModel):
    category_id: int
    section_id: int
    progress_id: int
    saved_at: datetime
    submitted_at: Optional[datetime] = None
    section_photo_url: Optional[str] = None
    answers_kv: Dict[str, Any]
    reminders_kv: Dict[str, bool] = Field(default_factory=dict)
    display_name: Optional[str] = None

class UserReminderRow(BaseModel):
    progress_id: int
    category_id: int
    section_id: int
    section_name: str
    step_id: int
    question_id: Optional[str] = None
    step_title: Optional[str] = None
    enabled: bool
    value: Any = None
    saved_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None

# ---------- NEW: Progress Leaf schemas ----------
class ProgressLeafCreate(BaseModel):
    contact_ids: List[int]  # bulk add

class ProgressLeafPatch(BaseModel):
    status: str  # "active" | "removed"

class ProgressLeafOut(BaseModel):
    id: int
    user_id: int
    category_id: int
    section_id: int
    progress_id: int
    contact_id: int
    status: str
    created_at: datetime
    updated_at: datetime


from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database import SessionLocal
from app.dependencies import get_current_user

# masters
from app.models.category import CategoryMaster, CategorySectionMaster, CategoryProgressLeaf, ProgressLeafStatus
from app.models.step import FormStep, StepOption, StepType
# user
from app.models.user_forms import UserSectionProgress, UserStepAnswer, SectionProgressStatus, UserStepReminder

from app.schemas.forms_user import (
    StepsCatalogOut, FormStepOut, StepOptionOut,
    SaveSectionAnswersIn, SavedSectionOut, AnswerItem, UserReminderRow,
    ProgressLeafCreate, ProgressLeafOut, ProgressLeafPatch
)

# 🔐 NEW: encryption helpers for answers
from app.encryption_module.forms_encryption import (
    encrypt_answer_value,
    decrypt_answer_value,
)

# ---------- helpers (add these small helpers near the top) ----------
def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]

def _normalize_file_scalar(x):
    # allow existing int ids
    if isinstance(x, int):
        return x
    # allow numeric strings: "123" -> 123
    if isinstance(x, str):
        s = x.strip()
        if s.isdigit():
            return int(s)
        # allow http(s) URLs
        if s.startswith(("http://", "https://")):
            return s
    # reject anything else
    raise HTTPException(
        status_code=400,
        detail="file/photo expects int, URL string, [int], or [URL].",
    )

def _is_http_url(s: Optional[str]) -> bool:
    return isinstance(s, str) and s.startswith(("http://", "https://"))

# NEW: contact ownership helper (mirrors Memories)
from sqlalchemy import or_
from app.models.contact import Contact

def _ensure_user_contact(db: Session, user_id: int, contact_id: int):
    q = db.query(Contact.id).filter(Contact.id == contact_id)
    if hasattr(Contact, "owner_user_id") and hasattr(Contact, "linked_user_id"):
        q = q.filter(or_(Contact.owner_user_id == user_id, Contact.linked_user_id == user_id))
    elif hasattr(Contact, "owner_user_id"):
        q = q.filter(Contact.owner_user_id == user_id)
    elif hasattr(Contact, "user_id"):
        q = q.filter(Contact.user_id == user_id)
    if not q.first():
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found for this user")

router = APIRouter(prefix="/user/forms", tags=["User Forms"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- helpers ----------

def _nest_options(options: List[StepOption]) -> List[Dict[str, Any]]:
    by_parent: Dict[Optional[int], List[StepOption]] = {}
    for opt in options:
        by_parent.setdefault(opt.parent_option_id, []).append(opt)
    for arr in by_parent.values():
        arr.sort(key=lambda o: o.display_order)

    def build(parent_id: Optional[int]):
        children = by_parent.get(parent_id, [])
        out = []
        for o in children:
            out.append({
                "id": o.id,
                "label": o.label,
                "value": o.value,
                "display_order": o.display_order,
                "meta": o.meta,
                "children": build(o.id)
            })
        return out

    return build(None)

def _validate_and_normalize(step: FormStep, raw):
    t = step.type

    # ----- handle None first -----
    if raw is None:
        if step.mandatory:
            raise HTTPException(status_code=400, detail=f"Step {step.id} is mandatory.")
        return None

    # ----- list / checklist -----
    if t in (StepType.list, StepType.checklist):
        vals = _as_list(raw)
        if not all(isinstance(x, (str, int)) for x in vals):
            raise HTTPException(
                status_code=400,
                detail=f"Step {step.id}: list/checklist expects array of strings/ids."
            )
        return vals

    # ----- hierarchical -----
    if t == StepType.hierarchical:
        if not isinstance(raw, (list, dict)):
            raise HTTPException(
                status_code=400,
                detail=f"Step {step.id}: hierarchical expects list or object."
            )
        return raw

    # ----- single_select -----
    if t == StepType.single_select:
        if not isinstance(raw, (str, int)):
            raise HTTPException(
                status_code=400,
                detail=f"Step {step.id}: single_select expects string/id."
            )
        return raw

    # ----- open (text/number) -----
    if t == StepType.open:
        if not isinstance(raw, (str, int, float)):
            raise HTTPException(
                status_code=400,
                detail=f"Step {step.id}: open expects text/number."
            )
        return raw

    # ----- date types -----
    if t in (StepType.date_mm_yyyy, StepType.date_dd_mm_yyyy):
        if not isinstance(raw, str):
            raise HTTPException(
                status_code=400,
                detail=f"Step {step.id}: date expects string."
            )
        return raw

    # ----- google_location (allow dict OR plain string) -----
    if t == StepType.google_location:
        # Accept structured object (place result) OR a plain string typed by the user
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            return raw.strip()
        raise HTTPException(
            status_code=400,
            detail=f"Step {step.id}: google_location expects object or string."
        )

    # ----- photo / file_upload -----
    if t in (StepType.photo, StepType.file_upload):
        vals_in = _as_list(raw)
        vals_out = [_normalize_file_scalar(v) for v in vals_in]
        # preserve original cardinality
        if isinstance(raw, list):
            return vals_out
        return vals_out[0] if vals_out else None

    # ----- fallback (return as-is) -----
    return raw

# =========================
# NEW: simple section meta
# =========================
@router.get("/section-meta/{section_id}")
def get_section_meta(
    section_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Given a section_id, return its category_id and name.
    This lets the frontend (VaultDetail) know which category to use
    when calling /user/forms/save.
    """
    sec = db.query(CategorySectionMaster).filter(
        CategorySectionMaster.id == section_id
    ).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found")

    return {
        "section_id": sec.id,
        "category_id": sec.category_id,
        "section_name": sec.name,
    }

# ---------- Endpoints (existing) ----------

@router.get("/catalog/{category_id}/{section_id}", response_model=StepsCatalogOut)
def get_steps_for_section(category_id: int, section_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    cat = db.query(CategoryMaster).filter(CategoryMaster.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    sec = db.query(CategorySectionMaster).filter(
        CategorySectionMaster.id == section_id,
        CategorySectionMaster.category_id == category_id
    ).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found")

    steps = (
        db.query(FormStep)
        .filter(FormStep.section_master_id == section_id)
        .order_by(FormStep.display_order.asc(), FormStep.id.asc())
        .all()
    )

    step_ids = [s.id for s in steps]
    if step_ids:
        opts = db.query(StepOption).filter(StepOption.step_id.in_(step_ids)).all()
    else:
        opts = []

    by_step: Dict[int, List[StepOption]] = {}
    for o in opts:
        by_step.setdefault(o.step_id, []).append(o)

    out_steps = []
    for s in steps:
        nested_opts = _nest_options(by_step.get(s.id, []))
        out_steps.append(FormStepOut(
            id=s.id,
            section_master_id=s.section_master_id,
            step_name=s.step_name,
            question_id=s.question_id,
            title=s.title,
            top_one_liner=s.top_one_liner,
            bottom_one_line=s.bottom_one_line,
            display_order=s.display_order,
            type=s.type.value,
            # ---- tolerant defaults for models without these columns ----
            nested=bool(getattr(s, "nested", False)),
            validation=s.validation,
            mandatory=s.mandatory,
            skippable=bool(getattr(s, "skippable", False)),
            eligible_reminder=s.eligible_reminder,
            privacy_nudge=s.privacy_nudge,
            privacy_liner=s.privacy_liner,
            config=s.config,
            options=[StepOptionOut(**o) for o in nested_opts]
        ))

    return StepsCatalogOut(
        category_id=category_id,
        section_id=section_id,
        section_name=sec.name,
        steps=out_steps
    )

@router.get("/data/{category_id}/{section_id}", response_model=SavedSectionOut)
def get_saved_answers(
    category_id: int,
    section_id: int,
    progress_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # base query for this user/category/section
    base_q = db.query(UserSectionProgress).filter(
        UserSectionProgress.user_id == user.id,
        UserSectionProgress.category_id == category_id,
        UserSectionProgress.section_id == section_id,
    )

    # if a specific progress is requested, narrow to it
    q = base_q.filter(UserSectionProgress.id == progress_id) if progress_id else base_q

    # ALWAYS assign p (previous code only did this inside the if)
    p = q.order_by(
        UserSectionProgress.saved_at.desc(),
        UserSectionProgress.id.desc(),
    ).first()

    if not p:
        # nothing saved yet
        return SavedSectionOut(
            category_id=category_id,
            section_id=section_id,
            progress_id=0,
            saved_at=datetime.utcnow(),
            submitted_at=None,
            answers_kv={},
            display_name=None,
        )

    # map step_id -> question_id
    steps = db.query(FormStep).filter(FormStep.section_master_id == section_id).all()
    q_by_step = {s.id: (s.question_id or f"step:{s.id}") for s in steps}

    # answers only for this progress
    rows = db.query(UserStepAnswer).filter(UserStepAnswer.progress_id == p.id).all()
    answers_kv = {
        q_by_step.get(r.step_id, f"step:{r.step_id}"): decrypt_answer_value(r.value)
        for r in rows
    }

    rem_rows = db.query(UserStepReminder).filter(UserStepReminder.progress_id == p.id).all()
    reminders_kv = {
        q_by_step.get(r.step_id, f"step:{r.step_id}"): bool(r.wants_reminder)
        for r in rem_rows
        if bool(r.wants_reminder)  # only include truthy; drop falsy to keep response small
    }

    return SavedSectionOut(
        category_id=category_id,
        section_id=section_id,
        progress_id=p.id,
        saved_at=p.saved_at,
        submitted_at=p.submitted_at,
        section_photo_url=p.section_photo_url,
        answers_kv=answers_kv,
        reminders_kv=reminders_kv, 
        display_name=p.display_name,
    )

@router.post("/save", response_model=SavedSectionOut)
def save_section_answers(
    body: SaveSectionAnswersIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Load steps for validation / id<->question map
    steps = db.query(FormStep).filter(FormStep.section_master_id == body.section_id).all()
    by_qid = {(s.question_id or f"step:{s.id}"): s for s in steps}
    by_id  = {s.id: s for s in steps}

    # Normalize incoming answers
    incoming: Dict[int, Any] = {}
    incoming_reminders: Dict[int, bool] = {} 
    if getattr(body, "answers_kv", None):
        for qid, raw in body.answers_kv.items():
            s = by_qid.get(qid)
            if not s:
                raise HTTPException(status_code=400, detail=f"Unknown question_id: {qid}")
            normalized = _validate_and_normalize(s, raw)
            # 🔐 encrypt before storing
            incoming[s.id] = encrypt_answer_value(normalized)
    if getattr(body, "answers", None):
        for item in body.answers:
            s = by_id.get(item.step_id)
            if not s:
                raise HTTPException(status_code=400, detail=f"Step {item.step_id} not in this section.")
            normalized = _validate_and_normalize(s, item.value)
            # 🔐 encrypt before storing
            incoming[item.step_id] = encrypt_answer_value(normalized)

            if getattr(s, "eligible_reminder", False) and item.wants_reminder is not None:
                incoming_reminders[item.step_id] = bool(item.wants_reminder)

    # optional: also accept reminders_kv by question_id
    if getattr(body, "reminders_kv", None):
        for qid, want in body.reminders_kv.items():
            s = by_qid.get(qid)
            if s and getattr(s, "eligible_reminder", False):
                incoming_reminders[s.id] = bool(want)

    # --- Find or create the progress row ---
    p = None

    # 1) Update an existing record if progress_id is supplied
    if getattr(body, "progress_id", None):
        p = db.query(UserSectionProgress).filter(
            UserSectionProgress.id == body.progress_id,
            UserSectionProgress.user_id == user.id,
            UserSectionProgress.category_id == body.category_id,
            UserSectionProgress.section_id == body.section_id,
        ).first()
        if not p:
            raise HTTPException(status_code=404, detail="Progress not found for this user/section.")

    # 2) If not found, optionally upsert by record_key (guards against duplicate keys)
    if p is None:
        rkey = getattr(body, "record_key", None) or uuid4().hex
        p = db.query(UserSectionProgress).filter(
            UserSectionProgress.user_id == user.id,
            UserSectionProgress.category_id == body.category_id,
            UserSectionProgress.section_id == body.section_id,
            UserSectionProgress.record_key == rkey,
        ).first()
        if p is None:
            # CREATE a new entry (this is what you want when clicking the plus button)
            p = UserSectionProgress(
                user_id=user.id,
                category_id=body.category_id,
                section_id=body.section_id,
                record_key=rkey,  # UNIQUE per entry (migration ensured proper default/constraint)
                status=SectionProgressStatus.submitted,
                submitted_at=datetime.utcnow(),
            )
            db.add(p)
            db.flush()  # get p.id

    # mark status (simple flow = submitted)
    p.status = SectionProgressStatus.submitted
    p.submitted_at = datetime.utcnow()

    if body.section_photo_url is not None:
        if body.section_photo_url != "" and not _is_http_url(body.section_photo_url):
            raise HTTPException(status_code=400, detail="section_photo_url must be http(s) URL or empty")
        p.section_photo_url = body.section_photo_url or None

    # Upsert answers for this progress
    existing = {
        r.step_id: r
        for r in db.query(UserStepAnswer).filter(UserStepAnswer.progress_id == p.id).all()
    }
    for step_id, enc_value in incoming.items():
        row = existing.get(step_id)
        if row:
            row.value = enc_value
        else:
            db.add(UserStepAnswer(progress_id=p.id, step_id=step_id, value=enc_value))

    # --- reminders upsert ---
    if incoming_reminders:
        # fetch existing reminders for this progress
        r_existing = {
            r.step_id: r
            for r in db.query(UserStepReminder).filter(UserStepReminder.progress_id == p.id).all()
        }

        for step_id, want in incoming_reminders.items():
            rr = r_existing.get(step_id)
            if rr:
                # update flag
                rr.wants_reminder = bool(want)
                # keep enabled in sync with wants_reminder for UX simplicity
                rr.enabled = bool(want)
                # defensive backfill in case older rows missed required fields
                if getattr(rr, "user_id", None) is None:
                    rr.user_id = user.id
                if getattr(rr, "category_id", None) is None:
                    rr.category_id = p.category_id
                if getattr(rr, "section_id", None) is None:
                    rr.section_id = p.section_id
            else:
                # create with all NOT NULL columns populated
                want_bool = bool(want)
                db.add(UserStepReminder(
                    user_id=user.id,
                    wants_reminder=want_bool,
                    category_id=p.category_id,
                    section_id=p.section_id,
                    progress_id=p.id,
                    step_id=step_id,
                    # keep enabled in sync with wants_reminder
                    enabled=want_bool,
                ))
    
    if getattr(body, "display_name", None) is not None:
        cleaned = body.display_name.strip()
        p.display_name = cleaned or None

    db.commit()
    db.refresh(p)

    # Build KV keyed by question_id
    q_by_step = {s.id: (s.question_id or f"step:{s.id}") for s in steps}
    rows = db.query(UserStepAnswer).filter(UserStepAnswer.progress_id == p.id).all()
    answers_kv = {
        q_by_step.get(r.step_id, f"step:{r.step_id}"): decrypt_answer_value(r.value)
        for r in rows
    }
    rem_rows = db.query(UserStepReminder).filter(UserStepReminder.progress_id == p.id).all()
    reminders_kv = {
        q_by_step.get(r.step_id, f"step:{r.step_id}"): bool(r.wants_reminder)
        for r in rem_rows
        if bool(r.wants_reminder)
    }

    return SavedSectionOut(
        category_id=body.category_id,
        section_id=body.section_id,
        progress_id=p.id,
        saved_at=p.saved_at,
        submitted_at=p.submitted_at,
        section_photo_url=p.section_photo_url,
        answers_kv=answers_kv,
        reminders_kv=reminders_kv,
        display_name=p.display_name,
    )

@router.get("/list/{category_id}/{section_id}", response_model=List[SavedSectionOut])
def list_entries(category_id: int, section_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(UserSectionProgress).filter(
        UserSectionProgress.user_id == user.id,
        UserSectionProgress.category_id == category_id,
        UserSectionProgress.section_id == section_id,
    ).order_by(UserSectionProgress.saved_at.desc()).all()

    steps = db.query(FormStep).filter(FormStep.section_master_id == section_id).all()
    q_by_step = {s.id: (s.question_id or f"step:{s.id}") for s in steps}

    out = []
    for p in rows:
        items = db.query(UserStepAnswer).filter(UserStepAnswer.progress_id == p.id).all()
        kv = {
            q_by_step.get(r.step_id, f"step:{r.step_id}"): decrypt_answer_value(r.value)
            for r in items
        }

        rem_items = db.query(UserStepReminder).filter(UserStepReminder.progress_id == p.id).all()
        rkv = {
            q_by_step.get(r.step_id, f"step:{r.step_id}"): bool(r.wants_reminder)
            for r in rem_items
            if bool(r.wants_reminder)
        }

        out.append(SavedSectionOut(
            category_id=category_id,
            section_id=section_id,
            progress_id=p.id,
            saved_at=p.saved_at,
            submitted_at=p.submitted_at,
            section_photo_url=p.section_photo_url,
            answers_kv=kv,
            reminders_kv=rkv, 
            display_name=p.display_name,
        ))
    return out

@router.get("/reminders", response_model=List[UserReminderRow])
def list_all_reminders(
    only_enabled: bool = Query(True, description="Return only enabled reminders"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # Always return only subscribed reminders
    q = db.query(UserStepReminder).filter(
        UserStepReminder.user_id == user.id,
        UserStepReminder.wants_reminder.is_(True),
    )
    if only_enabled:
        q = q.filter(UserStepReminder.enabled.is_(True))

    rems = q.all()
    if not rems:
        return []

    # collect ids for batch lookups
    step_ids = list({r.step_id for r in rems})
    sec_ids  = list({r.section_id for r in rems})
    prog_ids = list({r.progress_id for r in rems})

    # steps (question_id, title, eligible flag)
    steps = db.query(FormStep).filter(FormStep.id.in_(step_ids)).all()
    step_by_id = {s.id: s for s in steps}

    # sections (name)
    secs = db.query(CategorySectionMaster).filter(CategorySectionMaster.id.in_(sec_ids)).all()
    sec_name_by_id = {s.id: s.name for s in secs}

    # answers (value) and progress timestamps
    ans_rows = db.query(UserStepAnswer).filter(UserStepAnswer.progress_id.in_(prog_ids)).all()
    val_by_key = {
        (a.progress_id, a.step_id): decrypt_answer_value(a.value)
        for a in ans_rows
    }

    prog_rows = db.query(UserSectionProgress).filter(UserSectionProgress.id.in_(prog_ids)).all()
    prog_by_id = {p.id: p for p in prog_rows}

    out: List[UserReminderRow] = []
    for r in rems:
        st = step_by_id.get(r.step_id)
        sec_name = sec_name_by_id.get(r.section_id, "")
        prog = prog_by_id.get(r.progress_id)

        out.append(UserReminderRow(
            progress_id=r.progress_id,
            category_id=r.category_id,
            section_id=r.section_id,
            section_name=sec_name,
            step_id=r.step_id,
            question_id=(st.question_id if st else None),
            step_title=(st.title if st else None),
            enabled=bool(r.enabled),
            value=val_by_key.get((r.progress_id, r.step_id)),
            saved_at=(prog.saved_at if prog else None),
            submitted_at=(prog.submitted_at if prog else None),
        ))

    # newest first
    out.sort(key=lambda x: (x.saved_at or x.submitted_at or datetime.min), reverse=True)
    return out


# DELETE a single entry/progress
@router.delete("/progress/{progress_id}")
def delete_progress(
    progress_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Ensure the progress belongs to this user
    p = db.query(UserSectionProgress).filter(
        UserSectionProgress.id == progress_id,
        UserSectionProgress.user_id == user.id,
    ).first()

    if not p:
        raise HTTPException(status_code=404, detail="Progress not found")

    # If your ORM relationships don't have cascade delete, remove children explicitly
    db.query(UserStepAnswer).filter(UserStepAnswer.progress_id == p.id).delete(synchronize_session=False)
    db.query(UserStepReminder).filter(UserStepReminder.progress_id == p.id).delete(synchronize_session=False)

    db.delete(p)
    db.commit()

    return {"detail": "Progress deleted"}

# =========================
# NEW: Progress Leaves API
# =========================

def _get_owned_progress_or_404(db: Session, user_id: int, progress_id: int) -> UserSectionProgress:
    p = db.query(UserSectionProgress).filter(
        UserSectionProgress.id == progress_id,
        UserSectionProgress.user_id == user_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Progress not found")
    return p

@router.get("/progress/{progress_id}/leaves", response_model=List[ProgressLeafOut])
def list_progress_leaves(
    progress_id: int,
    # Change default so we include non-active (accepted/removed) by default.
    include_removed: bool = Query(True, description="If true (default), return all leaves regardless of status"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = _get_owned_progress_or_404(db, user.id, progress_id)

    q = db.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.progress_id == p.id)

    # When include_removed is False, limit to ACTIVE only (legacy behavior).
    if not include_removed:
        q = q.filter(CategoryProgressLeaf.status == ProgressLeafStatus.active)

    rows = q.all()
    out: List[ProgressLeafOut] = []
    for r in rows:
        out.append(ProgressLeafOut(
            id=r.id,
            user_id=r.user_id,
            category_id=r.category_id,
            section_id=r.section_id,
            progress_id=r.progress_id,
            contact_id=r.contact_id,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            created_at=r.created_at,
            updated_at=r.updated_at,
        ))
    return out

@router.post("/progress/{progress_id}/leaves", response_model=List[ProgressLeafOut])
def add_progress_leaves(
    progress_id: int,
    body: ProgressLeafCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = _get_owned_progress_or_404(db, user.id, progress_id)

    created_or_existing: List[CategoryProgressLeaf] = []
    for cid in body.contact_ids:
        _ensure_user_contact(db, user.id, cid)
        row = db.query(CategoryProgressLeaf).filter(
            CategoryProgressLeaf.progress_id == p.id,
            CategoryProgressLeaf.contact_id == cid,
        ).first()
        if row:
            row.status = ProgressLeafStatus.active
        else:
            row = CategoryProgressLeaf(
                user_id=user.id,
                category_id=p.category_id,
                section_id=p.section_id,
                progress_id=p.id,
                contact_id=cid,
                status=ProgressLeafStatus.active,
            )
            db.add(row)
        created_or_existing.append(row)

    db.commit()
    out: List[ProgressLeafOut] = []
    for r in created_or_existing:
        db.refresh(r)
        out.append(ProgressLeafOut(
            id=r.id,
            user_id=r.user_id,
            category_id=r.category_id,
            section_id=r.section_id,
            progress_id=r.progress_id,
            contact_id=r.contact_id,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            created_at=r.created_at,
            updated_at=r.updated_at,
        ))
    return out

@router.patch("/progress/{progress_id}/leaves")
def replace_progress_leaves(
    progress_id: int,
    body: ProgressLeafCreate,   # carries contact_ids: List[int]
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
   
    p = _get_owned_progress_or_404(db, user.id, progress_id)

    desired: set[int] = set(int(c) for c in body.contact_ids or [])

    # validate ownership
    for cid in desired:
        _ensure_user_contact(db, user.id, cid)

    # current rows (all)
    rows = db.query(CategoryProgressLeaf).filter(
        CategoryProgressLeaf.progress_id == p.id
    ).all()

    existing_by_contact: Dict[int, CategoryProgressLeaf] = {r.contact_id: r for r in rows}

    # upsert additions / re-activate
    for cid in desired:
        row = existing_by_contact.get(cid)
        if row:
            row.status = ProgressLeafStatus.active
        else:
            row = CategoryProgressLeaf(
                user_id=user.id,
                category_id=p.category_id,
                section_id=p.section_id,
                progress_id=p.id,
                contact_id=cid,
                status=ProgressLeafStatus.active,
            )
            db.add(row)

    # remove extras: any ACTIVE contact not in desired -> delete
    for r in rows:
        if r.contact_id not in desired and r.status == ProgressLeafStatus.active:
            db.delete(r)

    db.commit()
    return {"ok": True}

@router.delete("/progress/{progress_id}/leaves/{contact_id}")
def delete_progress_leaf_by_contact(
    progress_id: int,
    contact_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Remove a single leaf by contact id for this progress.
    """
    _ = _get_owned_progress_or_404(db, user.id, progress_id)
    r = db.query(CategoryProgressLeaf).filter(
        CategoryProgressLeaf.progress_id == progress_id,
        CategoryProgressLeaf.user_id == user.id,
        CategoryProgressLeaf.contact_id == contact_id,
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Leaf not found")
    db.delete(r)
    db.commit()
    return {"detail": "Leaf removed"}




# ---------- NEW: Get a single progress entry by id ----------
@router.get("/progress/{progress_id}", response_model=SavedSectionOut)
def get_progress_detail(
    progress_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
   
    # Ensure progress belongs to this user
    p = db.query(UserSectionProgress).filter(
        UserSectionProgress.id == progress_id,
        UserSectionProgress.user_id == user.id,
    ).first()

    if not p:
        raise HTTPException(status_code=404, detail="Progress not found")

    # Load steps for this section to map step_id -> question_id
    steps = db.query(FormStep).filter(
        FormStep.section_master_id == p.section_id
    ).all()
    q_by_step = {s.id: (s.question_id or f"step:{s.id}") for s in steps}

    # Answers for this progress
    rows = db.query(UserStepAnswer).filter(
        UserStepAnswer.progress_id == p.id
    ).all()
    answers_kv = {
        q_by_step.get(r.step_id, f"step:{r.step_id}"): decrypt_answer_value(r.value)
        for r in rows
    }

    # Reminders for this progress
    rem_rows = db.query(UserStepReminder).filter(
        UserStepReminder.progress_id == p.id
    ).all()
    reminders_kv = {
        q_by_step.get(r.step_id, f"step:{r.step_id}"): bool(r.wants_reminder)
        for r in rem_rows
        if bool(r.wants_reminder)
    }

    return SavedSectionOut(
        category_id=p.category_id,
        section_id=p.section_id,
        progress_id=p.id,
        saved_at=p.saved_at,
        submitted_at=p.submitted_at,
        section_photo_url=p.section_photo_url,
        answers_kv=answers_kv,
        reminders_kv=reminders_kv,
        display_name=p.display_name,
    )
