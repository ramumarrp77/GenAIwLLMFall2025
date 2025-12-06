"""
Query Snowflake AI Observability event table
"""

from snowflake.snowpark.context import get_active_session
import pandas as pd

session = get_active_session()

def get_evaluation_runs(limit: int = 10):
    """Get recent evaluation runs"""
    query = f"""
    SELECT DISTINCT
        run_name,
        MIN(timestamp) as timestamp,
        COUNT(*) as record_count
    FROM SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS
    GROUP BY run_name
    ORDER BY MIN(timestamp) DESC
    LIMIT {limit}
    """
    result = session.sql(query).collect()
    return pd.DataFrame([row.as_dict() for row in result])

def get_evaluation_summary(run_name: str):
    """Get aggregate scores for a specific run"""
    escaped_run = run_name.replace("'", "''")
    query = f"""
    SELECT 
        metric_name,
        AVG(score) as avg_score,
        MIN(score) as min_score,
        MAX(score) as max_score,
        COUNT(*) as record_count
    FROM SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS
    WHERE run_name = '{escaped_run}'
    GROUP BY metric_name
    """
    result = session.sql(query).collect()
    return pd.DataFrame([row.as_dict() for row in result])

def get_record_details(run_name: str, record_index: int = 0):
    """Get detailed evaluation for a specific record"""
    escaped_run = run_name.replace("'", "''")
    query = f"""
    SELECT 
        input_text,
        output_text,
        metric_name,
        score,
        reasoning
    FROM SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS
    WHERE run_name = '{escaped_run}'
    LIMIT 1 OFFSET {record_index}
    """
    result = session.sql(query).collect()
    if result:
        return result[0].as_dict()
    return None

def get_quality_trends(days: int = 7):
    """Get quality trends over time"""
    query = f"""
    SELECT 
        DATE(timestamp) as date,
        metric_name,
        AVG(score) as avg_score
    FROM SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS
    WHERE timestamp > DATEADD('day', -{days}, CURRENT_TIMESTAMP())
    GROUP BY DATE(timestamp), metric_name
    ORDER BY date DESC, metric_name
    """
    result = session.sql(query).collect()
    return pd.DataFrame([row.as_dict() for row in result])