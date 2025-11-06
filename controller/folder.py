# app/controller/folder.py
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime  # NEW
from app.models.folder import (
    Folder,
    FolderBranch,
    FolderLeaf,
    FolderTrigger,
    AssignmentStatus,
    TriggerState,
)
from app.models.relationship import RelationshipRequest, RequestStatus  # NEW
from app.schemas.folder import (
    FolderCreate, FolderUpdate, FolderResponse,
    BranchCreate, BranchUpdate,
    LeafCreate, LeafUpdate,
    TriggerUpsert, TriggerResponse, FolderComputedStatus
)

# -------------------- Defaults --------------------

DEFAULT_FOLDER_NAMES = ["Will", "Life Insurance", "Cards"]

def create_default_folders_for_user(db: Session, user_id: int) -> List[Folder]:
    """
    Create default folders for a brand-new user.
    Idempotent: if any of the names already exist for this user, they won't be duplicated.
    NOTE: Only call this during signup so existing users never receive defaults retroactively.
    """
    existing_names = {
        name for (name,) in db.query(Folder.name)
        .filter(Folder.user_id == user_id, Folder.name.in_(DEFAULT_FOLDER_NAMES))
        .all()
    }

    created: List[Folder] = []
    for name in DEFAULT_FOLDER_NAMES:
        if name not in existing_names:
            f = Folder(user_id=user_id, name=name)
            db.add(f)
            created.append(f)

    if created:
        db.commit()
        for f in created:
            db.refresh(f)

    return created

# -------------------- Status Computation --------------------

def _compute_status_and_missing(db: Session, folder_id: int) -> Tuple[FolderComputedStatus, Optional[str]]:
    active_branches = db.execute(
        select(func.count(FolderBranch.id)).where(
            FolderBranch.folder_id == folder_id,
            or_(FolderBranch.status == AssignmentStatus.active, FolderBranch.status == AssignmentStatus.pending)
        )
    ).scalar_one()

    active_leaves = db.execute(
        select(func.count(FolderLeaf.id)).where(
            FolderLeaf.folder_id == folder_id,
            or_(FolderLeaf.status == AssignmentStatus.active, FolderLeaf.status == AssignmentStatus.pending)
        )
    ).scalar_one()

    trigger_count = db.execute(
        select(func.count(FolderTrigger.id)).where(
            FolderTrigger.folder_id == folder_id,
            FolderTrigger.state != TriggerState.cancelled
        )
    ).scalar_one()

    missing_bits = []
    if active_branches < 1:
        missing_bits.append("active branch")
    if active_leaves < 1:
        missing_bits.append("active leaf")
    if trigger_count != 1:
        missing_bits.append("exactly 1 (non-cancelled) trigger")

    if missing_bits:
        return FolderComputedStatus.incomplete, ", ".join(missing_bits)

    return FolderComputedStatus.complete, None

# -------------------- Folder CRUD --------------------

def create_folder(db: Session, user_id: int, data: FolderCreate) -> Folder:
    folder = Folder(user_id=user_id, name=data.name)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder

def update_folder(db: Session, user_id: int, folder_id: int, data: FolderUpdate) -> Optional[Folder]:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(folder, field, value)
    db.commit()
    db.refresh(folder)
    return folder

def delete_folder(db: Session, user_id: int, folder_id: int) -> Optional[Folder]:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None

    # NEW: Revoke any still-sent relationship requests for this folder
    pending_rrs = (
        db.query(RelationshipRequest)
        .filter(
            RelationshipRequest.folder_id == folder_id,
            RelationshipRequest.status == RequestStatus.sent,
        )
        .all()
    )
    for rr in pending_rrs:
        rr.status = RequestStatus.revoked
        rr.revoked_at = datetime.utcnow()

    db.delete(folder)
    db.commit()
    return folder

def get_user_folders(db: Session, user_id: int) -> List[dict]:
    folders = db.query(Folder).filter(Folder.user_id == user_id).all()
    result = []
    for f in folders:
        status, missing = _compute_status_and_missing(db, f.id)
        result.append({
            "id": f.id,
            "name": f.name,
            "status": status,
            "missing": missing,
            "created_at": f.created_at,
            "updated_at": f.updated_at
        })
    return result

def get_folder(db: Session, user_id: int, folder_id: int) -> Optional[dict]:
    f = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not f:
        return None
    status, missing = _compute_status_and_missing(db, f.id)
    return {
        "id": f.id,
        "name": f.name,
        "status": status,
        "missing": missing,
        "created_at": f.created_at,
        "updated_at": f.updated_at
    }

# -------------------- Branches --------------------

def add_branch(db: Session, user_id: int, folder_id: int, data: BranchCreate):
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None, "folder_not_found"
    
    existing = db.query(FolderBranch).filter(
        FolderBranch.folder_id == folder_id,
        FolderBranch.contact_id == data.contact_id
    ).first()
    if existing:
        return None, "branch_exists"
    
    row = FolderBranch(folder_id=folder_id, **data.model_dump())
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
        return row, None
    except IntegrityError:
        db.rollback()
        return None, "branch_exists"

def update_branch(db: Session, user_id: int, folder_id: int, branch_id: int, data: BranchUpdate) -> Optional[FolderBranch]:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None
    row = db.query(FolderBranch).filter(
        FolderBranch.id == branch_id,
        FolderBranch.folder_id == folder_id
    ).first()
    if not row:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

def list_branches(db: Session, user_id: int, folder_id: int) -> Optional[List[FolderBranch]]:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None
    return db.query(FolderBranch).filter(FolderBranch.folder_id == folder_id).all()

def delete_branch(db: Session, user_id: int, folder_id: int, branch_id: int) -> bool:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return False
    row = db.query(FolderBranch).filter(
        FolderBranch.id == branch_id,
        FolderBranch.folder_id == folder_id
    ).first()
    if not row:
        return False

    # NEW: Revoke any still-sent relationship requests for this folder/contact
    contact_id = row.contact_id
    pending_rrs = (
        db.query(RelationshipRequest)
        .filter(
            RelationshipRequest.folder_id == folder_id,
            RelationshipRequest.contact_id == contact_id,
            RelationshipRequest.status == RequestStatus.sent,
        )
        .all()
    )
    for rr in pending_rrs:
        rr.status = RequestStatus.revoked
        rr.revoked_at = datetime.utcnow()

    db.delete(row)
    db.commit()
    return True

# -------------------- Leaves --------------------

def add_leaf(db: Session, user_id: int, folder_id: int, data: LeafCreate) -> Optional[FolderLeaf]:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None
    existing = db.query(FolderLeaf).filter(
        FolderLeaf.folder_id == folder_id,
        FolderLeaf.contact_id == data.contact_id
    ).first()
    if existing:
        return None
    row = FolderLeaf(folder_id=folder_id, **data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def update_leaf(db: Session, user_id: int, folder_id: int, leaf_id: int, data: LeafUpdate) -> Optional[FolderLeaf]:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None
    row = db.query(FolderLeaf).filter(
        FolderLeaf.id == leaf_id,
        FolderLeaf.folder_id == folder_id
    ).first()
    if not row:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

def list_leaves(db: Session, user_id: int, folder_id: int) -> Optional[List[FolderLeaf]]:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None
    return db.query(FolderLeaf).filter(FolderLeaf.folder_id == folder_id).all()

def delete_leaf(db: Session, user_id: int, folder_id: int, leaf_id: int) -> bool:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return False
    row = db.query(FolderLeaf).filter(
        FolderLeaf.id == leaf_id,
        FolderLeaf.folder_id == folder_id
    ).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True

# -------------------- Trigger --------------------

def upsert_trigger(db: Session, user_id: int, folder_id: int, data: TriggerUpsert) -> Optional[FolderTrigger]:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None

    existing = db.query(FolderTrigger).filter(FolderTrigger.folder_id == folder_id).first()
    payload = data.model_dump()

    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing

    new_row = FolderTrigger(folder_id=folder_id, **payload)
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return new_row

def get_trigger(db: Session, user_id: int, folder_id: int) -> Optional[FolderTrigger]:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()
    if not folder:
        return None
    return db.query(FolderTrigger).filter(FolderTrigger.folder_id == folder_id).first()
