# app/routers/categories.py
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.database import SessionLocal
from app.dependencies import get_current_user, get_current_admin
from app.models.category import (
    CategoryMaster, CategorySectionMaster,
    UserCategory, UserCategorySection,
    CategoryProgressLeaf, ProgressLeafStatus
)
from app.schemas.category import (
    CategoryMasterCreate, CategoryMasterUpdate, CategoryMasterResponse,
    SectionMasterCreate, SectionMasterUpdate, SectionMasterResponse,
    UserCategoryCreate, UserCategoryResponse,
    UserCategorySectionCreate, UserCategorySectionResponse,
)
from app.controller.death import _verify_quick_token_leaf  # single-leaf verifier (already existing)
from app.models.death import AuditLog
from app.models.user import User
from app.models.contact import Contact
from app.models.step import FormStep, StepOption, StepType
# stdlib (needed for token encode/verify)
import hmac, hashlib, json, base64

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.schemas.releases import ReleaseItemOut
from app.models.step import FormStep, StepType
from app.models.user_forms import UserSectionProgress, UserStepAnswer
from app.models.category import CategoryMaster, CategorySectionMaster, CategoryProgressLeaf, ProgressLeafStatus
from app.models.contact import Contact

# --- Name helpers (add once in this module) ---
from typing import Dict


def _contact_display_name(c: Contact) -> str:
    parts = [c.title, c.first_name, c.middle_name, c.last_name, c.local_name]
    parts = [str(p).strip() for p in parts if p]
    name = " ".join([p for p in parts if p])
    if name:
        return name
    return c.company or f"Contact #{c.id}"

def _user_display_name(u: User) -> str:
    return getattr(u, "display_name", None) or f"User #{u.id}"

# ---------- shared DB dep ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- tiny utils used in this module ----------
def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def _b64urldec(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _get_api_base_url() -> str:
    from app.config import settings
    return settings.BACKEND_URL.rstrip("/")




# ======================================================
# CATALOG (USER-AUTH)  -> requires user JWT
# ======================================================

router = APIRouter(prefix="/catalog", tags=["Category Catalog"])

# ---------- CATEGORY MASTER ----------
@router.post("/categories", response_model=CategoryMasterResponse)
def create_category_master(
    body: CategoryMasterCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    sort_index = body.sort_index
    if sort_index is None:
        sort_index = db.execute(
            select(func.coalesce(func.max(CategoryMaster.sort_index), 0))
        ).scalar_one() + 1
    c = CategoryMaster(code=body.code, name=body.name, sort_index=sort_index, icon=body.icon)
    db.add(c); db.commit(); db.refresh(c)
    return c

@router.get("/categories", response_model=List[CategoryMasterResponse])
def list_category_masters(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return (
        db.query(CategoryMaster)
        .order_by(CategoryMaster.sort_index.asc(), CategoryMaster.id.asc())
        .all()
    )

@router.put("/categories/{category_id}", response_model=CategoryMasterResponse)
def update_category_master(
    category_id: int,
    body: CategoryMasterUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(CategoryMaster, category_id)
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    return c

@router.delete("/categories/{category_id}")
def delete_category_master(
    category_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(CategoryMaster, category_id)
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(c); db.commit()
    return {"detail": "Category deleted"}

# ---------- SECTION MASTER ----------
@router.post("/categories/{category_id}/sections", response_model=SectionMasterResponse)
def create_section_master(
    category_id: int,
    body: SectionMasterCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not db.get(CategoryMaster, category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    sort_index = body.sort_index
    if sort_index is None:
        sort_index = (
            db.query(func.coalesce(func.max(CategorySectionMaster.sort_index), 0))
              .filter(CategorySectionMaster.category_id == category_id)
              .scalar() + 1
        )
    s = CategorySectionMaster(
        category_id=category_id,
        code=body.code,
        name=body.name,
        sort_index=sort_index,
        file_import=bool(body.file_import or False),  # ← NEW
    )
    db.add(s); db.commit(); db.refresh(s)
    return s


@router.get("/categories/{category_id}/sections", response_model=List[SectionMasterResponse])
def list_section_masters(
    category_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return (
        db.query(CategorySectionMaster)
        .filter(CategorySectionMaster.category_id == category_id)
        .order_by(CategorySectionMaster.sort_index.asc(), CategorySectionMaster.id.asc())
        .all()
    )

@router.put("/sections/{section_id}", response_model=SectionMasterResponse)
def update_section_master(
    section_id: int,
    body: SectionMasterUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = db.get(CategorySectionMaster, section_id)
    if not s:
        raise HTTPException(status_code=404, detail="Section not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s

@router.delete("/sections/{section_id}")
def delete_section_master(
    section_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = db.get(CategorySectionMaster, section_id)
    if not s:
        raise HTTPException(status_code=404, detail="Section not found")
    db.delete(s); db.commit()
    return {"detail": "Section deleted"}

# ======================================================
# USER ADOPTION (USER-AUTH) -> requires user JWT
# ======================================================

user_router = APIRouter(prefix="/categories", tags=["User Categories"])

@user_router.post("/user", response_model=UserCategoryResponse)
def adopt_category(
    body: UserCategoryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not db.get(CategoryMaster, body.category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    existing = (
        db.query(UserCategory)
        .filter(UserCategory.user_id == user.id, UserCategory.category_id == body.category_id)
        .first()
    )
    if existing:
        return existing
    uc = UserCategory(user_id=user.id, category_id=body.category_id, event_type=body.event_type)
    db.add(uc); db.commit(); db.refresh(uc)
    return uc

@user_router.get("/user", response_model=List[UserCategoryResponse])
def list_user_categories(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return db.query(UserCategory).filter(UserCategory.user_id == user.id).all()

@user_router.delete("/user/{user_category_id}")
def remove_user_category(
    user_category_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    uc = db.query(UserCategory).filter(
        UserCategory.id == user_category_id,
        UserCategory.user_id == user.id
    ).first()
    if not uc:
        raise HTTPException(status_code=404, detail="User category not found")
    db.delete(uc); db.commit()
    return {"detail": "User category deleted"}

@user_router.post("/user/{user_category_id}/sections", response_model=UserCategorySectionResponse)
def adopt_section(
    user_category_id: int,
    body: UserCategorySectionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    uc = db.query(UserCategory).filter(
        UserCategory.id == user_category_id,
        UserCategory.user_id == user.id
    ).first()
    if not uc:
        raise HTTPException(status_code=404, detail="User category not found")
    if not db.get(CategorySectionMaster, body.section_master_id):
        raise HTTPException(status_code=404, detail="Section master not found")
    exists = db.query(UserCategorySection).filter(
        UserCategorySection.user_category_id == uc.id,
        UserCategorySection.section_master_id == body.section_master_id
    ).first()
    if exists:
        return exists
    us = UserCategorySection(user_category_id=uc.id, section_master_id=body.section_master_id)
    db.add(us); db.commit(); db.refresh(us)
    return us

@user_router.delete("/user/{user_category_id}/sections/{user_section_id}")
def remove_user_section(
    user_category_id: int,
    user_section_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    uc = db.query(UserCategory).filter(
        UserCategory.id == user_category_id,
        UserCategory.user_id == user.id
    ).first()
    if not uc:
        raise HTTPException(status_code=404, detail="User category not found")
    us = db.query(UserCategorySection).filter(
        UserCategorySection.id == user_section_id,
        UserCategorySection.user_category_id == uc.id
    ).first()
    if not us:
        raise HTTPException(status_code=404, detail="User category section not found")
    db.delete(us); db.commit()
    return {"detail": "User section deleted"}

# ======================================================
# ADMIN CATALOG (ADMIN-AUTH) -> requires admin JWT
# ======================================================

admin_router = APIRouter(prefix="/admin/catalog", tags=["Category Catalog (Admin)"])

@admin_router.post("/categories", response_model=CategoryMasterResponse)
def admin_create_category(
    body: CategoryMasterCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    sort_index = body.sort_index
    if sort_index is None:
        sort_index = db.execute(
            select(func.coalesce(func.max(CategoryMaster.sort_index), 0))
        ).scalar_one() + 1
    c = CategoryMaster(code=body.code, name=body.name, sort_index=sort_index, icon=body.icon)
    db.add(c); db.commit(); db.refresh(c)
    return c

@admin_router.get("/categories", response_model=List[CategoryMasterResponse])
def admin_list_categories(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return (
        db.query(CategoryMaster)
        .order_by(CategoryMaster.sort_index.asc(), CategoryMaster.id.asc())
        .all()
    )

@admin_router.put("/categories/{category_id}", response_model=CategoryMasterResponse)
def admin_update_category(
    category_id: int,
    body: CategoryMasterUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    c = db.get(CategoryMaster, category_id)
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    return c

@admin_router.delete("/categories/{category_id}")
def admin_delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    c = db.get(CategoryMaster, category_id)
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(c); db.commit()
    return {"detail": "Category deleted"}

@admin_router.post("/categories/{category_id}/sections", response_model=SectionMasterResponse)
def admin_create_section(
    category_id: int,
    body: SectionMasterCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    if not db.get(CategoryMaster, category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    sort_index = body.sort_index
    if sort_index is None:
        sort_index = (
            db.query(func.coalesce(func.max(CategorySectionMaster.sort_index), 0))
              .filter(CategorySectionMaster.category_id == category_id)
              .scalar() + 1
        )
    s = CategorySectionMaster(
        category_id=category_id,
        code=body.code,
        name=body.name,
        sort_index=sort_index,
        file_import=bool(body.file_import or False),  # ← NEW
    )
    db.add(s); db.commit(); db.refresh(s)
    return s


@admin_router.get("/categories/{category_id}/sections", response_model=List[SectionMasterResponse])
def admin_list_sections(
    category_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return (
        db.query(CategorySectionMaster)
        .filter(CategorySectionMaster.category_id == category_id)
        .order_by(CategorySectionMaster.sort_index.asc(), CategorySectionMaster.id.asc())
        .all()
    )

@admin_router.put("/sections/{section_id}", response_model=SectionMasterResponse)
def admin_update_section(
    section_id: int,
    body: SectionMasterUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    s = db.get(CategorySectionMaster, section_id)
    if not s:
        raise HTTPException(status_code=404, detail="Section not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s

@admin_router.delete("/sections/{section_id}")
def admin_delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    s = db.get(CategorySectionMaster, section_id)
    if not s:
        raise HTTPException(status_code=404, detail="Section not found")
    db.delete(s); db.commit()
    return {"detail": "Section deleted"}

# ======================================================
# PUBLIC QUICK (no auth) — leaves
# ======================================================

public_leaf_router = APIRouter(prefix="/catalog/leaves", tags=["Leaves (public quick)"])

# ---------------- BULK token helpers (NO EXPIRY) ----------------
def _gen_quick_token_leaf_bulk(root_user_id: int, contact_id: int, decision: str) -> str:
    """
    decision: "accept_all" | "reject_all"
    """
    from app.config import settings
    secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
    payload = {"rid": int(root_user_id), "cid": int(contact_id), "dec": str(decision)}
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(secret, data, hashlib.sha256).digest()
    return f"{_b64url(data)}.{_b64url(sig)}"

def _verify_quick_token_leaf_bulk(token: str, root_user_id: int, contact_id: int, decision: str) -> bool:
    try:
        from app.config import settings
        secret = getattr(settings, "SECRET_KEY", "dev-secret").encode()
        parts = token.split(".")
        if len(parts) != 2:
            return False
        data_b = _b64urldec(parts[0])
        sig_b  = _b64urldec(parts[1])
        exp_sig = hmac.new(secret, data_b, hashlib.sha256).digest()
        if not hmac.compare_digest(sig_b, exp_sig):
            return False
        payload = json.loads(data_b.decode())
        if int(payload.get("rid")) != int(root_user_id):
            return False
        if int(payload.get("cid")) != int(contact_id):
            return False
        if str(payload.get("dec")) != str(decision):
            return False
        # no expiry check
        return True
    except Exception:
        return False

def _compose_leaf_bulk_accept_url(root_user_id: int, contact_id: int, token: str) -> str:
    api = _get_api_base_url()
    return f"{api}/catalog/leaves/a/bulk/{root_user_id}/{contact_id}/{token}"

def _compose_leaf_bulk_reject_url(root_user_id: int, contact_id: int, token: str) -> str:
    api = _get_api_base_url()
    return f"{api}/catalog/leaves/r/bulk/{root_user_id}/{contact_id}/{token}"

# ---------------- PUBLIC BULK endpoints ----------------
@public_leaf_router.get("/a/bulk/{root_user_id}/{contact_id}/{token:path}")
def leaf_accept_bulk(root_user_id: int, contact_id: int, token: str, db: Session = Depends(get_db)):
    if not _verify_quick_token_leaf_bulk(token, root_user_id, contact_id, "accept_all"):
        return HTMLResponse("<h3>Invalid or expired link.</h3>", status_code=400)

    leaves = (
        db.query(CategoryProgressLeaf)
        .filter(
            CategoryProgressLeaf.user_id == root_user_id,
            CategoryProgressLeaf.contact_id == contact_id,
            CategoryProgressLeaf.status == ProgressLeafStatus.active,
        )
        .all()
    )
    if not leaves:
        return HTMLResponse("<h3>Nothing to do.</h3><p>No active items found.</p>", status_code=200)

    for lf in leaves:
        lf.status = ProgressLeafStatus.accepted
        db.add(AuditLog(
            actor_type="contact",
            actor_id=contact_id,
            action="leaf_accept_bulk_link",
            entity_type="CategoryProgressLeaf",
            entity_id=lf.id,
            data_json=None
        ))
    db.commit()
    return HTMLResponse(f"<h3>Done</h3><p>Accepted {len(leaves)} item(s).</p>", status_code=200)

@public_leaf_router.get("/r/bulk/{root_user_id}/{contact_id}/{token:path}")
def leaf_reject_bulk(root_user_id: int, contact_id: int, token: str, db: Session = Depends(get_db)):
    if not _verify_quick_token_leaf_bulk(token, root_user_id, contact_id, "reject_all"):
        return HTMLResponse("<h3>Invalid or expired link.</h3>", status_code=400)

    leaves = (
        db.query(CategoryProgressLeaf)
        .filter(
            CategoryProgressLeaf.user_id == root_user_id,
            CategoryProgressLeaf.contact_id == contact_id,
            CategoryProgressLeaf.status == ProgressLeafStatus.active,
        )
        .all()
    )
    if not leaves:
        return HTMLResponse("<h3>Nothing to do.</h3><p>No active items found.</p>", status_code=200)

    for lf in leaves:
        lf.status = ProgressLeafStatus.removed
        db.add(AuditLog(
            actor_type="contact",
            actor_id=contact_id,
            action="leaf_reject_bulk_link",
            entity_type="CategoryProgressLeaf",
            entity_id=lf.id,
            data_json=None
        ))
    db.commit()
    return HTMLResponse(f"<h3>Done</h3><p>Declined {len(leaves)} item(s).</p>", status_code=200)




# ======================================================
# PUBLIC: name map by leaf token
# ======================================================
@public_leaf_router.get("/names/by-leaf/{leaf_id}/{token:path}")
def names_by_leaf_token(
    leaf_id: int,
    token: str,
    db: Session = Depends(get_db),
):
    
    # Accept either accept-token or reject-token for convenience
    ok = _verify_quick_token_leaf(token, leaf_id, "accept") or _verify_quick_token_leaf(token, leaf_id, "reject")
    if not ok:
        return {"user": {}, "contact": {}}

    leaf = db.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.id == leaf_id).first()
    if not leaf:
        return {"user": {}, "contact": {}}

    owner = db.query(User).filter(User.id == leaf.user_id).first()
    contact = db.query(Contact).filter(Contact.id == leaf.contact_id).first()

    user_map: Dict[int, str] = {}
    contact_map: Dict[int, str] = {}

    if owner:
        user_map[owner.id] = _user_display_name(owner)
    if contact:
        contact_map[contact.id] = _contact_display_name(contact)

    return {"user": user_map, "contact": contact_map}




# ---------------- PUBLIC SINGLE endpoints ----------------
@public_leaf_router.get("/a/{leaf_id}/{token:path}")
def leaf_accept(leaf_id: int, token: str, db: Session = Depends(get_db)):
    if not _verify_quick_token_leaf(token, leaf_id, "accept"):
        return HTMLResponse("<h3>Invalid or expired link.</h3>", status_code=400)

    leaf = db.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.id == leaf_id).first()
    if not leaf:
        return HTMLResponse("<h3>Not found.</h3>", status_code=404)

    if leaf.status == ProgressLeafStatus.removed:
        return HTMLResponse("<h3>Link no longer valid.</h3><p>This assignment was declined earlier.</p>", status_code=400)

    leaf.status = ProgressLeafStatus.accepted
    db.add(AuditLog(
        actor_type="contact",
        actor_id=leaf.contact_id,
        action="leaf_accept",
        entity_type="CategoryProgressLeaf",
        entity_id=leaf.id,
        data_json=None
    ))
    db.commit()
    return HTMLResponse("<h3>Thanks!</h3><p>You've accepted the assignment.</p>", status_code=200)

@public_leaf_router.get("/r/{leaf_id}/{token:path}")
def leaf_reject(leaf_id: int, token: str, db: Session = Depends(get_db)):
    if not _verify_quick_token_leaf(token, leaf_id, "reject"):
        return HTMLResponse("<h3>Invalid or expired link.</h3>", status_code=400)

    leaf = db.query(CategoryProgressLeaf).filter(CategoryProgressLeaf.id == leaf_id).first()
    if not leaf:
        return HTMLResponse("<h3>Not found.</h3>", status_code=404)

    leaf.status = ProgressLeafStatus.removed
    db.add(AuditLog(
        actor_type="contact",
        actor_id=leaf.contact_id,
        action="leaf_reject",
        entity_type="CategoryProgressLeaf",
        entity_id=leaf.id,
        data_json=None
    ))
    db.commit()
    return HTMLResponse("<h3>Done</h3><p>You declined the assignment.</p>", status_code=200)

# ======================================================
# LEAVES (USER-AUTH) -> requires user JWT
# ======================================================

# ======================================================
# LEAVES (USER-AUTH) -> requires user JWT
# ======================================================

leaf_user_router = APIRouter(prefix="/catalog/leaves", tags=["Leaves (user)"])

# ======================================================
# USER-AUTH: name map by owner (show all contacts for that owner)
# ======================================================
@leaf_user_router.get("/names/owner/{owner_user_id}")
def names_for_owner_all_contacts(
    owner_user_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    
    invited = (
        db.query(CategoryProgressLeaf)
        .join(Contact, Contact.id == CategoryProgressLeaf.contact_id)
        .filter(
            CategoryProgressLeaf.user_id == owner_user_id,
            Contact.linked_user_id == user.id
        )
        .first()
    )
    if not invited:
        return {"user": {}, "contact": {}}

    owner = db.query(User).filter(User.id == owner_user_id).first()
    user_map = {}
    if owner:
        user_map[owner.id] = _user_display_name(owner)

    contacts = db.query(Contact).filter(Contact.owner_user_id == owner_user_id).all()
    contact_map = {c.id: _contact_display_name(c) for c in contacts}

    return {"user": user_map, "contact": contact_map}


def _actor_is_assignee(db: Session, *, user_id: int, leaf: CategoryProgressLeaf) -> bool:
    """
    You assign leaves to a Contact; the invitee is the Contact's linked user.
    """
    c = db.query(Contact).filter(Contact.id == leaf.contact_id).first()
    return bool(c and c.linked_user_id == user_id)

@leaf_user_router.get("/todo")
def list_my_leaves_todo(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = (
        db.query(CategoryProgressLeaf, User)
        .join(Contact, Contact.id == CategoryProgressLeaf.contact_id)
        .join(User, User.id == CategoryProgressLeaf.user_id)  # owner/root
        .filter(Contact.linked_user_id == user.id)
        .order_by(CategoryProgressLeaf.id.desc())
    )

    out = []
    for leaf, owner in q.all():
        out.append({
            "id": leaf.id,
            "status": getattr(leaf.status, "value", str(leaf.status)),
            "inviter_user_id": owner.id,
            "inviter_display_name": getattr(owner, "display_name", None) or f"User #{owner.id}",
            "invited_at": getattr(leaf, "created_at", None),
        })
    return out

@leaf_user_router.post("/accept-as-invitee/bulk/{root_user_id}")
def accept_leaves_bulk_as_invitee(root_user_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    contacts = db.query(Contact).filter(Contact.linked_user_id == user.id).all()
    cids = [c.id for c in contacts]
    if not cids:
        raise HTTPException(status_code=404, detail="No linked contacts found")

    leaves = (
        db.query(CategoryProgressLeaf)
        .filter(
            CategoryProgressLeaf.user_id == root_user_id,
            CategoryProgressLeaf.contact_id.in_(cids),
            CategoryProgressLeaf.status == ProgressLeafStatus.active
        ).all()
    )
    if not leaves:
        return {"ok": True, "updated": 0}

    for leaf in leaves:
        leaf.status = ProgressLeafStatus.accepted
        # ---- HOTFIX: don't let AuditLog failure 500 the request in prod ----
        try:
            db.add(AuditLog(
                actor_type="user",
                actor_id=user.id,
                action="leaf_accept_bulk_app",
                entity_type="CategoryProgressLeaf",
                entity_id=leaf.id,
                data_json=None
            ))
        except Exception:
            # optional: log to your logger instead of crashing
            pass

    db.commit()
    return {"ok": True, "updated": len(leaves)}


@leaf_user_router.post("/reject-as-invitee/bulk/{root_user_id}")
def reject_leaves_bulk_as_invitee(
    root_user_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    contacts = db.query(Contact).filter(Contact.linked_user_id == user.id).all()
    cids = [c.id for c in contacts]
    if not cids:
        raise HTTPException(status_code=404, detail="No linked contacts found")

    leaves = (
        db.query(CategoryProgressLeaf)
        .filter(
            CategoryProgressLeaf.user_id == root_user_id,
            CategoryProgressLeaf.contact_id.in_(cids),
            CategoryProgressLeaf.status == ProgressLeafStatus.active
        ).all()
    )
    if not leaves:
        return {"ok": True, "updated": 0}

    for leaf in leaves:
        leaf.status = ProgressLeafStatus.removed
        db.add(AuditLog(
            actor_type="user",
            actor_id=user.id,
            action="leaf_reject_bulk_app",
            entity_type="CategoryProgressLeaf",
            entity_id=leaf.id,
            data_json=None
        ))
    db.commit()
    return {"ok": True, "updated": len(leaves)}







def _is_http_url(s: Any) -> bool:
    return isinstance(s, str) and s.startswith(("http://", "https://"))

def _file_id_to_url(file_id: int) -> str:
    """Map your numeric file id to a public URL.
       Adjust to your real files service if different."""
    base = _get_api_base_url()  # you already have this helper above
    return f"{base}/files/{int(file_id)}"

def _value_to_urls(val) -> List[str]:
    """Normalize answers (ints, strings, lists) into a list of URLs."""
    if val is None:
        return []
    if isinstance(val, list):
        urls = []
        for v in val:
            if isinstance(v, int):
                urls.append(_file_id_to_url(v))
            elif _is_http_url(v):
                urls.append(v)
        return urls
    # scalar
    if isinstance(val, int):
        return [_file_id_to_url(val)]
    if _is_http_url(val):
        return [val]
    return []

def _gather_file_urls_for_progress(db: Session, progress_id: int, section_id: int) -> List[str]:
    """Collect all image/file URLs for this entry based on step types and section photo."""
    urls: List[str] = []

    # section photo (if present)
    p = db.query(UserSectionProgress).filter(UserSectionProgress.id == progress_id).first()
    if p and p.section_photo_url and _is_http_url(p.section_photo_url):
        urls.append(p.section_photo_url)

    # find photo/file steps for this section
    steps = db.query(FormStep).filter(FormStep.section_master_id == section_id).all()
    types_by_id = {s.id: s.type for s in steps if s.type in (StepType.photo, StepType.file_upload)}

    if types_by_id:
        rows = db.query(UserStepAnswer).filter(UserStepAnswer.progress_id == progress_id).all()
        for r in rows:
            if r.step_id in types_by_id:
                urls.extend(_value_to_urls(r.value))

    # dedupe while keeping order
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique

def _progress_to_release_item(
    db: Session,
    p: UserSectionProgress,
    category: CategoryMaster,
    section: CategorySectionMaster,
) -> ReleaseItemOut:
    title = section.name or f"Section #{section.id}"

    answers_kv, display = _answers_display_for_progress(db, section.id, p.id)
    urls = _gather_file_urls_for_progress(db, p.id, section.id)

    meta: Dict[str, Any] = {
        "category_name": category.name,
        "section_name": section.name,
        "notes": None,
        "answers": answers_kv,          # raw map
        "display": display,             # ready-to-render rows
        "progress_id": p.id,
        "section_photo_url": p.section_photo_url,
        "submitted_at": p.submitted_at,
        "saved_at": p.saved_at,
    }

    return ReleaseItemOut(
        id=p.id,
        title=title,
        urls=urls,
        meta=meta,
        updated_at=(p.saved_at or p.submitted_at or datetime.utcnow()).isoformat(),
    )


@leaf_user_router.get("/releases/{owner_user_id}", response_model=List[ReleaseItemOut])
def list_releases_for_invitee(
    owner_user_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
   

    # all contacts that represent the current viewer
    contacts = db.query(Contact).filter(Contact.linked_user_id == user.id).all()
    contact_ids = [c.id for c in contacts]
    if not contact_ids:
        return []

    # find leaves created by the owner, addressed to any of these contacts
    leaves = (
        db.query(CategoryProgressLeaf)
        .filter(
            CategoryProgressLeaf.user_id == owner_user_id,
            CategoryProgressLeaf.contact_id.in_(contact_ids),
            CategoryProgressLeaf.status.in_([ProgressLeafStatus.active, ProgressLeafStatus.accepted]),
        )
        .all()
    )
    if not leaves:
        return []

    # fetch all progress ids, sections, categories in batch
    prog_ids = list({lf.progress_id for lf in leaves})
    progresses = db.query(UserSectionProgress).filter(UserSectionProgress.id.in_(prog_ids)).all()
    prog_by_id = {p.id: p for p in progresses}

    sec_ids = list({p.section_id for p in progresses})
    sections = db.query(CategorySectionMaster).filter(CategorySectionMaster.id.in_(sec_ids)).all()
    sec_by_id = {s.id: s for s in sections}

    cat_ids = list({p.category_id for p in progresses})
    cats = db.query(CategoryMaster).filter(CategoryMaster.id.in_(cat_ids)).all()
    cat_by_id = {c.id: c for c in cats}

    out: List[ReleaseItemOut] = []
    for lf in leaves:
        p = prog_by_id.get(lf.progress_id)
        if not p:
            continue
        sec = sec_by_id.get(p.section_id)
        cat = cat_by_id.get(p.category_id)
        if not sec or not cat:
            continue
        out.append(_progress_to_release_item(db, p, cat, sec))

    # newest first
    out.sort(key=lambda x: x.updated_at or "", reverse=True)
    return out


# Optional mirror so your fallback also works:
forms_user_router = APIRouter(prefix="/user/forms", tags=["User Forms (releases mirror)"])

@forms_user_router.get("/releases/{owner_user_id}", response_model=List[ReleaseItemOut])
def list_releases_for_invitee_alias(
    owner_user_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Reuse the same logic by calling the above function
    return list_releases_for_invitee(owner_user_id, db=db, user=user)





def _answers_display_for_progress(
    db: Session,
    section_id: int,
    progress_id: int
) -> tuple[dict, list[dict]]:
   
    steps = db.query(FormStep).filter(FormStep.section_master_id == section_id).order_by(FormStep.display_order.asc()).all()
    step_by_id = {s.id: s for s in steps}
    qid_by_id = {s.id: (s.question_id or f"step:{s.id}") for s in steps}
    title_by_id = {s.id: (s.title or f"Step {s.id}") for s in steps}

    # options (for label mapping)
    opts = db.query(StepOption).filter(StepOption.step_id.in_([s.id for s in steps] or [0])).all()
    by_step_val_to_label = {}
    for o in opts:
        by_step_val_to_label.setdefault(o.step_id, {})[str(o.value)] = o.label

    rows = db.query(UserStepAnswer).filter(UserStepAnswer.progress_id == progress_id).all()

    answers_kv: dict = {}
    display: list = []

    for r in rows:
        s = step_by_id.get(r.step_id)
        if not s:
            continue
        qid = qid_by_id.get(r.step_id, f"step:{r.step_id}")
        answers_kv[qid] = r.value

        label = title_by_id.get(r.step_id, qid)

        # pretty value
        pretty = None
        if s.type in (StepType.photo, StepType.file_upload):
            # don’t show raw ids/urls as text here (the UI shows files from urls)
            pretty = None
        elif s.type in (StepType.list, StepType.checklist):
            arr = r.value if isinstance(r.value, list) else [r.value]
            mapped = []
            valmap = by_step_val_to_label.get(r.step_id, {})
            for v in arr:
                mapped.append(valmap.get(str(v), str(v)))
            pretty = ", ".join([str(x) for x in mapped if x is not None]) or None
        elif s.type == StepType.single_select:
            pretty = by_step_val_to_label.get(r.step_id, {}).get(str(r.value), str(r.value))
        else:
            pretty = str(r.value) if r.value is not None else None

        display.append({
            "label": label,
            "value": pretty,
            "raw": r.value,
            "step_id": r.step_id,
            "question_id": qid,
        })

    return answers_kv, display


