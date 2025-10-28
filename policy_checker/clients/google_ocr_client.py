"""
Google Cloud Vision API Client - OCR wrapper
"""

import base64
import requests
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image
from typing import Dict

from ..config import (
    GOOGLE_CLOUD_VISION_API_KEY,
    GOOGLE_CLOUD_VISION_ENDPOINT,
    OCR_TIMEOUT
)


class GoogleOCRClient:
    """Wrapper for Google Cloud Vision API"""
    
    def __init__(self):
        self.api_key = GOOGLE_CLOUD_VISION_API_KEY
        self.endpoint = f"{GOOGLE_CLOUD_VISION_ENDPOINT}?key={self.api_key}"
    
    def _pdf_to_images(self, pdf_bytes: bytes) -> list:
        """Convert PDF pages to images"""
        images = []
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Render page to image at 300 DPI
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                img_bytes = pix.tobytes("png")
                images.append(img_bytes)
            doc.close()
        except Exception as e:
            print(f"PDF conversion error: {e}")
        return images
    
    def call_vision_api(self, file_bytes: bytes) -> Dict:
        """
        Makes API call to Google Cloud Vision.
        Converts PDF to images first if needed.
        
        Args:
            file_bytes: Raw file bytes
        
        Returns:
            Raw API response dict or error dict
        """
        if not self.api_key:
            return {
                "error": "Google Cloud Vision API key not configured"
            }
        
        try:
            # Check if it's a PDF
            if file_bytes[:4] == b'%PDF':
                # Convert PDF to images
                images = self._pdf_to_images(file_bytes)
                if not images:
                    return {"error": "Failed to convert PDF to images"}
                # Use first page for OCR
                file_bytes = images[0]
            
            # Encode to base64
            encoded_content = base64.b64encode(file_bytes).decode('utf-8')
            
            # Build payload
            payload = {
                "requests": [{
                    "image": {"content": encoded_content},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
                }]
            }
            
            # Make request
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=OCR_TIMEOUT
            )
            
            if response.status_code != 200:
                return {
                    "error": f"API error: {response.status_code} - {response.text}"
                }
            
            return response.json()
        
        except requests.exceptions.Timeout:
            return {"error": "Request timed out"}
        
        except Exception as e:
            return {"error": f"API call failed: {str(e)}"}