"""Snowflake Cortex LLM wrapper for LangGraph."""

import snowflake.connector
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
import logging
from config import snowflake_config

logger = logging.getLogger(__name__)

class SnowflakeCortexLLM:
    """Snowflake Cortex LLM wrapper for LangGraph."""
    
    def __init__(self, model: str = "llama3.1-70b"):
        """
        Initialize Snowflake Cortex LLM.
        
        Args:
            model: Model name (default: llama3.1-70b)
        """
        self.model = model
        self.connection = None
    
    def _get_connection(self):
        """Get or create Snowflake connection."""
        if self.connection is None or self.connection.is_closed():
            self.connection = snowflake.connector.connect(
                user=snowflake_config.user,
                password=snowflake_config.password,  # PAT token
                account=snowflake_config.account,
                warehouse=snowflake_config.warehouse,
                database=snowflake_config.database,
                schema=snowflake_config.schema,
                role=snowflake_config.role
            )
        return self.connection
    
    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        """
        Invoke the LLM with messages.
        
        Args:
            messages: List of messages
            
        Returns:
            AI response message
        """
        # Convert messages to prompt string
        prompt_parts = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                prompt_parts.append(f"System: {msg.content}")
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")
        
        prompt = "\n\n".join(prompt_parts)
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Escape single quotes
            escaped_prompt = prompt.replace("'", "''")
            
            # Call Snowflake Cortex COMPLETE
            query = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                '{self.model}',
                '{escaped_prompt}'
            ) as response
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            
            response_text = result[0] if result else "No response"
            
            return AIMessage(content=response_text)
            
        except Exception as e:
            logger.error(f"Error calling Snowflake Cortex: {e}")
            return AIMessage(content=f"Error: {str(e)}")
    
    def __del__(self):
        """Close connection when object is destroyed."""
        if self.connection and not self.connection.is_closed():
            self.connection.close()