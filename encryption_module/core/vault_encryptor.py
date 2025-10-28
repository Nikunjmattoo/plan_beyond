"""High-level vault file encryption orchestration."""
import json
import base64
import hashlib
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from io import BytesIO
import logging

from .crypto_engine import CryptoEngine
from .s3_operations import S3Operations
from ..exceptions import (
    EncryptionException,
    ValidationException,
    InvalidJSONException
)
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class EncryptedVaultResult:
    """Result of vault file encryption."""
    file_id: str
    encrypted_dek: str  # Base64-encoded KMS-encrypted DEK
    encrypted_form_data: str  # Base64-encoded ciphertext
    nonce_form_data: str  # Base64-encoded nonce
    has_source_file: bool
    source_file_s3_key: Optional[str] = None
    source_file_nonce: Optional[str] = None
    source_file_mime_type: Optional[str] = None
    source_file_size_bytes: Optional[int] = None


def encrypt_vault_file(
    form_data: Dict,
    source_file: Optional[bytes],
    source_file_name: Optional[str],
    source_file_mime_type: Optional[str],
    user_id: str,
    creation_mode: str = "manual"
) -> EncryptedVaultResult:
    """
    Encrypt vault file (form data + optional source file) using KMS-protected DEK.
    
    Args:
        form_data: Dictionary of form field values
        source_file: Source file bytes (optional, for import mode)
        source_file_name: Original filename
        source_file_mime_type: MIME type of source file
        user_id: Owner user ID
        creation_mode: 'import' or 'manual'
        
    Returns:
        EncryptedVaultResult with all encrypted components
        
    Raises:
        ValidationException: If input validation fails
        EncryptionException: If encryption fails
        InvalidJSONException: If form_data cannot be serialized
    """
    # Validate inputs
    if not form_data or not isinstance(form_data, dict):
        raise ValidationException(
            "Form data must be a non-empty dictionary",
            details={
                "form_data_type": type(form_data).__name__,
                "form_data_empty": not form_data
            }
        )
    
    if not user_id:
        raise ValidationException(
            "User ID cannot be empty",
            details={"user_id": user_id}
        )
    
    if source_file and not source_file_mime_type:
        raise ValidationException(
            "MIME type required when source file is provided",
            details={"has_source_file": True, "mime_type_provided": False}
        )
    
    # Validate creation_mode
    if creation_mode not in ['import', 'manual']:
        raise ValidationException(
            f"Invalid creation mode: '{creation_mode}'",
            details={
                "provided_mode": creation_mode,
                "valid_modes": ['import', 'manual']
            }
        )
    
    # CRITICAL FIX: Validate zero-byte file
    if source_file is not None:
        # Handle both bytes and BytesIO objects
        if isinstance(source_file, BytesIO):
            current_pos = source_file.tell()
            source_file.seek(0, 2)  # Seek to end
            file_size = source_file.tell()
            source_file.seek(current_pos)  # Reset to original position
            
            if file_size == 0:
                raise ValidationException(
                    "Cannot encrypt zero-byte file",
                    details={
                        "file_size": 0,
                        "file_name": source_file_name,
                        "mime_type": source_file_mime_type
                    }
                )
        elif isinstance(source_file, bytes):
            if len(source_file) == 0:
                raise ValidationException(
                    "Cannot encrypt zero-byte file",
                    details={
                        "file_size": 0,
                        "file_name": source_file_name,
                        "mime_type": source_file_mime_type
                    }
                )
    
    try:
        crypto = CryptoEngine()
        
        # Generate unique file ID
        file_id = hashlib.sha256(
            f"{user_id}_{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]
        
        logger.info(f"Starting encryption for file_id: {file_id}, user: {user_id}")
        
        # Generate data encryption key via KMS (raises KeyGenerationException on failure)
        plaintext_dek, encrypted_dek = crypto.generate_data_key()
        
        # Serialize form data to JSON
        try:
            json_bytes = json.dumps(form_data).encode('utf-8')
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize form data to JSON: {e}")
            raise InvalidJSONException(
                "Form data cannot be serialized to JSON",
                details={
                    "error": str(e),
                    "form_data_keys": list(form_data.keys()) if isinstance(form_data, dict) else None
                }
            )
        
        # Encrypt form data (ALWAYS present) - raises EncryptionException on failure
        nonce_form = crypto.generate_nonce()
        encrypted_form = crypto.encrypt_data(json_bytes, plaintext_dek, nonce_form)
        
        logger.info(f"Successfully encrypted form data for file: {file_id}")
        
        # Encrypt source file (OPTIONAL - only for import mode)
        source_file_s3_key = None
        source_file_nonce = None
        source_file_size = None
        
        if source_file:
            try:
                # Handle BytesIO objects
                if isinstance(source_file, BytesIO):
                    current_pos = source_file.tell()
                    source_file.seek(0)
                    file_bytes = source_file.read()
                    source_file.seek(current_pos)
                else:
                    file_bytes = source_file
                
                # Generate nonce for file
                nonce_file = crypto.generate_nonce()
                
                # Encrypt file data
                encrypted_file = crypto.encrypt_data(file_bytes, plaintext_dek, nonce_file)
                
                logger.info(f"Successfully encrypted source file for file: {file_id}")
                
                # Upload encrypted file to S3 (raises S3UploadException on failure)
                s3 = S3Operations()
                source_file_s3_key = s3.upload_encrypted_file(
                    encrypted_file, file_id, user_id, 'source'
                )
                source_file_nonce = base64.b64encode(nonce_file).decode('utf-8')
                source_file_size = len(file_bytes)
                
                logger.info(f"Successfully uploaded encrypted file to S3: {source_file_s3_key}")
                
            except Exception as e:
                # If source file encryption/upload fails, clean up and raise
                logger.exception(f"Failed to encrypt/upload source file for file: {file_id}")
                # Note: If S3 upload partially succeeded, you might want to clean it up here
                raise  # Re-raise the exception (already properly typed from crypto or s3)
        
        # Zero out plaintext key from memory
        del plaintext_dek
        
        logger.info(f"Encryption complete for file: {file_id}")
        
        return EncryptedVaultResult(
            file_id=file_id,
            encrypted_dek=base64.b64encode(encrypted_dek).decode('utf-8'),
            encrypted_form_data=base64.b64encode(encrypted_form).decode('utf-8'),
            nonce_form_data=base64.b64encode(nonce_form).decode('utf-8'),
            has_source_file=source_file is not None,
            source_file_s3_key=source_file_s3_key,
            source_file_nonce=source_file_nonce,
            source_file_mime_type=source_file_mime_type,
            source_file_size_bytes=source_file_size
        )
        
    except (ValidationException, InvalidJSONException):
        raise  # Re-raise validation exceptions as-is
    except Exception as e:
        # Catch any unexpected errors and wrap them
        if not isinstance(e, (EncryptionException, Exception)):
            logger.exception(f"Unexpected error during vault file encryption: {file_id if 'file_id' in locals() else 'unknown'}")
            raise EncryptionException(
                "Unexpected error during vault file encryption",
                details={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user_id
                }
            )
        raise  # Re-raise if already a proper exception type