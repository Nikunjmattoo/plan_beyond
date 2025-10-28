"""Database operations for vault files using centralized app.models."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

from app.models.vault import VaultFile, VaultFileAccess
from ..exceptions import (
    DatabaseWriteException,
    DatabaseReadException,
    DuplicateFileException,
    FileNotFoundException,
    UnauthorizedAccessException,
    AccessAlreadyExistsException,
    AccessNotFoundException
)

logger = logging.getLogger(__name__)


class VaultDatabaseOperations:
    """Manages database operations for vault files."""

    def __init__(self, db: Session):
        """
        Initialize with existing database session.

        Args:
            db: SQLAlchemy session from your app's dependency injection
        """
        self.db = db

    # ==========================================
    # VAULT FILE OPERATIONS
    # ==========================================

    def create_vault_file(
        self,
        file_id: str,
        owner_user_id: str,
        template_id: str,
        creation_mode: str,
        encrypted_dek: str,
        encrypted_form_data: str,
        nonce_form_data: str,
        has_source_file: bool = False,
        source_file_s3_key: Optional[str] = None,
        source_file_nonce: Optional[str] = None,
        source_file_original_name: Optional[str] = None,
        source_file_mime_type: Optional[str] = None,
        source_file_size_bytes: Optional[int] = None
    ) -> VaultFile:
        """
        Create a new vault file.
        
        Raises:
            DuplicateFileException: If file_id already exists
            DatabaseWriteException: If database write fails
        """
        try:
            vault_file = VaultFile(
                file_id=file_id,
                owner_user_id=owner_user_id,
                template_id=template_id,
                creation_mode=creation_mode,
                encrypted_dek=encrypted_dek,
                encrypted_form_data=encrypted_form_data,
                nonce_form_data=nonce_form_data,
                has_source_file=has_source_file,
                source_file_s3_key=source_file_s3_key,
                source_file_nonce=source_file_nonce,
                source_file_original_name=source_file_original_name,
                source_file_mime_type=source_file_mime_type,
                source_file_size_bytes=source_file_size_bytes
            )
            self.db.add(vault_file)
            self.db.commit()
            self.db.refresh(vault_file)
            logger.info(f"Created vault file: {file_id} for user: {owner_user_id}")
            return vault_file
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Duplicate file_id or integrity constraint violation: {file_id}")
            
            # Check if it's a duplicate key error
            error_msg = str(e.orig).lower()
            if 'duplicate' in error_msg or 'unique' in error_msg:
                raise DuplicateFileException(
                    f"Vault file with ID '{file_id}' already exists",
                    details={
                        "file_id": file_id,
                        "owner_user_id": owner_user_id,
                        "error": str(e.orig)
                    }
                )
            
            raise DatabaseWriteException(
                "Database integrity constraint violation",
                details={
                    "file_id": file_id,
                    "error": str(e.orig)
                }
            )
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.exception(f"Database error creating vault file: {file_id}")
            raise DatabaseWriteException(
                "Failed to create vault file in database",
                details={
                    "file_id": file_id,
                    "owner_user_id": owner_user_id,
                    "error": str(e)
                }
            )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error creating vault file: {file_id}")
            raise DatabaseWriteException(
                "Unexpected error creating vault file",
                details={
                    "file_id": file_id,
                    "error": str(e)
                }
            )

    def get_vault_file(self, file_id: str) -> Optional[VaultFile]:
        """
        Get vault file by ID.
        
        Raises:
            DatabaseReadException: If database read fails
        """
        try:
            return self.db.query(VaultFile).filter(VaultFile.file_id == file_id).first()
        except SQLAlchemyError as e:
            logger.exception(f"Database error reading vault file: {file_id}")
            raise DatabaseReadException(
                "Failed to read vault file from database",
                details={"file_id": file_id, "error": str(e)}
            )
        except Exception as e:
            logger.exception(f"Unexpected error reading vault file: {file_id}")
            raise DatabaseReadException(
                "Unexpected error reading vault file",
                details={"file_id": file_id, "error": str(e)}
            )

    def get_user_vault_files(
        self,
        user_id: str,
        template_id: Optional[str] = None,
        status: str = 'active'
    ) -> List[VaultFile]:
        """
        Get all vault files for a user.
        
        Raises:
            DatabaseReadException: If database read fails
        """
        try:
            query = self.db.query(VaultFile).filter(
                VaultFile.owner_user_id == user_id,
                VaultFile.status == status
            )
            if template_id:
                query = query.filter(VaultFile.template_id == template_id)
            return query.order_by(VaultFile.created_at.desc()).all()
            
        except SQLAlchemyError as e:
            logger.exception(f"Database error reading user vault files: {user_id}")
            raise DatabaseReadException(
                "Failed to read user vault files from database",
                details={"user_id": user_id, "error": str(e)}
            )
        except Exception as e:
            logger.exception(f"Unexpected error reading user vault files: {user_id}")
            raise DatabaseReadException(
                "Unexpected error reading user vault files",
                details={"user_id": user_id, "error": str(e)}
            )

    def update_vault_file(
        self,
        file_id: str,
        encrypted_form_data: str,
        nonce_form_data: str
    ) -> bool:
        """
        Update vault file form data (for edits).
        
        Raises:
            FileNotFoundException: If file doesn't exist
            DatabaseWriteException: If update fails
        """
        try:
            vault_file = self.db.query(VaultFile).filter(VaultFile.file_id == file_id).first()
            if not vault_file:
                raise FileNotFoundException(
                    f"Vault file '{file_id}' not found",
                    details={"file_id": file_id}
                )

            vault_file.encrypted_form_data = encrypted_form_data
            vault_file.nonce_form_data = nonce_form_data
            vault_file.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Updated vault file: {file_id}")
            return True
            
        except FileNotFoundException:
            raise  # Re-raise FileNotFoundException as-is
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.exception(f"Database error updating vault file: {file_id}")
            raise DatabaseWriteException(
                "Failed to update vault file in database",
                details={"file_id": file_id, "error": str(e)}
            )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error updating vault file: {file_id}")
            raise DatabaseWriteException(
                "Unexpected error updating vault file",
                details={"file_id": file_id, "error": str(e)}
            )

    def delete_vault_file(self, file_id: str, soft_delete: bool = True) -> bool:
        """
        Delete vault file (soft or hard delete) with S3 cleanup.
        
        Raises:
            FileNotFoundException: If file doesn't exist
            DatabaseWriteException: If delete fails
        """
        try:
            vault_file = self.db.query(VaultFile).filter(VaultFile.file_id == file_id).first()
            if not vault_file:
                raise FileNotFoundException(
                    f"Vault file '{file_id}' not found",
                    details={"file_id": file_id}
                )

            # 🔥 NEW: Clean up S3 file if it exists
            if vault_file.has_source_file and vault_file.source_file_s3_key:
                try:
                    from .s3_operations import S3Operations
                    s3_ops = S3Operations()
                    s3_ops.delete_encrypted_file(vault_file.source_file_s3_key)
                    logger.info(f"Deleted S3 file: {vault_file.source_file_s3_key}")
                except Exception as s3_error:
                    logger.warning(f"Failed to delete S3 file {vault_file.source_file_s3_key}: {s3_error}")
                    # Continue with DB deletion even if S3 fails

            if soft_delete:
                vault_file.status = 'deleted'
                vault_file.updated_at = datetime.utcnow()
            else:
                self.db.delete(vault_file)

            self.db.commit()
            logger.info(f"Deleted vault file (soft={soft_delete}): {file_id}")
            return True
            
        except FileNotFoundException:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.exception(f"Database error deleting vault file: {file_id}")
            raise DatabaseWriteException(
                "Failed to delete vault file from database",
                details={"file_id": file_id, "soft_delete": soft_delete, "error": str(e)}
            )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error deleting vault file: {file_id}")
            raise DatabaseWriteException(
                "Unexpected error deleting vault file",
                details={"file_id": file_id, "error": str(e)}
            )
    def grant_access(
        self,
        file_id: str,
        recipient_user_id: str,
        granted_by_user_id: str,
        status: str = 'pending'
    ) -> VaultFileAccess:
        """
        Grant access to a vault file.
        
        Raises:
            AccessAlreadyExistsException: If access already exists
            DatabaseWriteException: If grant fails
        """
        try:
            access = VaultFileAccess(
                file_id=file_id,
                recipient_user_id=recipient_user_id,
                granted_by_user_id=granted_by_user_id,
                status=status
            )
            self.db.add(access)
            self.db.commit()
            self.db.refresh(access)
            logger.info(f"Granted access to file {file_id} for user {recipient_user_id}")
            return access
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Access already exists for file {file_id}, user {recipient_user_id}")
            raise AccessAlreadyExistsException(
                f"Access already exists for user '{recipient_user_id}' on file '{file_id}'",
                details={
                    "file_id": file_id,
                    "recipient_user_id": recipient_user_id,
                    "error": str(e.orig)
                }
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.exception(f"Database error granting access: {file_id}")
            raise DatabaseWriteException(
                "Failed to grant file access in database",
                details={
                    "file_id": file_id,
                    "recipient_user_id": recipient_user_id,
                    "error": str(e)
                }
            )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error granting access: {file_id}")
            raise DatabaseWriteException(
                "Unexpected error granting file access",
                details={"file_id": file_id, "error": str(e)}
            )

    def activate_access(self, file_id: str, recipient_user_id: str) -> bool:
        """
        Activate pending access (when recipient accepts).
        
        Raises:
            AccessNotFoundException: If access not found
            DatabaseWriteException: If activation fails
        """
        try:
            access = self.db.query(VaultFileAccess).filter(
                VaultFileAccess.file_id == file_id,
                VaultFileAccess.recipient_user_id == recipient_user_id
            ).first()

            if not access:
                raise AccessNotFoundException(
                    f"Access record not found for file '{file_id}' and user '{recipient_user_id}'",
                    details={"file_id": file_id, "recipient_user_id": recipient_user_id}
                )

            if access.status != 'pending':
                raise DatabaseWriteException(
                    f"Cannot activate access with status '{access.status}'",
                    details={
                        "file_id": file_id,
                        "recipient_user_id": recipient_user_id,
                        "current_status": access.status
                    }
                )

            access.status = 'active'
            access.activated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Activated access for file {file_id}, user {recipient_user_id}")
            return True
            
        except (AccessNotFoundException, DatabaseWriteException):
            raise  # Re-raise as-is
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.exception(f"Database error activating access: {file_id}")
            raise DatabaseWriteException(
                "Failed to activate file access in database",
                details={
                    "file_id": file_id,
                    "recipient_user_id": recipient_user_id,
                    "error": str(e)
                }
            )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error activating access: {file_id}")
            raise DatabaseWriteException(
                "Unexpected error activating file access",
                details={"file_id": file_id, "error": str(e)}
            )

    def revoke_access(self, file_id: str, recipient_user_id: str) -> bool:
        """
        Revoke access to a vault file.
        
        Raises:
            AccessNotFoundException: If access not found
            DatabaseWriteException: If revocation fails
        """
        try:
            access = self.db.query(VaultFileAccess).filter(
                VaultFileAccess.file_id == file_id,
                VaultFileAccess.recipient_user_id == recipient_user_id
            ).first()

            if not access:
                raise AccessNotFoundException(
                    f"Access record not found for file '{file_id}' and user '{recipient_user_id}'",
                    details={"file_id": file_id, "recipient_user_id": recipient_user_id}
                )

            access.status = 'revoked'
            access.revoked_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Revoked access for file {file_id}, user {recipient_user_id}")
            return True
            
        except AccessNotFoundException:
            raise  # Re-raise as-is
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.exception(f"Database error revoking access: {file_id}")
            raise DatabaseWriteException(
                "Failed to revoke file access in database",
                details={
                    "file_id": file_id,
                    "recipient_user_id": recipient_user_id,
                    "error": str(e)
                }
            )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error revoking access: {file_id}")
            raise DatabaseWriteException(
                "Unexpected error revoking file access",
                details={"file_id": file_id, "error": str(e)}
            )

    def check_access(self, file_id: str, user_id: str) -> bool:
        """
        Check if user can access file (owner or active access).
        
        Raises:
            UnauthorizedAccessException: If user lacks access
            DatabaseReadException: If check fails
        """
        try:
            # Check if owner
            vault_file = self.db.query(VaultFile).filter(VaultFile.file_id == file_id).first()
            if not vault_file:
                raise FileNotFoundException(
                    f"Vault file '{file_id}' not found",
                    details={"file_id": file_id}
                )

            if vault_file.owner_user_id == user_id:
                return True  # Owner has implicit access

            # Check if in access list with active status
            access = self.db.query(VaultFileAccess).filter(
                VaultFileAccess.file_id == file_id,
                VaultFileAccess.recipient_user_id == user_id,
                VaultFileAccess.status == 'active'
            ).first()

            has_access = access is not None
            
            if not has_access:
                raise UnauthorizedAccessException(
                    f"User '{user_id}' does not have access to file '{file_id}'",
                    details={
                        "file_id": file_id,
                        "user_id": user_id,
                        "owner_id": vault_file.owner_user_id
                    }
                )
            
            return True
            
        except (FileNotFoundException, UnauthorizedAccessException):
            raise  # Re-raise as-is
        except SQLAlchemyError as e:
            logger.exception(f"Database error checking access: {file_id}")
            raise DatabaseReadException(
                "Failed to check file access in database",
                details={
                    "file_id": file_id,
                    "user_id": user_id,
                    "error": str(e)
                }
            )
        except Exception as e:
            logger.exception(f"Unexpected error checking access: {file_id}")
            raise DatabaseReadException(
                "Unexpected error checking file access",
                details={"file_id": file_id, "error": str(e)}
            )

    def get_file_access_list(self, file_id: str) -> List[VaultFileAccess]:
        """
        Get all access entries for a file.
        
        Raises:
            DatabaseReadException: If read fails
        """
        try:
            return self.db.query(VaultFileAccess).filter(
                VaultFileAccess.file_id == file_id
            ).all()
        except SQLAlchemyError as e:
            logger.exception(f"Database error reading access list: {file_id}")
            raise DatabaseReadException(
                "Failed to read file access list from database",
                details={"file_id": file_id, "error": str(e)}
            )
        except Exception as e:
            logger.exception(f"Unexpected error reading access list: {file_id}")
            raise DatabaseReadException(
                "Unexpected error reading file access list",
                details={"file_id": file_id, "error": str(e)}
            )

    def get_user_shared_files(self, user_id: str, status: str = 'active') -> List[VaultFile]:
        """
        Get all files shared WITH this user.
        
        Raises:
            DatabaseReadException: If read fails
        """
        try:
            return self.db.query(VaultFile).join(VaultFileAccess).filter(
                VaultFileAccess.recipient_user_id == user_id,
                VaultFileAccess.status == status
            ).all()
        except SQLAlchemyError as e:
            logger.exception(f"Database error reading shared files: {user_id}")
            raise DatabaseReadException(
                "Failed to read shared files from database",
                details={"user_id": user_id, "error": str(e)}
            )
        except Exception as e:
            logger.exception(f"Unexpected error reading shared files: {user_id}")
            raise DatabaseReadException(
                "Unexpected error reading shared files",
                details={"user_id": user_id, "error": str(e)}
            )

    def record_access(self, file_id: str, user_id: str):
        """
        Record that user accessed the file.
        
        Raises:
            DatabaseWriteException: If recording fails
        """
        try:
            access = self.db.query(VaultFileAccess).filter(
                VaultFileAccess.file_id == file_id,
                VaultFileAccess.recipient_user_id == user_id
            ).first()

            if access:
                access.last_accessed_at = datetime.utcnow()
                access.access_count += 1
                self.db.commit()
                logger.info(f"Recorded access for file {file_id}, user {user_id}")
                
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.exception(f"Database error recording access: {file_id}")
            raise DatabaseWriteException(
                "Failed to record file access in database",
                details={
                    "file_id": file_id,
                    "user_id": user_id,
                    "error": str(e)
                }
            )
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error recording access: {file_id}")
            raise DatabaseWriteException(
                "Unexpected error recording file access",
                details={"file_id": file_id, "error": str(e)}
            )