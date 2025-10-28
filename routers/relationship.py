# app/routers/relationship.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import RedirectResponse

from app.database import SessionLocal
from app.dependencies import get_current_user
from app.schemas.relationship import (
    RelationshipRequestCreate, RelationshipRequestResponse,
    RelationshipRequestAccept, RelationshipRequestReject, BranchResponsibilityItem,
    BranchTodoItem, BranchTodoSummary,  # <-- NEW
)
from app.controller.relationship import (
    send_relationship_requests, revoke_request, list_my_requests,
    accept_request, reject_request, list_branch_responsibilities,
    mark_trigger_happened,
    accept_request_by_token, reject_request_by_token,
    public_request_status,
    list_branch_todos, list_branch_todos_summary,   # <-- NEW
)
from app.config import settings

router = APIRouter(tags=["relationships"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- OWNER: send invites -----

@router.post("/folders/{folder_id}/relationship-requests", response_model=List[RelationshipRequestResponse])
def send_requests(
    folder_id: int,
    body: List[RelationshipRequestCreate],
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    rows = send_relationship_requests(db, owner_user_id=user.id, folder_id=folder_id, creates=body)
    if not rows:
        raise HTTPException(status_code=404, detail="Folder not found or no valid contacts to invite")
    return rows

# ----- OWNER: revoke -----

@router.post("/relationship-requests/{request_id}/revoke", response_model=RelationshipRequestResponse)
def revoke(request_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = revoke_request(db, owner_user_id=user.id, request_id=request_id)
    if not row:
        raise HTTPException(status_code=404, detail="Request not found or not revocable")
    return row

# ----- BRANCH: list my requests (auth) -----

@router.get("/relationship-requests/me", response_model=List[RelationshipRequestResponse])
def my_requests(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_my_requests(db, branch_user_id=user.id)

# ----- BRANCH: accept / reject (auth) -----

@router.post("/relationship-requests/{request_id}/accept", response_model=RelationshipRequestResponse)
def accept(request_id: int, body: RelationshipRequestAccept, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = accept_request(db, branch_user_id=user.id, request_id=request_id, body=body)
    if not row:
        raise HTTPException(status_code=400, detail="Invalid, expired, or revoked request")
    return row

@router.post("/relationship-requests/{request_id}/reject", response_model=RelationshipRequestResponse)
def reject(request_id: int, body: RelationshipRequestReject, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = reject_request(db, branch_user_id=user.id, request_id=request_id, body=body)
    if not row:
        raise HTTPException(status_code=400, detail="Invalid, expired, or revoked request")
    return row

# ----- BRANCH: responsibilities -----

@router.get("/branch/responsibilities", response_model=List[BranchResponsibilityItem])
def responsibilities(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_branch_responsibilities(db, branch_user_id=user.id)

# ----- BRANCH: mark event happened -----

@router.post("/folders/{folder_id}/trigger/mark-happened")
def mark_happened(folder_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ok = mark_trigger_happened(db, branch_user_id=user.id, folder_id=folder_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Not allowed or trigger not actionable")
    return {"detail": "Trigger marked as happened"}

# ================= PUBLIC, NO-AUTH LINKS (short) =================
# These now expose clear statuses via the redirect query param.

_STATUS_TO_PARAM = {
    "invalid": "invalid",
    "expired": "expired",
    "revoked": "revoked",
    "already_accepted": "already_accepted",
    "already_rejected": "already_rejected",
    "sent": "sent",  # internal; transitions to accepted/declined below
}

@router.get("/rr/a/{request_id}/{token}")
def public_accept(request_id: int, token: str, db: Session = Depends(get_db)):
    status = public_request_status(db, request_id=request_id, token=token)
    if status == "sent":
        ok = accept_request_by_token(db, request_id=request_id, token=token)
        param = "accepted" if ok else "invalid"
        return RedirectResponse(url=f"{settings.APP_URL}/confirmation?status={param}", status_code=302)

    # not actionable: surface exact status (revoked, expired, etc.)
    param = _STATUS_TO_PARAM.get(status, "invalid")
    return RedirectResponse(url=f"{settings.APP_URL}/confirmation?status={param}", status_code=302)

@router.get("/rr/r/{request_id}/{token}")
def public_reject(request_id: int, token: str, db: Session = Depends(get_db)):
    status = public_request_status(db, request_id=request_id, token=token)
    if status == "sent":
        ok = reject_request_by_token(db, request_id=request_id, token=token)
        param = "declined" if ok else "invalid"
        return RedirectResponse(url=f"{settings.APP_URL}/confirmation?status={param}", status_code=302)

    param = _STATUS_TO_PARAM.get(status, "invalid")
    return RedirectResponse(url=f"{settings.APP_URL}/confirmation?status={param}", status_code=302)

@router.get("/branch/todos", response_model=List[BranchTodoItem])
def branch_todos(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_branch_todos(db, branch_user_id=user.id)

@router.get("/branch/todos/summary", response_model=BranchTodoSummary)
def branch_todos_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_branch_todos_summary(db, branch_user_id=user.id)