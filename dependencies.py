# dependencies.py
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import user as user_model
from app.models import admin as admin_model

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_token_header(request: Request):
    authorization: str = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return authorization.split(" ")[1]

def _decode_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    token: str = Depends(get_token_header),
    db: Session = Depends(get_db)
):
    payload = _decode_token(token)
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(user_model.User).filter(user_model.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_current_admin(
    token: str = Depends(get_token_header),
    db: Session = Depends(get_db)
):
    payload = _decode_token(token)
    is_admin = payload.get("adm") is True
    admin_id = payload.get("sub")
    if not is_admin or not admin_id:
        raise HTTPException(status_code=401, detail="Admin token required")
    admin = db.query(admin_model.Admin).filter(admin_model.Admin.id == int(admin_id)).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    return admin

def get_current_user_id(
    token: str = Depends(get_token_header),
    db: Session = Depends(get_db)
) -> str:
    """
    Get current user ID as string (for vault operations).
    Similar to get_current_user but returns just the ID.
    """
    payload = _decode_token(token)
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Verify user exists
    user = db.query(user_model.User).filter(user_model.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return str(user.id)  # Return as string