import streamlit as st
import os
import time
from parallel_chain import ParallelChain

st.set_page_config(
    page_title="Parallel Agents - iPhone Review Analysis",
    page_icon="⚡",
    layout="wide"
)

if 'results' not in st.session_state:
    st.session_state.results = {}
if 'execution_times' not in st.session_state:
    st.session_state.execution_times = {}

def main():
    st.title("⚡ Parallel Agent Execution")
    st.subheader("Multi-Aspect iPhone Review Analysis with LangChain")
    
    if not os.path.exists('.env'):
        st.error("Create .env file with credentials")
        st.code("""
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_pat_token
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=LAB_DB
SNOWFLAKE_SCHEMA=PUBLIC
SERPAPI_API_KEY=your_serpapi_key
        """)
        st.stop()
    
    with st.sidebar:
        st.header("⚙️ Execution Settings")
        execution_mode = st.radio(
            "Execution Mode:",
            ["Sequential", "Parallel"],
            help="Sequential runs agents one by one. Parallel runs all simultaneously."
        )
        
        show_backend = st.toggle("Show Backend Process", True)
        
        st.header("🤖 Analysis Agents")
        st.write("1. 😊 Sentiment Agent - Snowflake SENTIMENT()")
        st.write("2. 🔍 Feature Agent - Cortex Search")
        st.write("3. 📰 News Agent - SerpAPI")
        st.write("4. ⚠️ Quality Agent - LLM Analysis")
        st.write("")
        st.write("5. 📊 Aggregator - Final Report")
        
        if st.button("Clear Results"):
            st.session_state.results = {}
            st.session_state.execution_times = {}
            st.rerun()
    
    st.header("💬 iPhone Review Analysis")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        user_query = st.text_input(
            "What aspect of iPhone would you like to analyze?",
            placeholder="e.g., iPhone 15 Pro camera quality"
        )
    with col2:
        analyze_button = st.button("🚀 Analyze Reviews", type="primary")
    
    with st.expander("💡 Example Queries", expanded=False):
        examples = [
            "iPhone 15 battery performance",
            "iPhone 15 Pro camera quality",
            "iPhone 15 screen issues",
            "iPhone 15 overall performance"
        ]
        for example in examples:
            if st.button(example, key=f"ex_{hash(example)}"):
                st.session_state.temp_query = example
                st.rerun()
    
    if 'temp_query' in st.session_state:
        user_query = st.session_state.temp_query
        del st.session_state.temp_query
        analyze_button = True
    
    if analyze_button and user_query:
        st.markdown("---")
        
        is_parallel = (execution_mode == "Parallel")
        
        st.subheader(f"{'⚡ Parallel' if is_parallel else '🔄 Sequential'} Execution Mode")
        
        chain = ParallelChain()
        
        start_time = time.time()
        results = chain.execute_analysis(user_query, is_parallel, show_backend)
        total_time = time.time() - start_time
        
        st.session_state.results = results
        st.session_state.execution_times = {
            'mode': execution_mode,
            'total_time': total_time,
            'agent_times': results.get('agent_times', {})
        }
        
        st.success(f"✅ Analysis completed in {total_time:.2f} seconds")
        
        if st.session_state.execution_times.get('agent_times'):
            st.write("**Individual Agent Times:**")
            cols = st.columns(4)
            agent_names = ['Sentiment', 'Features', 'News', 'Quality']
            for i, (agent, exec_time) in enumerate(st.session_state.execution_times['agent_times'].items()):
                with cols[i % 4]:
                    st.metric(agent_names[i], f"{exec_time:.2f}s")
    
    if st.session_state.results:
        st.markdown("---")
        st.header("📊 Analysis Results")
        
        tabs = st.tabs(["📋 Final Report", "😊 Sentiment", "🔍 Features", "📰 News", "⚠️ Quality"])
        
        with tabs[0]:
            st.subheader("Comprehensive Analysis Report")
            if 'final_report' in st.session_state.results:
                st.write(st.session_state.results['final_report'])
        
        with tabs[1]:
            st.subheader("Sentiment Analysis")
            if 'sentiment' in st.session_state.results:
                st.write(st.session_state.results['sentiment'])
        
        with tabs[2]:
            st.subheader("Feature Extraction")
            if 'features' in st.session_state.results:
                st.write(st.session_state.results['features'])
        
        with tabs[3]:
            st.subheader("Latest News Context")
            if 'news' in st.session_state.results:
                st.write(st.session_state.results['news'])
        
        with tabs[4]:
            st.subheader("Quality Issues")
            if 'quality' in st.session_state.results:
                st.write(st.session_state.results['quality'])

if __name__ == "__main__":
    main()