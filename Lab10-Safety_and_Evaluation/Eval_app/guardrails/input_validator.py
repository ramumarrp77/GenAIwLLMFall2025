"""
Input validation using Pydantic
"""

from pydantic import BaseModel, Field, field_validator, ValidationError
import re

class SecureUserInput(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    user_id: str = Field(default="system", pattern=r'^[a-zA-Z0-9_-]+$')
    
    @field_validator('query')
    @classmethod
    def detect_injection(cls, v: str) -> str:
        patterns = [
            r'ignore\s+(all\s+)?previous\s+instructions?',
            r'disregard.*instructions?',
            r'forget\s+everything',
            r'you\s+are\s+now',
            r'reveal.*prompt',
        ]
        for pattern in patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Input contains disallowed patterns')
        return v.strip()

def validate_input(query: str) -> dict:
    """Validate user input and return result"""
    try:
        validated = SecureUserInput(query=query)
        return {
            "valid": True,
            "query": validated.query,
            "message": "Input validation passed"
        }
    except ValidationError as e:
        return {
            "valid": False,
            "query": query,
            "message": e.errors()[0]['msg']
        }