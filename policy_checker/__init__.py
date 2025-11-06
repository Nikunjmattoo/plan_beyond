"""
TPB Policy Checker Module

Public API:
- extract_from_file(): OCR + Policy Check + Extract fields from uploaded file
- check_form_fields(): Policy check on manually entered form fields
"""

from .main import extract_from_file, check_form_fields

__version__ = "1.0.0"
__all__ = ["extract_from_file", "check_form_fields"]