"""
Snowflake Cortex helper functions
"""

from snowflake.snowpark.context import get_active_session
import json

session = get_active_session()

def call_cortex(prompt: str, model: str = "llama3.1-70b") -> str:
    """Call Snowflake Cortex COMPLETE function"""
    escaped_prompt = prompt.replace("'", "''")
    query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{escaped_prompt}') as response"
    result = session.sql(query).collect()
    return result[0]['RESPONSE']

def call_cortex_structured(prompt: str, schema: dict, model: str = "mistral-large2") -> str:
    """Call Cortex with structured JSON output using response_format"""
    escaped_prompt = prompt.replace("'", "''")
    schema_json = json.dumps(schema).replace("'", "''")
    
    query = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{model}',
        PARSE_JSON('[{{"role": "user", "content": "{escaped_prompt}"}}]'),
        OBJECT_CONSTRUCT(
            'response_format', 
            OBJECT_CONSTRUCT(
                'type', 'json_object',
                'schema', PARSE_JSON('{schema_json}')
            )
        )
    ) as response
    """
    
    result = session.sql(query).collect()
    return result[0]['RESPONSE']