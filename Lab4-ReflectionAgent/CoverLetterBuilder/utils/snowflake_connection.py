# Snowflake connection and Cortex LLM utilities
# Using regular snowflake.connector (not snowpark)

import snowflake.connector
from config import SNOWFLAKE_CONFIG, LLM_MODEL

# Global connection variable
_connection = None

def get_connection():
    """Get or create Snowflake connection"""
    global _connection
    
    if _connection is None or _connection.is_closed():
        print("Creating Snowflake connection...")
        _connection = snowflake.connector.connect(
            account=SNOWFLAKE_CONFIG['account'],
            user=SNOWFLAKE_CONFIG['user'],
            password=SNOWFLAKE_CONFIG['password'],
            warehouse=SNOWFLAKE_CONFIG['warehouse'],
            database=SNOWFLAKE_CONFIG['database'],
            schema=SNOWFLAKE_CONFIG['schema'],
            role=SNOWFLAKE_CONFIG['role']
        )
        print("✓ Connection created")
    
    return _connection


def call_llm(prompt, model=LLM_MODEL):
    """
    Call Snowflake Cortex LLM
    Simple wrapper - just pass prompt, get response
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Escape single quotes for SQL
    escaped_prompt = prompt.replace("'", "''")
    
    # Call Cortex
    query = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{model}',
        '{escaped_prompt}'
    ) AS response
    """
    
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    
    return result[0] if result else ""


def close_connection():
    """Close Snowflake connection"""
    global _connection
    if _connection and not _connection.is_closed():
        _connection.close()
        _connection = None
        print("✓ Connection closed")