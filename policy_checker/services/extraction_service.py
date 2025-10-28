"""
Extraction Service - Handles field extraction from text using LLM
"""

import json
from typing import Dict
from ..clients.gemini_client import GeminiClient


class ExtractionService:
    """Service for extracting structured data from text"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
    
    def extract_fields_from_text(
        self,
        text: str,
        fields_to_extract: Dict[str, Dict]
    ) -> Dict:
        """
        Extract structured fields from text using LLM.
        
        Args:
            text: Document text (from OCR)
            fields_to_extract: Dict of field definitions
                Example:
                {
                    "policy_number": {
                        "type": "string",
                        "format": "POL-XXXXXX"
                    },
                    "amount": {
                        "type": "number"
                    },
                    "date": {
                        "type": "date",
                        "format": "YYYY-MM-DD"
                    }
                }
        
        Returns:
            {
                "extracted_data": dict,
                "confidence_scores": dict,
                "fields_extracted": int,
                "fields_empty": int,
                "error": str | None
            }
        """
        # Build prompt
        fields_definition = json.dumps(fields_to_extract, indent=2)
        
        prompt = f"""Extract structured data from this document text.

Expected fields (with types and formats):
{fields_definition}

Document text:
{text[:10000]}

Instructions:
- Extract the exact values matching the field definitions
- Follow the specified format for each field
- For dates, convert to YYYY-MM-DD format
- For numbers, extract numeric value only (no currency symbols)
- If a field cannot be found, set its value to null
- Provide confidence score (0.0 to 1.0) for each field

Respond ONLY in valid JSON format (no markdown):
{{
    "extracted_data": {{
        "field_name": "extracted_value_or_null",
        ...
    }},
    "confidence_scores": {{
        "field_name": 0.95,
        ...
    }}
}}
"""
        
        # Call LLM
        response = self.gemini_client.call_gemini(prompt, max_tokens=2048)
        
        # Check for errors
        if "error" in response:
            return {
                "extracted_data": {},
                "confidence_scores": {},
                "fields_extracted": 0,
                "fields_empty": len(fields_to_extract),
                "error": response["error"]
            }
        
        # Parse response
        try:
            result_text = self._extract_json_from_response(response)
            result = json.loads(result_text)
            
            extracted_data = result.get("extracted_data", {})
            confidence_scores = result.get("confidence_scores", {})
            
            # Count extracted vs empty
            fields_extracted = sum(1 for v in extracted_data.values() if v is not None)
            fields_empty = len(extracted_data) - fields_extracted
            
            return {
                "extracted_data": extracted_data,
                "confidence_scores": confidence_scores,
                "fields_extracted": fields_extracted,
                "fields_empty": fields_empty,
                "error": None
            }
        except Exception as e:
            return {
                "extracted_data": {},
                "confidence_scores": {},
                "fields_extracted": 0,
                "fields_empty": len(fields_to_extract),
                "error": f"Failed to parse extraction response: {str(e)}"
            }
    
    def _extract_json_from_response(self, response: Dict) -> str:
        """Extract JSON from Gemini response (handles markdown)"""
        if "candidates" not in response or len(response["candidates"]) == 0:
            raise ValueError("No candidates in response")
        
        text = response["candidates"][0]["content"]["parts"][0]["text"]
        
        # Remove markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        return text