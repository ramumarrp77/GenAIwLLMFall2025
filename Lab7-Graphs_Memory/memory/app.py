"""
Flavor Memory - Personal Food Diary Assistant
Demonstrates: Short-term memory, Summarization, Knowledge Graphs
"""

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime

# Import our modules
from utils import SnowflakeCortexLLM, get_snowflake_connection, get_neo4j_graph
from utils.neo4j_connection import initialize_schema
from chatbot import ConversationHandler
import config

# Page config
st.set_page_config(
    page_title="🍜 Flavor Memory - Ram's Food Diary",
    page_icon="🍜",
    layout="wide"
)

# Initialize connections (cached)
@st.cache_resource
def init_connections():
    """Initialize all connections"""
    llm = SnowflakeCortexLLM()
    graph = get_neo4j_graph()
    snowflake_conn = get_snowflake_connection()
    
    # Initialize schema
    initialize_schema(graph)
    
    return llm, graph, snowflake_conn

llm, graph, snowflake_conn = init_connections()

# Initialize conversation handler
@st.cache_resource
def init_handler(_llm, _graph, _snowflake_conn):
    """Initialize conversation handler"""
    return ConversationHandler(_llm, _graph, _snowflake_conn)

handler = init_handler(llm, graph, snowflake_conn)

# Initialize session state
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'memory_events' not in st.session_state:
    st.session_state.memory_events = []

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("🍜 Flavor Memory")
    st.caption(f"Welcome, {config.USER_NAME}!")
    
    st.markdown("---")
    
    # New Chat button
    if st.button("🆕 New Chat", use_container_width=True):
        session_id = handler.start_new_session()
        st.session_state.current_session_id = session_id
        st.session_state.messages = []
        st.session_state.memory_events = []
        st.rerun()
    
    # Past Chats
    st.subheader("📜 Past Chats")
    
    sessions = handler.get_all_sessions()
    
    if sessions:
        # Group by date
        from datetime import date
        
        today = date.today()
        
        for session in sessions[:10]:  # Show last 10
            session_date = session['last_updated'].date()
            
            # Date label
            if session_date == today:
                date_label = "Today"
            elif (today - session_date).days == 1:
                date_label = "Yesterday"
            else:
                date_label = session_date.strftime("%b %d")
            
            # Session button
            button_label = f"{date_label}: {session['title']}"
            if st.button(button_label, key=session['session_id']):
                handler.load_session(session['session_id'])
                st.session_state.current_session_id = session['session_id']
                
                # Load messages
                archived = handler.archiver.load_session_messages(session['session_id'])
                st.session_state.messages = [
                    {"role": msg['role'], "content": msg['content']}
                    for msg in archived
                ]
                st.session_state.memory_events = []
                st.rerun()
    else:
        st.info("No past chats yet")
    
    st.markdown("---")
    
    # Current Session Stats
    st.subheader("📊 Current Session")
    
    if st.session_state.current_session_id:
        short_term_stats = handler.short_term.get_stats()
        
        # Calculate over_limit safely
        is_over_limit = short_term_stats['tokens'] > short_term_stats['token_limit']
        
        # Messages count
        st.metric("Messages", short_term_stats['messages'])
        
        # Token usage with color warning
        token_usage = f"{short_term_stats['tokens']}/{short_term_stats['token_limit']}"
        
        if is_over_limit:
            st.metric("Tokens", token_usage, delta="⚠️ Over limit", delta_color="inverse")
        else:
            st.metric("Tokens", token_usage)
        
        # Progress bar for tokens
        progress = min(short_term_stats['tokens'] / short_term_stats['token_limit'], 1.0)
        st.progress(progress)
        
        # Summarization status
        if short_term_stats['has_summary']:
            st.success("✅ Summarized")
        else:
            if is_over_limit:
                st.warning("⏳ Needs summarization")
            else:
                st.info("💬 Active conversation")
        
        # View short-term memory button
        if st.button("🔍 View Short-term Memory", use_container_width=True):
            st.session_state.show_memory = True
        
    else:
        st.info("Start a new chat!")
    
    st.markdown("---")
    
    # Knowledge Graph Stats
    st.subheader("💾 Food Memory")
    
    kg_stats = handler.long_term.query_memory("stats")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Restaurants", kg_stats.get('restaurants', 0))
        st.metric("Dishes", kg_stats.get('dishes', 0))
    with col2:
        st.metric("Cuisines", kg_stats.get('cuisines', 0))
    
    # View graph button
    if st.button("🗺️ View Food Map", use_container_width=True):
        st.session_state.show_graph = True
    
    st.markdown("---")
    
    # Settings
    st.subheader("⚙️ Settings")
    show_backend = st.checkbox("Show Backend Process", value=False)


# ============================================================================
# MAIN AREA
# ============================================================================

st.title("🍜 Flavor Memory")
st.caption("Your personal food diary assistant")

# Show short-term memory if requested
if st.session_state.get('show_memory', False):
    with st.expander("🧠 Short-term Memory Contents", expanded=True):
        
        short_term_stats = handler.short_term.get_stats()
        
        # Stats header
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Messages in RAM", short_term_stats['messages'])
        with col2:
            st.metric("Current Tokens", short_term_stats['tokens'])
        with col3:
            if short_term_stats['has_summary']:
                st.metric("Status", "📝 Summarized", delta="Condensed")
            else:
                st.metric("Status", "💬 Active")
        
        st.markdown("---")
        
        # Get all messages including summary
        memory_contents = handler.short_term.get_all_messages()
        
        if memory_contents:
            for item in memory_contents:
                if item['type'] == 'summary':
                    st.info(item['content'])
                else:
                    role = "user" if item['role'] in ["user", "human"] else "assistant"
                    with st.chat_message(role):
                        st.write(item['content'])
        else:
            st.write("No messages in memory yet")
        
        if st.button("Close Memory View"):
            st.session_state.show_memory = False
            st.rerun()

# Show graph visualization if requested
if st.session_state.get('show_graph', False):
    with st.expander("🗺️ Ram's Food Map", expanded=True):
        
        # Get graph data
        graph_data = handler.long_term.get_graph_visualization_data()
        
        if graph_data:
            # Build NetworkX graph
            G = nx.DiGraph()
            
            for record in graph_data:
                G.add_node(record['source'])
                G.add_node(record['target'], type=record['target_type'])
                G.add_edge(record['source'], record['target'], rel=record['relationship'])
            
            # Visualize
            fig, ax = plt.subplots(figsize=(12, 8))
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Colors
            colors = {
                'Restaurant': 'lightcoral',
                'Dish': 'lightblue',
                'Cuisine': 'lightgreen',
                'Location': 'lightyellow',
                'Ingredient': 'lightpink'
            }
            
            node_colors = [colors.get(G.nodes[n].get('type', ''), 'lightgray') for n in G.nodes()]
            
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1500, alpha=0.9, ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=8, ax=ax)
            nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, ax=ax)
            
            edge_labels = nx.get_edge_attributes(G, 'rel')
            nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6, ax=ax)
            
            ax.set_title("Ram's Food Knowledge Graph", fontsize=14, fontweight='bold')
            ax.axis('off')
            
            st.pyplot(fig)
            
            if st.button("Close Graph"):
                st.session_state.show_graph = False
                st.rerun()
        else:
            st.info("No food memories yet! Start chatting about restaurants.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Display memory events (summarization, extraction)
for event in st.session_state.memory_events:
    if event['type'] == 'summarization':
        st.success(f"✅ **Summarization Completed!** Condensed {event['messages_removed']} old messages into a summary. Token usage reduced.")
    elif event['type'] == 'extraction' and show_backend:
        with st.expander("💾 Saved to Knowledge Graph", expanded=False):
            st.write("**Extracted entities:**")
            for entity in event['entities']:
                st.write(f"• {entity}")

# Chat input
if prompt := st.chat_input("Tell me about a restaurant you tried..."):
    
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    # Process with spinner
    with st.spinner("🤔 Thinking..."):
        
        # Get response from handler
        result = handler.chat(prompt)
        
        # Add assistant message to UI
        st.session_state.messages.append({
            "role": "assistant",
            "content": result['response']
        })
        
        # Track memory events
        if result['summarization_info']['summarized']:
            st.session_state.memory_events.append({
                "type": "summarization",
                "messages_removed": result['summarization_info']['messages_before'] - result['summarization_info']['messages_after']
            })
        
        if result['extraction_info'].get('extracted', False):
            st.session_state.memory_events.append({
                "type": "extraction",
                "entities": result['extraction_info']['entities']
            })
        
        # Rerun to show response
        st.rerun()

# Initial greeting
if not st.session_state.messages:
    with st.chat_message("assistant"):
        greeting = f"Hi {config.USER_NAME}! 🍜 I'm Flavor Memory, your personal food diary assistant. Tell me about restaurants you've tried, dishes you loved, or ask me about your food history!"
        st.write(greeting)
        st.session_state.messages.append({"role": "assistant", "content": greeting})

# Footer
st.markdown("---")
st.caption("🎓 Lab 7: Memory Management Demo | Short-term (Summarization) + Long-term (Knowledge Graphs)")