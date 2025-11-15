"""
Database Tools - RAG and Snowflake Operations
Uses same RAG logic as your RAGAgent
"""

import snowflake.connector
from snowflake.connector import DictCursor
import json

class DatabaseTools:
    """
    Database operations tools
    Uses same RAG pattern from your existing RAGAgent
    """
    
    def __init__(self, config: dict):
        self.config = config
        print("[DATABASE TOOLS] Initialized")
    
    def search_reviews_rag(self, query: str) -> dict:
        """
        RAG: Search reviews using vector similarity
        EXACT same logic as your execute_rag_query
        """
        print(f"\n[DATABASE TOOL] search_reviews_rag")
        print(f"[DATABASE TOOL] Query: {query}")
        
        try:
            conn = snowflake.connector.connect(**self.config)
            cursor = conn.cursor()
            
            print(f"[DATABASE TOOL] Generating query embedding...")
            
            # EXACT same RAG query from your code
            escaped_query = query.replace("'", "''")
            
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
                  AND VECTOR_COSINE_SIMILARITY(REVIEW_EMBEDDINGS::VECTOR(FLOAT, 1024), uq.query_embedding) > 0.3
                ORDER BY similarity_score DESC
                LIMIT 5
            )
            SELECT 
                LISTAGG(REVIEWTITLE || ' (Rating: ' || RATINGSCORE || ') - ' || REVIEWDESCRIPTION, ' | ') 
                WITHIN GROUP (ORDER BY similarity_score DESC) as retrieved_reviews
            FROM relevant_reviews
            """
            
            print(f"[DATABASE TOOL] Performing vector similarity search...")
            cursor.execute(rag_query)
            result = cursor.fetchone()
            retrieved_reviews = result[0] if result and result[0] else "No relevant reviews found"
            
            cursor.close()
            conn.close()
            
            print(f"[DATABASE TOOL] ✅ Retrieved relevant reviews")
            print(f"[DATABASE TOOL]    Preview: {retrieved_reviews[:100]}...")
            
            return {
                "success": True,
                "retrieved_reviews": retrieved_reviews
            }
            
        except Exception as e:
            print(f"[DATABASE TOOL] ❌ Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def analyze_sentiment(self, topic: str) -> dict:
        """Analyze sentiment for a specific topic"""
        print(f"\n[DATABASE TOOL] analyze_sentiment")
        print(f"[DATABASE TOOL] Topic: {topic}")
        
        try:
            conn = snowflake.connector.connect(**self.config)
            cursor = conn.cursor(DictCursor)
            
            query = f"""
            SELECT 
                RATINGSCORE,
                COUNT(*) as count,
                AVG(RATINGSCORE) as avg_rating
            FROM LAB_DB.PUBLIC.IPHONE_TABLE
            WHERE LOWER(REVIEWDESCRIPTION) LIKE '%{topic.lower()}%'
            GROUP BY RATINGSCORE
            ORDER BY RATINGSCORE DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            total = sum(r['COUNT'] for r in results)
            positive = sum(r['COUNT'] for r in results if r['RATINGSCORE'] >= 4)
            negative = sum(r['COUNT'] for r in results if r['RATINGSCORE'] <= 2)
            
            print(f"[DATABASE TOOL] ✅ Analyzed {total} reviews")
            print(f"[DATABASE TOOL]    Positive: {positive}, Negative: {negative}")
            
            return {
                "success": True,
                "total_reviews": total,
                "positive_count": positive,
                "negative_count": negative,
                "sentiment": "positive" if positive > negative else "negative",
                "details": results
            }
            
        except Exception as e:
            print(f"[DATABASE TOOL] ❌ Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_table_info(self) -> dict:
        """Get database table information"""
        print(f"\n[DATABASE TOOL] get_table_info")
        
        try:
            conn = snowflake.connector.connect(**self.config)
            cursor = conn.cursor(DictCursor)
            
            # Get tables
            cursor.execute("SHOW TABLES")
            tables = [row['name'] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            print(f"[DATABASE TOOL] ✅ Retrieved {len(tables)} tables")
            
            return {
                "success": True,
                "tables": tables
            }
            
        except Exception as e:
            print(f"[DATABASE TOOL] ❌ Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def query_database(self, sql: str) -> dict:
        """Execute SQL query on Snowflake"""
        print(f"\n[DATABASE TOOL] query_database")
        print(f"[DATABASE TOOL] SQL: {sql[:100]}...")
        
        try:
            conn = snowflake.connector.connect(**self.config)
            cursor = conn.cursor(DictCursor)
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            print(f"[DATABASE TOOL] ✅ Returned {len(results)} rows")
            
            return {
                "success": True,
                "rows": results,
                "row_count": len(results)
            }
        except Exception as e:
            print(f"[DATABASE TOOL] ❌ Error: {str(e)}")
            return {"success": False, "error": str(e)}