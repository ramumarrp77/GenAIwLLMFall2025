import streamlit as st
from snowflake_connection import call_cortex_complete

class RouterAgent:
    def __init__(self):
        self.name = "Query Classification Specialist"
        self.model = "claude-3-5-sonnet"
        
    def classify_query(self, user_query: str, show_backend: bool = False) -> str:
        """Classify user query and route to appropriate tool"""
        
        prompt = f"""You are a Query Classification Specialist for iPhone customer support.

Available tools:
- RAG_AGENT: For questions about iPhone features, reviews, user experiences, product quality
- NEWS_AGENT: For questions about latest iPhone news, updates, releases, announcements  
- MAPS_AGENT: For questions about Apple Store locations, directions, store hours

User query: "{user_query}"

You must select EXACTLY ONE tool. Return only the tool name with no other text:
RAG_AGENT or NEWS_AGENT or MAPS_AGENT"""

        if show_backend:
            st.write("🔍 **Router Agent Classification**")
            with st.expander("Router Agent Backend", expanded=False):
                st.write(f"**Model:** {self.model}")
                st.code(prompt, language="text")
        
        with st.spinner("🔄 Router Agent analyzing query..."):
            result = call_cortex_complete(prompt, self.model)
            
        if show_backend:
            with st.expander("Router Agent Backend", expanded=False):
                st.write(f"**Raw Router Output:** {result}")
        
        # Clean the result to ensure it's one of our tools
        result = result.strip().upper()
        valid_tools = ['RAG_AGENT', 'NEWS_AGENT', 'MAPS_AGENT']
        
        if result in valid_tools:
            return result
        else:
            # Default fallback if router gives unexpected output
            return 'RAG_AGENT'
            
    def display_routing_decision(self, selected_tool: str):
        """Display the routing decision visually"""
        tool_info = {
            'RAG_AGENT': {'icon': '📊', 'name': 'RAG Agent', 'description': 'iPhone Reviews Analysis'},
            'NEWS_AGENT': {'icon': '📰', 'name': 'News Agent', 'description': 'Latest iPhone Information'},
            'MAPS_AGENT': {'icon': '🗺️', 'name': 'Maps Agent', 'description': 'Apple Store Locator'}
        }
        
        info = tool_info.get(selected_tool, {'icon': '❓', 'name': 'Unknown', 'description': 'Unknown tool'})
        
        st.success(f"🎯 Router selected: {info['icon']} **{info['name']}** - {info['description']}")