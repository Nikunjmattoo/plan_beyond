# # app/routers/s3_upload.py
# import mimetypes
# import re
# from uuid import uuid4
# from typing import Optional
# import boto3
# from botocore.exceptions import BotoCoreError, ClientError
# from fastapi import APIRouter, File, UploadFile, HTTPException, Query
# from fastapi.responses import RedirectResponse
# from app.config import settings  # uses your pydantic Settings

# router = APIRouter()

# # --- config ---
# AWS_REGION = settings.AWS_REGION
# S3_BUCKET = settings.S3_BUCKET
# S3_PUBLIC_BASE_URL = settings.S3_PUBLIC_BASE_URL  
# BACKEND_URL = getattr(settings, "BACKEND_URL", "http://localhost:8000")

# s3 = boto3.client(
#     "s3",
#     region_name=AWS_REGION,
#     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
# )

# SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
# ALLOWED_IMAGE_TYPES = {
#     "image/jpeg", "image/png", "image/webp", "image/gif", "image/heic", "image/heif",
# }

# def _safe_filename(name: str) -> str:
#     name = (name or "image").strip().replace(" ", "_")
#     return SAFE_NAME_RE.sub("", name) or "image"

# @router.get("/health")
# def s3_health():
#     try:
#         s3.head_bucket(Bucket=S3_BUCKET)
#         loc = s3.get_bucket_location(Bucket=S3_BUCKET).get("LocationConstraint") or "us-east-1"
#         return {"ok": True, "bucket": S3_BUCKET, "region": loc}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"S3 not reachable: {e}")

# # ---------- NEW: short, stable URL that redirects to a fresh presigned GET ----------
# @router.get("/media/{path:path}", include_in_schema=False)
# def serve_private_media(path: str):
#     """Return a short app URL that redirects to a fresh presigned GET URL."""
#     try:
#         url = s3.generate_presigned_url(
#             ClientMethod="get_object",
#             Params={"Bucket": S3_BUCKET, "Key": path},
#             ExpiresIn=3600,  # 1 hour
#         )
#     except (BotoCoreError, ClientError) as e:
#         raise HTTPException(status_code=500, detail=f"Failed to sign URL: {e}")
#     return RedirectResponse(url)

# @router.post("/upload")
# async def upload_file_to_s3(
#     file: UploadFile = File(...),
#     folder: str = Query(default="uploads"),
#     return_public_url: bool = Query(
#         default=False,
#         description="If bucket has a public-read policy, set this true to also return the plain S3 URL.",
#     ),
# ):
#     # infer/normalize the content type (allow ANY)
#     inferred_ct = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"

#     original = _safe_filename(file.filename or "file")
#     prefix = folder.strip("/ ")
#     key = f"{prefix}/{uuid4().hex}_{original}" if prefix else f"{uuid4().hex}_{original}"

#     extra_args = {"ContentType": inferred_ct}  # no ACLs (Object Ownership enforced)

#     try:
#         file.file.seek(0)
#         s3.upload_fileobj(file.file, S3_BUCKET, key, ExtraArgs=extra_args)
#     except ClientError as e:
#         code = e.response.get("Error", {}).get("Code", "")
#         msg = e.response.get("Error", {}).get("Message", str(e))
#         raise HTTPException(status_code=500, detail=f"S3 upload failed: {code or ''} {msg}")

#     app_url = f"{S3_PUBLIC_BASE_URL}/{key}"

#     resp = {
#         "bucket": S3_BUCKET,
#         "key": key,
#         "content_type": inferred_ct,
#         "app_url": app_url,
#     }
#     if return_public_url:
#         resp["public_url"] = f"{S3_PUBLIC_BASE_URL}/{key}"

#     return resp
# @router.post("/presign-form")
# def create_presigned_post(
#     filename: str,
#     content_type: Optional[str] = "image/*",
#     folder: str = Query(default="uploads"),
#     expires_in: int = Query(default=60, ge=1, le=3600),
# ):
#     safe = _safe_filename(filename or "image")
#     prefix = folder.strip("/ ")
#     key = f"{prefix}/{uuid4().hex}_{safe}" if prefix else f"{uuid4().hex}_{safe}"

#     conditions = [["starts-with", "$Content-Type", "image/"]]
#     fields = {}
#     if content_type and content_type != "image/*":
#         fields["Content-Type"] = content_type
#         conditions.append({"Content-Type": content_type})

#     try:
#         post = s3.generate_presigned_post(
#             Bucket=S3_BUCKET, Key=key, Fields=fields, Conditions=conditions, ExpiresIn=expires_in
#         )
#     except (BotoCoreError, ClientError) as e:
#         raise HTTPException(status_code=500, detail=f"Failed to generate presigned form: {e}")

#     # Also return the app_url for later access (redirects)
#     return {
#         "key": key,
#         "post": post,
#         "app_url": f"{S3_PUBLIC_BASE_URL}/{key}",
#         "public_url": f"{S3_PUBLIC_BASE_URL}/{key}",  # will work only if bucket policy allows
#     }

# @router.post("/presign-put")
# def create_presigned_put(
#     filename: str,
#     content_type: str = "image/jpeg",
#     folder: str = Query(default="uploads"),
#     expires_in: int = Query(default=60, ge=1, le=3600),
# ):
#     safe = _safe_filename(filename or "image")
#     prefix = folder.strip("/ ")
#     key = f"{prefix}/{uuid4().hex}_{safe}" if prefix else f"{uuid4().hex}_{safe}"

#     try:
#         url = s3.generate_presigned_url(
#             ClientMethod="put_object",
#             Params={"Bucket": S3_BUCKET, "Key": key, "ContentType": content_type},
#             ExpiresIn=expires_in,
#         )
#     except (BotoCoreError, ClientError) as e:
#         raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {e}")

#     return {
#         "key": key,
#         "put_url": url,
#         "app_url": f"{S3_PUBLIC_BASE_URL}/{key}",
#         "public_url": f"{S3_PUBLIC_BASE_URL}/{key}",  # works only with a public-read bucket policy
#     }







# app/routers/s3_upload.py
import mimetypes
import re
from uuid import uuid4
from typing import Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.config import settings  # uses your pydantic Settings

router = APIRouter()

# --- config ---
AWS_REGION = settings.AWS_REGION
S3_BUCKET = settings.S3_BUCKET
S3_PUBLIC_BASE_URL = settings.S3_PUBLIC_BASE_URL  
BACKEND_URL = getattr(settings, "BACKEND_URL", "http://localhost:8000")

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "image/heic", "image/heif",
}

def _safe_filename(name: str) -> str:
    name = (name or "image").strip().replace(" ", "_")
    return SAFE_NAME_RE.sub("", name) or "image"

@router.get("/health")
def s3_health():
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
        loc = s3.get_bucket_location(Bucket=S3_BUCKET).get("LocationConstraint") or "us-east-1"
        return {"ok": True, "bucket": S3_BUCKET, "region": loc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 not reachable: {e}")

# ---------- NEW: short, stable URL that redirects to a fresh presigned GET ----------
@router.get("/media/{path:path}", include_in_schema=False)
def serve_private_media(path: str):
    """Return a short app URL that redirects to a fresh presigned GET URL."""
    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": S3_BUCKET, "Key": path},
            ExpiresIn=3600,  # 1 hour
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign URL: {e}")
    return RedirectResponse(url)

@router.post("/upload")
async def upload_file_to_s3(
    file: UploadFile = File(...),
    folder: str = Query(default="uploads"),
    return_public_url: bool = Query(
        default=False,
        description="If bucket has a public-read policy, set this true to also return the plain S3 URL.",
    ),
):
    # infer/normalize the content type (allow ANY)
    inferred_ct = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"

    original = _safe_filename(file.filename or "file")
    prefix = folder.strip("/ ")
    key = f"{prefix}/{uuid4().hex}_{original}" if prefix else f"{uuid4().hex}_{original}"

    extra_args = {"ContentType": inferred_ct}  # no ACLs (Object Ownership enforced)

    try:
        file.file.seek(0)
        s3.upload_fileobj(file.file, S3_BUCKET, key, ExtraArgs=extra_args)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", str(e))
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {code or ''} {msg}")

    app_url = f"{S3_PUBLIC_BASE_URL}/{key}"

    resp = {
        "bucket": S3_BUCKET,
        "key": key,
        "content_type": inferred_ct,
        "app_url": app_url,
    }
    if return_public_url:
        resp["public_url"] = f"{S3_PUBLIC_BASE_URL}/{key}"

    return resp

@router.post("/presign-form")
def create_presigned_post(
    filename: str,
    content_type: Optional[str] = "image/*",
    folder: str = Query(default="uploads"),
    expires_in: int = Query(default=60, ge=1, le=3600),
):
    safe = _safe_filename(filename or "image")
    prefix = folder.strip("/ ")
    key = f"{prefix}/{uuid4().hex}_{safe}" if prefix else f"{uuid4().hex}_{safe}"

    conditions = [["starts-with", "$Content-Type", "image/"]]
    fields = {}
    if content_type and content_type != "image/*":
        fields["Content-Type"] = content_type
        conditions.append({"Content-Type": content_type})

    try:
        post = s3.generate_presigned_post(
            Bucket=S3_BUCKET, Key=key, Fields=fields, Conditions=conditions, ExpiresIn=expires_in
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned form: {e}")

    # Also return the app_url for later access (redirects)
    return {
        "key": key,
        "post": post,
        "app_url": f"{S3_PUBLIC_BASE_URL}/{key}",
        "public_url": f"{S3_PUBLIC_BASE_URL}/{key}",  # will work only if bucket policy allows
    }

@router.post("/presign-put")
def create_presigned_put(
    filename: str,
    content_type: str = "image/jpeg",
    folder: str = Query(default="uploads"),
    expires_in: int = Query(default=60, ge=1, le=3600),
):
    safe = _safe_filename(filename or "image")
    prefix = folder.strip("/ ")
    key = f"{prefix}/{uuid4().hex}_{safe}" if prefix else f"{uuid4().hex}_{safe}"

    try:
        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": S3_BUCKET, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {e}")

    return {
        "key": key,
        "put_url": url,
        "app_url": f"{S3_PUBLIC_BASE_URL}/{key}",
        "public_url": f"{S3_PUBLIC_BASE_URL}/{key}",  # works only with a public-read bucket policy
    }
