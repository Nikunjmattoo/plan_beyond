"""
Module 3: Vault - Crypto Engine Tests (Tests 1-25)

Tests KMS operations and AES-256-GCM encryption/decryption.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from encryption_module.core.crypto_engine import CryptoEngine
from encryption_module.exceptions import (
    KeyGenerationException,
    KMSEncryptionException,
    KMSDecryptionException,
    EncryptionException,
    DecryptionException,
    AuthenticationFailedException,
    InvalidKeyException
)


# ==============================================
# INITIALIZATION TESTS (Tests 1-3)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_crypto_engine_initialization():
    """
    Test #1: CryptoEngine initializes with KMS client
    """
    # Arrange & Act
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

    # Assert
    assert engine.kms == mock_kms
    assert engine.kms_key_id is not None


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_crypto_engine_kms_client_creation():
    """
    Test #2: KMS client created with correct region
    """
    # Arrange & Act
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

    # Assert
    mock_boto.assert_called_once()
    call_args = mock_boto.call_args
    assert call_args[0][0] == 'kms'


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_crypto_engine_init_failure_raises_exception():
    """
    Test #3: Initialization failure raises KMSEncryptionException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_boto.side_effect = Exception("KMS unavailable")

        # Act & Assert
        with pytest.raises(KMSEncryptionException):
            engine = CryptoEngine()


# ==============================================
# KEY GENERATION TESTS (Tests 4-8)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_generate_data_key_success():
    """
    Test #4: Generate 256-bit data key successfully
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        plaintext_key = os.urandom(32)
        encrypted_key = os.urandom(64)
        mock_kms.generate_data_key.return_value = {
            'Plaintext': plaintext_key,
            'CiphertextBlob': encrypted_key
        }

        engine = CryptoEngine()

        # Act
        plain, encrypted = engine.generate_data_key()

    # Assert
    assert plain == plaintext_key
    assert encrypted == encrypted_key
    assert len(plain) == 32  # 256 bits
    mock_kms.generate_data_key.assert_called_once()


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_generate_data_key_calls_kms_with_correct_params():
    """
    Test #5: generate_data_key() calls KMS with AES_256 spec
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        mock_kms.generate_data_key.return_value = {
            'Plaintext': os.urandom(32),
            'CiphertextBlob': os.urandom(64)
        }

        engine = CryptoEngine()

        # Act
        engine.generate_data_key()

    # Assert
    call_args = mock_kms.generate_data_key.call_args
    assert call_args[1]['KeySpec'] == 'AES_256'


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_generate_data_key_kms_failure():
    """
    Test #6: KMS failure raises KeyGenerationException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Denied'}}
        mock_kms.generate_data_key.side_effect = ClientError(error_response, 'GenerateDataKey')

        engine = CryptoEngine()

        # Act & Assert
        with pytest.raises(KeyGenerationException):
            engine.generate_data_key()


@pytest.mark.unit
@pytest.mark.vault
def test_generate_data_key_returns_tuple():
    """
    Test #7: generate_data_key() returns tuple of two bytes objects
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        mock_kms.generate_data_key.return_value = {
            'Plaintext': os.urandom(32),
            'CiphertextBlob': os.urandom(64)
        }

        engine = CryptoEngine()

        # Act
        result = engine.generate_data_key()

    # Assert
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], bytes)
    assert isinstance(result[1], bytes)


@pytest.mark.unit
@pytest.mark.vault
def test_generate_data_key_unexpected_error():
    """
    Test #8: Unexpected error during key generation raises KeyGenerationException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        mock_kms.generate_data_key.side_effect = RuntimeError("Unexpected error")

        engine = CryptoEngine()

        # Act & Assert
        with pytest.raises(KeyGenerationException):
            engine.generate_data_key()


# ==============================================
# KEY DECRYPTION TESTS (Tests 9-14)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_data_key_success():
    """
    Test #9: Decrypt data key successfully via KMS
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        plaintext_key = os.urandom(32)
        encrypted_key = os.urandom(64)
        mock_kms.decrypt.return_value = {'Plaintext': plaintext_key}

        engine = CryptoEngine()

        # Act
        decrypted = engine.decrypt_data_key(encrypted_key)

    # Assert
    assert decrypted == plaintext_key
    mock_kms.decrypt.assert_called_once_with(CiphertextBlob=encrypted_key)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_data_key_empty_key_raises_exception():
    """
    Test #10: Decrypting empty key raises InvalidKeyException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        # Act & Assert
        with pytest.raises(InvalidKeyException):
            engine.decrypt_data_key(b'')


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_data_key_invalid_ciphertext():
    """
    Test #11: Invalid ciphertext raises InvalidKeyException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        error_response = {'Error': {'Code': 'InvalidCiphertextException', 'Message': 'Invalid'}}
        mock_kms.decrypt.side_effect = ClientError(error_response, 'Decrypt')

        engine = CryptoEngine()

        # Act & Assert
        with pytest.raises(InvalidKeyException):
            engine.decrypt_data_key(os.urandom(64))


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_data_key_kms_failure():
    """
    Test #12: KMS decryption failure raises KMSDecryptionException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Denied'}}
        mock_kms.decrypt.side_effect = ClientError(error_response, 'Decrypt')

        engine = CryptoEngine()

        # Act & Assert
        with pytest.raises(KMSDecryptionException):
            engine.decrypt_data_key(os.urandom(64))


@pytest.mark.unit
@pytest.mark.vault
def test_decrypt_data_key_returns_bytes():
    """
    Test #13: decrypt_data_key() returns bytes object
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        plaintext_key = os.urandom(32)
        mock_kms.decrypt.return_value = {'Plaintext': plaintext_key}

        engine = CryptoEngine()

        # Act
        result = engine.decrypt_data_key(os.urandom(64))

    # Assert
    assert isinstance(result, bytes)


@pytest.mark.unit
@pytest.mark.vault
def test_decrypt_data_key_unexpected_error():
    """
    Test #14: Unexpected error during decryption raises KMSDecryptionException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        mock_kms.decrypt.side_effect = RuntimeError("Unexpected error")

        engine = CryptoEngine()

        # Act & Assert
        with pytest.raises(KMSDecryptionException):
            engine.decrypt_data_key(os.urandom(64))


# ==============================================
# NONCE GENERATION TESTS (Tests 15-17)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_generate_nonce_creates_12_bytes():
    """
    Test #15: Nonce is exactly 12 bytes (96 bits)
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        # Act
        nonce = engine.generate_nonce()

    # Assert
    assert isinstance(nonce, bytes)
    assert len(nonce) == 12


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_generate_nonce_is_random():
    """
    Test #16: Each nonce is unique (randomness check)
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        # Act
        nonces = [engine.generate_nonce() for _ in range(100)]

    # Assert - All nonces should be unique
    unique_nonces = set(nonces)
    assert len(unique_nonces) == 100


@pytest.mark.unit
@pytest.mark.vault
def test_generate_nonce_failure():
    """
    Test #17: Nonce generation failure raises EncryptionException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        # Act & Assert
        with patch('encryption_module.core.crypto_engine.os.urandom', side_effect=OSError("No random source")):
            with pytest.raises(EncryptionException):
                engine.generate_nonce()


# ==============================================
# DATA ENCRYPTION TESTS (Tests 18-21)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_data_success():
    """
    Test #18: Encrypt data with AES-256-GCM
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        key = os.urandom(32)  # 256-bit key
        nonce = os.urandom(12)  # 96-bit nonce
        data = b"Test data to encrypt"

        # Act
        ciphertext = engine.encrypt_data(data, key, nonce)

    # Assert
    assert isinstance(ciphertext, bytes)
    assert len(ciphertext) > len(data)  # Ciphertext includes auth tag
    assert ciphertext != data


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_encrypt_data_returns_different_output_for_same_data():
    """
    Test #19: Same data with different nonces produces different ciphertext
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        key = os.urandom(32)
        data = b"Same data"

        nonce1 = os.urandom(12)
        nonce2 = os.urandom(12)

        # Act
        ciphertext1 = engine.encrypt_data(data, key, nonce1)
        ciphertext2 = engine.encrypt_data(data, key, nonce2)

    # Assert
    assert ciphertext1 != ciphertext2


@pytest.mark.unit
@pytest.mark.vault
def test_encrypt_empty_data():
    """
    Test #20: Encrypting empty data raises EncryptionException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        key = os.urandom(32)
        nonce = os.urandom(12)

        # Act & Assert
        with pytest.raises(EncryptionException):
            engine.encrypt_data(b'', key, nonce)


@pytest.mark.unit
@pytest.mark.vault
def test_encrypt_large_data():
    """
    Test #21: Encrypt large data (10MB)
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        key = os.urandom(32)
        nonce = os.urandom(12)
        large_data = os.urandom(10 * 1024 * 1024)  # 10MB

        # Act
        ciphertext = engine.encrypt_data(large_data, key, nonce)

    # Assert
    assert isinstance(ciphertext, bytes)
    assert len(ciphertext) > len(large_data)


# ==============================================
# DATA DECRYPTION TESTS (Tests 22-25)
# ==============================================

@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_data_success():
    """
    Test #22: Decrypt data successfully (round-trip test)
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        key = os.urandom(32)
        nonce = os.urandom(12)
        original_data = b"Test data for round-trip"

        ciphertext = engine.encrypt_data(original_data, key, nonce)

        # Act
        decrypted = engine.decrypt_data(ciphertext, key, nonce)

    # Assert
    assert decrypted == original_data


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_with_wrong_key_fails():
    """
    Test #23: Decryption with wrong key raises AuthenticationFailedException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        key1 = os.urandom(32)
        key2 = os.urandom(32)  # Different key
        nonce = os.urandom(12)
        data = b"Secret data"

        ciphertext = engine.encrypt_data(data, key1, nonce)

        # Act & Assert
        with pytest.raises(AuthenticationFailedException):
            engine.decrypt_data(ciphertext, key2, nonce)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_with_wrong_nonce_fails():
    """
    Test #24: Decryption with wrong nonce raises AuthenticationFailedException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        key = os.urandom(32)
        nonce1 = os.urandom(12)
        nonce2 = os.urandom(12)  # Different nonce
        data = b"Secret data"

        ciphertext = engine.encrypt_data(data, key, nonce1)

        # Act & Assert
        with pytest.raises(AuthenticationFailedException):
            engine.decrypt_data(ciphertext, key, nonce2)


@pytest.mark.unit
@pytest.mark.vault
@pytest.mark.critical
def test_decrypt_tampered_ciphertext_fails():
    """
    Test #25: Decrypting tampered ciphertext raises AuthenticationFailedException
    """
    # Arrange
    with patch('encryption_module.core.crypto_engine.boto3.client') as mock_boto:
        mock_kms = Mock()
        mock_boto.return_value = mock_kms

        engine = CryptoEngine()

        key = os.urandom(32)
        nonce = os.urandom(12)
        data = b"Secret data"

        ciphertext = engine.encrypt_data(data, key, nonce)

        # Tamper with ciphertext
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0xFF  # Flip bits
        tampered = bytes(tampered)

        # Act & Assert
        with pytest.raises(AuthenticationFailedException):
            engine.decrypt_data(tampered, key, nonce)
