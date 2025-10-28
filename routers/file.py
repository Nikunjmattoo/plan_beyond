from fastapi import APIRouter, Depends, File, HTTPException, Form, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.file import File as FileModel
from app.database import SessionLocal
from app.schemas.file import FileCreate, FileResponse, FileUpdate
from app.controller.file import create_file, get_files_in_folder, delete_file, update_file
from app.dependencies import get_current_user
import os
import shutil

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

PLAN_LIMITS = {
    "basic": 5 * 1024 * 1024 * 1024, 
    "pro": 10 * 1024 * 1024 * 1024,  
    "professional": 15 * 1024 * 1024 * 1024  
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# -------------------- File Add --------------------

@router.post("/", response_model=FileResponse)
async def upload_file(
    folder_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    total_size = db.query(func.sum(FileModel.size)).filter(FileModel.user_id == user.id).scalar() or 0

    user_plan = getattr(user, "userRole", "basic")
    if hasattr(user_plan, "value"):  
        user_plan = user_plan.value
    plan_limit = PLAN_LIMITS.get(user_plan, PLAN_LIMITS["basic"])

    if total_size + file_size > plan_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Storage limit exceeded. Your plan allows {plan_limit / (1024**3)} GB total."
        )

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.seek(0)  
    
        return await create_file(db, user.id, folder_id, file)

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)  
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- File, Storage Fetch --------------------

@router.get("/folder/{folder_id}", response_model=list[FileResponse])
def list_files(folder_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_files_in_folder(db, user_id=user.id, folder_id=folder_id)


@router.get("/remaining-storage")
def get_remaining_storage(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    
    total_used = db.query(func.sum(FileModel.size)).filter(FileModel.user_id == user.id).scalar() or 0

    user_plan = getattr(user, "plan", "basic")  
    if hasattr(user_plan, "value"):  
        user_plan = user_plan.value

    plan_limit = PLAN_LIMITS.get(user_plan, PLAN_LIMITS["basic"])

   
    remaining = plan_limit - total_used
    if remaining < 0:
        remaining = 0

    return {
        "plan": user_plan,
        "total_limit_bytes": plan_limit,
        "used_bytes": total_used,
        "remaining_bytes": remaining,
        "total_limit_mb": round(plan_limit / (1024 * 1024), 2),
        "used_mb": round(total_used / (1024 * 1024), 2),
        "remaining_mb": round(remaining / (1024 * 1024), 2)
    }


# -------------------- File Update --------------------
@router.put("/{file_id}", response_model=FileResponse)
def update(file_id: int, update_data: FileUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    file = update_file(db, user.id, file_id, update_data)
    if not file:
        raise HTTPException(status_code=404, detail="File not found or deleted")
    return file


# -------------------- File Delete --------------------
@router.delete("/{file_id}")
def delete(file_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    file = delete_file(db, user.id, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return {"detail": "File marked as deleted"}






@router.post("/raw", response_model=FileResponse)
async def upload_file_raw(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # Reuse the same logic but with folder_id=None
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    total_size = db.query(func.sum(FileModel.size)).filter(FileModel.user_id == user.id).scalar() or 0

    user_plan = getattr(user, "userRole", "basic")
    if hasattr(user_plan, "value"):
        user_plan = user_plan.value
    plan_limit = PLAN_LIMITS.get(user_plan, PLAN_LIMITS["basic"])

    if total_size + file_size > plan_limit:
        raise HTTPException(status_code=400, detail="Storage limit exceeded for your plan.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.seek(0)
        return await create_file(db, user.id, None, file)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
