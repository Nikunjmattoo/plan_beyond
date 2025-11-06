"""Pydantic schemas for vault API requests/responses."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# ==========================================
# REQUEST SCHEMAS
# ==========================================

class VaultFileSaveRequest(BaseModel):
    """Request to save vault file."""
    template_id: str = Field(..., description="Template ID")
    form_data: Dict = Field(..., description="Form field data as JSON")
    creation_mode: str = Field(..., description="'import' or 'manual'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "template_lastwill",
                "form_data": {
                    "beneficiary_name": "John Doe",
                    "relationship": "Son",
                    "share_percentage": "50%"
                },
                "creation_mode": "manual"
            }
        }


class VaultFileShareRequest(BaseModel):
    """Request to share vault file with user."""
    recipient_user_id: str = Field(..., description="User ID to share with")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recipient_user_id": "user_456"
            }
        }


class VaultFileAccessActivateRequest(BaseModel):
    """Request to activate pending access."""
    file_id: str = Field(..., description="Vault file ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "abc123xyz456"
            }
        }


# ==========================================
# RESPONSE SCHEMAS
# ==========================================

class VaultFileSaveResponse(BaseModel):
    """Response after saving vault file."""
    success: bool
    file_id: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "file_id": "abc123xyz456",
                "message": "Vault file saved successfully"
            }
        }


class VaultFileMetadataResponse(BaseModel):
    """Response with vault file metadata."""
    file_id: str
    owner_user_id: str
    template_id: str
    creation_mode: str
    has_source_file: bool
    source_file_original_name: Optional[str] = None
    source_file_mime_type: Optional[str] = None
    source_file_size_bytes: Optional[int] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class VaultFileDecryptionMetadataResponse(BaseModel):
    """Response with decryption metadata for frontend."""
    encryption_key: str = Field(..., description="Base64-encoded plaintext DEK")
    encrypted_form_data: str = Field(..., description="Base64-encoded encrypted form")
    nonce_form_data: str = Field(..., description="Base64-encoded nonce")
    has_source_file: bool
    source_file_s3_url: Optional[str] = Field(None, description="Presigned S3 URL")
    source_file_nonce: Optional[str] = Field(None, description="Base64-encoded nonce for file")
    source_file_name: Optional[str] = None
    source_file_mime_type: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "encryption_key": "base64_encoded_key...",
                "encrypted_form_data": "base64_encrypted_data...",
                "nonce_form_data": "base64_nonce...",
                "has_source_file": True,
                "source_file_s3_url": "https://s3.amazonaws.com/...",
                "source_file_nonce": "base64_nonce...",
                "source_file_name": "LastWill.pdf",
                "source_file_mime_type": "application/pdf"
            }
        }


class VaultFileDecryptedResponse(BaseModel):
    """Response with decrypted vault file data."""
    form_data: Dict
    has_source_file: bool
    source_file_name: Optional[str] = None
    source_file_mime_type: Optional[str] = None
    source_file_base64: Optional[str] = Field(None, description="Base64-encoded decrypted file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "form_data": {
                    "beneficiary_name": "John Doe",
                    "relationship": "Son"
                },
                "has_source_file": True,
                "source_file_name": "LastWill.pdf",
                "source_file_mime_type": "application/pdf",
                "source_file_base64": "base64_pdf_data..."
            }
        }


class VaultFileListResponse(BaseModel):
    """Response with list of vault files."""
    files: List[VaultFileMetadataResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "files": [],
                "total": 0
            }
        }


class VaultFileAccessResponse(BaseModel):
    """Response for access operations."""
    success: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Access granted successfully"
            }
        }


class VaultFileAccessListItem(BaseModel):
    """Single access list entry."""
    recipient_user_id: str
    status: str
    granted_at: datetime
    activated_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    access_count: int
    
    class Config:
        from_attributes = True


class VaultFileAccessListResponse(BaseModel):
    """Response with file access list."""
    file_id: str
    access_list: List[VaultFileAccessListItem]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "abc123",
                "access_list": [],
                "total": 0
            }
        }