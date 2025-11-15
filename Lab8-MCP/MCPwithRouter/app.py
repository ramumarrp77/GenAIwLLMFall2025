import streamlit as st
from mcp_brain import MCPBrain
from mcp_client import MCPClient

# Page config
st.set_page_config(
    page_title="Lab 8: MCP Routing Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'brain' not in st.session_state:
    st.session_state.brain = MCPBrain()

if 'client' not in st.session_state:
    st.session_state.client = MCPClient()

if 'available_tools' not in st.session_state:
    st.session_state.available_tools = st.session_state.client.get_all_tools()

def process_query(user_query: str, show_backend: bool):
    """
    Complete MCP flow:
    1. Brain decides which tool
    2. Client routes to tool
    3. Tool executes
    4. Brain generates response
    """
    
    # Step 1: Brain decides
    decision = st.session_state.brain.decide_tool(
        user_query,
        st.session_state.available_tools
    )
    
    # Step 2: Client routes and executes
    tool_result = st.session_state.client.call_tool(
        decision.get('server', 'database-server'),
        decision['tool_name'],
        decision.get('arguments', {})
    )
    
    # Step 3: Brain generates final response
    final_response = st.session_state.brain.generate_final_response(
        user_query,
        tool_result,
        decision
    )
    
    return {
        'decision': decision,
        'tool_result': tool_result,
        'final_response': final_response
    }

def main():
    # Header
    st.title("🤖 Lab 8: MCP Routing Agent with Snowflake Cortex")
    st.markdown("**Intelligent routing across Database, News, and Location services**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Show backend toggle
        show_backend = st.checkbox("Show Backend Process", value=True)
        
        st.markdown("---")
        
        # Server information
        st.header("🏭 MCP Servers")
        server_info = st.session_state.client.get_server_info()
        st.metric("Total Servers", server_info['total_servers'])
        st.metric("Total Tools", server_info['total_tools'])
        
        with st.expander("📋 View All Servers"):
            for server in server_info['servers']:
                st.write(f"- {server}")
        
        with st.expander("🔧 View All Tools"):
            for tool in st.session_state.available_tools:
                st.write(f"**{tool['server']}.{tool['name']}**")
                st.caption(tool['description'])
                st.write("")
        
        st.markdown("---")
        
        # New conversation
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")
        
        # Info
        st.info("""
        **How it works:**
        1. 🧠 Brain (Cortex) decides which tool
        2. 📬 Client routes to server
        3. ⚙️ Server executes tool
        4. 📊 Brain generates response
        """)
    
    # Main chat area
    st.markdown("### 💬 Chat")
    
    # Example queries
    with st.expander("📝 Example Queries", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📊 Database Queries:**")
            examples_db = [
                "What do people say about iPhone camera quality?",
                "Show me negative reviews about battery life",
                "How is the iPhone display rated?"
            ]
            for ex in examples_db:
                if st.button(ex, key=f"db_{ex}"):
                    st.session_state.temp_query = ex
                    st.rerun()
        
        with col2:
            st.markdown("**📰 News Queries:**")
            examples_news = [
                "What's the latest news about iPhone 16?",
                "Any recent iPhone software updates?",
                "iPhone price changes news"
            ]
            for ex in examples_news:
                if st.button(ex, key=f"news_{ex}"):
                    st.session_state.temp_query = ex
                    st.rerun()
        
        with col3:
            st.markdown("**📍 Location Queries:**")
            examples_loc = [
                "Find Apple Store near Boston",
                "Directions to nearest Apple Store from Northeastern",
                "Apple Store hours in Boston"
            ]
            for ex in examples_loc:
                if st.button(ex, key=f"loc_{ex}"):
                    st.session_state.temp_query = ex
                    st.rerun()
    
    # Display chat history
    for i, (query, response, metadata) in enumerate(st.session_state.chat_history):
        # User message
        with st.chat_message("user"):
            st.write(query)
        
        # Assistant message
        with st.chat_message("assistant"):
            st.write(response)
            
            # Show backend details if enabled
            if show_backend and metadata:
                with st.expander("🔍 Backend Details"):
                    decision = metadata.get('decision', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🎯 Server Selected", decision.get('server', 'N/A'))
                        st.metric("🔧 Tool Used", decision.get('tool_name', 'N/A'))
                    
                    with col2:
                        st.write("**💭 Reasoning:**")
                        st.caption(decision.get('reasoning', 'N/A'))
                    
                    st.write("**📊 Tool Result:**")
                    tool_result = metadata.get('tool_result', {})
                    if tool_result.get('success'):
                        st.json(tool_result, expanded=False)
                    else:
                        st.error(f"Tool error: {tool_result.get('error', 'Unknown error')}")
    
    # Chat input
    user_input = st.chat_input("Ask about iPhones, news, or Apple stores...")
    
    # Handle example button clicks
    if 'temp_query' in st.session_state:
        user_input = st.session_state.temp_query
        del st.session_state.temp_query
    
    if user_input:
        # Add user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("🔄 Processing your request..."):
                result = process_query(user_input, show_backend)
                
                # Display response
                st.write(result['final_response'])
                
                # Show backend if enabled
                if show_backend:
                    with st.expander("🔍 Backend Details"):
                        decision = result['decision']
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("🎯 Server Selected", decision.get('server', 'N/A'))
                            st.metric("🔧 Tool Used", decision.get('tool_name', 'N/A'))
                        
                        with col2:
                            st.write("**💭 Reasoning:**")
                            st.caption(decision.get('reasoning', 'N/A'))
                        
                        st.write("**📊 Tool Result:**")
                        tool_result = result['tool_result']
                        if tool_result.get('success'):
                            st.json(tool_result, expanded=False)
                        else:
                            st.error(f"Tool error: {tool_result.get('error', 'Unknown error')}")
        
        # Add to chat history
        st.session_state.chat_history.append((
            user_input,
            result['final_response'],
            {
                'decision': result['decision'],
                'tool_result': result['tool_result']
            }
        ))
        
        st.rerun()

if __name__ == "__main__":
    main()