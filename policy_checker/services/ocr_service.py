"""
OCR Service - Handles text extraction from files
"""

from typing import Dict
from ..clients.google_ocr_client import GoogleOCRClient
from ..constants import STATUS_SUCCESS, STATUS_SERVICE_UNAVAILABLE, STATUS_NO_CONTENT


class OCRService:
    """Service for OCR text extraction"""
    
    def __init__(self):
        self.ocr_client = GoogleOCRClient()
    
    def extract_text_from_file(self, file_bytes: bytes) -> Dict:
        """
        Extract text from file using OCR.
        
        Args:
            file_bytes: Raw file bytes (PDF, image, etc.)
        
        Returns:
            {
                "status": "success" | "service_unavailable" | "no_content",
                "text": str | None,
                "text_length": int,
                "error": str | None
            }
        """
        # Call OCR client
        response = self.ocr_client.call_vision_api(file_bytes)
        
        # Check for errors
        if "error" in response:
            return {
                "status": STATUS_SERVICE_UNAVAILABLE,
                "text": None,
                "text_length": 0,
                "error": response["error"]
            }
        
        # Parse response
        if "responses" in response and len(response["responses"]) > 0:
            response_data = response["responses"][0]
            
            # Check for API errors
            if "error" in response_data:
                error_msg = response_data["error"].get("message", "Unknown OCR error")
                return {
                    "status": STATUS_SERVICE_UNAVAILABLE,
                    "text": None,
                    "text_length": 0,
                    "error": f"OCR API error: {error_msg}"
                }
            
            # Extract text
            if "fullTextAnnotation" in response_data:
                extracted_text = response_data["fullTextAnnotation"]["text"]
                
                if not extracted_text or len(extracted_text.strip()) == 0:
                    return {
                        "status": STATUS_NO_CONTENT,
                        "text": None,
                        "text_length": 0,
                        "error": "No text found in document"
                    }
                
                return {
                    "status": STATUS_SUCCESS,
                    "text": extracted_text,
                    "text_length": len(extracted_text),
                    "error": None
                }
            else:
                return {
                    "status": STATUS_NO_CONTENT,
                    "text": None,
                    "text_length": 0,
                    "error": "No text detected in image"
                }
        else:
            return {
                "status": STATUS_SERVICE_UNAVAILABLE,
                "text": None,
                "text_length": 0,
                "error": "Invalid OCR API response"
            }