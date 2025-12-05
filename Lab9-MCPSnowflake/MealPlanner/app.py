"""Streamlit app for Lab 9: MCP Integration with LangGraph."""

import streamlit as st
import time
from typing import Dict, Any

from config import snowflake_config
from mcp_client import SnowflakeMCPClient
from graph import NutritionMCPAgent
from utils import setup_logging

# Setup
setup_logging()
st.set_page_config(
    page_title="Lab 9: Nutrition MCP Assistant",
    page_icon="🍎",
    layout="wide"
)

# Initialize session state
def init_session_state():
    """Initialize Streamlit session state."""
    if 'mcp_client' not in st.session_state:
        try:
            snowflake_config.validate()
            st.session_state.mcp_client = SnowflakeMCPClient(snowflake_config)
            st.session_state.connection_status = "connected"
        except Exception as e:
            st.session_state.connection_status = f"error: {str(e)}"
            st.session_state.mcp_client = None
    
    if 'agent' not in st.session_state and st.session_state.mcp_client:
        st.session_state.agent = NutritionMCPAgent(st.session_state.mcp_client)
    
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    
    if 'tools' not in st.session_state:
        st.session_state.tools = []
    
    if 'execution_trace' not in st.session_state:
        st.session_state.execution_trace = []

init_session_state()

# Header
st.title("🍎 Lab 9: Nutrition MCP Assistant")
st.markdown("### MCP Integration with LangGraph State Management")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("🔌 MCP Server Status")
    
    # Connection status
    if st.session_state.connection_status == "connected":
        st.success("✅ Connected to MCP Server")
        st.info(f"**Server:** `{snowflake_config.mcp_server_name}`")
        st.info(f"**Database:** `{snowflake_config.database}.{snowflake_config.schema}`")
        
        # Discover tools button
        if st.button("🔄 Refresh Tools"):
            with st.spinner("Discovering tools..."):
                try:
                    st.session_state.mcp_client.initialize()
                    tools = st.session_state.mcp_client.list_tools()
                    st.session_state.tools = tools
                    st.success(f"Discovered {len(tools)} tools!")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # Display tools
        if st.session_state.tools:
            st.markdown("---")
            st.subheader("🛠️ Available Tools")
            for tool in st.session_state.tools:
                with st.expander(f"**{tool.title}**"):
                    st.markdown(f"**Name:** `{tool.name}`")
                    st.markdown(f"**Description:** {tool.description}")
                    st.json(tool.input_schema)
    else:
        st.error(f"❌ Connection Failed")
        st.error(st.session_state.connection_status)
    
    st.markdown("---")
    st.subheader("⚙️ Settings")
    show_steps = st.checkbox("Show Execution Steps", value=True)
    show_state = st.checkbox("Show State Details", value=True)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Chat with Nutrition Assistant")
    
    # Display conversation history
    for msg in st.session_state.conversation:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about nutrition..."):
        if not st.session_state.mcp_client:
            st.error("⚠️ MCP client not connected. Please check your configuration.")
        else:
            # Add user message
            st.session_state.conversation.append({
                "role": "user",
                "content": prompt
            })
            st.chat_message("user").markdown(prompt)
            
            # Execute agent with real-time step display
            with st.chat_message("assistant"):
                # Create placeholder for steps
                step_container = st.container()
                response_container = st.empty()
                
                try:
                    start_time = time.time()
                    
                    # Execute agent
                    result = st.session_state.agent.run(prompt)
                    execution_time = time.time() - start_time
                    
                    # Display execution steps
                    if show_steps and "execution_steps" in result:
                        with step_container:
                            st.markdown("**🔄 Execution Steps:**")
                            for step in result["execution_steps"]:
                                if step["status"] == "running":
                                    st.info(f"⏳ **{step['step']}**: {step['details']}")
                                elif step["status"] == "completed":
                                    st.success(f"✅ **{step['step']}**: {step['details']}")
                                elif step["status"] == "error":
                                    st.error(f"❌ **{step['step']}**: {step['details']}")
                            st.markdown("---")
                    
                    # Display response
                    response = result.get("analysis", "No response generated")
                    response_container.markdown(response)
                    
                    # Add to conversation
                    st.session_state.conversation.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    # Store execution trace
                    st.session_state.execution_trace.append({
                        "query": prompt,
                        "result": result,
                        "execution_time": execution_time
                    })
                    
                    # Show execution time
                    st.caption(f"⏱️ Executed in {execution_time:.2f}s")
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.conversation.append({
                        "role": "assistant",
                        "content": error_msg
                    })

with col2:
    st.subheader("📊 Monitoring")
    
    # Show latest execution steps
    if show_steps and st.session_state.execution_trace:
        with st.expander("🔄 Latest Execution Flow", expanded=True):
            latest = st.session_state.execution_trace[-1]
            result = latest["result"]
            
            if "execution_steps" in result:
                # Group steps by name to show flow
                step_groups = {}
                for step in result["execution_steps"]:
                    step_name = step["step"]
                    if step_name not in step_groups:
                        step_groups[step_name] = []
                    step_groups[step_name].append(step)
                
                # Display each step group
                for step_name, steps in step_groups.items():
                    # Show the last status for each step
                    last_step = steps[-1]
                    if last_step["status"] == "completed":
                        st.success(f"✅ **{step_name}**")
                    elif last_step["status"] == "error":
                        st.error(f"❌ **{step_name}**")
                    else:
                        st.info(f"⏳ **{step_name}**")
                    
                    st.caption(last_step['details'])
    
    # Show current state
    if show_state and st.session_state.execution_trace:
        with st.expander("🔍 State Details", expanded=False):
            latest = st.session_state.execution_trace[-1]
            result = latest["result"]
            
            st.markdown(f"**Query:** {latest['query']}")
            st.markdown(f"**Intent:** `{result.get('detected_intent', 'N/A')}`")
            st.markdown(f"**Tool:** `{result.get('selected_tool', 'N/A')}`")
            st.markdown(f"**Arguments:**")
            st.json(result.get('tool_args', {}))
            
            # Show tool result preview
            if result.get('tool_result'):
                st.markdown("**Tool Result:**")
                tool_res = result['tool_result']
                if hasattr(tool_res, 'success'):
                    if tool_res.success:
                        st.success("Success")
                        st.text(str(tool_res.content)[:500] + "..." if len(str(tool_res.content)) > 500 else str(tool_res.content))
                    else:
                        st.error(f"Error: {tool_res.error}")

# Example queries
st.markdown("---")
st.subheader("💡 Example Queries")

examples = [
    "Find high protein vegetarian meals",
    "Calculate macros for 30g protein, 50g carbs, 15g fat",
    "Score a 380 calorie meal with 32g protein against 400 calorie target",
    "Show me low-carb meals",
    "Find cheese with around 25g protein"
]

cols = st.columns(len(examples))
for i, example in enumerate(examples):
    if cols[i].button(example, key=f"example_{i}", use_container_width=True):
        st.session_state.example_query = example
        st.rerun()

# Handle example query
if 'example_query' in st.session_state:
    example = st.session_state.example_query
    del st.session_state.example_query
    
    # Add to conversation
    st.session_state.conversation.append({"role": "user", "content": example})
    
    # Execute agent with proper timing
    try:
        start_time = time.time()
        result = st.session_state.agent.run(example)
        execution_time = time.time() - start_time
        
        response = result.get("analysis", "No response")
        st.session_state.conversation.append({"role": "assistant", "content": response})
        st.session_state.execution_trace.append({
            "query": example,
            "result": result,
            "execution_time": execution_time
        })
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.rerun()

# Footer with graph visualization
if st.session_state.execution_trace:
    st.markdown("---")
    with st.expander("📈 Full Execution History"):
        for i, trace in enumerate(reversed(st.session_state.execution_trace), 1):
            st.markdown(f"### Query {len(st.session_state.execution_trace) - i + 1}: {trace['query']}")
            
            if "execution_steps" in trace["result"]:
                cols = st.columns(6)
                steps = trace["result"]["execution_steps"]
                
                # Group steps by unique step names
                step_map = {}
                for step in steps:
                    if step["step"] not in step_map:
                        step_map[step["step"]] = step
                    else:
                        # Keep the completed/error status
                        if step["status"] in ["completed", "error"]:
                            step_map[step["step"]] = step
                
                for idx, (step_name, step_data) in enumerate(step_map.items()):
                    if idx < 6:
                        with cols[idx]:
                            if step_data["status"] == "completed":
                                st.success(f"✅")
                            elif step_data["status"] == "error":
                                st.error(f"❌")
                            else:
                                st.info(f"⏳")
                            st.caption(step_name)
                            st.caption(step_data.get("details", "")[:30] + "...")
            
            st.markdown(f"**Execution Time:** {trace.get('execution_time', 0):.2f}s")
            st.markdown("---")