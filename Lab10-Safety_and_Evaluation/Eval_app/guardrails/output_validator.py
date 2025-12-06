"""
Output validation using Pydantic
"""

from pydantic import BaseModel, Field, model_validator, ValidationError
from typing import List, Self

class SafeLLMOutput(BaseModel):
    content: str = Field(max_length=2000)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str] = Field(min_length=1)
    
    @model_validator(mode='after')
    def validate_high_confidence(self) -> Self:
        if self.confidence > 0.8 and len(self.sources) < 2:
            raise ValueError('High confidence requires multiple sources')
        return self

def validate_output(output_json: str) -> dict:
    """Validate LLM output structure"""
    try:
        validated = SafeLLMOutput.model_validate_json(output_json)
        return {
            "valid": True,
            "output": validated.model_dump(),
            "message": "Output validation passed"
        }
    except ValidationError as e:
        return {
            "valid": False,
            "output": None,
            "message": str(e)
        }