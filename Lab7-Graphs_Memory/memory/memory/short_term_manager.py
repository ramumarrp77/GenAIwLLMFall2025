"""
Short-term memory with auto-summarization and persistence
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.messages.utils import count_tokens_approximately
from typing import List, Dict
import config


class ShortTermMemoryManager:
    """
    Manages short-term memory with automatic summarization
    Now includes persistence support
    """
    
    def __init__(self, llm, token_limit: int = None):
        self.llm = llm
        self.token_limit = token_limit or config.TOKEN_LIMIT
        self.messages = []
        self.summary = None
        self.keep_messages = 5  # Keep last 5 messages after summarization
    
    def add_message(self, role: str, content: str):
        """Add a message to short-term memory"""
        if role == "user":
            self.messages.append(HumanMessage(content=content))
        elif role == "assistant":
            self.messages.append(AIMessage(content=content))
        elif role == "system":
            self.messages.append(SystemMessage(content=content))
    
    def load_state(self, summary: str = None, messages: List[Dict] = None):
        """
        Load short-term memory state from persistence
        Called when loading a session
        """
        self.messages = []
        self.summary = summary
        
        if messages:
            for msg in messages:
                self.add_message(msg['role'], msg['content'])
    
    def get_state_for_persistence(self) -> Dict:
        """
        Get current state for persistence
        Returns summary and messages as simple dicts
        """
        messages = []
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                role = msg.type
            
            messages.append({
                "role": role,
                "content": msg.content
            })
        
        return {
            "summary": self.summary,
            "messages": messages
        }
    
    def check_and_summarize(self) -> dict:
        """
        Check if summarization needed and perform it
        """
        
        current_tokens = count_tokens_approximately(self.messages)
        messages_before = len(self.messages)
        
        # Check if we need to summarize
        if current_tokens > self.token_limit and len(self.messages) > self.keep_messages:
            
            # Split messages
            old_messages = self.messages[:-self.keep_messages]
            recent_messages = self.messages[-self.keep_messages:]
            
            # Create summary
            summary_text = self._create_summary(old_messages)
            self.summary = summary_text
            
            # Replace messages with recent only
            self.messages = recent_messages
            
            messages_after = len(self.messages)
            new_tokens = count_tokens_approximately(self.messages)
            
            print(f"✅ Summarization completed: {messages_before} -> {messages_after} messages")
            
            return {
                "current_tokens": new_tokens,
                "limit": self.token_limit,
                "summarized": True,
                "messages_before": messages_before,
                "messages_after": messages_after,
                "messages_removed": messages_before - messages_after,
                "summary": self.summary
            }
        
        return {
            "current_tokens": current_tokens,
            "limit": self.token_limit,
            "summarized": False,
            "messages_before": messages_before,
            "messages_after": messages_before
        }
    
    def _create_summary(self, messages: List) -> str:
        """Create summary of old messages"""
        
        if not messages:
            return ""
        
        conversation = "\n".join([
            f"{msg.type}: {msg.content}"
            for msg in messages
        ])
        
        prompt = f"""Summarize this conversation about food and restaurants, preserving key facts like restaurant names, dishes, and Ram's preferences:

{conversation}

Concise summary (2-3 sentences):"""
        
        summary = self.llm.invoke(prompt)
        
        # Clean the summary
        summary = summary.replace('[INST]', '').replace('[/INST]', '')
        summary = summary.replace('<<SYS>>', '').replace('<</SYS>>', '')
        summary = summary.strip()
        
        return summary
    
    def get_context_for_llm(self) -> List:
        """Get messages for LLM including summary"""
        
        if self.summary:
            summary_msg = SystemMessage(content=f"Previous conversation summary: {self.summary}")
            return [summary_msg] + self.messages
        
        return self.messages
    
    def get_token_count(self) -> int:
        """Get current token count"""
        return count_tokens_approximately(self.messages)
    
    def get_stats(self) -> dict:
        """Get statistics about short-term memory"""
        return {
            "messages": len(self.messages),
            "tokens": self.get_token_count(),
            "has_summary": bool(self.summary),
            "token_limit": self.token_limit
        }
    
    def get_all_messages(self) -> List[Dict]:
        """Get all messages as dictionaries for display"""
        result = []
        
        # Add summary if exists
        if self.summary:
            result.append({
                "role": "system",
                "content": f"📝 Summary of earlier conversation:\n{self.summary}",
                "type": "summary"
            })
        
        # Add current messages
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                role = msg.type
            
            result.append({
                "role": role,
                "content": msg.content,
                "type": "message"
            })
        
        return result
    
    def clear(self):
        """Clear all memory"""
        self.messages = []
        self.summary = None