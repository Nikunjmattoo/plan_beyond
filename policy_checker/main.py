"""
Main API - Public functions for policy checking and extraction

Two main functions:
1. extract_from_file() - Complete flow: OCR → Policy → Extract
2. check_form_fields() - Policy check for manually entered fields
"""

from typing import Dict
from .services.ocr_service import OCRService
from .services.policy_service import PolicyService
from .services.extraction_service import ExtractionService
from .utils import (
    build_success_response,
    build_error_response,
    build_policy_violation_response,
    build_form_check_response
)
from .constants import (
    STATUS_SERVICE_UNAVAILABLE,
    STATUS_NO_CONTENT,
    STATUS_POLICY_VIOLATION
)


# Initialize services
ocr_service = OCRService()
policy_service = PolicyService()
extraction_service = ExtractionService()


async def extract_from_file(
    file_bytes: bytes,
    fields_to_extract: Dict[str, Dict]
) -> Dict:
    """
    Complete extraction flow from uploaded file.
    
    Flow:
        1. OCR: Extract text from file
        2. Policy Check: Verify content is safe
        3. Extraction: Extract structured fields (if approved)
    
    Args:
        file_bytes: Raw file bytes (PDF, image, etc.)
        fields_to_extract: Field definitions with types and formats
            Example:
            {
                "policy_number": {"type": "string", "format": "POL-XXXXXX"},
                "amount": {"type": "number"},
                "date": {"type": "date", "format": "YYYY-MM-DD"}
            }
    
    Returns:
        Complete response with all stages:
        {
            "status": "success" | "service_unavailable" | "no_content" | "policy_violation",
            "processed_at": "ISO timestamp",
            "ocr": {...},
            "policy_check": {...},
            "extraction": {...}
        }
    """
    
    # Step 1: OCR - Extract text
    ocr_result = ocr_service.extract_text_from_file(file_bytes)
    
    # Check OCR errors
    if ocr_result["status"] == STATUS_SERVICE_UNAVAILABLE:
        return build_error_response(
            status=STATUS_SERVICE_UNAVAILABLE,
            error_stage="ocr",
            error_message=ocr_result["error"]
        )
    
    if ocr_result["status"] == STATUS_NO_CONTENT:
        return build_error_response(
            status=STATUS_NO_CONTENT,
            error_stage="ocr",
            error_message=ocr_result["error"]
        )
    
    extracted_text = ocr_result["text"]
    
    # Step 2: Policy Check
    policy_result = policy_service.check_policy_for_text(extracted_text)
    
    # Check policy errors
    if policy_result.get("error"):
        return build_error_response(
            status=STATUS_SERVICE_UNAVAILABLE,
            error_stage="policy",
            error_message=policy_result["error"],
            ocr_result=ocr_result
        )
    
    # Check if policy violated
    if not policy_result["approved"]:
        return build_policy_violation_response(
            ocr_result=ocr_result,
            policy_result=policy_result
        )
    
    # Step 3: Extract Fields (policy approved)
    extraction_result = extraction_service.extract_fields_from_text(
        text=extracted_text,
        fields_to_extract=fields_to_extract
    )
    
    # Check extraction errors
    if extraction_result.get("error"):
        return build_error_response(
            status=STATUS_SERVICE_UNAVAILABLE,
            error_stage="extraction",
            error_message=extraction_result["error"],
            ocr_result=ocr_result,
            policy_result=policy_result
        )
    
    # Step 4: Build success response
    return build_success_response(
        extracted_data=extraction_result["extracted_data"],
        confidence_scores=extraction_result["confidence_scores"],
        policy_check=policy_result,
        ocr_result=ocr_result
    )


async def check_form_fields(fields: Dict[str, str]) -> Dict:
    """
    Policy check for manually entered form fields.
    
    Args:
        fields: Dict of field_name: field_value
            Example:
            {
                "beneficiary_notes": "Some text...",
                "special_instructions": "More text..."
            }
    
    Returns:
        {
            "status": "success" | "policy_violation" | "service_unavailable",
            "processed_at": "ISO timestamp",
            "policy_check": {
                "overall_approved": bool,
                "field_results": [
                    {
                        "field_name": str,
                        "approved": bool,
                        "reason": str | None,
                        "policy_breach_code": str | None,
                        "suggested_action": str | None
                    }
                ]
            }
        }
    """
    
    # Policy check
    policy_result = policy_service.check_policy_for_fields(fields)
    
    # Build response
    return build_form_check_response(policy_result) 