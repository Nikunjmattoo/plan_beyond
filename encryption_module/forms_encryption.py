# app/encryption_module/forms_encryption.py
"""
Encryption helpers for UserStepAnswer.value using the core encryption module.

We:
- Generate a KMS-protected data key (DEK) per value
- Encrypt the JSON-serialized value with AES-256-GCM
- Store encrypted_dek, nonce, ciphertext in the JSON column

If the value is not in encrypted envelope format, we treat it as plaintext
(for backward compatibility).
"""

import base64
import json
import logging
from typing import Any, Dict

from .core.crypto_engine import CryptoEngine
from .exceptions import (
    EncryptionException,
    DecryptionException,
    InvalidJSONException,
)

logger = logging.getLogger(__name__)

# Single engine instance is fine; boto3 client is thread-safe for typical FastAPI use.
_crypto_engine = CryptoEngine()

# Marker key to identify encrypted payloads
ENC_MARKER = "__enc"


def is_encrypted_value(obj: Any) -> bool:
    """Check if a JSON value is in our encrypted envelope format."""
    return (
        isinstance(obj, dict)
        and obj.get(ENC_MARKER) is True
        and "ciphertext" in obj
        and "dek" in obj
        and "nonce" in obj
    )


def encrypt_answer_value(value: Any) -> Dict[str, Any]:
    """
    Encrypt a single answer value.

    Returns a JSON-serializable dict that can be stored directly in UserStepAnswer.value:
        {
          "__enc": true,
          "alg": "AES-256-GCM",
          "dek": "<base64 KMS-encrypted DEK>",
          "nonce": "<base64 nonce>",
          "ciphertext": "<base64 ciphertext>"
        }
    """
    try:
        # 1) Generate DEK via KMS
        plaintext_dek, encrypted_dek = _crypto_engine.generate_data_key()

        # 2) Generate nonce
        nonce = _crypto_engine.generate_nonce()

        # 3) Serialize the value as JSON; wrap in an object so we can evolve schema later
        payload_bytes = json.dumps({"v": value}).encode("utf-8")

        # 4) Encrypt payload
        ciphertext = _crypto_engine.encrypt_data(payload_bytes, plaintext_dek, nonce)

        # 5) Zero out plaintext key from memory
        del plaintext_dek

        # 6) Return envelope
        return {
            ENC_MARKER: True,
            "alg": "AES-256-GCM",
            "dek": base64.b64encode(encrypted_dek).decode("utf-8"),
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
        }

    except EncryptionException:
        # Already a typed encryption-module exception; just bubble up
        raise
    except Exception as e:
        logger.exception("Unexpected error during answer encryption")
        raise EncryptionException(
            "Failed to encrypt answer value",
            details={"error": str(e), "error_type": type(e).__name__},
        )


def decrypt_answer_value(obj: Any) -> Any:
    """
    Decrypt an answer value if it is in encrypted envelope format.

    If it's not encrypted (no ENC_MARKER), return as-is (backward compatible).
    """
    if not is_encrypted_value(obj):
        # Legacy/plaintext path
        return obj

    try:
        # 1) Decode fields
        encrypted_dek = base64.b64decode(obj["dek"])
        nonce = base64.b64decode(obj["nonce"])
        ciphertext = base64.b64decode(obj["ciphertext"])

        # 2) Decrypt DEK via KMS
        plaintext_dek = _crypto_engine.decrypt_data_key(encrypted_dek)

        # 3) Decrypt ciphertext
        plaintext_bytes = _crypto_engine.decrypt_data(ciphertext, plaintext_dek, nonce)

        # 4) Zero out plaintext DEK
        del plaintext_dek

        # 5) Parse JSON payload
        try:
            decoded = json.loads(plaintext_bytes.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise InvalidJSONException(
                "Failed to parse decrypted answer JSON",
                details={"error": str(e)},
            )

        # We stored {"v": original_value}
        return decoded.get("v")

    except (DecryptionException, InvalidJSONException):
        # Already nice and structured for your global handlers
        raise
    except Exception as e:
        logger.exception("Unexpected error during answer decryption")
        raise DecryptionException(
            "Failed to decrypt answer value",
            details={"error": str(e), "error_type": type(e).__name__},
        )
