"""
LLM-as-a-Judge evaluation
"""

from pydantic import BaseModel, Field
import sys
sys.path.append('utils')
from cortex_helpers import call_cortex_structured

JUDGE_PROMPT = """Evaluate this AI response for {metric} (1-5 scale).

Query: {query}
Response: {response}

Return JSON only."""

class JudgeResult(BaseModel):
    score: int = Field(ge=1, le=5)
    reasoning: str

def evaluate_response(query: str, response: str, metric: str = "helpfulness") -> dict:
    """Evaluate response using LLM-as-a-Judge"""
    try:
        prompt = JUDGE_PROMPT.format(metric=metric, query=query, response=response)
        result = call_cortex_structured(prompt, JudgeResult.model_json_schema())
        evaluation = JudgeResult.model_validate_json(result)
        
        return {
            "score": evaluation.score,
            "reasoning": evaluation.reasoning,
            "metric": metric
        }
    except Exception as e:
        return {
            "score": 0,
            "reasoning": f"Evaluation failed: {str(e)}",
            "metric": metric
        }

COMPARE_PROMPT = """Compare these two responses. Which is better?

Query: {query}
Response A: {response_a}
Response B: {response_b}

Return JSON only."""

class ComparisonResult(BaseModel):
    winner: str = Field(pattern=r'^(A|B|tie)$')
    reasoning: str

def compare_responses(query: str, response_a: str, response_b: str) -> dict:
    """Compare two responses"""
    try:
        prompt = COMPARE_PROMPT.format(query=query, response_a=response_a, response_b=response_b)
        result = call_cortex_structured(prompt, ComparisonResult.model_json_schema())
        comparison = ComparisonResult.model_validate_json(result)
        
        return {
            "winner": comparison.winner,
            "reasoning": comparison.reasoning
        }
    except Exception as e:
        return {
            "winner": "error",
            "reasoning": f"Comparison failed: {str(e)}"
        }