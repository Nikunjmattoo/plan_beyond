"""Core KMS + AES-256-GCM cryptography operations."""
import boto3
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from botocore.exceptions import ClientError
from typing import Tuple
import logging

from .config import KMS_KEY_ID, AWS_REGION
from ..exceptions import (
    KeyGenerationException,
    KMSEncryptionException,
    KMSDecryptionException,
    EncryptionException,
    DecryptionException,
    AuthenticationFailedException,
    InvalidKeyException
)

logger = logging.getLogger(__name__)


class CryptoEngine:
    """Handles KMS operations and AES-256-GCM encryption/decryption."""
    
    def __init__(self):
        try:
            self.kms = boto3.client('kms', region_name=AWS_REGION)
            self.kms_key_id = KMS_KEY_ID
        except Exception as e:
            logger.exception("Failed to initialize KMS client")
            raise KMSEncryptionException(
                "Failed to initialize KMS client",
                details={"error": str(e), "region": AWS_REGION}
            )
    
    def generate_data_key(self) -> Tuple[bytes, bytes]:
        """
        Generate 256-bit data encryption key via KMS.
        
        Returns:
            tuple: (plaintext_key: bytes, encrypted_key: bytes)
            
        Raises:
            KeyGenerationException: If key generation fails
        """
        try:
            response = self.kms.generate_data_key(
                KeyId=self.kms_key_id,
                KeySpec='AES_256'
            )
            return response['Plaintext'], response['CiphertextBlob']
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.exception("KMS key generation failed")
            raise KeyGenerationException(
                "Failed to generate data encryption key",
                details={
                    "kms_key_id": self.kms_key_id,
                    "aws_error_code": error_code,
                    "error_message": str(e)
                }
            )
        except Exception as e:
            logger.exception("Unexpected error during key generation")
            raise KeyGenerationException(
                "Unexpected error during key generation",
                details={"error": str(e)}
            )
    
    def decrypt_data_key(self, encrypted_key: bytes) -> bytes:
        """
        Decrypt data encryption key using KMS.
        Automatically logged in CloudTrail.
        
        Args:
            encrypted_key: KMS-encrypted DEK
            
        Returns:
            bytes: Plaintext DEK
            
        Raises:
            KMSDecryptionException: If KMS decryption fails
            InvalidKeyException: If encrypted key is invalid
        """
        if not encrypted_key:
            raise InvalidKeyException(
                "Encrypted key cannot be empty",
                details={"encrypted_key_length": 0}
            )
        
        try:
            response = self.kms.decrypt(CiphertextBlob=encrypted_key)
            return response['Plaintext']
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.exception("KMS decryption failed")
            
            # Handle specific KMS errors
            if error_code == 'InvalidCiphertextException':
                raise InvalidKeyException(
                    "Invalid encrypted key format",
                    details={
                        "aws_error_code": error_code,
                        "encrypted_key_length": len(encrypted_key)
                    }
                )
            
            raise KMSDecryptionException(
                "Failed to decrypt data encryption key",
                details={
                    "aws_error_code": error_code,
                    "error_message": str(e),
                    "encrypted_key_length": len(encrypted_key)
                }
            )
        except Exception as e:
            logger.exception("Unexpected error during KMS decryption")
            raise KMSDecryptionException(
                "Unexpected error during key decryption",
                details={"error": str(e)}
            )
    
    def generate_nonce(self) -> bytes:
        """
        Generate 96-bit nonce for GCM mode.
        
        Returns:
            bytes: 12-byte random nonce
            
        Raises:
            EncryptionException: If nonce generation fails
        """
        try:
            return os.urandom(12)
        except Exception as e:
            logger.exception("Failed to generate nonce")
            raise EncryptionException(
                "Failed to generate encryption nonce",
                details={"error": str(e)}
            )
    
    def encrypt_data(self, data: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            data: Plaintext bytes
            key: 256-bit encryption key
            nonce: 96-bit nonce
            
        Returns:
            bytes: Ciphertext (includes authentication tag)
            
        Raises:
            EncryptionException: If encryption fails
            InvalidKeyException: If key is invalid
        """
        # Validate inputs
        if not data:
            raise EncryptionException(
                "Data to encrypt cannot be empty",
                details={"data_length": 0}
            )
        
        if len(key) != 32:
            raise InvalidKeyException(
                "Encryption key must be 32 bytes (256 bits)",
                details={"key_length": len(key), "expected_length": 32}
            )
        
        if len(nonce) != 12:
            raise EncryptionException(
                "Nonce must be 12 bytes (96 bits)",
                details={"nonce_length": len(nonce), "expected_length": 12}
            )
        
        try:
            aesgcm = AESGCM(key)
            return aesgcm.encrypt(nonce, data, None)
            
        except Exception as e:
            logger.exception("AES-GCM encryption failed")
            raise EncryptionException(
                "Failed to encrypt data with AES-256-GCM",
                details={
                    "error": str(e),
                    "data_length": len(data),
                    "key_length": len(key),
                    "nonce_length": len(nonce)
                }
            )
    
    def decrypt_data(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            ciphertext: Encrypted bytes
            key: 256-bit encryption key
            nonce: 96-bit nonce
            
        Returns:
            bytes: Plaintext bytes
            
        Raises:
            DecryptionException: If decryption fails
            AuthenticationFailedException: If authentication tag verification fails (data tampered)
            InvalidKeyException: If key is invalid
        """
        # Validate inputs
        if not ciphertext:
            raise DecryptionException(
                "Ciphertext cannot be empty",
                details={"ciphertext_length": 0}
            )
        
        if len(key) != 32:
            raise InvalidKeyException(
                "Decryption key must be 32 bytes (256 bits)",
                details={"key_length": len(key), "expected_length": 32}
            )
        
        if len(nonce) != 12:
            raise DecryptionException(
                "Nonce must be 12 bytes (96 bits)",
                details={"nonce_length": len(nonce), "expected_length": 12}
            )
        
        try:
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(nonce, ciphertext, None)
            
        except InvalidTag:
            logger.error("GCM authentication tag verification failed - possible tampering")
            raise AuthenticationFailedException(
                "Data authentication failed - file may have been tampered with",
                details={
                    "ciphertext_length": len(ciphertext),
                    "security_warning": "Authentication tag mismatch indicates possible data tampering"
                }
            )
        except Exception as e:
            logger.exception("AES-GCM decryption failed")
            raise DecryptionException(
                "Failed to decrypt data with AES-256-GCM",
                details={
                    "error": str(e),
                    "ciphertext_length": len(ciphertext),
                    "key_length": len(key),
                    "nonce_length": len(nonce)
                }
            )