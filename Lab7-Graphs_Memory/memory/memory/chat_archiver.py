"""
Chat archiver - Stores complete chat history AND short-term memory state in Snowflake
"""

import uuid
from datetime import datetime
from typing import List, Dict
import config


class ChatArchiver:
    """
    Stores:
    1. Complete chat history in CHAT_MESSAGES
    2. Current short-term memory state in SHORT_TERM_MEMORY
    """
    
    def __init__(self, snowflake_conn):
        self.conn = snowflake_conn
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Create tables if they don't exist"""
        
        cursor = self.conn.cursor()
        
        # Sessions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS CHAT_SESSIONS (
            session_id VARCHAR PRIMARY KEY,
            user_name VARCHAR,
            title VARCHAR,
            created_at TIMESTAMP,
            last_updated TIMESTAMP,
            message_count INT DEFAULT 0
        )
        """)
        
        # Complete messages archive table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS CHAT_MESSAGES (
            message_id VARCHAR PRIMARY KEY,
            session_id VARCHAR,
            timestamp TIMESTAMP,
            role VARCHAR,
            content TEXT,
            tokens INT,
            was_summarized BOOLEAN DEFAULT FALSE
        )
        """)
        
        # Short-term memory state table - NEW
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS SHORT_TERM_MEMORY (
            session_id VARCHAR,
            message_index INT,
            role VARCHAR,
            content TEXT,
            is_summary BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP,
            PRIMARY KEY (session_id, message_index)
        )
        """)
        
        self.conn.commit()
        cursor.close()
    
    def create_session(self, first_message: str = None) -> str:
        """Create new chat session"""
        
        session_id = str(uuid.uuid4())
        
        # Auto-generate title from first message
        title = "New Chat"
        if first_message:
            title = first_message[:50] + "..." if len(first_message) > 50 else first_message
        
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO CHAT_SESSIONS (session_id, user_name, title, created_at, last_updated, message_count)
        VALUES (%s, %s, %s, %s, %s, 0)
        """, (session_id, config.USER_NAME, title, datetime.now(), datetime.now()))
        
        self.conn.commit()
        cursor.close()
        
        return session_id
    
    def save_message(self, session_id: str, role: str, content: str, tokens: int, was_summarized: bool = False):
        """Save a single message to archive"""
        
        message_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        
        # Insert message
        cursor.execute("""
        INSERT INTO CHAT_MESSAGES (message_id, session_id, timestamp, role, content, tokens, was_summarized)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (message_id, session_id, datetime.now(), role, content, tokens, was_summarized))
        
        # Update session
        cursor.execute("""
        UPDATE CHAT_SESSIONS 
        SET last_updated = %s, 
            message_count = message_count + 1
        WHERE session_id = %s
        """, (datetime.now(), session_id))
        
        self.conn.commit()
        cursor.close()
    
    # ==================== SHORT-TERM MEMORY PERSISTENCE ====================
    
    def save_short_term_state(self, session_id: str, messages: List[Dict], summary: str = None):
        """
        Save current short-term memory state
        Replaces entire state (delete old, insert new)
        """
        
        cursor = self.conn.cursor()
        
        try:
            # Delete old short-term memory for this session
            cursor.execute("""
            DELETE FROM SHORT_TERM_MEMORY WHERE session_id = %s
            """, (session_id,))
            
            message_index = 0
            
            # Save summary if exists
            if summary:
                cursor.execute("""
                INSERT INTO SHORT_TERM_MEMORY (session_id, message_index, role, content, is_summary, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (session_id, message_index, "system", summary, True, datetime.now()))
                message_index += 1
            
            # Save current messages
            for msg in messages:
                cursor.execute("""
                INSERT INTO SHORT_TERM_MEMORY (session_id, message_index, role, content, is_summary, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (session_id, message_index, msg['role'], msg['content'], False, datetime.now()))
                message_index += 1
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error saving short-term memory: {e}")
        finally:
            cursor.close()
    
    def load_short_term_state(self, session_id: str) -> Dict:
        """
        Load short-term memory state for a session
        Returns: {"summary": str or None, "messages": List[Dict]}
        """
        
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT role, content, is_summary
        FROM SHORT_TERM_MEMORY
        WHERE session_id = %s
        ORDER BY message_index ASC
        """, (session_id,))
        
        summary = None
        messages = []
        
        for row in cursor.fetchall():
            role = row[0]
            content = row[1]
            is_summary = row[2]
            
            if is_summary:
                summary = content
            else:
                messages.append({
                    "role": role,
                    "content": content
                })
        
        cursor.close()
        
        return {
            "summary": summary,
            "messages": messages
        }
    
    def clear_short_term_state(self, session_id: str):
        """Clear short-term memory for a session"""
        
        cursor = self.conn.cursor()
        cursor.execute("""
        DELETE FROM SHORT_TERM_MEMORY WHERE session_id = %s
        """, (session_id,))
        
        self.conn.commit()
        cursor.close()
    
    # ==================== EXISTING METHODS ====================
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all chat sessions for Ram"""
        
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT session_id, title, created_at, last_updated, message_count
        FROM CHAT_SESSIONS
        WHERE user_name = %s
        ORDER BY last_updated DESC
        """, (config.USER_NAME,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "session_id": row[0],
                "title": row[1],
                "created_at": row[2],
                "last_updated": row[3],
                "message_count": row[4]
            })
        
        cursor.close()
        return sessions
    
    def load_session_messages(self, session_id: str) -> List[Dict]:
        """Load all messages from a session (complete archive)"""
        
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT role, content, timestamp, tokens, was_summarized
        FROM CHAT_MESSAGES
        WHERE session_id = %s
        ORDER BY timestamp ASC
        """, (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "role": row[0],
                "content": row[1],
                "timestamp": row[2],
                "tokens": row[3],
                "was_summarized": row[4]
            })
        
        cursor.close()
        return messages
    
    def get_session_stats(self) -> Dict:
        """Get overall chat statistics"""
        
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT 
            COUNT(DISTINCT session_id) as total_sessions,
            COUNT(*) as total_messages,
            SUM(CASE WHEN was_summarized THEN 1 ELSE 0 END) as summarized_messages
        FROM CHAT_MESSAGES
        WHERE session_id IN (
            SELECT session_id FROM CHAT_SESSIONS WHERE user_name = %s
        )
        """, (config.USER_NAME,))
        
        row = cursor.fetchone()
        cursor.close()
        
        return {
            "total_sessions": row[0] or 0,
            "total_messages": row[1] or 0,
            "summarized_messages": row[2] or 0
        }