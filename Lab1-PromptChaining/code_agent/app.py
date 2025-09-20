import streamlit as st
import os
from agent_chain import AgentChain

# Page config
st.set_page_config(
    page_title="Code Generation Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = {}

def main():
    st.title("🤖 Code Generation Agent")
    st.subheader("Prompt Chaining with Snowflake Cortex")
    
    # Check .env file
    if not os.path.exists('.env'):
        st.error("❌ Create .env file with Snowflake credentials")
        st.code("""
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
        """)
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        show_backend = st.toggle("Show Backend Process", True)
        
        st.header("🤖 Agent Chain")
        st.write("1. 💻 Code Generation")
        st.write("2. 🧪 Test Generation") 
        st.write("3. 📦 Requirements")
        st.write("4. 📚 Documentation")
        st.write("5. ✅ Validation")
        
        if st.button("Clear Results"):
            st.session_state.results = {}
            st.rerun()
    
    # Main interface
    st.header("💬 Chat Interface")
    
    # Example prompts
    examples = [
        "Create a personal expense tracker with category analysis",
        "Build a password generator with customizable security levels", 
        "Create a JSON to CSV converter with validation",
        "Build a simple chat bot for customer support",
        "Create a file organizer that sorts by date and type",
        "Build a URL shortener with analytics tracking",
        "Create a markdown to HTML converter",
        "Build a weather data aggregator from multiple APIs"
    ]
    
    selected_example = st.selectbox("Example prompts:", [""] + examples)
    
    # Chat input
    user_input = st.chat_input("What do you want to build?")
    
    if selected_example and selected_example != "":
        user_input = selected_example
    
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Display agent response
        with st.chat_message("assistant"):
            st.write("🚀 Starting agent chain...")
            
            # Execute chain
            chain = AgentChain()
            results = chain.execute_chain(user_input, show_backend)
            
            # Store results
            st.session_state.results = results
    
    # Display results
    if st.session_state.results:
        st.markdown("---")
        st.header("📁 Generated Files")
        
        # Tabs for results
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "💻 Code", "🧪 Tests", "📦 Requirements", "📚 README", "✅ Review"
        ])
        
        with tab1:
            if 'code' in st.session_state.results:
                st.code(st.session_state.results['code'], language="python")
        
        with tab2:
            if 'test' in st.session_state.results:
                st.code(st.session_state.results['test'], language="python")
        
        with tab3:
            if 'requirements' in st.session_state.results:
                st.code(st.session_state.results['requirements'])
        
        with tab4:
            if 'docs' in st.session_state.results:
                st.markdown(st.session_state.results['docs'])
        
        with tab5:
            if 'validation' in st.session_state.results:
                st.write(st.session_state.results['validation'])

if __name__ == "__main__":
    main()