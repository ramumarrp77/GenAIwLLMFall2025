"""
TruLens evaluation wrapper for custom evaluations
"""

from snowflake.snowpark.context import get_active_session

session = get_active_session()

def evaluate_with_cortex_sentiment(text: str) -> float:
    """Evaluate text sentiment using Cortex"""
    try:
        escaped_text = text.replace("'", "''")
        query = f"SELECT SNOWFLAKE.CORTEX.SENTIMENT('{escaped_text}') as sentiment"
        result = session.sql(query).collect()
        return result[0]['SENTIMENT']
    except Exception as e:
        print(f"Sentiment evaluation error: {e}")
        return 0.0

def evaluate_context_relevance(query: str, contexts: list) -> dict:
    """Evaluate if retrieved contexts are relevant to query"""
    try:
        # Simple relevance check using keyword overlap
        query_keywords = set(query.lower().split())
        
        relevance_scores = []
        for ctx in contexts:
            ctx_keywords = set(ctx.lower().split())
            overlap = len(query_keywords.intersection(ctx_keywords))
            score = min(overlap / len(query_keywords), 1.0) if query_keywords else 0.0
            relevance_scores.append(score)
        
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        
        return {
            "metric": "context_relevance",
            "score": round(avg_relevance, 2),
            "individual_scores": relevance_scores
        }
    except Exception as e:
        return {
            "metric": "context_relevance",
            "score": 0.0,
            "error": str(e)
        }

def calculate_token_efficiency(input_tokens: int, output_tokens: int, response_quality: float) -> dict:
    """Calculate token efficiency metrics"""
    total_tokens = input_tokens + output_tokens
    efficiency = response_quality / total_tokens if total_tokens > 0 else 0.0
    
    return {
        "total_tokens": total_tokens,
        "quality_score": response_quality,
        "efficiency": round(efficiency, 6),
        "cost_per_quality_point": round((total_tokens * 0.0002) / response_quality, 6) if response_quality > 0 else 0.0
    }