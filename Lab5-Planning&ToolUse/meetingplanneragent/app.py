# Meeting Planner Chatbot - Streamlit App (Updated)

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import run_conversation_turn

# Page config
st.set_page_config(
    page_title="Meeting Planner Assistant",
    page_icon="📅",
    layout="centered"
)

st.title("📅 Meeting Planner Assistant")
st.markdown("AI-powered meeting scheduler with conversational intelligence")

# Initial greeting message
INITIAL_GREETING = """Hello! I'm your Meeting Planner Assistant. I can help you schedule team meetings by:
- Checking attendee availability
- Finding suitable venues
- Checking weather forecasts
- Sending meeting invitations

Who would you like to invite to the meeting?"""

# Initialize session state
if 'graph_state' not in st.session_state:
    st.session_state.graph_state = {
        'messages': [
            AIMessage(content=INITIAL_GREETING)
        ],  # Start with greeting as LangChain message
        'attendees': None,
        'date_preference': None,
        'duration': None,
        'venue_preference': None,
        'location': 'Boston, MA',
        'tools_to_call': None,
        'tools_called': None,
        'current_tool': None,
        'tool_results': None,
        'need_final_answer': None,
        'ready_to_finalize': False
    }

# Sidebar - Show current state
with st.sidebar:
    st.header("📊 Current Information")
    
    state = st.session_state.graph_state
    
    st.subheader("Collected Details")
    attendees = state.get('attendees', None)
    st.write(f"**Attendees:** {', '.join(attendees) if attendees else '❌ Not set'}")
    st.write(f"**Date:** {state.get('date_preference') or '❌ Not set'}")
    st.write(f"**Duration:** {state.get('duration') or '❌ Not set'}")
    st.write(f"**Venue:** {state.get('venue_preference') or '❌ Not set'}")
    
    st.markdown("---")
    
    st.subheader("🔧 Tools Status")
    tools_done = state.get('tools_called', []) or []
    st.write("✅ Calendar" if 'calendar_tool' in tools_done else "⭕ Calendar")
    st.write("✅ Weather" if 'weather_tool' in tools_done else "⭕ Weather")
    st.write("✅ Venues" if 'places_tool' in tools_done else "⭕ Venues")
    st.write("✅ Email" if 'email_tool' in tools_done else "⭕ Email")
    
    st.markdown("---")
    
    # Conversation stats
    msg_count = len(state.get('messages', []))
    user_msgs = len([m for m in state.get('messages', []) if isinstance(m, HumanMessage)])
    st.metric("Total Messages", msg_count)
    st.metric("User Messages", user_msgs)
    
    st.markdown("---")
    
    if st.button("🔄 New Conversation"):
        st.session_state.graph_state = {
            'messages': [
                AIMessage(content=INITIAL_GREETING)
            ],
            'attendees': None,
            'date_preference': None,
            'duration': None,
            'venue_preference': None,
            'location': 'Boston, MA',
            'tools_to_call': None,
            'tools_called': None,
            'current_tool': None,
            'tool_results': None,
            'need_final_answer': None,
            'ready_to_finalize': False
        }
        st.rerun()

# Main chat area
st.markdown("---")

# Display chat messages from history (handle LangChain message objects)
for message in st.session_state.graph_state['messages']:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

# Chat input
if prompt := st.chat_input("Type your message..."):
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Show processing indicator
    with st.spinner("🤔 Thinking and planning..."):
        try:
            # Run conversation turn through LangGraph
            # IMPORTANT: Pass the existing state to preserve it
            updated_state = run_conversation_turn(prompt, st.session_state.graph_state)
            
            # Update session state with new state
            st.session_state.graph_state = updated_state
            
            # Rerun to show updates
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.caption("🚀 Built with LangGraph + Snowflake Cortex | Conversational AI Planning")