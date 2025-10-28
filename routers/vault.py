"""API endpoints for vault file encryption operations with input validation."""
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional
import base64

from app.dependencies import get_db, get_current_user_id
from app.schemas.vault_schemas import (
    VaultFileSaveRequest,
    VaultFileSaveResponse,
    VaultFileMetadataResponse,
    VaultFileDecryptionMetadataResponse,
    VaultFileDecryptedResponse,
    VaultFileListResponse,
    VaultFileShareRequest,
    VaultFileAccessResponse,
    VaultFileAccessActivateRequest,
    VaultFileAccessListResponse,
    VaultFileAccessListItem
)

from app.encryption_module.core.vault_encryptor import encrypt_vault_file
from app.encryption_module.core.vault_decryptor import decrypt_vault_file, get_decryption_metadata
from app.encryption_module.core.db_operations import VaultDatabaseOperations

# Import error handling
from app.encryption_module.error_handlers import register_error_handlers
from app.encryption_module.schemas.error_responses import ERROR_RESPONSES
from app.encryption_module.exceptions import NotFileOwnerException

# Import validators
from app.encryption_module.validators import (
    validate_upload_file,
    validate_form_data,
    validate_creation_mode,
    validate_template_id,
    sanitize_filename
)


router = APIRouter(prefix="/api/vault", tags=["vault"])

# ==========================================
# SAVE VAULT FILE
# ==========================================

@router.post(
    "/save",
    response_model=VaultFileSaveResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES
)
async def save_vault_file(
    template_id: str = Form(...),
    form_data: str = Form(..., description="JSON string of form data"),
    creation_mode: str = Form(..., description="'import' or 'manual'"),
    source_file: Optional[UploadFile] = File(None),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Save encrypted vault file with input validation.
    
    - **template_id**: Template identifier
    - **form_data**: JSON string of form field data (max 1MB)
    - **creation_mode**: 'import' or 'manual'
    - **source_file**: Optional file upload (max 10MB, allowed types: PDF, Word, Excel, Images)
    
    Validations enforced:
    - File size: 10MB max
    - Form data: 1MB max
    - MIME types: PDF, Word, Excel, Images, Text, CSV
    - Form fields: 100 max, 10K chars per field
    """
    # Validate inputs
    validate_template_id(template_id)
    validate_creation_mode(creation_mode)
    
    # Validate and parse form data (raises exceptions on failure)
    form_data_dict = validate_form_data(form_data)
    
    # Validate and read source file if provided
    source_file_bytes = None
    source_file_name = None
    source_file_mime = None
    
    if source_file:
        # Validate file (size + MIME type)
        source_file_bytes = await validate_upload_file(source_file)
        source_file_name = sanitize_filename(source_file.filename)
        source_file_mime = source_file.content_type
    
    # Encrypt (raises exceptions on failure)
    encrypted_result = encrypt_vault_file(
        form_data=form_data_dict,
        source_file=source_file_bytes,
        source_file_name=source_file_name,
        source_file_mime_type=source_file_mime,
        user_id=current_user_id,
        creation_mode=creation_mode
    )
    
    # Store in database (raises exceptions on failure)
    db_ops = VaultDatabaseOperations(db)
    db_ops.create_vault_file(
        file_id=encrypted_result.file_id,
        owner_user_id=current_user_id,
        template_id=template_id,
        creation_mode=creation_mode,
        encrypted_dek=encrypted_result.encrypted_dek,
        encrypted_form_data=encrypted_result.encrypted_form_data,
        nonce_form_data=encrypted_result.nonce_form_data,
        has_source_file=encrypted_result.has_source_file,
        source_file_s3_key=encrypted_result.source_file_s3_key,
        source_file_nonce=encrypted_result.source_file_nonce,
        source_file_original_name=source_file_name,
        source_file_mime_type=encrypted_result.source_file_mime_type,
        source_file_size_bytes=encrypted_result.source_file_size_bytes
    )
    
    return VaultFileSaveResponse(
        success=True,
        file_id=encrypted_result.file_id,
        message="Vault file saved successfully"
    )


# ==========================================
# GET VAULT FILE METADATA
# ==========================================

@router.get(
    "/{file_id}",
    response_model=VaultFileMetadataResponse,
    responses=ERROR_RESPONSES
)
async def get_vault_file_metadata(
    file_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get vault file metadata (without decrypting)."""
    db_ops = VaultDatabaseOperations(db)
    
    # Check access (raises UnauthorizedAccessException if denied)
    db_ops.check_access(file_id, current_user_id)
    
    # Get file (raises FileNotFoundException if not found)
    vault_file = db_ops.get_vault_file(file_id)
    
    return VaultFileMetadataResponse.model_validate(vault_file)


# ==========================================
# GET DECRYPTION METADATA (FOR FRONTEND)
# ==========================================

@router.get(
    "/{file_id}/decrypt-metadata",
    response_model=VaultFileDecryptionMetadataResponse,
    responses=ERROR_RESPONSES
)
async def get_vault_file_decryption_metadata(
    file_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get decryption metadata for frontend.
    Backend decrypts DEK via KMS, frontend decrypts data in browser.
    """
    db_ops = VaultDatabaseOperations(db)
    
    # Get decryption metadata (includes auth check, raises exceptions on failure)
    metadata = get_decryption_metadata(file_id, current_user_id, db_ops)
    
    return VaultFileDecryptionMetadataResponse(
        encryption_key=metadata.encryption_key,
        encrypted_form_data=metadata.encrypted_form_data,
        nonce_form_data=metadata.nonce_form_data,
        has_source_file=metadata.has_source_file,
        source_file_s3_url=metadata.source_file_s3_url,
        source_file_nonce=metadata.source_file_nonce,
        source_file_name=metadata.source_file_name,
        source_file_mime_type=metadata.source_file_mime_type
    )


# ==========================================
# DECRYPT VAULT FILE (BACKEND)
# ==========================================

@router.get(
    "/{file_id}/decrypt",
    response_model=VaultFileDecryptedResponse,
    responses=ERROR_RESPONSES
)
async def decrypt_vault_file_endpoint(
    file_id: str,
    include_source_file: bool = False,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Decrypt vault file on backend and return plaintext.
    Use this for server-side processing. For frontend display, use /decrypt-metadata.
    """
    db_ops = VaultDatabaseOperations(db)
    
    # Decrypt (includes auth check, raises exceptions on failure)
    decrypted = decrypt_vault_file(
        file_id=file_id,
        user_id=current_user_id,
        db_operations=db_ops,
        decrypt_source_file=include_source_file
    )
    
    # Convert source file to base64 if present
    source_file_base64 = None
    if decrypted.source_file_data:
        source_file_base64 = base64.b64encode(decrypted.source_file_data).decode('utf-8')
    
    return VaultFileDecryptedResponse(
        form_data=decrypted.form_data,
        has_source_file=decrypted.has_source_file,
        source_file_name=decrypted.source_file_name,
        source_file_mime_type=decrypted.source_file_mime_type,
        source_file_base64=source_file_base64
    )


# ==========================================
# LIST USER'S VAULT FILES
# ==========================================

@router.get(
    "/",
    response_model=VaultFileListResponse,
    responses=ERROR_RESPONSES
)
async def list_user_vault_files(
    template_id: Optional[str] = None,
    status_filter: str = "active",
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all vault files for current user.
    
    - **template_id**: Filter by template (optional)
    - **status_filter**: Filter by status (default: 'active')
    """
    db_ops = VaultDatabaseOperations(db)
    
    # Get user's files (raises exceptions on failure)
    files = db_ops.get_user_vault_files(
        user_id=current_user_id,
        template_id=template_id,
        status=status_filter
    )
    
    return VaultFileListResponse(
        files=[VaultFileMetadataResponse.model_validate(f) for f in files],
        total=len(files)
    )


# ==========================================
# SHARE VAULT FILE
# ==========================================

@router.post(
    "/{file_id}/share",
    response_model=VaultFileAccessResponse,
    responses=ERROR_RESPONSES
)
async def share_vault_file(
    file_id: str,
    share_request: VaultFileShareRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Share vault file with another user (creates pending access)."""
    db_ops = VaultDatabaseOperations(db)
    
    # Get file (raises FileNotFoundException if not found)
    vault_file = db_ops.get_vault_file(file_id)
    
    # Verify current user is owner
    if vault_file.owner_user_id != current_user_id:
        raise NotFileOwnerException(
            "Only the file owner can share this file",
            details={
                "file_id": file_id,
                "owner_id": vault_file.owner_user_id,
                "requesting_user_id": current_user_id
            }
        )
    
    # Grant access (raises exceptions on failure)
    db_ops.grant_access(
        file_id=file_id,
        recipient_user_id=share_request.recipient_user_id,
        granted_by_user_id=current_user_id,
        status="pending"
    )
    
    return VaultFileAccessResponse(
        success=True,
        message=f"Access granted to user {share_request.recipient_user_id} (pending acceptance)"
    )


# ==========================================
# ACTIVATE ACCESS (ACCEPT SHARED FILE)
# ==========================================

@router.post(
    "/access/activate",
    response_model=VaultFileAccessResponse,
    responses=ERROR_RESPONSES
)
async def activate_file_access(
    activate_request: VaultFileAccessActivateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Activate pending access (recipient accepts shared file)."""
    db_ops = VaultDatabaseOperations(db)
    
    # Activate access (raises exceptions on failure)
    db_ops.activate_access(
        file_id=activate_request.file_id,
        recipient_user_id=current_user_id
    )
    
    return VaultFileAccessResponse(
        success=True,
        message="Access activated successfully"
    )


# ==========================================
# REVOKE ACCESS
# ==========================================

@router.delete(
    "/{file_id}/share/{recipient_user_id}",
    response_model=VaultFileAccessResponse,
    responses=ERROR_RESPONSES
)
async def revoke_file_access(
    file_id: str,
    recipient_user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Revoke access to vault file (owner only)."""
    db_ops = VaultDatabaseOperations(db)
    
    # Get file (raises FileNotFoundException if not found)
    vault_file = db_ops.get_vault_file(file_id)
    
    # Verify current user is owner
    if vault_file.owner_user_id != current_user_id:
        raise NotFileOwnerException(
            "Only the file owner can revoke access",
            details={
                "file_id": file_id,
                "owner_id": vault_file.owner_user_id,
                "requesting_user_id": current_user_id
            }
        )
    
    # Revoke access (raises exceptions on failure)
    db_ops.revoke_access(file_id, recipient_user_id)
    
    return VaultFileAccessResponse(
        success=True,
        message=f"Access revoked for user {recipient_user_id}"
    )


# ==========================================
# GET ACCESS LIST
# ==========================================

@router.get(
    "/{file_id}/access",
    response_model=VaultFileAccessListResponse,
    responses=ERROR_RESPONSES
)
async def get_file_access_list(
    file_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get list of users with access to file (owner only)."""
    db_ops = VaultDatabaseOperations(db)
    
    # Get file (raises FileNotFoundException if not found)
    vault_file = db_ops.get_vault_file(file_id)
    
    # Verify current user is owner
    if vault_file.owner_user_id != current_user_id:
        raise NotFileOwnerException(
            "Only the file owner can view the access list",
            details={
                "file_id": file_id,
                "owner_id": vault_file.owner_user_id,
                "requesting_user_id": current_user_id
            }
        )
    
    # Get access list (raises exceptions on failure)
    access_list = db_ops.get_file_access_list(file_id)
    
    return VaultFileAccessListResponse(
        file_id=file_id,
        access_list=[VaultFileAccessListItem.model_validate(a) for a in access_list],
        total=len(access_list)
    )


# ==========================================
# DELETE VAULT FILE
# ==========================================

@router.delete(
    "/{file_id}",
    response_model=VaultFileAccessResponse,
    responses=ERROR_RESPONSES
)
async def delete_vault_file_endpoint(
    file_id: str,
    hard_delete: bool = False,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete vault file (owner only).
    
    - **hard_delete**: If True, permanently delete. If False, soft delete (default).
    """
    db_ops = VaultDatabaseOperations(db)
    
    # Get file (raises FileNotFoundException if not found)
    vault_file = db_ops.get_vault_file(file_id)
    
    # Verify current user is owner
    if vault_file.owner_user_id != current_user_id:
        raise NotFileOwnerException(
            "Only the file owner can delete this file",
            details={
                "file_id": file_id,
                "owner_id": vault_file.owner_user_id,
                "requesting_user_id": current_user_id
            }
        )
    
    # Delete (raises exceptions on failure)
    db_ops.delete_vault_file(file_id, soft_delete=not hard_delete)
    
    delete_type = "permanently deleted" if hard_delete else "soft deleted"
    return VaultFileAccessResponse(
        success=True,
        message=f"File {delete_type} successfully"
    )