"""
Vault encryption models - encrypted vault files with KMS-protected DEKs.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, BigInteger, TIMESTAMP, 
    ForeignKey, CheckConstraint, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class CreationMode(str, enum.Enum):
    import_mode = "import"
    manual = "manual"


class VaultFileStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    deleted = "deleted"


class AccessStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    revoked = "revoked"


class VaultFile(Base):
    """Encrypted vault file with KMS-protected data encryption key."""
    __tablename__ = "vault_files"
    __table_args__ = (
        CheckConstraint("creation_mode IN ('import', 'manual')", name='check_creation_mode'),
        CheckConstraint("status IN ('active', 'archived', 'deleted')", name='check_vault_status'),
    )

    file_id = Column(String(64), primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # FIXED: Changed from String(50) to Integer
    template_id = Column(String(50), nullable=False, index=True)

    creation_mode = Column(String(10), nullable=False)

    # Encryption: Form data (ALWAYS present)
    encrypted_dek = Column(Text, nullable=False)
    encrypted_form_data = Column(Text, nullable=False)
    nonce_form_data = Column(String(32), nullable=False)

    # Encryption: Source file (OPTIONAL - only for import mode)
    has_source_file = Column(Boolean, nullable=False, default=False)
    source_file_s3_key = Column(String(500), nullable=True)
    source_file_nonce = Column(String(32), nullable=True)
    source_file_original_name = Column(String(255), nullable=True)
    source_file_mime_type = Column(String(100), nullable=True)
    source_file_size_bytes = Column(BigInteger, nullable=True)

    status = Column(String(20), nullable=False, default='active', index=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_user_id])  # NEW: Add relationship to User
    access_list = relationship(
        "VaultFileAccess",
        back_populates="vault_file",
        cascade="all, delete-orphan",
        order_by="VaultFileAccess.granted_at"
    )


class VaultFileAccess(Base):
    """Access control list for vault files - owner NOT included (implicit access)."""
    __tablename__ = "vault_file_access"
    __table_args__ = (
        UniqueConstraint("file_id", "recipient_user_id", name="uq_file_recipient"),
        CheckConstraint("status IN ('pending', 'active', 'revoked')", name='check_access_status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    file_id = Column(String(64), ForeignKey("vault_files.file_id", ondelete="CASCADE"), nullable=False, index=True)

    recipient_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # FIXED: Changed from String(50) to Integer
    granted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # FIXED: Changed from String(50) to Integer

    status = Column(String(20), nullable=False, default='pending', index=True)

    granted_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    activated_at = Column(TIMESTAMP, nullable=True)
    revoked_at = Column(TIMESTAMP, nullable=True)
    last_accessed_at = Column(TIMESTAMP, nullable=True)

    access_count = Column(Integer, nullable=False, default=0)

    # Relationships
    vault_file = relationship("VaultFile", back_populates="access_list")
    recipient = relationship("User", foreign_keys=[recipient_user_id])  # NEW: Add relationship to User
    granted_by = relationship("User", foreign_keys=[granted_by_user_id])  # NEW: Add relationship to User