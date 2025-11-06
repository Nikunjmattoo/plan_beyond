from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import get_current_user, get_current_admin

from app.schemas.step import (
    StepCreate, StepUpdate, StepResponse,
    StepOptionCreate, StepOptionResponse
)
from app.controller.step import (
    create_step, bulk_create_steps, update_step, delete_step,
    list_steps_for_section, add_options, list_options, delete_option
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================= USER =========================
router = APIRouter(prefix="/steps", tags=["Step Definitions"])

@router.post("/sections/{section_master_id}", response_model=StepResponse)
def create_one_step(
    section_master_id: int,
    body: StepCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    step = create_step(db, section_master_id=section_master_id, data=body)
    _ = step.options
    return step

@router.post("/sections/{section_master_id}/bulk", response_model=List[StepResponse])
def create_steps_bulk(
    section_master_id: int,
    rows: List[StepCreate],
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return bulk_create_steps(db, section_master_id=section_master_id, rows=rows)

@router.get("/sections/{section_master_id}", response_model=List[StepResponse])
def list_steps(
    section_master_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return list_steps_for_section(db, section_master_id)

@router.put("/steps/{step_id}", response_model=StepResponse)
def edit_step(
    step_id: int,
    body: StepUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    updated = update_step(db, step_id, body)
    if not updated:
        raise HTTPException(status_code=404, detail="Step not found")
    return updated

@router.delete("/steps/{step_id}")
def remove_step(
    step_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ok = delete_step(db, step_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Step not found")
    return {"detail": "Step deleted"}

@router.post("/steps/{step_id}/options", response_model=StepResponse)
def add_step_options(
    step_id: int,
    rows: List[StepOptionCreate],
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    step = add_options(db, step_id, rows)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    return step

@router.get("/steps/{step_id}/options", response_model=List[StepOptionResponse])
def get_step_options(
    step_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return list_options(db, step_id)

@router.delete("/options/{option_id}")
def remove_option(
    option_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ok = delete_option(db, option_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Option not found")
    return {"detail": "Option deleted"}

# ========================= ADMIN =========================
admin_steps_router = APIRouter(prefix="/admin/steps", tags=["Step Definitions (Admin)"])

@admin_steps_router.post("/sections/{section_master_id}", response_model=StepResponse)
def admin_create_one_step(
    section_master_id: int,
    body: StepCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    step = create_step(db, section_master_id=section_master_id, data=body)
    _ = step.options
    return step

@admin_steps_router.post("/sections/{section_master_id}/bulk", response_model=List[StepResponse])
def admin_create_steps_bulk(
    section_master_id: int,
    rows: List[StepCreate],
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return bulk_create_steps(db, section_master_id=section_master_id, rows=rows)

@admin_steps_router.get("/sections/{section_master_id}", response_model=List[StepResponse])
def admin_list_steps(
    section_master_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_steps_for_section(db, section_master_id)

@admin_steps_router.put("/steps/{step_id}", response_model=StepResponse)
def admin_edit_step(
    step_id: int,
    body: StepUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    updated = update_step(db, step_id, body)
    if not updated:
        raise HTTPException(status_code=404, detail="Step not found")
    return updated

@admin_steps_router.delete("/steps/{step_id}")
def admin_remove_step(
    step_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    ok = delete_step(db, step_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Step not found")
    return {"detail": "Step deleted"}

@admin_steps_router.post("/steps/{step_id}/options", response_model=StepResponse)
def admin_add_step_options(
    step_id: int,
    rows: List[StepOptionCreate],
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    step = add_options(db, step_id, rows)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    return step

@admin_steps_router.get("/steps/{step_id}/options", response_model=List[StepOptionResponse])
def admin_get_step_options(
    step_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return list_options(db, step_id)

@admin_steps_router.delete("/options/{option_id}")
def admin_remove_option(
    option_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    ok = delete_option(db, option_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Option not found")
    return {"detail": "Option deleted"}
