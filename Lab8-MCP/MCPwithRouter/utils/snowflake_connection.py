import snowflake.connector
import os
from dotenv import load_dotenv
from snowflake.connector import DictCursor

load_dotenv()

SNOWFLAKE_CONFIG = {
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'database': os.getenv('SNOWFLAKE_DATABASE'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA'),
    'role': os.getenv('SNOWFLAKE_ROLE', 'PUBLIC')
}

def get_snowflake_connection():
    """Get Snowflake connection"""
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

def execute_cortex_query(prompt: str, model: str = "mistral-large2") -> str:
    """
    Execute a Snowflake Cortex query
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        query = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            '{model}',
            '{prompt.replace("'", "''")}'
        ) as response
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        response = result[0] if result else ""
        
        cursor.close()
        conn.close()
        
        return response
        
    except Exception as e:
        return f"Error: {str(e)}"

def execute_query(sql: str) -> list:
    """Execute SQL query and return results"""
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor(DictCursor)
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        return [{"error": str(e)}]