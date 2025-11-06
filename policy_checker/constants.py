"""
Constants - Status codes, policy breach codes, field types, and limits
"""

# ===========================
# STATUS CODES
# ===========================
STATUS_SUCCESS = "success"
STATUS_SERVICE_UNAVAILABLE = "service_unavailable"
STATUS_NO_CONTENT = "no_content"
STATUS_POLICY_VIOLATION = "policy_violation"
STATUS_EXTRACTION_FAILED = "extraction_failed"

# ===========================
# TOKEN LIMITS (Gemini 2.0 Flash)
# ===========================
MAX_INPUT_TOKENS = 1_000_000  # 1M input limit
MAX_OUTPUT_TOKENS = 8_000     # 8K output limit
SAFE_INPUT_TOKENS = 50_000    # Safe limit for OCR text (conservative)

# ===========================
# RATE LIMITING
# ===========================
MAX_REQUESTS_PER_MINUTE = 60  # Adjust based on your tier
MAX_CONCURRENT_REQUESTS = 10  # Parallel processing limit

# ===========================
# INPUT VALIDATION
# ===========================
MAX_TEXT_LENGTH = 200_000     # Characters (roughly 50K tokens)
MIN_TEXT_LENGTH = 10          # Minimum meaningful text
MAX_FIELD_COUNT = 50          # Max fields in form check
MAX_FIELD_LENGTH = 5000       # Max length per field

# ===========================
# TIMEOUT SETTINGS
# ===========================
REQUEST_TIMEOUT = 30          # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2             # exponential backoff multiplier

# ===========================
# POLICY BREACH CODES
# ===========================
POLICY_BREACH_CODES = {
    # Violence & Terrorism
    "TERRORISM": "Terrorism planning, support, or extremist content",
    "VIOLENCE": "Violent content, threats, or graphic violence",
    "WEAPONS": "Weapons, ammunition, or firearms trafficking",
    "EXPLOSIVES": "Explosives, bombs, or dangerous materials",
    
    # Illegal Activities
    "ILLEGAL_DRUGS": "Illegal drug production, trafficking, or sale",
    "HUMAN_TRAFFICKING": "Human trafficking or forced labor",
    "MONEY_LAUNDERING": "Money laundering schemes or financial fraud",
    "FRAUD": "Fraudulent schemes, scams, or deceptive practices",
    
    # Harmful Content
    "CHILD_ABUSE": "Child abuse, exploitation, or CSAM",
    "HATE_SPEECH": "Hate speech, discrimination, or harassment",
    "SELF_HARM": "Self-harm instructions or suicide encouragement",
    "ANIMAL_CRUELTY": "Animal abuse or cruelty",
    
    # Privacy & Security
    "DOXXING": "Personal information disclosure for harassment",
    "IDENTITY_THEFT": "Identity theft or impersonation attempts",
    
    # Other
    "GRAPHIC_CONTENT": "Graphic violence or disturbing imagery"
}

# Policy Violation Categories (list for quick checks)
POLICY_VIOLATION_CATEGORIES = list(POLICY_BREACH_CODES.keys())

# ===========================
# FIELD TYPES
# ===========================
FIELD_TYPE_STRING = "string"
FIELD_TYPE_NUMBER = "number"
FIELD_TYPE_DATE = "date"
FIELD_TYPE_BOOLEAN = "boolean"
FIELD_TYPE_ARRAY = "array"
FIELD_TYPE_OBJECT = "object"

# ===========================
# LLM CONFIGURATION
# ===========================
LLM_PROVIDER = "gemini"
LLM_MODEL = "gemini-2.0-flash-exp"
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 2000

# ===========================
# TEMPLATE TYPES
# ===========================
DOCUMENT_TEMPLATES = [
    "passport",
    "license",
    "id_card",
    "financial",
    "medical",
    "legal",
    "general"
]

FORM_TEMPLATES = [
    "contact",
    "profile",
    "financial",
    "medical",
    "general"
]