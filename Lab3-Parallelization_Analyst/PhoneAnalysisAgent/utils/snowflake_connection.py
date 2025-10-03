import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_snowflake_connection():
    """Get Snowflake connection using PAT token"""
    try:
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
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
        return f"Error: {e}"
    finally:
        conn.close()

def execute_sentiment_analysis(query_text: str) -> str:
    """Execute sentiment analysis using Snowflake SENTIMENT() function"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        escaped_query = query_text.replace("'", "''")
        
        sentiment_query = f"""
        SELECT 
            SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) as sentiment_score,
            CASE 
                WHEN SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) > 0.3 THEN 'Positive'
                WHEN SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) < -0.3 THEN 'Negative'
                ELSE 'Neutral'
            END as sentiment_category,
            RATINGSCORE,
            COUNT(*) as review_count
        FROM LAB_DB.PUBLIC.IPHONE_TABLE
        WHERE REVIEWDESCRIPTION ILIKE '%{escaped_query}%'
        GROUP BY sentiment_score, sentiment_category, RATINGSCORE
        ORDER BY review_count DESC
        LIMIT 10
        """
        
        cursor.execute(sentiment_query)
        results = cursor.fetchall()
        
        if not results:
            return "No sentiment data found"
        
        # Format results
        output = "Sentiment Analysis Results:\n"
        positive = sum(r[3] for r in results if r[1] == 'Positive')
        negative = sum(r[3] for r in results if r[1] == 'Negative')
        neutral = sum(r[3] for r in results if r[1] == 'Neutral')
        total = positive + negative + neutral
        
        if total > 0:
            output += f"Positive: {positive} ({positive/total*100:.1f}%), "
            output += f"Negative: {negative} ({negative/total*100:.1f}%), "
            output += f"Neutral: {neutral} ({neutral/total*100:.1f}%)"
        else:
            output += "No sentiment data available"
        
        return output
    except Exception as e:
        return f"Sentiment analysis error: {e}"
    finally:
        conn.close()

def execute_feature_search(query_text: str) -> str:
    """Execute feature search using vector similarity"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        escaped_query = query_text.replace("'", "''")
        
        feature_query = f"""
        WITH user_query AS (
            SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', '{escaped_query}') as query_embedding
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
              AND VECTOR_COSINE_SIMILARITY(REVIEW_EMBEDDINGS::VECTOR(FLOAT, 1024), uq.query_embedding) > 0.3
            ORDER BY similarity_score DESC
            LIMIT 10
        )
        SELECT 
            LISTAGG(REVIEWTITLE || ' (Rating: ' || RATINGSCORE || ') - ' || REVIEWDESCRIPTION, ' | ') 
            WITHIN GROUP (ORDER BY similarity_score DESC) as feature_reviews
        FROM relevant_reviews
        """
        
        cursor.execute(feature_query)
        result = cursor.fetchone()
        return result[0] if result and result[0] else "No feature-related reviews found"
    except Exception as e:
        return f"Feature search error: {e}"
    finally:
        conn.close()

def execute_quality_search(query_text: str) -> str:
    """Get reviews for quality analysis"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        escaped_query = query_text.replace("'", "''")
        
        quality_query = f"""
        SELECT 
            LISTAGG(REVIEWTITLE || ' - ' || REVIEWDESCRIPTION, ' | ') 
            WITHIN GROUP (ORDER BY RATINGSCORE ASC) as quality_reviews
        FROM (
            SELECT REVIEWTITLE, REVIEWDESCRIPTION, RATINGSCORE
            FROM LAB_DB.PUBLIC.IPHONE_TABLE
            WHERE REVIEWDESCRIPTION ILIKE '%{escaped_query}%'
              AND RATINGSCORE <= 3
            ORDER BY RATINGSCORE ASC
            LIMIT 10
        )
        """
        
        cursor.execute(quality_query)
        result = cursor.fetchone()
        return result[0] if result and result[0] else "No quality issues found"
    except Exception as e:
        return f"Quality search error: {e}"
    finally:
        conn.close()
import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_snowflake_connection():
    """Get Snowflake connection using PAT token"""
    try:
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
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
        return f"Error: {e}"
    finally:
        conn.close()

def execute_sentiment_analysis(query_text: str) -> str:
    """Execute sentiment analysis using Snowflake SENTIMENT() function"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        escaped_query = query_text.replace("'", "''")
        
        sentiment_query = f"""
        SELECT 
            SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) as sentiment_score,
            CASE 
                WHEN SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) > 0.3 THEN 'Positive'
                WHEN SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) < -0.3 THEN 'Negative'
                ELSE 'Neutral'
            END as sentiment_category,
            RATINGSCORE,
            COUNT(*) as review_count
        FROM LAB_DB.PUBLIC.IPHONE_TABLE
        WHERE REVIEWDESCRIPTION ILIKE '%{escaped_query}%'
        GROUP BY sentiment_score, sentiment_category, RATINGSCORE
        ORDER BY review_count DESC
        LIMIT 10
        """
        
        cursor.execute(sentiment_query)
        results = cursor.fetchall()
        
        if not results:
            return "No sentiment data found"
        
        # Format results
        output = "Sentiment Analysis Results:\n"
        positive = sum(r[3] for r in results if r[1] == 'Positive')
        negative = sum(r[3] for r in results if r[1] == 'Negative')
        neutral = sum(r[3] for r in results if r[1] == 'Neutral')
        total = positive + negative + neutral
        
        output += f"Positive: {positive} ({positive/total*100:.1f}%), "
        output += f"Negative: {negative} ({negative/total*100:.1f}%), "
        output += f"Neutral: {neutral} ({neutral/total*100:.1f}%)"
        
        return output
    except Exception as e:
        return f"Sentiment analysis error: {e}"
    finally:
        conn.close()

def execute_feature_search(query_text: str) -> str:
    """Execute feature search using vector similarity"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        escaped_query = query_text.replace("'", "''")
        
        feature_query = f"""
        WITH user_query AS (
            SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', '{escaped_query}') as query_embedding
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
              AND VECTOR_COSINE_SIMILARITY(REVIEW_EMBEDDINGS::VECTOR(FLOAT, 1024), uq.query_embedding) > 0.3
            ORDER BY similarity_score DESC
            LIMIT 10
        )
        SELECT 
            LISTAGG(REVIEWTITLE || ' (Rating: ' || RATINGSCORE || ') - ' || REVIEWDESCRIPTION, ' | ') 
            WITHIN GROUP (ORDER BY similarity_score DESC) as feature_reviews
        FROM relevant_reviews
        """
        
        cursor.execute(feature_query)
        result = cursor.fetchone()
        return result[0] if result and result[0] else "No feature-related reviews found"
    except Exception as e:
        return f"Feature search error: {e}"
    finally:
        conn.close()