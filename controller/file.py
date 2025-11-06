import hashlib
import os
from sqlalchemy.orm import Session
from app.models.file import File
from app.schemas.file import FileCreate, FileUpdate
from fastapi import UploadFile

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def create_file(db: Session, user_id: int, folder_id: int | None, file: UploadFile):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save to disk
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Compute SHA-256
    hash_sha256 = hashlib.sha256(content).hexdigest()

    db_file = File(
        user_id=user_id,
        folder_id=folder_id,
        name=file.filename,
        storage_ref=file_path,
        hash_sha256=hash_sha256,
        size=len(content),
        mime_type=file.content_type,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file(db: Session, file_id: int, user_id: int):
    return db.query(File).filter(
        File.id == file_id,
        File.user_id == user_id,
        File.is_deleted == False
    ).first()

def get_files_in_folder(db: Session, user_id: int, folder_id: int):
    return db.query(File).filter(
        File.user_id == user_id,
        File.folder_id == folder_id,
        File.is_deleted == False
    ).all()

def update_file(db: Session, user_id: int, file_id: int, update_data: FileUpdate):
    file = db.query(File).filter(File.id == file_id, File.user_id == user_id, File.is_deleted == False).first()
    if file and update_data.name:
        file.name = update_data.name
        db.commit()
        db.refresh(file)
    return file

def delete_file(db: Session, user_id: int, file_id: int):
    file = db.query(File).filter(File.id == file_id, File.user_id == user_id).first()
    if file:
        if os.path.exists(file.storage_ref):
            try:
                os.remove(file.storage_ref)
            except OSError as e:
                print(f"Error deleting file {file.storage_ref}: {e}")
        db.delete(file)
        db.commit()
    return file