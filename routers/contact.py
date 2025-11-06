# app/routers/contact.py
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from app.schemas.contact import ContactCreate, ContactResponse
from app.controller import contact as contact_crud
from app.database import SessionLocal
from app.dependencies import get_current_user
from app.models import user as user_model
from app.models import contact as contact_model
from fastapi.responses import FileResponse
import json
import logging
import os
from app.config import settings
import smtplib
from email.mime.text import MIMEText

# ✨ If you already have admin auth, import it:
from app.dependencies import get_current_admin
from app.models import admin as admin_model  # adjust path if different

router = APIRouter(tags=["contacts"])
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _to_bool_str(s: Optional[str], default: bool = False) -> bool:
    if s is None:
        return default
    return str(s).strip().lower() == "true"

def _has_admin_role(roles) -> bool:
    """
    Be tolerant: roles might be list/tuple/set, a JSON string like '["admin"]',
    a CSV string 'admin,manager', or a plain string 'admin'.
    """
    if not roles:
        return False
    if isinstance(roles, (list, tuple, set)):
        return any(str(r).strip().lower() == "admin" for r in roles)
    if isinstance(roles, str):
        s = roles.strip()
        if s.lower() == "admin":
            return True
        try:
            parsed = json.loads(s)
            if isinstance(parsed, (list, tuple, set)):
                return any(str(r).strip().lower() == "admin" for r in parsed)
        except json.JSONDecodeError:
            pass
        # fall back to CSV-ish check
        return any(part.strip().lower() == "admin" for part in s.split(","))
    return False

def _send_plain_email(to_addr: str, subject: str, body: str):
    """Send a plain text email via Gmail SMTP (same setup you already use)."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_EMAIL
    msg["To"] = to_addr
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
        server.send_message(msg)
        
def _compose_signup_url() -> str:
    base = settings.APP_URL.rstrip("/")
    return f"{base}/register"
        
# -------------------- Contact Add --------------------
@router.post("/", response_model=ContactResponse)
async def create_contact(
    title: str = Form(""),
    first_name: str = Form(""),
    middle_name: str = Form(""),
    last_name: str = Form(""),
    local_name: str = Form(""),
    company: str = Form(""),
    contact_image: Optional[str] = Form(None),          
    contact_image_file: Optional[UploadFile] = File(None),
    job_type: str = Form(""),
    website: str = Form(""),
    category: str = Form(""),
    relation: str = Form(""),
    phone_numbers: str = Form("[]"),
    emails: str = Form("[]"),
    whatsapp_numbers: str = Form("[]"),
    flat_building_no: str = Form(""),
    street: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    country: str = Form(""),
    postal_code: str = Form(""),
    date_of_birth: str = Form(""),
    anniversary: str = Form(""),
    notes: str = Form(""),
    share_by_whatsapp: str = Form("false"),
    share_by_sms: str = Form("false"),
    share_by_email: str = Form("false"),
    release_on_pass: Optional[str] = Form(None),
    share_after_death: Optional[str] = Form(None),
    is_emergency_contact: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    try:
        sad_bool = _to_bool_str(release_on_pass, default=False) if release_on_pass is not None \
            else _to_bool_str(share_after_death, default=False)

        contact = ContactCreate(
            title=title or None,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            local_name=local_name,
            company=company,
            job_type=job_type,
            website=website,
            category=category,
            relation=relation,
            phone_numbers=json.loads(phone_numbers),
            contact_image=(contact_image or None),
            contact_image_file=contact_image_file,
            emails=json.loads(emails),
            whatsapp_numbers=json.loads(whatsapp_numbers),
            flat_building_no=flat_building_no,
            street=street,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            date_of_birth=date_of_birth,
            anniversary=anniversary,
            notes=notes,
            share_by_whatsapp=_to_bool_str(share_by_whatsapp),
            share_by_sms=_to_bool_str(share_by_sms),
            share_by_email=_to_bool_str(share_by_email),
            share_after_death=sad_bool,
            is_emergency_contact=_to_bool_str(is_emergency_contact)
        )
        return await contact_crud.create_contact(
            db=db,
            contact=contact,
            owner_user_id=current_user.id
        )
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid JSON in request data: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/invite")
async def invite_contact(
    current_user: user_model.User = Depends(get_current_user),
    email: str = Form(""),
    message: str = Form(""),
):
    try:       
        print("Inviting contact:", email, message, current_user) 
        if not email and not message:
            raise HTTPException(status_code=404, detail="Something went to wrong")           
            
        username = current_user.display_name
        subject = "Invitation from Plan Beyond"

        body = (
            f"Hello,\n\n"
            "You have been designated to receive certain items in Plan Beyond.\n"
            "Please create your account to continue:\n\n"
            f"{_compose_signup_url()}\n\n"
            f"— Plan Beyond Team\n\n"
            f"Message from {username}:\n{message}\n"
        )

        _send_plain_email(email, subject, body)
        
        return {"status_code" : 200, "detail": "User invited successfully"}
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid JSON in request data: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# -------------------- NEW: Soft-death eligibility --------------------
@router.get("/share/eligibility")
def share_after_death_eligibility(
    owner: str = Query(..., description="numeric user_id or display_name to check"),
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    s = str(owner).strip()
    if s.isdigit():
        owner_user_id = int(s)
        u = db.query(user_model.User).filter(user_model.User.id == owner_user_id).first()
        if not u:
            raise HTTPException(status_code=404, detail="Owner user not found")
    else:
        u = db.query(user_model.User).filter(user_model.User.display_name == s).first()
        if not u:
            raise HTTPException(status_code=404, detail="Owner user not found for given display_name")
        owner_user_id = u.id

    total = db.query(contact_model.Contact).filter(
        contact_model.Contact.owner_user_id == owner_user_id
    ).count()

    if total == 0:
        return {"owner_user_id": owner_user_id, "has_share_contacts": False, "true_count": 0, "total_contacts": 0}

    true_count = db.query(contact_model.Contact).filter(
        contact_model.Contact.owner_user_id == owner_user_id,
        contact_model.Contact.share_after_death.is_(True)
    ).count()

    return {
        "owner_user_id": owner_user_id,
        "has_share_contacts": true_count > 0,
        "true_count": true_count,
        "total_contacts": total,
    }

def _coerce_to_int_list(raw):
    if raw is None:
        return []
    if isinstance(raw, list):
        candidates = raw
    else:
        s = str(raw).strip()
        if not s:
            return []
        try:
            val = json.loads(s)
            candidates = val if isinstance(val, list) else [x for x in s.split(",")]
        except json.JSONDecodeError:
            candidates = [x for x in s.split(",")]
    out, seen = [], set()
    for x in candidates:
        try:
            i = int(x)
            if i not in seen:
                seen.add(i)
                out.append(i)
        except (ValueError, TypeError):
            continue
    return out

@router.put("/share")
async def update_contact_sharing(
    share_contacts: str = Form(...),
    selected_contact_ids: str = Form("[]"),
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    try:
        if share_contacts not in ["yes", "no"]:
            raise HTTPException(status_code=400, detail="share_contacts must be 'yes' or 'no'")

        contact_ids = _coerce_to_int_list(selected_contact_ids)

        user_contacts = db.query(contact_model.Contact).filter(
            contact_model.Contact.owner_user_id == current_user.id
        ).all()

        if share_contacts == "no":
            for c in user_contacts:
                c.share_after_death = False
        else:
            idset = set(contact_ids)
            for c in user_contacts:
                c.share_after_death = (c.id in idset)

        db.commit()
        return {"detail": "Contact sharing preferences updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating contact sharing for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# -------------------- Contact fetch (LIST) --------------------
@router.get("/", response_model=List[ContactResponse])
def get_contacts(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = Query(None),
):
    return contact_crud.get_contacts(db=db, user_id=current_user.id, skip=skip, limit=limit, search=search)

@router.get("/users/{user_id}/contacts", response_model=List[ContactResponse])
def get_user_contacts(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = Query(None)
):
    roles = getattr(current_user, 'roles', []) or []
    if not _has_admin_role(roles) and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non-admin users can only access their own contacts")
    query = db.query(contact_model.Contact).filter(contact_model.Contact.owner_user_id == user_id)
    if search:
        query = query.filter(
            contact_model.Contact.first_name.ilike(f"%{search}%") |
            contact_model.Contact.local_name.ilike(f"%{search}%")
        )
    return query.offset(skip).limit(limit).all()

# ✅ NEW: Admin-safe path using admin auth token
@router.get("/admin/users/{user_id}/contacts", response_model=List[ContactResponse])
def admin_get_user_contacts(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: admin_model.Admin = Depends(get_current_admin),  # requires admin JWT
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = Query(None)
):
    query = db.query(contact_model.Contact).filter(contact_model.Contact.owner_user_id == user_id)
    if search:
        query = query.filter(
            contact_model.Contact.first_name.ilike(f"%{search}%") |
            contact_model.Contact.local_name.ilike(f"%{search}%")
        )
    return query.offset(skip).limit(limit).all()

# Serve image
@router.get("/images/{owner_user_id}/contact/{filename}")
async def serve_contact_image(owner_user_id: int, filename: str):
    file_path = os.path.join("images", str(owner_user_id), "contact", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

# -------------------- Contact GET/PUT/DELETE by ID --------------------
@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    contact = contact_crud.get_contact_by_id(db=db, contact_id=contact_id)
    if not contact or contact.owner_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    title: str = Form(""),
    first_name: str = Form(""),
    middle_name: str = Form(""),
    last_name: str = Form(""),
    local_name: str = Form(""),
    company: str = Form(""),
    job_type: str = Form(""),
    website: str = Form(""),
    category: str = Form(""),
    relation: str = Form(""),
    phone_numbers: str = Form("[]"),
    emails: str = Form("[]"),
    whatsapp_numbers: str = Form("[]"),
    flat_building_no: str = Form(""),
    street: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    country: str = Form(""),
    postal_code: str = Form(""),
    date_of_birth: str = Form(""),
    anniversary: str = Form(""),
    notes: str = Form(""),
    share_by_whatsapp: str = Form("false"),
    share_by_sms: str = Form("false"),
    share_by_email: str = Form("false"),
    release_on_pass: Optional[str] = Form(None),
    share_after_death: Optional[str] = Form(None),
    is_emergency_contact: Optional[str] = Form(None),
    contact_image: Optional[str] = Form(None),           # <-- string URL
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    try:
        sad_bool = _to_bool_str(release_on_pass, default=False) if release_on_pass is not None \
            else _to_bool_str(share_after_death, default=False)

        contact = ContactCreate(
            title=title or None,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            local_name=local_name,
            company=company,
            job_type=job_type,
            website=website,
            category=category,
            relation=relation,
            phone_numbers=json.loads(phone_numbers),
            emails=json.loads(emails),
            whatsapp_numbers=json.loads(whatsapp_numbers),
            flat_building_no=flat_building_no,
            street=street,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            date_of_birth=date_of_birth,
            anniversary=anniversary,
            notes=notes,
            share_by_whatsapp=_to_bool_str(share_by_whatsapp),
            share_by_sms=_to_bool_str(share_by_sms),
            share_by_email=_to_bool_str(share_by_email),
            share_after_death=sad_bool,
            is_emergency_contact=_to_bool_str(is_emergency_contact),
            contact_image=contact_image,
            
        )
        existing_contact = contact_crud.get_contact_by_id(db=db, contact_id=contact_id)
        if not existing_contact or existing_contact.owner_user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Contact not found")
        updated_contact = await contact_crud.update_contact(
            db=db,
            contact_id=contact_id,
            updates=contact,
            owner_user_id=current_user.id
        )
        if not updated_contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return updated_contact
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in update_contact: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid JSON in request data: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating contact {contact_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    try:
        existing_contact = contact_crud.get_contact_by_id(db=db, contact_id=contact_id)
        if not existing_contact or existing_contact.owner_user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Contact not found")
        deleted_contact = contact_crud.delete_contact(db=db, contact_id=contact_id)
        if not deleted_contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"detail": "Contact deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting contact {contact_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
