# policy_checker/middleware/validation.py

"""
Input validation and sanitization
"""

from functools import wraps
from flask import request, jsonify
from ..constants import (
    MAX_TEXT_LENGTH,
    MIN_TEXT_LENGTH,
    MAX_FIELD_COUNT,
    MAX_FIELD_LENGTH
)


def validate_policy_check_import(f):
    """Validate policy check import request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        
        # Check required fields
        if not data or "ocr_text" not in data:
            return jsonify({"error": "Missing required field: ocr_text"}), 400
        
        ocr_text = data.get("ocr_text", "")
        
        # Check text length
        if len(ocr_text) < MIN_TEXT_LENGTH:
            return jsonify({
                "error": f"Text too short (minimum {MIN_TEXT_LENGTH} characters)"
            }), 400
        
        if len(ocr_text) > MAX_TEXT_LENGTH:
            return jsonify({
                "error": f"Text too large (maximum {MAX_TEXT_LENGTH} characters)"
            }), 413
        
        # Sanitize null bytes
        data["ocr_text"] = ocr_text.replace("\x00", "")
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_policy_check_form(f):
    """Validate policy check form request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        
        # Check required fields
        if not data or "field_list" not in data:
            return jsonify({"error": "Missing required field: field_list"}), 400
        
        field_list = data.get("field_list", {})
        
        # Check field count
        if len(field_list) > MAX_FIELD_COUNT:
            return jsonify({
                "error": f"Too many fields (maximum {MAX_FIELD_COUNT})"
            }), 400
        
        # Check individual field lengths
        for key, value in field_list.items():
            if isinstance(value, str) and len(value) > MAX_FIELD_LENGTH:
                return jsonify({
                    "error": f"Field '{key}' exceeds maximum length ({MAX_FIELD_LENGTH})"
                }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function