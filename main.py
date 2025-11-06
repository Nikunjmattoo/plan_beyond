# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine

# ============================================
# RATE LIMITER & ERROR HANDLER IMPORTS (NEW)
# ============================================
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.encryption_module.rate_limiter import limiter, rate_limit_exceeded_handler
from app.encryption_module.error_handlers import register_error_handlers
# ============================================

# --- Routers (import as modules for some, explicit for others) ---
from app.routers import auth, s3_upload, user, contact, file
from app.routers import trustees, memories, forms_user

# NEW: Import policy checker router
from app.routers import policy

# NEW: Import reminder router
from app.routers import reminder

# Import category routers with explicit names (they live in one file)
from app.routers.categories import (
    router as catalog_router,                # /catalog (user-auth)
    user_router as user_categories_router,   # /categories (user-auth)
    admin_router as admin_catalog_router,    # /admin/catalog (admin-auth)
    public_leaf_router,                      # /catalog/leaves/a|r/... (public quick links)
    leaf_user_router,                        # /catalog/leaves (user-auth: todo/accept/reject)
)

# Import steps routers with explicit names from steps.py
from app.routers.steps import (
    router as steps_router,            # /steps (user-auth)
    admin_steps_router as admin_steps_router,  # /admin/steps (admin-auth)
)

from app.routers.messages import router as messages_router  # /messages

# NEW: import the death router (defines prefix="/v1/death")
from app.routers.death import death_router

from app.routers import vault

import os

# --- Bootstrap ---
os.makedirs("images", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ============================================
# REGISTER RATE LIMITER & ERROR HANDLERS (NEW)
# ============================================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
register_error_handlers(app)  # Register encryption error handlers
# ============================================

# Static mounts
app.mount("/images", StaticFiles(directory="images"), name="images")
app.include_router(s3_upload.router, prefix="/s3", tags=["S3"]) 
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ----------------------------
# Include routers (clear order)
# ----------------------------

# Auth / core resources
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(contact.router, prefix="/contacts", tags=["contacts"])
app.include_router(file.router, prefix="/files", tags=["Files"])

# NEW: Policy Checker
app.include_router(policy.router, prefix="/api", tags=["Policy Checker"])

# NEW: Reminder System
app.include_router(reminder.router, tags=["Reminders"])

# Misc
app.include_router(trustees.router)
app.include_router(memories.router)
app.include_router(forms_user.router)
app.include_router(vault.router, tags=["Vault"])

# Catalog (user + admin)
app.include_router(catalog_router)            # /catalog/*
app.include_router(user_categories_router)    # /categories (user adoption)
app.include_router(admin_catalog_router)      # /admin/catalog/*

# Steps (user + admin)
app.include_router(steps_router)              # /steps/*
app.include_router(admin_steps_router)        # /admin/steps/*

# NEW: include the death router so /v1/death/* exists
app.include_router(death_router)              # /v1/death/*
app.include_router(public_leaf_router)
app.include_router(leaf_user_router)

app.include_router(messages_router)  # /messages/*




app.include_router(policy.router_api)
# -------------
# CORS settings
# -------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        # add prod origins if needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Swagger JWT Security Scheme
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Plan Beyond API",
        version="1.0.0",
        description="API with JWT authentication",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", []).append({"BearerAuth": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema

@app.get("/")
def root():
    return {"message": "API is running"}

app.openapi = custom_openapi