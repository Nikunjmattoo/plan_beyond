from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal
from app.dependencies import get_current_user

from app.schemas.folder import (
    FolderCreate, FolderUpdate, FolderResponse,
    BranchCreate, BranchUpdate, BranchResponse,
    LeafCreate, LeafUpdate, LeafResponse,
    TriggerUpsert, TriggerResponse
)
from app.controller.folder import (
    create_folder, update_folder, delete_folder, get_user_folders, get_folder,
    add_branch, update_branch, list_branches, delete_branch,
    add_leaf, update_leaf, list_leaves, delete_leaf,
    upsert_trigger, get_trigger
)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- Folder Create --------------------

@router.post("/", response_model=FolderResponse)
def create(folder: FolderCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = create_folder(db, user_id=user.id, data=folder)
    enriched = get_folder(db, user_id=user.id, folder_id=f.id)
    return enriched

@router.post("/{folder_id}/branches", response_model=BranchResponse)
def create_branch(folder_id: int, body: BranchCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    result, error = add_branch(db, user_id=user.id, folder_id=folder_id, data=body)
    if not result:
        if error == "folder_not_found":
            raise HTTPException(status_code=404, detail="Folder not found")
        elif error == "branch_exists":
            raise HTTPException(status_code=400, detail="Branch with this contact_id already exists")
        else:
            raise HTTPException(status_code=500, detail="Failed to create branch")
    return result

@router.post("/{folder_id}/leaves", response_model=LeafResponse)
def create_leaf(folder_id: int, body: LeafCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = add_leaf(db, user_id=user.id, folder_id=folder_id, data=body)
    if not row:
        raise HTTPException(status_code=400, detail="Leaf with this contact_id already exists or folder not found")
    return row

# -------------------- Folder Fetch --------------------

@router.get("/", response_model=List[FolderResponse])
def list_user_folders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_user_folders(db, user_id=user.id)

@router.get("/{folder_id}", response_model=FolderResponse)
def get_one(folder_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = get_folder(db, user_id=user.id, folder_id=folder_id)
    if not f:
        raise HTTPException(status_code=404, detail="Folder not found")
    return f

@router.get("/{folder_id}/branches", response_model=List[BranchResponse])
def get_branches(folder_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = list_branches(db, user_id=user.id, folder_id=folder_id)
    if rows is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    return rows

@router.get("/{folder_id}/leaves", response_model=List[LeafResponse])
def get_leaves(folder_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = list_leaves(db, user_id=user.id, folder_id=folder_id)
    if rows is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    return rows

@router.get("/{folder_id}/trigger", response_model=TriggerResponse)
def get_one_trigger(folder_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trigger = get_trigger(db, user_id=user.id, folder_id=folder_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    return trigger

# -------------------- Folder Update --------------------

@router.put("/{folder_id}", response_model=FolderResponse)
def update(folder_id: int, update_data: FolderUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = update_folder(db, user_id=user.id, folder_id=folder_id, data=update_data)
    if not f:
        raise HTTPException(status_code=404, detail="Folder not found")
    enriched = get_folder(db, user_id=user.id, folder_id=folder_id)
    return enriched

@router.put("/{folder_id}/branches/{branch_id}", response_model=BranchResponse)
def edit_branch(folder_id: int, branch_id: int, body: BranchUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = update_branch(db, user_id=user.id, folder_id=folder_id, branch_id=branch_id, data=body)
    if not row:
        raise HTTPException(status_code=404, detail="Branch not found")
    return row

@router.put("/{folder_id}/leaves/{leaf_id}", response_model=LeafResponse)
def edit_leaf(folder_id: int, leaf_id: int, body: LeafUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = update_leaf(db, user_id=user.id, folder_id=folder_id, leaf_id=leaf_id, data=body)
    if not row:
        raise HTTPException(status_code=404, detail="Leaf not found")
    return row

@router.put("/{folder_id}/trigger", response_model=TriggerResponse)
def put_trigger(folder_id: int, body: TriggerUpsert, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = upsert_trigger(db, user_id=user.id, folder_id=folder_id, data=body)
    if not row:
        raise HTTPException(status_code=404, detail="Folder not found")
    return row

# -------------------- Folder Delete --------------------

@router.delete("/{folder_id}")
def delete(folder_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = delete_folder(db, user_id=user.id, folder_id=folder_id)
    if not f:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"detail": "Folder deleted successfully"}

@router.delete("/{folder_id}/branches/{branch_id}")
def remove_branch(folder_id: int, branch_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ok = delete_branch(db, user_id=user.id, folder_id=folder_id, branch_id=branch_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Branch not found")
    return {"detail": "Branch removed"}

@router.delete("/{folder_id}/leaves/{leaf_id}")
def remove_leaf(folder_id: int, leaf_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ok = delete_leaf(db, user_id=user.id, folder_id=folder_id, leaf_id=leaf_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Leaf not found")
    return {"detail": "Leaf removed"}