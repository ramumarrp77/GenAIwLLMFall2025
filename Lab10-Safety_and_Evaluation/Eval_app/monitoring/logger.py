"""
Logging interactions to Snowflake
"""

from snowflake.snowpark.context import get_active_session

session = get_active_session()

def create_logging_table():
    """Create table for logging interactions"""
    session.sql("""
    CREATE TABLE IF NOT EXISTS llm_interactions (
        id NUMBER AUTOINCREMENT,
        timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
        input_text VARCHAR,
        output_text VARCHAR,
        input_tokens NUMBER,
        output_tokens NUMBER,
        latency_seconds FLOAT,
        cost FLOAT,
        validation_status VARCHAR,
        policy_status VARCHAR,
        PRIMARY KEY (id)
    )
    """).collect()

def log_interaction(input_text: str, output_text: str, metrics: dict, 
                   validation_status: str, policy_status: str):
    """Log interaction to Snowflake table"""
    try:
        escaped_input = input_text.replace("'", "''")
        escaped_output = output_text.replace("'", "''")
        
        session.sql(f"""
        INSERT INTO llm_interactions 
        (input_text, output_text, input_tokens, output_tokens, latency_seconds, cost, validation_status, policy_status)
        VALUES (
            '{escaped_input}',
            '{escaped_output}',
            {metrics['input_tokens']},
            {metrics['output_tokens']},
            {metrics['latency_seconds']},
            {metrics['total_cost']},
            '{validation_status}',
            '{policy_status}'
        )
        """).collect()
        return True
    except Exception as e:
        print(f"Logging error: {e}")
        return False