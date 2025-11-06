"""High-level vault file decryption orchestration."""
import json
import base64
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from .crypto_engine import CryptoEngine
from .s3_operations import S3Operations
from .db_operations import VaultDatabaseOperations
from ..exceptions import (
    DecryptionException,
    UnauthorizedAccessException,
    FileNotFoundException,
    InvalidJSONException
)

logger = logging.getLogger(__name__)


@dataclass
class DecryptedVaultData:
    """Result of vault file decryption."""
    form_data: Dict
    has_source_file: bool
    source_file_data: Optional[bytes] = None
    source_file_name: Optional[str] = None
    source_file_mime_type: Optional[str] = None


@dataclass
class DecryptionMetadata:
    """Metadata needed for frontend decryption."""
    encryption_key: str  # Base64-encoded plaintext DEK (decrypted by KMS)
    encrypted_form_data: str  # Base64
    nonce_form_data: str  # Base64
    has_source_file: bool
    source_file_s3_url: Optional[str] = None  # Presigned URL
    source_file_nonce: Optional[str] = None  # Base64
    source_file_name: Optional[str] = None
    source_file_mime_type: Optional[str] = None


def decrypt_vault_file(
    file_id: str,
    user_id: str,
    db_operations: VaultDatabaseOperations,
    decrypt_source_file: bool = False
) -> DecryptedVaultData:
    """
    Decrypt complete vault file (form data + optional source file).
    
    Args:
        file_id: Vault file ID
        user_id: Requesting user ID
        db_operations: Database operations instance
        decrypt_source_file: If True, also decrypt and return source file
        
    Returns:
        DecryptedVaultData with decrypted components
        
    Raises:
        UnauthorizedAccessException: If user not authorized
        FileNotFoundException: If file not found
        DecryptionException: If decryption fails
        InvalidJSONException: If decrypted form data is not valid JSON
    """
    logger.info(f"Starting decryption for file: {file_id}, user: {user_id}")
    
    # Check authorization (raises UnauthorizedAccessException if denied)
    try:
        db_operations.check_access(file_id, user_id)
    except UnauthorizedAccessException:
        logger.warning(f"Unauthorized access attempt: file={file_id}, user={user_id}")
        raise
    except FileNotFoundException:
        logger.warning(f"File not found: {file_id}")
        raise
    
    # Get vault file from database (raises DatabaseReadException on failure)
    vault_file = db_operations.get_vault_file(file_id)
    if not vault_file:
        raise FileNotFoundException(
            f"Vault file '{file_id}' not found",
            details={"file_id": file_id}
        )
    
    try:
        crypto = CryptoEngine()
        
        # Decode and decrypt DEK using KMS (raises KMSDecryptionException on failure)
        try:
            encrypted_dek = base64.b64decode(vault_file.encrypted_dek)
        except Exception as e:
            raise DecryptionException(
                "Failed to decode encrypted DEK",
                details={"file_id": file_id, "error": str(e)}
            )
        
        plaintext_dek = crypto.decrypt_data_key(encrypted_dek)
        
        logger.info(f"Successfully decrypted DEK for file: {file_id}")
        
        # Decode and decrypt form data
        try:
            encrypted_form = base64.b64decode(vault_file.encrypted_form_data)
            nonce_form = base64.b64decode(vault_file.nonce_form_data)
        except Exception as e:
            raise DecryptionException(
                "Failed to decode encrypted form data or nonce",
                details={"file_id": file_id, "error": str(e)}
            )
        
        # Decrypt form data (raises DecryptionException or AuthenticationFailedException)
        decrypted_json = crypto.decrypt_data(encrypted_form, plaintext_dek, nonce_form)
        
        logger.info(f"Successfully decrypted form data for file: {file_id}")
        
        # Parse JSON
        try:
            form_data = json.loads(decrypted_json.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise InvalidJSONException(
                "Decrypted form data is not valid JSON",
                details={
                    "file_id": file_id,
                    "error": str(e),
                    "position": e.pos if hasattr(e, 'pos') else None
                }
            )
        except UnicodeDecodeError as e:
            raise DecryptionException(
                "Failed to decode decrypted data as UTF-8",
                details={"file_id": file_id, "error": str(e)}
            )
        
        # Decrypt source file if requested and exists
        source_file_data = None
        if decrypt_source_file and vault_file.has_source_file:
            try:
                s3 = S3Operations()
                
                # Download encrypted file from S3 (raises S3DownloadException on failure)
                encrypted_file = s3.download_encrypted_file(vault_file.source_file_s3_key)
                
                logger.info(f"Downloaded encrypted source file from S3 for file: {file_id}")
                
                # Decode nonce
                try:
                    nonce_file = base64.b64decode(vault_file.source_file_nonce)
                except Exception as e:
                    raise DecryptionException(
                        "Failed to decode source file nonce",
                        details={"file_id": file_id, "error": str(e)}
                    )
                
                # Decrypt file (raises DecryptionException or AuthenticationFailedException)
                source_file_data = crypto.decrypt_data(encrypted_file, plaintext_dek, nonce_file)
                
                logger.info(f"Successfully decrypted source file for file: {file_id}")
                
            except Exception as e:
                # If source file decryption fails, log and re-raise
                logger.exception(f"Failed to decrypt source file for file: {file_id}")
                raise
        
        # Zero out plaintext key
        del plaintext_dek
        
        # Record access (raises DatabaseWriteException on failure, but we don't want to fail)
        try:
            if user_id != vault_file.owner_user_id:
                db_operations.record_access(file_id, user_id)
        except Exception as e:
            # Log but don't fail decryption if access recording fails
            logger.warning(f"Failed to record access for file {file_id}: {e}")
        
        logger.info(f"Decryption complete for file: {file_id}")
        
        return DecryptedVaultData(
            form_data=form_data,
            has_source_file=vault_file.has_source_file,
            source_file_data=source_file_data,
            source_file_name=vault_file.source_file_original_name,
            source_file_mime_type=vault_file.source_file_mime_type
        )
        
    except (DecryptionException, InvalidJSONException, UnauthorizedAccessException, FileNotFoundException):
        raise  # Re-raise known exceptions
    except Exception as e:
        # Wrap unexpected exceptions
        logger.exception(f"Unexpected error during vault file decryption: {file_id}")
        raise DecryptionException(
            "Unexpected error during vault file decryption",
            details={
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


def get_decryption_metadata(
    file_id: str,
    user_id: str,
    db_operations: VaultDatabaseOperations
) -> DecryptionMetadata:
    """
    Get decryption metadata for frontend (decrypts DEK, generates S3 URL).
    Backend decrypts DEK via KMS, frontend decrypts data in browser.
    
    Args:
        file_id: Vault file ID
        user_id: Requesting user ID
        db_operations: Database operations instance
        
    Returns:
        DecryptionMetadata with keys and URLs for frontend
        
    Raises:
        UnauthorizedAccessException: If user not authorized
        FileNotFoundException: If file not found
        DecryptionException: If metadata generation fails
    """
    logger.info(f"Getting decryption metadata for file: {file_id}, user: {user_id}")
    
    # Check authorization (raises UnauthorizedAccessException if denied)
    try:
        db_operations.check_access(file_id, user_id)
    except UnauthorizedAccessException:
        logger.warning(f"Unauthorized access attempt: file={file_id}, user={user_id}")
        raise
    except FileNotFoundException:
        logger.warning(f"File not found: {file_id}")
        raise
    
    # Get vault file from database
    vault_file = db_operations.get_vault_file(file_id)
    if not vault_file:
        raise FileNotFoundException(
            f"Vault file '{file_id}' not found",
            details={"file_id": file_id}
        )
    
    try:
        crypto = CryptoEngine()
        
        # Decode and decrypt DEK using KMS (raises KMSDecryptionException on failure)
        try:
            encrypted_dek = base64.b64decode(vault_file.encrypted_dek)
        except Exception as e:
            raise DecryptionException(
                "Failed to decode encrypted DEK",
                details={"file_id": file_id, "error": str(e)}
            )
        
        plaintext_dek = crypto.decrypt_data_key(encrypted_dek)
        
        logger.info(f"Successfully decrypted DEK for metadata: {file_id}")
        
        # Generate S3 presigned URL if source file exists
        source_file_s3_url = None
        if vault_file.has_source_file:
            try:
                s3 = S3Operations()
                source_file_s3_url = s3.generate_presigned_download_url(
                    vault_file.source_file_s3_key
                )
                logger.info(f"Generated presigned URL for file: {file_id}")
            except Exception as e:
                # Log but don't fail metadata generation
                logger.warning(f"Failed to generate presigned URL for file {file_id}: {e}")
                # You might want to raise here depending on requirements
        
        # Record access (don't fail if this fails)
        try:
            if user_id != vault_file.owner_user_id:
                db_operations.record_access(file_id, user_id)
        except Exception as e:
            logger.warning(f"Failed to record access for file {file_id}: {e}")
        
        logger.info(f"Decryption metadata generation complete for file: {file_id}")
        
        return DecryptionMetadata(
            encryption_key=base64.b64encode(plaintext_dek).decode('utf-8'),
            encrypted_form_data=vault_file.encrypted_form_data,
            nonce_form_data=vault_file.nonce_form_data,
            has_source_file=vault_file.has_source_file,
            source_file_s3_url=source_file_s3_url,
            source_file_nonce=vault_file.source_file_nonce,
            source_file_name=vault_file.source_file_original_name,
            source_file_mime_type=vault_file.source_file_mime_type
        )
        
    except (DecryptionException, UnauthorizedAccessException, FileNotFoundException):
        raise  # Re-raise known exceptions
    except Exception as e:
        # Wrap unexpected exceptions
        logger.exception(f"Unexpected error getting decryption metadata: {file_id}")
        raise DecryptionException(
            "Unexpected error getting decryption metadata",
            details={
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )