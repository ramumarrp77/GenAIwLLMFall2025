# Snowflake connection and Cortex LLM utilities

from snowflake.snowpark import Session
from config import SNOWFLAKE_CONFIG, LLM_MODEL

# Global session variable
_session = None

def get_session():
    """Get or create Snowflake session"""
    global _session
    
    if _session is None:
        print("Creating Snowflake session...")
        _session = Session.builder.configs(SNOWFLAKE_CONFIG).create()
        print("Session created")
    
    return _session


def call_llm(prompt, model=LLM_MODEL):
    """
    Call Snowflake Cortex LLM
    Simple wrapper - just pass prompt, get response
    """
    session = get_session()
    
    # Escape single quotes for SQL
    escaped_prompt = prompt.replace("'", "''")
    
    # Call Cortex
    query = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{model}',
        '{escaped_prompt}'
    ) AS response
    """
    
    result = session.sql(query).collect()
    return result[0]['RESPONSE']


def close_session():
    """Close Snowflake session"""
    global _session
    if _session:
        _session.close()
        _session = None
        print("Session closed")