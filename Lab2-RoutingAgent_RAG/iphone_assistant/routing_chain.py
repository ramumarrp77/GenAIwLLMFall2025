import streamlit as st
from router_agent import RouterAgent
from rag_agent import RAGAgent
from news_agent import NewsAgent
from map_agent import MapsAgent
from snowflake_connection import call_cortex_complete

class RoutingChain:
    def __init__(self):
        self.router = RouterAgent()
        self.tools = {
            'RAG_AGENT': RAGAgent(),
            'NEWS_AGENT': NewsAgent(), 
            'MAPS_AGENT': MapsAgent()
        }
        
    def execute_routing_chain(self, user_query: str, show_backend: bool = False):
        """Execute complete routing chain: Router -> Tool -> Synthesizer"""
        
        st.subheader("🔀 Routing Agent Workflow")
        
        # Step 1: Router classifies the query
        st.write("**Step 1: Query Classification**")
        selected_tool = self.router.classify_query(user_query, show_backend)
        self.router.display_routing_decision(selected_tool)
        
        # Step 2: Execute the selected tool
        st.write("**Step 2: Specialized Tool Execution**")
        if selected_tool in self.tools:
            tool_output = self.tools[selected_tool].execute(user_query, show_backend)
        else:
            tool_output = "Tool not found"
            
        # Step 3: Synthesize final response
        st.write("**Step 3: Response Synthesis**")
        final_response = self._synthesize_response(user_query, selected_tool, tool_output, show_backend)
        
        return {
            'selected_tool': selected_tool,
            'tool_output': tool_output,
            'final_response': final_response
        }
    
    def _synthesize_response(self, user_query: str, selected_tool: str, tool_output: str, show_backend: bool = False):
        """Generate final natural language response"""
        
        synthesis_prompt = f"""You are a Customer Service Representative for iPhone support.

Customer question: "{user_query}"

Specialist analysis from {selected_tool.replace('_', ' ')}: {tool_output}

Provide a helpful, conversational response to the customer based on the specialist's findings.
Be natural, friendly, and directly address their question.

Return ONLY the customer response, no additional text."""

        if show_backend:
            with st.expander("🔧 Response Synthesizer - Backend Process", expanded=False):
                st.write("**Model Used:** claude-3-5-sonnet")
                st.write("**Synthesis Prompt:**")
                st.code(synthesis_prompt, language="text")
                st.write("**Raw Tool Output Being Synthesized:**")
                st.text_area("Tool Output:", tool_output[:500] + "..." if len(tool_output) > 500 else tool_output, height=100)
        
        with st.spinner("🔄 Synthesizing final response..."):
            final_response = call_cortex_complete(synthesis_prompt, 'claude-3-5-sonnet')
            
        if show_backend:
            with st.expander("🔧 Response Synthesizer - Backend Process", expanded=False):
                st.write("**Generated Final Response:**")
                st.text_area("Synthesized Response:", final_response, height=150)
        
        st.success("✅ Response Synthesizer completed")
        return final_response