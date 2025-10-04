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

def execute_sentiment_analysis(query_text: str, keywords: list = None) -> str:
    """Execute sentiment analysis using Snowflake SENTIMENT() with multiple keywords"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        
        if keywords and len(keywords) > 0:
            escaped_keywords = [kw.replace("'", "''") for kw in keywords]
            ilike_conditions = " OR ".join([f"REVIEWDESCRIPTION ILIKE '%{kw}%'" for kw in escaped_keywords])
            where_clause = f"WHERE {ilike_conditions}"
        else:
            escaped_query = query_text.replace("'", "''")
            where_clause = f"WHERE REVIEWDESCRIPTION ILIKE '%{escaped_query}%'"
        
        sentiment_query = f"""
        SELECT 
            SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) as sentiment_score,
            CASE 
                WHEN SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) > 0.3 THEN 'Positive'
                WHEN SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) < -0.3 THEN 'Negative'
                ELSE 'Neutral'
            END as sentiment_category,
            COUNT(*) as review_count
        FROM LAB_DB.PUBLIC.IPHONE_TABLE
        {where_clause}
        GROUP BY sentiment_score, sentiment_category
        ORDER BY review_count DESC
        LIMIT 20
        """
        
        cursor.execute(sentiment_query)
        results = cursor.fetchall()
        
        if not results:
            return "No sentiment data found"
        
        positive = sum(r[2] for r in results if r[1] == 'Positive')
        negative = sum(r[2] for r in results if r[1] == 'Negative')
        neutral = sum(r[2] for r in results if r[1] == 'Neutral')
        total = positive + negative + neutral
        
        if total > 0:
            output = f"Sentiment Analysis (Total: {total} reviews):\n"
            output += f"Positive: {positive} ({positive/total*100:.1f}%)\n"
            output += f"Negative: {negative} ({negative/total*100:.1f}%)\n"
            output += f"Neutral: {neutral} ({neutral/total*100:.1f}%)"
        else:
            output = "No sentiment data"
        
        return output
    except Exception as e:
        return f"Sentiment error: {e}"
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



def execute_cortex_analyst_query(question: str) -> str:
    """Execute Cortex Analyst query using existing semantic model"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        escaped_question = question.replace("'", "''")
        
        analyst_query = f"""
        SELECT SNOWFLAKE.CORTEX.ANALYST(
            'IPHONE_ANALYSIS_LAB3',
            '{escaped_question}'
        ) as result
        """
        
        cursor.execute(analyst_query)
        result = cursor.fetchone()
        return result[0] if result else "No analyst results"
    except Exception as e:
        return f"Cortex Analyst error: {e}"
    finally:
        conn.close()

def execute_cortex_search_quality(search_query: str) -> str:
    """Execute Cortex Search for quality analysis"""
    conn = get_snowflake_connection()
    if not conn:
        return "Connection failed"
    
    try:
        cursor = conn.cursor()
        escaped_query = search_query.replace('"', '\\"')
        
        search_sql = f"""
        SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'LAB_DB.PUBLIC.LAB3_CORTEX_SEARCH',
            '{{"query": "{escaped_query}", "limit": 10, "columns": ["REVIEWDESCRIPTION", "RATINGSCORE", "REVIEWTITLE"]}}'
        ) AS result
        """
        
        cursor.execute(search_sql)
        result = cursor.fetchone()
        
        if result and result[0]:
            import json
            search_data = json.loads(result[0]) if isinstance(result[0], str) else result[0]
            
            reviews = []
            if 'results' in search_data:
                for item in search_data['results']:
                    reviews.append(f"{item.get('REVIEWTITLE', 'N/A')} (Rating: {item.get('RATINGSCORE', 'N/A')}) - {item.get('REVIEWDESCRIPTION', 'N/A')}")
            
            return " | ".join(reviews) if reviews else "No results"
        
        return "No search results"
    except Exception as e:
        return f"Cortex Search error: {e}"
    finally:
        conn.close()