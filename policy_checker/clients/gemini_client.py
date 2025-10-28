"""
Gemini LLM API Client - LLM wrapper
"""

import requests
from typing import Dict, Optional

from ..config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_TIMEOUT,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS
)


class GeminiClient:
    """Wrapper for Gemini LLM API"""
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    
    def call_gemini(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict:
        """
        Makes API call to Gemini using X-goog-api-key header.
        
        Args:
            prompt: Text prompt for LLM
            max_tokens: Override default max tokens
            temperature: Override default temperature
        
        Returns:
            Raw API response dict or error dict
        """
        if not self.api_key:
            return {
                "error": "Gemini API key not configured"
            }
        
        try:
            # Build headers (like your working curl command)
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key
            }
            
            # Build payload
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": temperature or LLM_TEMPERATURE,
                    "maxOutputTokens": max_tokens or LLM_MAX_TOKENS
                }
            }
            
            # Make request
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=LLM_TIMEOUT
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