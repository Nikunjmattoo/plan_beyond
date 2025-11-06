"""Core encryption functionality."""

from .vault_encryptor import encrypt_vault_file, EncryptedVaultResult
from .vault_decryptor import (
    decrypt_vault_file,
    get_decryption_metadata,
    DecryptedVaultData,
    DecryptionMetadata
)
from .db_operations import VaultDatabaseOperations
from .crypto_engine import CryptoEngine
from .s3_operations import S3Operations

__all__ = [
    'encrypt_vault_file',
    'decrypt_vault_file',
    'get_decryption_metadata',
    'EncryptedVaultResult',
    'DecryptedVaultData',
    'DecryptionMetadata',
    'VaultDatabaseOperations',
    'CryptoEngine',
    'S3Operations',
]