# # app/routers/policy.py
# """
# Policy Checker API Routes for FastAPI
# Handles policy violation checking for imported files and form data
# """

# from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
# from fastapi.responses import JSONResponse
# from sqlalchemy.orm import Session
# from typing import Dict, Optional
# import logging

# from app.database import SessionLocal
# from app.dependencies import get_current_user
# from app.models.user import User

# # Import policy checker services
# from app.policy_checker.services.policy_service import PolicyService
# from app.policy_checker.services.ocr_service import OCRService
# from app.policy_checker.services.extraction_service import ExtractionService

# # Import validation constants
# from app.policy_checker.constants import (
#     MAX_TEXT_LENGTH,
#     MIN_TEXT_LENGTH,
#     MAX_FIELD_COUNT,
#     MAX_FIELD_LENGTH
# )

# # Pydantic models for request/response
# from pydantic import BaseModel, Field, validator
# from typing import List

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/policy", tags=["Policy Checker"])


# # ===========================
# # REQUEST/RESPONSE MODELS
# # ===========================

# class PolicyCheckImportRequest(BaseModel):
#     """Request model for policy check on imported text"""
#     ocr_text: str = Field(..., min_length=MIN_TEXT_LENGTH, max_length=MAX_TEXT_LENGTH)
#     template: Optional[str] = Field(default="general", description="Document template type")
    
#     @validator('ocr_text')
#     def sanitize_text(cls, v):
#         # Remove null bytes
#         return v.replace("\x00", "")


# class PolicyCheckImportResponse(BaseModel):
#     """Response model for policy check import"""
#     approved: bool
#     reason: Optional[str] = None
#     policy_breach_code: Optional[str] = None
#     risk_score: int = Field(ge=0, le=100)
#     error: Optional[str] = None


# class PolicyCheckFormRequest(BaseModel):
#     """Request model for policy check on form fields"""
#     field_list: Dict[str, str] = Field(..., description="Dictionary of field names and values")
#     template: Optional[str] = Field(default="general", description="Form template type")
    
#     @validator('field_list')
#     def validate_fields(cls, v):
#         if len(v) > MAX_FIELD_COUNT:
#             raise ValueError(f"Too many fields (maximum {MAX_FIELD_COUNT})")
        
#         for key, value in v.items():
#             if isinstance(value, str):
#                 if len(value) > MAX_FIELD_LENGTH:
#                     raise ValueError(f"Field '{key}' exceeds maximum length ({MAX_FIELD_LENGTH})")
#                 # Sanitize null bytes
#                 v[key] = value.replace("\x00", "")
        
#         return v


# class PolicyCheckFormResponse(BaseModel):
#     """Response model for policy check form"""
#     results: Dict[str, Dict]  # field_name -> {approved, reason, policy_breach_code}
#     overall_approved: bool


# class OCRRequest(BaseModel):
#     """Request for OCR extraction"""
#     file_path: str = Field(..., description="Path to file for OCR extraction")


# class OCRResponse(BaseModel):
#     """Response from OCR extraction"""
#     success: bool
#     text: Optional[str] = None
#     error: Optional[str] = None


# class ExtractionRequest(BaseModel):
#     """Request for structured data extraction"""
#     ocr_text: str = Field(..., min_length=MIN_TEXT_LENGTH, max_length=MAX_TEXT_LENGTH)
#     structure: Dict = Field(..., description="Expected structure of the document")
#     rules: Optional[Dict] = Field(default={}, description="Extraction rules")
#     template: str = Field(default="general", description="Template type")


# class ExtractionResponse(BaseModel):
#     """Response from structured data extraction"""
#     success: bool
#     extracted_data: Optional[Dict] = None
#     error: Optional[str] = None


# # ===========================
# # DEPENDENCIES
# # ===========================

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# # Initialize services (singleton pattern)
# policy_service = PolicyService()
# ocr_service = OCRService()
# extraction_service = ExtractionService()


# # ===========================
# # ENDPOINTS
# # ===========================

# @router.post(
#     "/check-import",
#     response_model=PolicyCheckImportResponse,
#     summary="Check policy violations in imported document text",
#     description="Analyzes OCR-extracted text from imported documents for policy violations"
# )
# async def check_policy_import(
#     request: PolicyCheckImportRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Check if imported document text violates content policy.
    
#     - **ocr_text**: The extracted text from the document
#     - **template**: Document type (passport, license, financial, medical, etc.)
    
#     Returns approval status, risk score, and breach details if rejected.
#     """
#     try:
#         logger.info(f"Policy check import for user {current_user.id}, text length: {len(request.ocr_text)}")
        
#         # Call policy service
#         result = policy_service.check_policy_for_text(request.ocr_text)
        
#         # Log the result
#         if not result.get("approved", False):
#             logger.warning(
#                 f"Policy violation detected for user {current_user.id}: "
#                 f"{result.get('policy_breach_code')} - {result.get('reason')}"
#             )
        
#         return PolicyCheckImportResponse(**result)
        
#     except Exception as e:
#         logger.error(f"Error in check_policy_import: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Policy check failed: {str(e)}"
#         )


# @router.post(
#     "/check-form",
#     response_model=PolicyCheckFormResponse,
#     summary="Check policy violations in form field data",
#     description="Analyzes form field values for policy violations"
# )
# async def check_policy_form(
#     request: PolicyCheckFormRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Check if form field values violate content policy.
    
#     - **field_list**: Dictionary of field names and their values
#     - **template**: Form template type
    
#     Returns per-field approval status and overall approval.
#     """
#     try:
#         logger.info(
#             f"Policy check form for user {current_user.id}, "
#             f"fields: {len(request.field_list)}"
#         )
        
#         # Call policy service
#         result = policy_service.check_policy_for_fields(request.field_list)
        
#         # Calculate overall approval
#         overall_approved = all(
#             field_result.get("approved", False) 
#             for field_result in result.get("results", {}).values()
#         )
        
#         # Log violations
#         violations = [
#             f"{field}: {data.get('policy_breach_code')}"
#             for field, data in result.get("results", {}).items()
#             if not data.get("approved", False)
#         ]
        
#         if violations:
#             logger.warning(
#                 f"Policy violations in form for user {current_user.id}: {violations}"
#             )
        
#         return PolicyCheckFormResponse(
#             results=result.get("results", {}),
#             overall_approved=overall_approved
#         )
        
#     except Exception as e:
#         logger.error(f"Error in check_policy_form: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Policy check failed: {str(e)}"
#         )


# @router.post(
#     "/ocr/extract",
#     response_model=OCRResponse,
#     summary="Extract text from document using OCR",
#     description="Performs OCR on uploaded document to extract text"
# )
# async def extract_text_ocr(
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Extract text from an uploaded document using OCR.
    
#     - **file**: The document file (PDF, image, etc.)
    
#     Returns extracted text or error message.
#     """
#     try:
#         logger.info(f"OCR extraction for user {current_user.id}, file: {file.filename}")
        
#         # Save uploaded file temporarily
#         import tempfile
#         import os
        
#         suffix = os.path.splitext(file.filename)[1]
#         with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
#             content = await file.read()
#             temp_file.write(content)
#             temp_path = temp_file.name
        
#         try:
#             # Extract text using OCR service
                        
#             with open(temp_path, 'rb') as f:
#                 file_bytes = f.read()

#             # Extract text
#             result = ocr_service.extract_text_from_file(file_bytes)

#             if result.get("status") != "success":
#                 return OCRResponse(
#                     success=False,
#                     error=result.get("error", "OCR extraction failed")
#                 )

#             extracted_text = result.get("text", "")
            
#             if not extracted_text or len(extracted_text.strip()) < MIN_TEXT_LENGTH:
#                 return OCRResponse(
#                     success=False,
#                     error="No text could be extracted from the document"
#                 )
            
#             return OCRResponse(
#                 success=True,
#                 text=extracted_text
#             )
            
#         finally:
#             # Clean up temp file
#             if os.path.exists(temp_path):
#                 os.unlink(temp_path)
        
#     except Exception as e:
#         logger.error(f"Error in extract_text_ocr: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"OCR extraction failed: {str(e)}"
#         )


# @router.post(
#     "/extract/structured",
#     response_model=ExtractionResponse,
#     summary="Extract structured data from document text",
#     description="Uses LLM to extract structured data from OCR text based on template"
# )
# async def extract_structured_data(
#     request: ExtractionRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Extract structured data from document text using LLM.
    
#     - **ocr_text**: The extracted text from the document
#     - **structure**: Expected structure/fields to extract
#     - **rules**: Extraction rules and validation
#     - **template**: Document template type
    
#     Returns extracted structured data.
#     """
#     try:
#         logger.info(
#             f"Structured extraction for user {current_user.id}, "
#             f"template: {request.template}"
#         )
        
#         # Call extraction service
#         result = extraction_service.extract_form_values(
#             ocr_text=request.ocr_text,
#             structure=request.structure,
#             rules=request.rules,
#             template=request.template
#         )
        
#         if result.get("error"):
#             return ExtractionResponse(
#                 success=False,
#                 error=result["error"]
#             )
        
#         return ExtractionResponse(
#             success=True,
#             extracted_data=result.get("extracted_data", {})
#         )
        
#     except Exception as e:
#         logger.error(f"Error in extract_structured_data: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Extraction failed: {str(e)}"
#         )


# @router.post(
#     "/import-file",
#     summary="Import file with complete workflow: OCR → Policy → Extraction",
#     description="Single endpoint that handles file upload, OCR extraction, policy check, and field extraction"
# )
# async def import_file(
#     file: UploadFile = File(...),
#     template: str = "general",
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Complete import workflow in ONE call:
#     1. Extract text from file via OCR
#     2. Check policy violations
#     3. If approved, extract structured fields
#     4. Return combined result
    
#     - **file**: Document file (PDF, image)
#     - **template**: Document type (passport, license, medical, financial, general)
    
#     Returns:
#     - If REJECTED: {success: false, approved: false, reason, policy_breach_code}
#     - If APPROVED: {success: true, approved: true, extracted_fields: {...}}
#     """
#     try:
#         logger.info(f"File import for user {current_user.id}, file: {file.filename}, template: {template}")
        
#         # Step 1: Read file
#         content = await file.read()
        
#         # Step 2: OCR - Extract text
#         ocr_result = ocr_service.extract_text_from_file(content)
        
#         if ocr_result.get("status") != "success":
#             return JSONResponse(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 content={
#                     "success": False,
#                     "approved": False,
#                     "error": ocr_result.get("error", "OCR extraction failed"),
#                     "step": "ocr"
#                 }
#             )
        
#         extracted_text = ocr_result.get("text", "")
        
#         # Step 3: Policy Check
#         policy_result = policy_service.check_policy_for_text(extracted_text)
        
#         if policy_result.get("error"):
#             return JSONResponse(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 content={
#                     "success": False,
#                     "approved": False,
#                     "error": policy_result.get("error"),
#                     "step": "policy_check"
#                 }
#             )
        
#         approved = policy_result.get("approved", False)
        
#         # If NOT approved, stop here and return rejection
#         if not approved:
#             logger.warning(
#                 f"Policy violation in import for user {current_user.id}: "
#                 f"{policy_result.get('policy_breach_code')} - {policy_result.get('reason')}"
#             )
#             return {
#                 "success": False,
#                 "approved": False,
#                 "reason": policy_result.get("reason"),
#                 "policy_breach_code": policy_result.get("policy_breach_code"),
#                 "risk_score": policy_result.get("risk_score", 0),
#                 "step": "policy_check"
#             }
        
#         # Step 4: Extract structured fields (only if approved)
#         # Define structure based on template
#         structures = {
#             "passport": {
#                 "name": "string",
#                 "passport_number": "string",
#                 "date_of_birth": "date",
#                 "nationality": "string",
#                 "issue_date": "date",
#                 "expiry_date": "date"
#             },
#             "license": {
#                 "name": "string",
#                 "license_number": "string",
#                 "date_of_birth": "date",
#                 "address": "string",
#                 "issue_date": "date",
#                 "expiry_date": "date"
#             },
#             "medical": {
#                 "patient_name": "string",
#                 "doctor_name": "string",
#                 "date": "date",
#                 "medications": "array",
#                 "diagnosis": "string"
#             },
#             "financial": {
#                 "account_holder": "string",
#                 "account_number": "string",
#                 "date": "date",
#                 "balance": "string",
#                 "transactions": "array"
#             },
#             "general": {
#                 "name": "string",
#                 "date": "date",
#                 "reference_number": "string"
#             }
#         }
        
#         structure = structures.get(template, structures["general"])
        
#         extraction_result = extraction_service.extract_fields_from_text(
#             text=extracted_text,
#             fields_to_extract=structure
#         )
        
#         extracted_fields = extraction_result.get("extracted_data", {})
        
#         # Success response with all data
#         return {
#             "success": True,
#             "approved": True,
#             "extracted_fields": extracted_fields,
#             "text_length": len(extracted_text),
#             "template": template,
#             "step": "complete"
#         }
        
#     except Exception as e:
#         logger.error(f"Error in import_file: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Import failed: {str(e)}"
#         )


# @router.get(
#     "/health",
#     summary="Health check for policy checker service",
#     description="Verify that policy checker and dependencies are operational"
# )
# async def health_check():
#     """
#     Check if the policy checker service and its dependencies are working.
#     """
#     try:
#         # Test Gemini connection
#         test_result = policy_service.check_policy_for_text("This is a test.")
        
#         if test_result.get("error"):
#             return JSONResponse(
#                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#                 content={
#                     "status": "unhealthy",
#                     "error": "LLM service unavailable",
#                     "details": test_result.get("error")
#                 }
#             )
        
#         return {
#             "status": "healthy",
#             "service": "policy_checker",
#             "llm_provider": "gemini",
#             "version": "1.0.0"
#         }
        
#     except Exception as e:
#         logger.error(f"Health check failed: {str(e)}")
#         return JSONResponse(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             content={
#                 "status": "unhealthy",
#                 "error": str(e)
#             }
#         )





# app/routers/policy.py
"""
Policy Checker API Routes for FastAPI
Handles policy violation checking for imported files and form data
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Optional
import logging

from app.database import SessionLocal
from app.dependencies import get_current_user
from app.models.user import User

# Import policy checker services
from app.policy_checker.services.policy_service import PolicyService
from app.policy_checker.services.ocr_service import OCRService
from app.policy_checker.services.extraction_service import ExtractionService

# Import validation constants
from app.policy_checker.constants import (
    MAX_TEXT_LENGTH,
    MIN_TEXT_LENGTH,
    MAX_FIELD_COUNT,
    MAX_FIELD_LENGTH
)

# Pydantic models for request/response
from pydantic import BaseModel, Field, validator
from typing import List

logger = logging.getLogger(__name__)

# Primary router (kept exactly as-is, with /policy prefix)
router = APIRouter(prefix="/policy", tags=["Policy Checker"])

# NEW: Public alias router to satisfy frontend calls like /api/import-file
# (No removals; we're only adding a second router.)
router_api = APIRouter(prefix="/api", tags=["Policy Checker (Alias)"])


# ===========================
# REQUEST/RESPONSE MODELS
# ===========================

class PolicyCheckImportRequest(BaseModel):
    """Request model for policy check on imported text"""
    ocr_text: str = Field(..., min_length=MIN_TEXT_LENGTH, max_length=MAX_TEXT_LENGTH)
    template: Optional[str] = Field(default="general", description="Document template type")
    
    @validator('ocr_text')
    def sanitize_text(cls, v):
        # Remove null bytes
        return v.replace("\x00", "")


class PolicyCheckImportResponse(BaseModel):
    """Response model for policy check import"""
    approved: bool
    reason: Optional[str] = None
    policy_breach_code: Optional[str] = None
    risk_score: int = Field(ge=0, le=100)
    error: Optional[str] = None


class PolicyCheckFormRequest(BaseModel):
    """Request model for policy check on form fields"""
    field_list: Dict[str, str] = Field(..., description="Dictionary of field names and values")
    template: Optional[str] = Field(default="general", description="Form template type")
    
    @validator('field_list')
    def validate_fields(cls, v):
        if len(v) > MAX_FIELD_COUNT:
            raise ValueError(f"Too many fields (maximum {MAX_FIELD_COUNT})")
        
        for key, value in v.items():
            if isinstance(value, str):
                if len(value) > MAX_FIELD_LENGTH:
                    raise ValueError(f"Field '{key}' exceeds maximum length ({MAX_FIELD_LENGTH})")
                # Sanitize null bytes
                v[key] = value.replace("\x00", "")
        
        return v


class PolicyCheckFormResponse(BaseModel):
    """Response model for policy check form"""
    results: Dict[str, Dict]  # field_name -> {approved, reason, policy_breach_code}
    overall_approved: bool


class OCRRequest(BaseModel):
    """Request for OCR extraction"""
    file_path: str = Field(..., description="Path to file for OCR extraction")


class OCRResponse(BaseModel):
    """Response from OCR extraction"""
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None


class ExtractionRequest(BaseModel):
    """Request for structured data extraction"""
    ocr_text: str = Field(..., min_length=MIN_TEXT_LENGTH, max_length=MAX_TEXT_LENGTH)
    structure: Dict = Field(..., description="Expected structure of the document")
    rules: Optional[Dict] = Field(default={}, description="Extraction rules")
    template: str = Field(default="general", description="Template type")


class ExtractionResponse(BaseModel):
    """Response from structured data extraction"""
    success: bool
    extracted_data: Optional[Dict] = None
    error: Optional[str] = None


# ===========================
# DEPENDENCIES
# ===========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize services (singleton pattern)
policy_service = PolicyService()
ocr_service = OCRService()
extraction_service = ExtractionService()


# ===========================
# INTERNAL SHARED IMPL
# ===========================

async def _import_file_impl(
    file: UploadFile,
    template: str,
    current_user: User,
    db: Session,
):
    """
    Shared implementation for import-file so we can expose it on
    both /policy/import-file and /api/import-file.
    """
    try:
        logger.info(f"File import for user {current_user.id}, file: {file.filename}, template: {template}")
        
        # Step 1: Read file
        content = await file.read()
        
        # Step 2: OCR - Extract text
        ocr_result = ocr_service.extract_text_from_file(content)
        
        if ocr_result.get("status") != "success":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "approved": False,
                    "error": ocr_result.get("error", "OCR extraction failed"),
                    "step": "ocr"
                }
            )
        
        extracted_text = ocr_result.get("text", "")
        
        # Step 3: Policy Check
        policy_result = policy_service.check_policy_for_text(extracted_text)
        
        if policy_result.get("error"):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "approved": False,
                    "error": policy_result.get("error"),
                    "step": "policy_check"
                }
            )
        
        approved = policy_result.get("approved", False)
        
        # If NOT approved, stop here and return rejection
        if not approved:
            logger.warning(
                f"Policy violation in import for user {current_user.id}: "
                f"{policy_result.get('policy_breach_code')} - {policy_result.get('reason')}"
            )
            return {
                "success": False,
                "approved": False,
                "reason": policy_result.get("reason"),
                "policy_breach_code": policy_result.get("policy_breach_code"),
                "risk_score": policy_result.get("risk_score", 0),
                "step": "policy_check"
            }
        
        # Step 4: Extract structured fields (only if approved)
        # Define structure based on template
        structures = {
            "passport": {
                "name": "string",
                "passport_number": "string",
                "date_of_birth": "date",
                "nationality": "string",
                "issue_date": "date",
                "expiry_date": "date"
            },
            "license": {
                "name": "string",
                "license_number": "string",
                "date_of_birth": "date",
                "address": "string",
                "issue_date": "date",
                "expiry_date": "date"
            },
            "medical": {
                "patient_name": "string",
                "doctor_name": "string",
                "date": "date",
                "medications": "array",
                "diagnosis": "string"
            },
            "financial": {
                "account_holder": "string",
                "account_number": "string",
                "date": "date",
                "balance": "string",
                "transactions": "array"
            },
            "general": {
                "name": "string",
                "date": "date",
                "reference_number": "string"
            }
        }
        
        structure = structures.get(template, structures["general"])
        
        extraction_result = extraction_service.extract_fields_from_text(
            text=extracted_text,
            fields_to_extract=structure
        )
        
        extracted_fields = extraction_result.get("extracted_data", {})
        
        # Success response with all data
        return {
            "success": True,
            "approved": True,
            "extracted_fields": extracted_fields,
            "text_length": len(extracted_text),
            "template": template,
            "step": "complete"
        }
        
    except Exception as e:
        logger.error(f"Error in import_file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


# ===========================
# ENDPOINTS (PRIMARY /policy)
# ===========================

@router.post(
    "/check-import",
    response_model=PolicyCheckImportResponse,
    summary="Check policy violations in imported document text",
    description="Analyzes OCR-extracted text from imported documents for policy violations"
)
async def check_policy_import(
    request: PolicyCheckImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if imported document text violates content policy.
    
    - **ocr_text**: The extracted text from the document
    - **template**: Document type (passport, license, financial, medical, etc.)
    
    Returns approval status, risk score, and breach details if rejected.
    """
    try:
        logger.info(f"Policy check import for user {current_user.id}, text length: {len(request.ocr_text)}")
        
        # Call policy service
        result = policy_service.check_policy_for_text(request.ocr_text)
        
        # Log the result
        if not result.get("approved", False):
            logger.warning(
                f"Policy violation detected for user {current_user.id}: "
                f"{result.get('policy_breach_code')} - {result.get('reason')}"
            )
        
        return PolicyCheckImportResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in check_policy_import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Policy check failed: {str(e)}"
        )


@router.post(
    "/check-form",
    response_model=PolicyCheckFormResponse,
    summary="Check policy violations in form field data",
    description="Analyzes form field values for policy violations"
)
async def check_policy_form(
    request: PolicyCheckFormRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if form field values violate content policy.
    
    - **field_list**: Dictionary of field names and their values
    - **template**: Form template type
    
    Returns per-field approval status and overall approval.
    """
    try:
        logger.info(
            f"Policy check form for user {current_user.id}, "
            f"fields: {len(request.field_list)}"
        )
        
        # Call policy service
        result = policy_service.check_policy_for_fields(request.field_list)
        
        # Calculate overall approval
        overall_approved = all(
            field_result.get("approved", False) 
            for field_result in result.get("results", {}).values()
        )
        
        # Log violations
        violations = [
            f"{field}: {data.get('policy_breach_code')}"
            for field, data in result.get("results", {}).items()
            if not data.get("approved", False)
        ]
        
        if violations:
            logger.warning(
                f"Policy violations in form for user {current_user.id}: {violations}"
            )
        
        return PolicyCheckFormResponse(
            results=result.get("results", {}),
            overall_approved=overall_approved
        )
        
    except Exception as e:
        logger.error(f"Error in check_policy_form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Policy check failed: {str(e)}"
        )


@router.post(
    "/ocr/extract",
    response_model=OCRResponse,
    summary="Extract text from document using OCR",
    description="Performs OCR on uploaded document to extract text"
)
async def extract_text_ocr(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract text from an uploaded document using OCR.
    
    - **file**: The document file (PDF, image, etc.)
    
    Returns extracted text or error message.
    """
    try:
        logger.info(f"OCR extraction for user {current_user.id}, file: {file.filename}")
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Extract text using OCR service
            with open(temp_path, 'rb') as f:
                file_bytes = f.read()

            # Extract text
            result = ocr_service.extract_text_from_file(file_bytes)

            if result.get("status") != "success":
                return OCRResponse(
                    success=False,
                    error=result.get("error", "OCR extraction failed")
                )

            extracted_text = result.get("text", "")
            
            if not extracted_text or len(extracted_text.strip()) < MIN_TEXT_LENGTH:
                return OCRResponse(
                    success=False,
                    error="No text could be extracted from the document"
                )
            
            return OCRResponse(
                success=True,
                text=extracted_text
            )
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error in extract_text_ocr: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR extraction failed: {str(e)}"
        )


@router.post(
    "/extract/structured",
    response_model=ExtractionResponse,
    summary="Extract structured data from document text",
    description="Uses LLM to extract structured data from OCR text based on template"
)
async def extract_structured_data(
    request: ExtractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract structured data from document text using LLM.
    
    - **ocr_text**: The extracted text from the document
    - **structure**: Expected structure/fields to extract
    - **rules**: Extraction rules and validation
    - **template**: Document template type
    
    Returns extracted structured data.
    """
    try:
        logger.info(
            f"Structured extraction for user {current_user.id}, "
            f"template: {request.template}"
        )
        
        # Call extraction service
        result = extraction_service.extract_form_values(
            ocr_text=request.ocr_text,
            structure=request.structure,
            rules=request.rules,
            template=request.template
        )
        
        if result.get("error"):
            return ExtractionResponse(
                success=False,
                error=result["error"]
            )
        
        return ExtractionResponse(
            success=True,
            extracted_data=result.get("extracted_data", {})
        )
        
    except Exception as e:
        logger.error(f"Error in extract_structured_data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )


@router.post(
    "/import-file",
    summary="Import file with complete workflow: OCR → Policy → Extraction",
    description="Single endpoint that handles file upload, OCR extraction, policy check, and field extraction"
)
async def import_file(
    file: UploadFile = File(...),
    template: str = "general",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete import workflow in ONE call:
    1. Extract text from file via OCR
    2. Check policy violations
    3. If approved, extract structured fields
    4. Return combined result
    """
    return await _import_file_impl(
        file=file,
        template=template,
        current_user=current_user,
        db=db,
    )


@router.get(
    "/health",
    summary="Health check for policy checker service",
    description="Verify that policy checker and dependencies are operational"
)
async def health_check():
    """
    Check if the policy checker service and its dependencies are working.
    """
    try:
        # Test Gemini connection
        test_result = policy_service.check_policy_for_text("This is a test.")
        
        if test_result.get("error"):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "error": "LLM service unavailable",
                    "details": test_result.get("error")
                }
            )
        
        return {
            "status": "healthy",
            "service": "policy_checker",
            "llm_provider": "gemini",
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# ===========================
# PUBLIC ALIASES (/api/*)
# ===========================
# These mirror selected endpoints so the frontend can call /api/... directly.

@router_api.post(
    "/import-file",
    summary="(Alias) Import file with complete workflow: OCR → Policy → Extraction",
    include_in_schema=False,
)
async def import_file_alias(
    file: UploadFile = File(...),
    template: str = "general",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Reuse the shared implementation
    return await _import_file_impl(
        file=file,
        template=template,
        current_user=current_user,
        db=db,
    )


@router_api.get(
    "/health",
    summary="(Alias) Health check for policy checker service",
    include_in_schema=False,
)
async def health_check_alias():
    try:
        test_result = policy_service.check_policy_for_text("This is a test.")
        if test_result.get("error"):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "error": "LLM service unavailable",
                    "details": test_result.get("error")
                }
            )
        return {
            "status": "healthy",
            "service": "policy_checker",
            "llm_provider": "gemini",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )

