"""
Lab 10: SafeAI Monitor - Streamlit in Snowflake Application
"""

import streamlit as st
from snowflake.snowpark.context import get_active_session
import os
import pandas as pd

# CRITICAL: Set before TruLens imports
os.environ["TRULENS_OTEL_TRACING"] = "1"

# Imports
import sys
sys.path.append('utils')
sys.path.append('guardrails')
sys.path.append('evaluation')
sys.path.append('monitoring')
sys.path.append('observability')

from cortex_helpers import call_cortex
from input_validator import validate_input
from policy_enforcer import check_policy
from metrics_collector import MetricsCollector
from llm_judge import evaluate_response, compare_responses
from logger import create_logging_table, log_interaction
from analytics import get_recent_interactions, get_aggregate_metrics, get_daily_trends, get_blocked_reasons
from instrumented_app import InstrumentedSafeAI
from trulens_manager import TruLensManager
from snowflake_observer import get_evaluation_runs, get_evaluation_summary

# Page config
st.set_page_config(
    page_title="SafeAI Monitor",
    page_icon="🛡️",
    layout="wide"
)

# Get session
session = get_active_session()

# Initialize session state
if 'initialized' not in st.session_state:
    create_logging_table()
    st.session_state.instrumented_app = InstrumentedSafeAI(session)
    st.session_state.trulens_manager = TruLensManager(session, st.session_state.instrumented_app)
    st.session_state.initialized = True

# Header
st.title("🛡️ SafeAI Monitor")
st.markdown("Production-Ready LLM with Guardrails & AI Observability")
st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🛡️ Safe Chat",
    "📊 Evaluation Lab",
    "🔬 AI Observability",
    "📈 Production Monitor"
])

# ============================================================================
# TAB 1: SAFE CHAT
# ============================================================================

with tab1:
    st.header("Safe Chat with Guardrails")
    st.markdown("Interactive demo showing guardrails in action")
    
    # User input
    user_query = st.text_area("Enter your query:", height=100, placeholder="Ask me anything...")
    
    if st.button("🚀 Send Safely", type="primary"):
        if user_query:
            # Create columns for pipeline stages
            col1, col2, col3, col4 = st.columns(4)
            
            # Stage 1: Input Validation
            with col1:
                with st.container(border=True):
                    st.markdown("**Stage 1**")
                    st.markdown("Input Validation")
                    input_result = validate_input(user_query)
                    if input_result['valid']:
                        st.success("✓ Passed")
                    else:
                        st.error("✗ Blocked")
                        st.caption(input_result['message'])
            
            # Stage 2: Policy Check
            with col2:
                with st.container(border=True):
                    st.markdown("**Stage 2**")
                    st.markdown("Policy Check")
                    if input_result['valid']:
                        policy_result = check_policy(user_query)
                        if policy_result['compliant']:
                            st.success("✓ Compliant")
                        else:
                            st.error("✗ Blocked")
                            st.caption(policy_result['reason'])
                    else:
                        st.warning("⊘ Skipped")
            
            # Stage 3: LLM Generation
            with col3:
                with st.container(border=True):
                    st.markdown("**Stage 3**")
                    st.markdown("LLM Generation")
                    if input_result['valid'] and policy_result['compliant']:
                        with st.spinner("Generating..."):
                            metrics = MetricsCollector()
                            metrics.start()
                            llm_response = call_cortex(user_query)
                            metrics_data = metrics.end(user_query, llm_response)
                        st.success("✓ Generated")
                        st.caption(f"{metrics_data['latency_seconds']}s")
                    else:
                        st.warning("⊘ Skipped")
                        llm_response = None
            
            # Stage 4: Logging
            with col4:
                with st.container(border=True):
                    st.markdown("**Stage 4**")
                    st.markdown("Logging")
                    if llm_response:
                        log_interaction(
                            user_query, 
                            llm_response, 
                            metrics_data,
                            "valid" if input_result['valid'] else "invalid",
                            "compliant" if policy_result['compliant'] else "blocked"
                        )
                        st.success("✓ Logged")
                    else:
                        st.warning("⊘ Skipped")
            
            # Display final response or block message
            st.markdown("---")
            if llm_response:
                st.success("**Final Response:**")
                st.write(llm_response)
                
                # Show metrics
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("Latency", f"{metrics_data['latency_seconds']}s")
                col_m2.metric("Input Tokens", metrics_data['input_tokens'])
                col_m3.metric("Output Tokens", metrics_data['output_tokens'])
                col_m4.metric("Cost", f"${metrics_data['total_cost']}")
            else:
                st.error("**Request Blocked by Guardrails**")
                if not input_result['valid']:
                    st.warning(f"Reason: {input_result['message']}")
                elif not policy_result['compliant']:
                    st.warning(f"Reason: {policy_result['reason']}")
                    if policy_result['violations']:
                        st.caption(f"Violations: {', '.join(policy_result['violations'])}")

# ============================================================================
# TAB 2: EVALUATION LAB
# ============================================================================

with tab2:
    st.header("Evaluation Lab")
    st.markdown("Test and evaluate LLM responses")
    
    eval_type = st.radio("Evaluation Type", ["Single Response", "Compare Responses"])
    
    if eval_type == "Single Response":
        st.subheader("Single Response Evaluation")
        
        col1, col2 = st.columns(2)
        with col1:
            eval_query = st.text_input("Query:", value="What is machine learning?")
        with col2:
            eval_metric = st.selectbox("Metric", ["helpfulness", "safety", "coherence"])
        
        if st.button("Generate & Evaluate"):
            with st.spinner("Generating response..."):
                response = call_cortex(eval_query)
            
            st.write("**Generated Response:**")
            st.info(response)
            
            with st.spinner("Evaluating..."):
                evaluation = evaluate_response(eval_query, response, eval_metric)
            
            col_e1, col_e2 = st.columns([1, 3])
            with col_e1:
                st.metric(f"{eval_metric.capitalize()} Score", f"{evaluation['score']}/5")
            with col_e2:
                st.write("**Reasoning:**")
                st.write(evaluation['reasoning'])
    
    else:
        st.subheader("Compare Two Responses")
        
        compare_query = st.text_input("Query:", value="Explain neural networks")
        
        col1, col2 = st.columns(2)
        with col1:
            model_a = st.selectbox("Model A", ["llama3.1-70b", "mistral-large2"], index=0)
        with col2:
            model_b = st.selectbox("Model B", ["llama3.1-70b", "mistral-large2"], index=1)
        
        if st.button("Generate & Compare"):
            with st.spinner("Generating responses..."):
                response_a = call_cortex(compare_query, model=model_a)
                response_b = call_cortex(compare_query, model=model_b)
            
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.write(f"**Response A ({model_a}):**")
                st.info(response_a)
            with col_r2:
                st.write(f"**Response B ({model_b}):**")
                st.info(response_b)
            
            with st.spinner("Comparing..."):
                comparison = compare_responses(compare_query, response_a, response_b)
            
            st.markdown("---")
            st.subheader("Comparison Result")
            if comparison['winner'] != "error":
                st.success(f"**Winner: Response {comparison['winner']}**")
                st.write(f"**Reasoning:** {comparison['reasoning']}")
            else:
                st.error(comparison['reasoning'])

# ============================================================================
# TAB 3: AI OBSERVABILITY
# ============================================================================

with tab3:
    st.header("🔬 AI Observability")
    st.markdown("Powered by Snowflake TruLens SDK")
    
    # Check if AI Observability is available
    try:
        session.sql("SELECT * FROM SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS LIMIT 1").collect()
        ai_obs_available = True
    except:
        ai_obs_available = False
        st.warning("⚠️ AI Observability is not enabled in this Snowflake account.")
        st.info("This tab requires Snowflake AI Observability feature. Contact your Snowflake admin to enable it.")
        st.markdown("**You can still use:**")
        st.markdown("- Tab 1: Safe Chat with guardrails")
        st.markdown("- Tab 2: Evaluation Lab with LLM-as-a-Judge")
        st.markdown("- Tab 4: Production monitoring with custom logging")
        st.stop()
    
    if not ai_obs_available:
        st.stop()
    
    # Section 1: Run Evaluation
    with st.expander("▶️ Run New Evaluation", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            dataset_name = st.text_input("Dataset Table Name", value="test_queries")
            judge_model = st.selectbox("Judge Model", ["llama3.1-70b", "mistral-large2"])
        
        with col2:
            metrics_to_compute = st.multiselect(
                "Metrics to Compute",
                ["context_relevance", "groundedness", "answer_relevance", "correctness", "coherence"],
                default=["context_relevance", "groundedness", "answer_relevance"]
            )
        
        if st.button("🚀 Start Evaluation Run"):
            with st.spinner("Running evaluation..."):
                try:
                    result = st.session_state.trulens_manager.run_evaluation(
                        dataset_name=dataset_name,
                        metrics=metrics_to_compute,
                        judge_model=judge_model
                    )
                    st.success(f"✓ Evaluation complete: {result['run_name']}")
                    st.json(result)
                except Exception as e:
                    st.error(f"Evaluation failed: {str(e)}")
    
    # Section 2: Recent Runs
    st.subheader("📊 Recent Evaluation Runs")
    
    try:
        runs_df = get_evaluation_runs(limit=10)
        if not runs_df.empty:
            st.dataframe(runs_df, use_container_width=True)
            
            # Select run for details
            selected_run = st.selectbox("View Run Details", runs_df['RUN_NAME'].tolist())
            
            if selected_run:
                summary_df = get_evaluation_summary(selected_run)
                st.subheader(f"Results for: {selected_run}")
                st.dataframe(summary_df, use_container_width=True)
                
                # Display scores as metrics
                if not summary_df.empty:
                    cols = st.columns(len(summary_df))
                    for idx, row in summary_df.iterrows():
                        with cols[idx]:
                            st.metric(
                                row['METRIC_NAME'],
                                f"{row['AVG_SCORE']:.2f}",
                                delta=None
                            )
        else:
            st.info("No evaluation runs found. Run an evaluation to see results here.")
    except Exception as e:
        st.warning(f"Unable to fetch evaluation runs: {str(e)}")
        st.info("Make sure you have run at least one evaluation.")

# ============================================================================
# TAB 4: PRODUCTION MONITOR
# ============================================================================

with tab4:
    st.header("📈 Production Monitor")
    st.markdown("Real-time metrics and analytics")
    
    # KPI Cards
    try:
        metrics = get_aggregate_metrics(days=7)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Calls", int(metrics.get('TOTAL_INTERACTIONS', 0)))
        with col2:
            st.metric("Avg Latency", f"{metrics.get('AVG_LATENCY', 0):.2f}s")
        with col3:
            st.metric("Total Cost", f"${metrics.get('TOTAL_COST', 0):.4f}")
        with col4:
            st.metric("Block Rate", f"{metrics.get('POLICY_BLOCK_RATE', 0):.1f}%")
    except Exception as e:
        st.warning("No data available yet. Start using the Safe Chat to generate metrics.")
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("Recent Activity")
    try:
        recent_df = get_recent_interactions(limit=10)
        if not recent_df.empty:
            # Format for display
            display_df = recent_df.copy()
            display_df['INPUT_TEXT'] = display_df['INPUT_TEXT'].str[:50] + "..."
            display_df['TIMESTAMP'] = pd.to_datetime(display_df['TIMESTAMP']).dt.strftime('%H:%M:%S')
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No interactions logged yet.")
    except Exception as e:
        st.info("No interactions logged yet. Use Safe Chat to start.")
    
    # Daily Trends
    st.subheader("7-Day Trends")
    try:
        trends_df = get_daily_trends(days=7)
        if not trends_df.empty:
            import plotly.express as px
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                fig1 = px.line(trends_df, x='DATE', y='INTERACTIONS', title='Daily Interactions')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col_chart2:
                fig2 = px.line(trends_df, x='DATE', y='DAILY_COST', title='Daily Cost')
                st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.info("Not enough data for trends yet.")
    
    # Blocked Reasons Distribution
    st.subheader("Blocked Requests Analysis")
    try:
        blocked_df = get_blocked_reasons()
        if not blocked_df.empty:
            import plotly.express as px
            fig = px.pie(blocked_df, names='REASON', values='COUNT', title='Block Reasons')
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        pass

# Footer
st.markdown("---")
st.caption("Lab 10: Guardrails & Evaluation | DAMG 7374 | Northeastern University")