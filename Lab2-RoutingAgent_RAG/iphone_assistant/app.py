import streamlit as st
import os
from routing_chain import RoutingChain

# Page config
st.set_page_config(
    page_title="iPhone Assistant - Routing Agent Demo",
    page_icon="📱",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'routing_results' not in st.session_state:
    st.session_state.routing_results = {}

def main():
    st.title("📱 iPhone Assistant")
    st.subheader("Routing Agent with RAG and Cortex")
    
    # Check .env file
    if not os.path.exists('.env'):
        st.error("❌ Create .env file with Snowflake credentials")
        st.code("""
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_pat_token
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=LAB_DB
SNOWFLAKE_SCHEMA=PUBLIC
        """)
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        show_backend = st.toggle("Show Backend Process", True)
        
        st.header("🤖 Routing System")
        st.write("**Router Agent**")
        st.write("↓ Classifies user queries")
        st.write("")
        st.write("**Available Tools:**")
        st.write("📊 RAG Agent - iPhone Reviews")
        st.write("📰 News Agent - Latest iPhone Info") 
        st.write("🗺️ Maps Agent - Apple Store Locator")
        st.write("")
        st.write("**Response Synthesizer**")
        st.write("↓ Natural language response")
        
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.session_state.routing_results = {}
            st.rerun()
    
    # Main chat interface
    st.header("💬 Chat with iPhone Assistant")
    
    # Display chat history
    for i, (user_msg, assistant_response, routing_info) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(user_msg)
        
        with st.chat_message("assistant"):
            st.write(assistant_response)
            
            if show_backend and routing_info:
                with st.expander("🔧 Backend Process", expanded=False):
                    st.write(f"**Router Selected:** {routing_info.get('selected_tool', 'Unknown')}")
                    st.write(f"**Tool Output:** {routing_info.get('tool_output', 'None')[:200]}...")
    
    # Example queries
    with st.expander("💡 Example Queries", expanded=False):
        examples = [
            "What do customers say about iPhone 15 battery life?",
            "What's the latest news about iPhone 17?",
            "How do I get to the Apple Store in Boston using public transport?",
            "Are there any camera quality issues with iPhone 15 Pro?",
            "What are recent iPhone software updates?",
            "Where's the nearest Apple Store from Northeastern University?"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{hash(example)}"):
                st.session_state.temp_query = example
                st.rerun()
    
    # Chat input
    user_input = st.chat_input("Ask me anything about iPhones, news, or Apple stores...")
    
    # Handle example button selection
    if 'temp_query' in st.session_state:
        user_input = st.session_state.temp_query
        del st.session_state.temp_query
    
    if user_input:
        # Add user message to chat
        with st.chat_message("user"):
            st.write(user_input)
        
        # Process with routing chain
        with st.chat_message("assistant"):
            with st.spinner("🔄 Processing your request..."):
                # Execute routing chain
                chain = RoutingChain()
                result = chain.execute_routing_chain(user_input, show_backend)
                
                # Display final response
                st.write(result['final_response'])
                
                # Add to chat history
                st.session_state.chat_history.append((
                    user_input, 
                    result['final_response'],
                    {
                        'selected_tool': result.get('selected_tool'),
                        'tool_output': result.get('tool_output')
                    }
                ))

if __name__ == "__main__":
    main()