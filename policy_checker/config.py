"""
Configuration - Load environment variables and API settings
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Google Cloud Vision API (OCR)
GOOGLE_CLOUD_VISION_API_KEY = os.getenv("GOOGLE_CLOUD_VISION_API_KEY")
GOOGLE_CLOUD_VISION_ENDPOINT = "https://vision.googleapis.com/v1/images:annotate"

# Google Gemini API (LLM)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# API Settings
OCR_TIMEOUT = 30  # seconds
LLM_TIMEOUT = 30  # seconds
LLM_TEMPERATURE = 0.1  # Low for consistency
LLM_MAX_TOKENS = 4096

# File limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Validation warnings
if not GOOGLE_CLOUD_VISION_API_KEY:
    print("⚠️  GOOGLE_CLOUD_VISION_API_KEY not set")

if not GEMINI_API_KEY:
    print("⚠️  GEMINI_API_KEY not set")

# Token Limits (Gemini 2.0 Flash)
MAX_INPUT_TOKENS = 1_000_000  # 1M input limit
MAX_OUTPUT_TOKENS = 8_000     # 8K output limit
SAFE_INPUT_TOKENS = 50_000    # Safe limit for OCR text (conservative)

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 60  # Adjust based on your tier
MAX_CONCURRENT_REQUESTS = 10  # Parallel processing limit

# Input Validation
MAX_TEXT_LENGTH = 200_000     # Characters (roughly 50K tokens)
MIN_TEXT_LENGTH = 10          # Minimum meaningful text
MAX_FIELD_COUNT = 50          # Max fields in form check
MAX_FIELD_LENGTH = 5000       # Max length per field

# Timeout Settings
REQUEST_TIMEOUT = 30          # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2             # exponential backoff multiplier
