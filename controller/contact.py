# app/controller/contact.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, String, asc
from app.models import contact as models
from app.models import MemoryCollection
from app.models import MemoryCollectionAssignment
from app.schemas import contact as schemas
from typing import Optional
import logging
import os
from fastapi import HTTPException
from datetime import datetime

logger = logging.getLogger(__name__)

def get_unique_filename(storage_path: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    while os.path.exists(os.path.join(storage_path, unique_filename)):
        unique_filename = f"{base}_{counter}{ext}"
        counter += 1
    return unique_filename

async def create_contact(db: Session, contact: schemas.ContactCreate, owner_user_id: int):
    try:
        phone_numbers = contact.phone_numbers or []
        emails = contact.emails or []
        whatsapp_numbers = contact.whatsapp_numbers or []

        image_to_store = ""  # default

        # 1) Prefer URL if provided
        if contact.contact_image and str(contact.contact_image).strip():
            image_to_store = str(contact.contact_image).strip()

        # 2) Else accept a file (legacy/local)
        elif contact.contact_image_file:
            f = contact.contact_image_file
            if f.content_type not in ["image/jpeg", "image/png", "image/gif"]:
                raise HTTPException(status_code=400, detail="Contact image must be JPEG, PNG, or GIF")
            if getattr(f, "size", None) and f.size > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Contact image must be less than 10MB")

            storage_path = os.path.join("images", str(owner_user_id), "contact")
            os.makedirs(storage_path, exist_ok=True)
            unique_filename = get_unique_filename(storage_path, f.filename)
            file_path = os.path.join(storage_path, unique_filename)
            with open(file_path, "wb") as out:
                out.write(await f.read())
            image_to_store = file_path

        db_contact = models.Contact(
            title=contact.title or "",
            first_name=contact.first_name,
            middle_name=contact.middle_name or "",
            last_name=contact.last_name or "",
            local_name=contact.local_name or "",
            company=contact.company or "",
            job_type=contact.job_type or "",
            website=contact.website or "",
            category=contact.category or "",
            relation=contact.relation or "",
            phone_numbers=phone_numbers,
            emails=emails,
            whatsapp_numbers=whatsapp_numbers,
            flat_building_no=contact.flat_building_no or "",
            street=contact.street or "",
            city=contact.city or "",
            state=contact.state or "",
            country=contact.country or "",
            postal_code=contact.postal_code or "",
            date_of_birth=contact.date_of_birth or "",
            anniversary=contact.anniversary or "",
            notes=contact.notes or "",
            contact_image=image_to_store,   # <-- store URL or local path
            owner_user_id=owner_user_id,
            share_by_whatsapp=bool(contact.share_by_whatsapp),
            share_by_sms=bool(contact.share_by_sms),
            share_by_email=bool(contact.share_by_email),
            share_after_death=bool(contact.share_after_death),
            is_emergency_contact=bool(contact.is_emergency_contact),
            created_at=datetime.utcnow(),
        )
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating contact for user {owner_user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create contact: {str(e)}")


# def get_contact_by_id(db: Session, contact_id: int):
#     try:
#         return db.query(models.Contact).filter(models.Contact.id == contact_id).first()
#     except Exception as e:
#         logger.error(f"Error fetching contact {contact_id}: {str(e)}")
#         raise

def get_contact_by_id(db: Session, contact_id: int):
    """
    Returns the Contact and attaches:
      contact.memory_collections_data = [{"id": <int>, "name": <str>}, ...]
    """
    try:
        contact = (
            db.query(models.Contact)
              .filter(models.Contact.id == contact_id)
              .first()
        )
        if contact is None:
            return None

        rows = (
            db.query(MemoryCollection.id, MemoryCollection.name)
              .join(
                  MemoryCollectionAssignment,
                  MemoryCollectionAssignment.collection_id == MemoryCollection.id,
              )
              .filter(MemoryCollectionAssignment.contact_id == contact_id)
              .order_by(asc(MemoryCollection.name))
              .all()
        )
        
        print("contact=================>>>>>>>>>>>>>", contact)

        # Attach a lightweight, read-only view
        contact.memory_collections_data = [
            {"id": cid, "name": cname} for (cid, cname) in rows
        ]
        
        print("contact=============>>>>>>>>>>>", contact.memory_collections_data)
        return contact

    except Exception as e:
        logger.error(f"Error fetching contact {contact_id} with collections: {str(e)}")
        raise
    
def get_contacts_old(db: Session, user_id: int, skip: int = 0, limit: int = 10, search: Optional[str] = None):
    try:
        query = db.query(models.Contact).filter(models.Contact.owner_user_id == user_id)
        if search:
            pat = f"%{search}%"
            query = query.filter(
                or_(
                    models.Contact.first_name.ilike(pat),
                    models.Contact.middle_name.ilike(pat),
                    models.Contact.last_name.ilike(pat),
                    models.Contact.local_name.ilike(pat),
                    models.Contact.company.ilike(pat),
                    models.Contact.emails.cast(String).ilike(pat),  # search text version
                )
            )

        return query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error fetching contacts for user {user_id}: {str(e)}")
        raise

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 10, search: Optional[str] = None):
    # NOTE: requires PostgreSQL. This searches inside the JSON array `emails`.
    from sqlalchemy import or_, select, exists, String, cast
    from sqlalchemy.sql import func
    from sqlalchemy.dialects import postgresql

    try:
        query = db.query(models.Contact).filter(models.Contact.owner_user_id == user_id)

        if search:
            pat = f"%{search}%"

            # LATERAL-style table-valued function over the JSONB array: jsonb_array_elements_text
            # Works on SQLAlchemy 2.x. If you're on 1.4, upgrade or replace with a text() EXISTS (shown in comment below).
            emails_jsonb = cast(models.Contact.emails, postgresql.JSONB)
            emails_tvf = (
                func.jsonb_array_elements_text(emails_jsonb)
                .table_valued("value")
                .alias("e")
            )

            email_match = exists(
                select(1)
                .select_from(emails_tvf)
                .where(emails_tvf.c.value.ilike(pat))
            )   

            # If you are on SQLAlchemy 1.4 and .table_valued is unavailable, replace `email_match` with:
            # from sqlalchemy.sql import text
            # email_match = text(
            #     "EXISTS (SELECT 1 FROM jsonb_array_elements_text(contacts.emails) AS e(value) WHERE e.value ILIKE :pat)"
            # ).bindparams(pat=pat)

            query = query.filter(
                or_(
                    models.Contact.first_name.ilike(pat),
                    models.Contact.middle_name.ilike(pat),
                    models.Contact.last_name.ilike(pat),
                    models.Contact.local_name.ilike(pat),
                    models.Contact.company.ilike(pat),
                    email_match,  # ✅ precise match within JSON array items
                    cast(models.Contact.emails, String).ilike(pat),  # fallback: substring in JSON text
                )
            )

        return query.order_by(models.Contact.id.desc()).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error fetching contacts for user {user_id}: {str(e)}")
        raise

async def update_contact(db: Session, contact_id: int, updates: schemas.ContactCreate, owner_user_id: int):
    try:
        contact = db.query(models.Contact).filter(
            models.Contact.id == contact_id,
            models.Contact.owner_user_id == owner_user_id
        ).first()
        if not contact:
            return None

        image_to_store = contact.contact_image or ""

        # 1) Prefer new URL if provided
        if updates.contact_image and str(updates.contact_image).strip():
            image_to_store = str(updates.contact_image).strip()

        # 2) Else if a new file is provided, save it and replace (delete old local if applicable)
        elif updates.contact_image_file:
            f = updates.contact_image_file
            if f.content_type not in ["image/jpeg", "image/png", "image/gif"]:
                raise HTTPException(status_code=400, detail="Contact image must be JPEG, PNG, or GIF")
            if getattr(f, "size", None) and f.size > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Contact image must be less than 10MB")

            storage_path = os.path.join("images", str(owner_user_id), "contact")
            os.makedirs(storage_path, exist_ok=True)
            unique_filename = get_unique_filename(storage_path, f.filename)
            new_path = os.path.join(storage_path, unique_filename)
            with open(new_path, "wb") as out:
                out.write(await f.read())

            # If old was local, remove it
            if contact.contact_image and contact.contact_image.startswith("images/") and os.path.exists(contact.contact_image):
                try:
                    os.remove(contact.contact_image)
                except OSError:
                    pass

            image_to_store = new_path

        # merge other fields (unchanged)
        contact.title = updates.title or contact.title
        contact.first_name = updates.first_name or contact.first_name
        contact.middle_name = updates.middle_name or contact.middle_name
        contact.last_name = updates.last_name or contact.last_name
        contact.local_name = updates.local_name or contact.local_name
        contact.company = updates.company or contact.company
        contact.job_type = updates.job_type or contact.job_type
        contact.website = updates.website or contact.website
        contact.category = updates.category or contact.category
        contact.relation = updates.relation or contact.relation
        contact.phone_numbers = updates.phone_numbers or contact.phone_numbers
        contact.emails = updates.emails or contact.emails
        contact.whatsapp_numbers = updates.whatsapp_numbers or contact.whatsapp_numbers
        contact.flat_building_no = updates.flat_building_no or contact.flat_building_no
        contact.street = updates.street or contact.street
        contact.city = updates.city or contact.city
        contact.state = updates.state or contact.state
        contact.country = updates.country or contact.country
        contact.postal_code = updates.postal_code or contact.postal_code
        contact.date_of_birth = updates.date_of_birth or contact.date_of_birth
        contact.anniversary = updates.anniversary or contact.anniversary
        contact.notes = updates.notes or contact.notes
        contact.share_by_whatsapp = bool(updates.share_by_whatsapp)
        contact.share_by_sms = bool(updates.share_by_sms)
        contact.share_by_email = bool(updates.share_by_email)
        contact.share_after_death = bool(updates.share_after_death)
        contact.is_emergency_contact = bool(updates.is_emergency_contact)

        # finally set image
        contact.contact_image = image_to_store

        db.commit()
        db.refresh(contact)
        return contact
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating contact {contact_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update contact: {str(e)}")


def delete_contact(db: Session, contact_id: int):
    try:
        contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
        if not contact:
            return None
        if contact.contact_image and os.path.exists(contact.contact_image):
            try:
                os.remove(contact.contact_image)
            except OSError:
                pass
        db.delete(contact)
        db.commit()
        return contact
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting contact {contact_id}: {str(e)}")
        raise
