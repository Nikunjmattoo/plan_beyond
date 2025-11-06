from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.death import DeathDeclaration, DeathType

from app.database import SessionLocal
from app.dependencies import get_current_admin, get_current_user
from app.schemas.death import (
    SoftDeathRequest,
    ContestCreate,
    DeathDeclarationResponse, ContestResponse,
    AdminSoftRetract, AdminHardDecision, AdminDisputeDecision
)
from app.controller.death import (
    admin_retract_soft_death, list_pending_hard, admin_decide_hard,
    list_disputes, admin_decide_dispute, declare_soft_death, declare_hard_death,
    create_contest, get_active_soft_info, get_active_hard_info,
    notify_admin_on_contest, quick_decide_dispute,
    _verify_quick_token, _verify_quick_token_hard, acknowledge_soft_death,
    approve_soft_by_trustee, decline_soft_by_trustee,
    get_pending_soft_info, get_pending_soft_multi_info, get_pending_hard_info,
)

death_router = APIRouter(prefix="/v1/death", tags=["death"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- SOFT DEATH ----------

@death_router.post("/soft", response_model=DeathDeclarationResponse)
def soft_death(body: SoftDeathRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Initiate a SOFT death message (trustees only).
    """
    decl = declare_soft_death(
        db,
        trustee_user_id=user.id,  # actor user id (trustee)
        root_user_id=body.root_user_id,
        message=body.message,
        media_ids=body.media_ids,
        audience_config=body.audience_config,
    )
    if not decl:
        raise HTTPException(status_code=400, detail="Soft death not allowed or locked.")
    return decl

@death_router.post("/soft/{declaration_id}/approve")
def approve_soft(declaration_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ok = approve_soft_by_trustee(db, declaration_id=declaration_id, actor_user_id=user.id)
    if not ok:
        raise HTTPException(status_code=400, detail="Approval failed")
    return {"ok": True, "message": "Recorded. It will broadcast to contacts once threshold is met."}

@death_router.post("/soft/{declaration_id}/decline", response_model=ContestResponse)
async def decline_soft(
    declaration_id: int,
    reason: str = Form(""),
    evidence_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = await decline_soft_by_trustee(
        db, declaration_id=declaration_id, actor_user_id=user.id, reason=reason, evidence_file=evidence_file
    )
    return c

# ---------- BANNERS ----------

@death_router.get("/active")
def get_active_soft(owner: str = Query(..., description="numeric user_id or exact display_name"),
                    db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    return get_active_soft_info(db, viewer_user_id=user.id, owner=owner)

@death_router.get("/hard/active")
def get_active_hard(owner: str = Query(..., description="numeric user_id or exact display_name"),
                    db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    return get_active_hard_info(db, viewer_user_id=user.id, owner=owner)

# ---------- QUICK LINKS ----------

@death_router.get("/contest/{contest_id}/quick")
def quick_action(contest_id: int,
                 decision: str = Query(..., pattern="^(approve|decline)$"),
                 token: str = Query(...),
                 db: Session = Depends(get_db)):
    if not _verify_quick_token(token, contest_id, decision):
        return HTMLResponse("<h3>Invalid or expired link.</h3>", status_code=400)

    ok, msg = quick_decide_dispute(db, contest_id=contest_id, decision=decision)
    if not ok:
        return HTMLResponse(f"<h3>Action failed:</h3><p>{msg}</p>", status_code=400)
    return HTMLResponse(f"<h3>Done</h3><p>{msg}</p>", status_code=200)

@death_router.get("/hard/{declaration_id}/quick")
def quick_action_hard(declaration_id: int,
                      decision: str = Query(..., pattern="^(accept|reject)$"),
                      token: str = Query(...),
                      db: Session = Depends(get_db)):
    if not _verify_quick_token_hard(token, declaration_id, decision):
        return HTMLResponse("<h3>Invalid or expired link.</h3>", status_code=400)

    row = admin_decide_hard(
        db, admin_id=0, declaration_id=declaration_id,
        decision=("accepted" if decision == "accept" else "rejected"),
        notes="[via quick link]",
    )
    if not row:
        return HTMLResponse("<h3>Action failed:</h3><p>Not reviewable.</p>", status_code=400)
    return HTMLResponse("<h3>Done</h3><p>Decision recorded.</p>", status_code=200)

# ---------- ADMIN ----------

@death_router.post("/soft/{declaration_id}/retract", response_model=DeathDeclarationResponse)
def retract_soft(declaration_id: int, body: AdminSoftRetract, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    row = admin_retract_soft_death(db, admin_id=admin.id, declaration_id=declaration_id, reason=body.reason)
    if not row:
        raise HTTPException(status_code=400, detail="Not retractable (must be an accepted soft death).")
    return row

@death_router.get("/death-requests", response_model=List[DeathDeclarationResponse])
def pending_hard(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return list_pending_hard(db)

@death_router.post("/death-requests/{declaration_id}/decide", response_model=DeathDeclarationResponse)
def decide_hard(declaration_id: int, body: AdminHardDecision, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    if body.decision not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid decision")
    row = admin_decide_hard(db, admin_id=admin.id, declaration_id=declaration_id, decision=body.decision, notes=body.notes)
    if not row:
        raise HTTPException(status_code=400, detail="Not reviewable")
    return row

@death_router.get("/disputes", response_model=List[ContestResponse])
def disputes(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return list_disputes(db)

@death_router.post("/disputes/{contest_id}/decide", response_model=ContestResponse)
def decide_dispute(contest_id: int, body: AdminDisputeDecision, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    if body.decision not in ("uphold_rollback", "dismiss"):
        raise HTTPException(status_code=400, detail="Invalid decision")
    row = admin_decide_dispute(db, admin_id=admin.id, contest_id=contest_id, decision=body.decision, notes=body.notes)
    if not row:
        raise HTTPException(status_code=400, detail="Not disputable")
    return row

@death_router.post("/{declaration_id}/ack")
def ack_soft_death(declaration_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ok = acknowledge_soft_death(db, trustee_user_id=user.id, declaration_id=declaration_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Not retractable (must be an accepted soft death) or not allowed.")
    return {"detail": "Acknowledged"}

@death_router.get("/soft/pending")
def get_pending_soft(owner: str = Query(..., description="numeric user_id or exact display_name"),
                     db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    return get_pending_soft_info(db, viewer_user_id=user.id, owner=owner)

@death_router.get("/soft/pending/all")
def get_all_pending_soft(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return get_pending_soft_multi_info(db, viewer_user_id=user.id)

# ---------- HARD DEATH SUBMISSION ----------

@death_router.post("/hard", response_model=DeathDeclarationResponse)
async def hard_death(
    root_user_id: int = Form(...),
    note: Optional[str] = Form(None),
    also_broadcast: bool = Form(False),
    evidence_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    decl = await declare_hard_death(
        db,
        trustee_user_id=user.id,
        root_user_id=root_user_id,
        evidence_file=evidence_file,
        note=note,
        also_broadcast=also_broadcast,
    )
    if not decl:
        raise HTTPException(status_code=400, detail="Hard death not allowed or locked.")
    return decl

@death_router.get("/hard/pending")
def get_pending_hard(owner: str = Query(..., description="numeric user_id or exact display_name"),
                     db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    return get_pending_hard_info(db, viewer_user_id=user.id, owner=owner)

# ---------- READ DECLARATION(S) FOR UI LOOKUPS ----------

@death_router.get("/declarations/{declaration_id}", response_model=DeathDeclarationResponse)
def get_declaration_by_id(
    declaration_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Return a single declaration (soft/hard) so the frontend can resolve root_user_id
    and display_name for contests, etc.
    """
    row = db.query(DeathDeclaration).filter(DeathDeclaration.id == declaration_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Declaration not found")
    return row

@death_router.get("/death-requests/{declaration_id}", response_model=DeathDeclarationResponse)
def get_hard_request_by_id(
    declaration_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Optional convenience read: fetch a single hard-death request by id.
    (The list endpoint exists already; this mirrors that for per-item fetches.)
    """
    row = (
        db.query(DeathDeclaration)
        .filter(
            DeathDeclaration.id == declaration_id,
            DeathDeclaration.type == DeathType.hard
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Hard request not found")
    return row
