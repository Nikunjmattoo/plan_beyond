"""
Policy Service - Handles policy violation checking
"""

import json
import html
from typing import Dict, List
from ..clients.gemini_client import GeminiClient
from ..constants import POLICY_BREACH_CODES


class PolicyService:
    """Service for policy violation checking"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
    
    def check_policy_for_text(self, text: str) -> Dict:
        """
        Check if text violates policy (for imported files).
        
        Args:
            text: Extracted text from document
        
        Returns:
            {
                "approved": bool,
                "reason": str | None,
                "policy_breach_code": str | None,
                "risk_score": int,
                "error": str | None
            }
        """
        # Build prompt
        prompt = f"""You are a content policy scanner for a digital vault service.

Analyze this text for policy violations. Check for:
- Terrorism planning or support
- Weapons/ammunition inventories or trafficking
- Violence or threats
- Illegal drug operations
- Human trafficking
- Money laundering
- Hate speech or extremism
- Child abuse material
- Self-harm instructions
- Explosives or dangerous materials

Text to analyze:
{text[:5000]}

Respond ONLY in valid JSON format (no markdown):
{{
    "approved": true or false,
    "reason": "brief explanation if rejected, null if approved",
    "policy_breach_code": "WEAPONS or TERRORISM or VIOLENCE etc if violated, null if approved",
    "risk_score": 0-100
}}
"""
        
        # Call LLM
        response = self.gemini_client.call_gemini(prompt)
        
        # Check for errors
        if "error" in response:
            return {
                "approved": False,
                "reason": None,
                "policy_breach_code": None,
                "risk_score": 0,
                "error": response["error"]
            }
        
        # Parse response
        try:
            result_text = self._extract_json_from_response(response)
            result = json.loads(result_text)
            # Sanitize reason to prevent XSS
            reason = result.get("reason")
            if reason:
                reason = html.escape(reason)

            return {
                "approved": result.get("approved", False),
                "reason": reason,
                "policy_breach_code": result.get("policy_breach_code"),
                "risk_score": result.get("risk_score", 0),
                "error": None
            }
        except Exception as e:
            return {
                "approved": False,
                "reason": None,
                "policy_breach_code": None,
                "risk_score": 0,
                "error": f"Failed to parse policy check response: {str(e)}"
            }
    
    def check_policy_for_fields(self, fields: Dict[str, str]) -> Dict:
        """
        Check if form fields violate policy.
        
        Args:
            fields: Dict of field_name: field_value
        
        Returns:
            {
                "overall_approved": bool,
                "field_results": [
                    {
                        "field_name": str,
                        "approved": bool,
                        "reason": str | None,
                        "policy_breach_code": str | None,
                        "suggested_action": str | None
                    }
                ],
                "error": str | None
            }
        """
        # Build fields text
        fields_text = "\n\n".join([
            f"Field: {name}\nValue: {value}"
            for name, value in fields.items()
        ])
        
        # Build prompt
        prompt = f"""You are a content policy scanner for a digital vault service.

Analyze these form fields for policy violations. Check for:
- Terrorism, weapons, violence
- Illegal drugs, human trafficking
- Hate speech, child abuse
- Self-harm content

Fields to check:
{fields_text}

Respond ONLY in valid JSON format (no markdown):
{{
    "overall_approved": true or false,
    "field_results": [
        {{
            "field_name": "exact_field_name",
            "approved": true or false,
            "reason": "explanation if rejected, null if approved",
            "policy_breach_code": "WEAPONS or TERRORISM etc if violated, null if approved",
            "suggested_action": "how to fix if rejected, null if approved"
        }}
    ]
}}
"""
        
        # Call LLM
        response = self.gemini_client.call_gemini(prompt)
        
        # Check for errors
        if "error" in response:
            return {
                "overall_approved": False,
                "field_results": [],
                "error": response["error"]
            }
        
        # Parse response
        try:
            result_text = self._extract_json_from_response(response)
            result = json.loads(result_text)
            
            return {
                "overall_approved": result.get("overall_approved", False),
                "field_results": result.get("field_results", []),
                "error": None
            }
        except Exception as e:
            return {
                "overall_approved": False,
                "field_results": [],
                "error": f"Failed to parse policy check response: {str(e)}"
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