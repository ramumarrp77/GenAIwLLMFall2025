"""
Analytics and monitoring queries
"""

from snowflake.snowpark.context import get_active_session
import pandas as pd

session = get_active_session()

def get_recent_interactions(limit: int = 10):
    """Get recent interactions"""
    query = f"""
    SELECT 
        timestamp,
        input_text,
        validation_status,
        policy_status,
        latency_seconds,
        cost
    FROM llm_interactions
    ORDER BY timestamp DESC
    LIMIT {limit}
    """
    result = session.sql(query).collect()
    return pd.DataFrame([row.as_dict() for row in result])

def get_aggregate_metrics(days: int = 7):
    """Get aggregate metrics for last N days"""
    query = f"""
    SELECT 
        COUNT(*) as total_interactions,
        AVG(latency_seconds) as avg_latency,
        SUM(cost) as total_cost,
        SUM(CASE WHEN validation_status != 'valid' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as validation_failure_rate,
        SUM(CASE WHEN policy_status != 'compliant' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as policy_block_rate
    FROM llm_interactions
    WHERE timestamp > DATEADD('day', -{days}, CURRENT_TIMESTAMP())
    """
    result = session.sql(query).collect()
    if result:
        return result[0].as_dict()
    return {}

def get_daily_trends(days: int = 7):
    """Get daily trend data"""
    query = f"""
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as interactions,
        AVG(latency_seconds) as avg_latency,
        SUM(cost) as daily_cost
    FROM llm_interactions
    WHERE timestamp > DATEADD('day', -{days}, CURRENT_TIMESTAMP())
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    """
    result = session.sql(query).collect()
    return pd.DataFrame([row.as_dict() for row in result])

def get_blocked_reasons():
    """Get distribution of blocked inputs"""
    query = """
    SELECT 
        policy_status as reason,
        COUNT(*) as count
    FROM llm_interactions
    WHERE policy_status != 'compliant'
    GROUP BY policy_status
    ORDER BY count DESC
    """
    result = session.sql(query).collect()
    return pd.DataFrame([row.as_dict() for row in result])