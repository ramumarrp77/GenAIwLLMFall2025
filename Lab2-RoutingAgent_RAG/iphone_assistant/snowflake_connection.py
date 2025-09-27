import snowflake.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_snowflake_connection():
    """Get Snowflake connection using PAT token"""
    try:
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),  # PAT token
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
            role=os.getenv("SNOWFLAKE_ROLE")
        )
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def call_cortex_complete(prompt: str, model: str = 'claude-3-5-sonnet') -> str:
    """Call Snowflake Cortex Complete function"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        escaped_prompt = prompt.replace("'", "''")
        
        query = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            '{model}',
            '{escaped_prompt}'
        ) as result
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result else "No result"
    except Exception as e:
        return f"Error with model {model}: {e}"
    finally:
        conn.close()

def execute_rag_query(query_text: str, similarity_threshold: float = 0.3) -> str:
    """Execute RAG query on iPhone reviews table"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        escaped_query = query_text.replace("'", "''")
        
        rag_query = f"""
        WITH user_query AS (
            SELECT '{escaped_query}' as search_text,
                   SNOWFLAKE.CORTEX.EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', '{escaped_query}') as query_embedding
        ),
        relevant_reviews AS (
            SELECT
                REVIEWTITLE,
                REVIEWDESCRIPTION,
                RATINGSCORE,
                VECTOR_COSINE_SIMILARITY(
                    REVIEW_EMBEDDINGS::VECTOR(FLOAT, 1024),
                    uq.query_embedding
                ) AS similarity_score
            FROM LAB_DB.PUBLIC.IPHONE_TABLE it
            CROSS JOIN user_query uq
            WHERE REVIEW_EMBEDDINGS IS NOT NULL
              AND VECTOR_COSINE_SIMILARITY(REVIEW_EMBEDDINGS::VECTOR(FLOAT, 1024), uq.query_embedding) > {similarity_threshold}
            ORDER BY similarity_score DESC
            LIMIT 5
        )
        SELECT 
            LISTAGG(REVIEWTITLE || ' (Rating: ' || RATINGSCORE || ') - ' || REVIEWDESCRIPTION, ' | ') 
            WITHIN GROUP (ORDER BY similarity_score DESC) as retrieved_reviews
        FROM relevant_reviews
        """
        
        cursor.execute(rag_query)
        result = cursor.fetchone()
        return result[0] if result and result[0] else "No relevant reviews found"
    except Exception as e:
        return f"RAG query error: {e}"
    finally:
        conn.close()

def test_connection():
    """Test Snowflake connection"""
    conn = get_snowflake_connection()
    if conn:
        conn.close()
        return True
    return False