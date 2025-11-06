"""
Encryption module for vault file operations.

This module provides end-to-end encryption for vault files using:
- AWS KMS for key management
- AES-256-GCM for data encryption
- S3 for encrypted file storage
- PostgreSQL for metadata and access control
"""

# Core encryption/decryption functions
from .core.vault_encryptor import encrypt_vault_file, EncryptedVaultResult
from .core.vault_decryptor import (
    decrypt_vault_file,
    get_decryption_metadata,
    DecryptedVaultData,
    DecryptionMetadata
)

# Database operations
from .core.db_operations import VaultDatabaseOperations

# Error handling
from .exceptions import (
    # Base
    BaseEncryptionException,
    ErrorCode,
    
    # Encryption/Decryption
    EncryptionException,
    DecryptionException,
    InvalidKeyException,
    AuthenticationFailedException,
    
    # Key Management
    KeyGenerationException,
    KeyNotFoundException,
    KMSEncryptionException,
    KMSDecryptionException,
    
    # File Operations
    FileNotFoundException,
    FileTooLargeException,
    InvalidFileTypeException,
    
    # Storage
    S3UploadException,
    S3DownloadException,
    S3DeleteException,
    S3AccessDeniedException,
    
    # Database
    DatabaseWriteException,
    DatabaseReadException,
    DuplicateFileException,
    
    # Access Control
    UnauthorizedAccessException,
    NotFileOwnerException,
    AccessNotFoundException,
    AccessAlreadyExistsException,
    
    # Validation
    InvalidJSONException,
    ValidationException
)

__all__ = [
    # Encryption functions
    'encrypt_vault_file',
    'decrypt_vault_file',
    'get_decryption_metadata',
    
    # Result classes
    'EncryptedVaultResult',
    'DecryptedVaultData',
    'DecryptionMetadata',
    
    # Database operations
    'VaultDatabaseOperations',
    
    # Base exception
    'BaseEncryptionException',
    'ErrorCode',
    
    # Specific exceptions
    'EncryptionException',
    'DecryptionException',
    'InvalidKeyException',
    'AuthenticationFailedException',
    'KeyGenerationException',
    'KeyNotFoundException',
    'KMSEncryptionException',
    'KMSDecryptionException',
    'FileNotFoundException',
    'FileTooLargeException',
    'InvalidFileTypeException',
    'S3UploadException',
    'S3DownloadException',
    'S3DeleteException',
    'S3AccessDeniedException',
    'DatabaseWriteException',
    'DatabaseReadException',
    'DuplicateFileException',
    'UnauthorizedAccessException',
    'NotFileOwnerException',
    'AccessNotFoundException',
    'AccessAlreadyExistsException',
    'InvalidJSONException',
    'ValidationException',
]