"""Configuration for KMS-based encryption with production-grade limits."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# AWS CONFIGURATION
# ==========================================

# AWS KMS Configuration
KMS_KEY_ID = os.getenv("KMS_KEY_ID")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

if not KMS_KEY_ID:
    raise ValueError("KMS_KEY_ID environment variable must be set")

# S3 Configuration (reuse existing S3_BUCKET)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME") or os.getenv("S3_BUCKET")
S3_PRESIGNED_URL_EXPIRY = 3600  # 1 hour

if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET or S3_BUCKET_NAME environment variable must be set")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# ==========================================
# ENCRYPTION CONSTANTS
# ==========================================

ENCRYPTION_ALGORITHM = "AES-256-GCM"
KEY_SIZE = 32  # 256 bits
NONCE_SIZE = 12  # 96 bits

# ==========================================
# FILE SIZE LIMITS
# ==========================================

# Maximum file sizes (in bytes)
MAX_SOURCE_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file
MAX_FORM_DATA_SIZE = 1 * 1024 * 1024     # 1 MB for form data JSON

# Human-readable sizes for error messages
MAX_SOURCE_FILE_SIZE_MB = MAX_SOURCE_FILE_SIZE / (1024 * 1024)
MAX_FORM_DATA_SIZE_MB = MAX_FORM_DATA_SIZE / (1024 * 1024)

# ==========================================
# MIME TYPE VALIDATION
# ==========================================

# Allowed MIME types for uploaded files
ALLOWED_MIME_TYPES = [
    # Images
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    
    # Documents
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.ms-excel",  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "text/plain",
    "text/csv",
]

# Human-readable list for error messages
ALLOWED_FILE_TYPES_DISPLAY = "PDF, Word, Excel, Images (JPG, PNG, GIF, WebP), Text, CSV"

# ==========================================
# FORM DATA VALIDATION
# ==========================================

# Form field limits
MAX_FIELD_COUNT = 100        # Maximum number of fields in form data
MAX_FIELD_LENGTH = 10000     # Maximum length of a single field value (characters)
MAX_FIELD_NAME_LENGTH = 100  # Maximum length of field name

# ==========================================
# RATE LIMITING
# ==========================================

# Per-user operation limits
MAX_ENCRYPTIONS_PER_USER_PER_DAY = 100
MAX_DECRYPTIONS_PER_USER_PER_HOUR = 200
MAX_SHARES_PER_FILE = 50
MAX_FILES_PER_USER = 5000

# Per-file access limits
MAX_DECRYPTIONS_PER_FILE_PER_HOUR = 100

# ==========================================
# TIMEOUT & RETRY SETTINGS
# ==========================================

# KMS operation timeouts
KMS_TIMEOUT_SECONDS = 10
KMS_MAX_RETRIES = 3

# S3 operation timeouts
S3_TIMEOUT_SECONDS = 30
S3_MAX_RETRIES = 3

# Database operation timeouts
DB_TIMEOUT_SECONDS = 5

# ==========================================
# SECURITY SETTINGS
# ==========================================

# Key rotation reminder (days)
KEY_ROTATION_REMINDER_DAYS = 365

# Audit log retention (days)
AUDIT_LOG_RETENTION_DAYS = 90

# Failed access attempt lockout
MAX_FAILED_ACCESS_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# ==========================================
# LOGGING CONFIGURATION
# ==========================================

# Log levels
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Sensitive fields to redact in logs
SENSITIVE_FIELDS = [
    "password",
    "secret",
    "token",
    "api_key",
    "encryption_key",
    "plaintext_dek",
]