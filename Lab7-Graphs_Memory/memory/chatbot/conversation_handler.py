"""
Main conversation handler - Orchestrates all memory layers with persistence
"""

from typing import List, Dict
from memory.short_term_manager import ShortTermMemoryManager
from memory.long_term_manager import LongTermMemoryManager
from memory.chat_archiver import ChatArchiver
from langchain_core.messages.utils import count_tokens_approximately
import config


class ConversationHandler:
    """
    Orchestrates all three memory layers:
    1. Short-term (with auto-summarization and persistence)
    2. Long-term (Neo4j knowledge graph)
    3. Archive (Snowflake complete history)
    """
    
    def __init__(self, llm, graph, snowflake_conn):
        self.llm = llm
        
        # Initialize all memory managers
        self.short_term = ShortTermMemoryManager(llm)
        self.long_term = LongTermMemoryManager(graph, llm)
        self.archiver = ChatArchiver(snowflake_conn)
        
        # Current session
        self.current_session_id = None
    
    def start_new_session(self) -> str:
        """Start a new chat session"""
        self.current_session_id = self.archiver.create_session()
        self.short_term = ShortTermMemoryManager(self.llm)  # Reset short-term memory
        
        # Clear any old short-term state
        self.archiver.clear_short_term_state(self.current_session_id)
        
        return self.current_session_id
    
    def load_session(self, session_id: str):
        """
        Load an existing chat session
        Restores short-term memory state from persistence
        """
        
        self.current_session_id = session_id
        
        # Load short-term memory state from Snowflake
        short_term_state = self.archiver.load_short_term_state(session_id)
        
        # Rebuild short-term memory
        self.short_term = ShortTermMemoryManager(self.llm)
        self.short_term.load_state(
            summary=short_term_state['summary'],
            messages=short_term_state['messages']
        )
        
        print(f"✅ Loaded session with {len(short_term_state['messages'])} messages in short-term memory")
        if short_term_state['summary']:
            print(f"📝 Summary loaded: {short_term_state['summary'][:100]}...")
    
    def _save_short_term_state(self):
        """Save current short-term memory state to persistence"""
        if self.current_session_id:
            state = self.short_term.get_state_for_persistence()
            self.archiver.save_short_term_state(
                self.current_session_id,
                state['messages'],
                state['summary']
            )
    
    def chat(self, user_message: str) -> dict:
        """
        Main chat function with short-term memory persistence
        """
        
        # Ensure we have a session
        if not self.current_session_id:
            self.current_session_id = self.archiver.create_session(user_message)
        
        # 1. Add user message to short-term
        self.short_term.add_message("user", user_message)
        
        # 2. Save to Snowflake archive
        user_tokens = count_tokens_approximately([user_message])
        self.archiver.save_message(
            self.current_session_id,
            "user",
            user_message,
            user_tokens
        )
        
        # 3. Save short-term state BEFORE summarization check
        self._save_short_term_state()
        
        # 4. Check if summarization needed
        summarization_info = self.short_term.check_and_summarize()
        
        # 5. If summarized, update the persisted state
        if summarization_info['summarized']:
            self._save_short_term_state()
            print("💾 Updated short-term memory state after summarization")
        
        # 6. Get context for LLM (includes summary if exists)
        context_messages = self.short_term.get_context_for_llm()
        
        # 7. Build prompt
        prompt = self._build_prompt(context_messages, user_message)
        
        # 8. Generate response
        raw_response = self.llm.invoke(prompt)
        
        # 9. Clean the response
        response = self._clean_response(raw_response)
        
        # 10. Add response to short-term
        self.short_term.add_message("assistant", response)
        
        # 11. Save response to Snowflake
        response_tokens = count_tokens_approximately([response])
        self.archiver.save_message(
            self.current_session_id,
            "assistant",
            response,
            response_tokens,
            was_summarized=summarization_info['summarized']
        )
        
        # 12. Save short-term state after adding response
        self._save_short_term_state()
        
        # 13. Check if we should extract to Neo4j
        extraction_info = {"checked": False, "extracted": False}
        
        if self.long_term.should_extract(user_message, response):
            extraction_info = self.long_term.extract_and_store(user_message, response)
            extraction_info["checked"] = True
        
        # 14. Get current stats
        memory_stats = {
            "short_term": self.short_term.get_stats(),
            "long_term": self.long_term.query_memory("stats"),
            "archive": self.archiver.get_session_stats()
        }
        
        return {
            "response": response,
            "summarization_info": summarization_info,
            "extraction_info": extraction_info,
            "memory_stats": memory_stats
        }
    
    def _clean_response(self, response: str) -> str:
        """Clean LLM response by removing instruction markers"""
        
        if not response:
            return ""
        
        # Remove instruction tags
        response = response.replace('[INST]', '').replace('[/INST]', '')
        response = response.replace('<<SYS>>', '').replace('<</SYS>>', '')
        response = response.replace('<s>', '').replace('</s>', '')
        
        # Remove prefixes
        response = response.strip()
        if response.startswith('Assistant:'):
            response = response[len('Assistant:'):].strip()
        if response.startswith('Ram:'):
            response = response[len('Ram:'):].strip()
        
        return response
    
    def _build_prompt(self, context_messages, current_question: str) -> str:
        """Build prompt with all context"""
        
        # Convert messages to text
        context = "\n".join([
            f"{msg.type}: {msg.content}" for msg in context_messages
        ])
        
        # Query Neo4j for relevant facts
        graph_context = self._get_relevant_graph_context(current_question)
        
        prompt_parts = []
        
        # System instruction
        prompt_parts.append(f"""You are Flavor Memory, a friendly food diary assistant for {config.USER_NAME}.

Your role:
- Help Ram remember restaurants, dishes, and food experiences
- Be conversational and enthusiastic about food
- Ask follow-up questions to learn more details
- Give recommendations when Ram asks

Important: Respond naturally without any special tags or markers.""")
        
        # Add graph context if relevant
        if graph_context:
            prompt_parts.append(f"\n--- Ram's Food Memory ---\n{graph_context}")
        
        # Add conversation context
        if context:
            prompt_parts.append(f"\n--- Conversation History ---\n{context}")
        
        # Current question
        prompt_parts.append(f"\nRam: {current_question}\n\nAssistant:")
        
        return "\n".join(prompt_parts)
    
    def _get_relevant_graph_context(self, question: str) -> str:
        """Get relevant facts from knowledge graph based on question"""
        
        question_lower = question.lower()
        context_parts = []
        
        # If asking about restaurants
        if any(word in question_lower for word in ['restaurant', 'place', 'where', 'ate', 'eaten', 'dined']):
            restaurants = self.long_term.query_memory("all_restaurants")
            if restaurants:
                recent = restaurants[:5]
                context_parts.append("Recent restaurants: " + ", ".join([r['restaurant'] for r in recent]))
        
        # If asking about dishes
        if any(word in question_lower for word in ['dish', 'food', 'meal', 'ordered', 'tried']):
            dishes = self.long_term.query_memory("all_dishes")
            if dishes:
                recent = dishes[:5]
                context_parts.append("Recent dishes: " + ", ".join([d['dish'] for d in recent]))
        
        # If asking about preferences
        if any(word in question_lower for word in ['favorite', 'prefer', 'like', 'love', 'best']):
            favs = self.long_term.query_memory("favorites")
            if favs:
                context_parts.append("Preferred cuisines: " + ", ".join([f['cuisine'] for f in favs]))
        
        return "\n".join(context_parts) if context_parts else ""
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all chat sessions"""
        return self.archiver.get_all_sessions()