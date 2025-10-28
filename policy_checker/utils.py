"""
Utility functions for building responses
"""

from typing import Dict, Optional
from datetime import datetime
from .constants import (
    STATUS_SUCCESS,
    STATUS_SERVICE_UNAVAILABLE,
    STATUS_NO_CONTENT,
    STATUS_POLICY_VIOLATION,
    STATUS_EXTRACTION_FAILED
)


def build_success_response(
    extracted_data: Dict,
    confidence_scores: Dict,
    policy_check: Dict,
    ocr_result: Dict
) -> Dict:
    """Build successful extraction response"""
    return {
        "status": STATUS_SUCCESS,
        "processed_at": datetime.utcnow().isoformat(),
        
        "ocr": {
            "success": True,
            "text_length": ocr_result.get("text_length", 0),
            "error": None
        },
        
        "policy_check": {
            "executed": True,
            "approved": policy_check.get("approved", False),
            "reason": policy_check.get("reason"),
            "policy_breach_code": policy_check.get("policy_breach_code"),
            "risk_score": policy_check.get("risk_score", 0),
            "error": None
        },
        
        "extraction": {
            "executed": True,
            "success": True,
            "extracted_data": extracted_data,
            "confidence_scores": confidence_scores,
            "error": None
        }
    }


def build_error_response(
    status: str,
    error_stage: str,
    error_message: str,
    ocr_result: Optional[Dict] = None,
    policy_result: Optional[Dict] = None
) -> Dict:
    """Build error response"""
    response = {
        "status": status,
        "processed_at": datetime.utcnow().isoformat(),
        
        "ocr": {
            "success": False if error_stage == "ocr" else (ocr_result is not None),
            "text_length": ocr_result.get("text_length", 0) if ocr_result else 0,
            "error": error_message if error_stage == "ocr" else None
        },
        
        "policy_check": {
            "executed": error_stage != "ocr",
            "approved": False,
            "reason": policy_result.get("reason") if policy_result else None,
            "policy_breach_code": policy_result.get("policy_breach_code") if policy_result else None,
            "risk_score": policy_result.get("risk_score", 0) if policy_result else 0,
            "error": error_message if error_stage == "policy" else None
        },
        
        "extraction": {
            "executed": False,
            "success": False,
            "extracted_data": None,
            "confidence_scores": None,
            "error": error_message if error_stage == "extraction" else None
        }
    }
    
    return response


def build_policy_violation_response(
    ocr_result: Dict,
    policy_result: Dict
) -> Dict:
    """Build response for policy violation"""
    return {
        "status": STATUS_POLICY_VIOLATION,
        "processed_at": datetime.utcnow().isoformat(),
        
        "ocr": {
            "success": True,
            "text_length": ocr_result.get("text_length", 0),
            "error": None
        },
        
        "policy_check": {
            "executed": True,
            "approved": False,
            "reason": policy_result.get("reason"),
            "policy_breach_code": policy_result.get("policy_breach_code"),
            "risk_score": policy_result.get("risk_score", 0),
            "error": None
        },
        
        "extraction": {
            "executed": False,
            "success": False,
            "extracted_data": None,
            "confidence_scores": None,
            "error": "Extraction skipped due to policy violation"
        }
    }


def build_form_check_response(policy_result: Dict) -> Dict:
    """Build response for form field policy check"""
    return {
        "status": STATUS_POLICY_VIOLATION if not policy_result.get("overall_approved") else STATUS_SUCCESS,
        "processed_at": datetime.utcnow().isoformat(),
        
        "policy_check": {
            "executed": True,
            "overall_approved": policy_result.get("overall_approved", False),
            "field_results": policy_result.get("field_results", []),
            "error": policy_result.get("error")
        }
    }