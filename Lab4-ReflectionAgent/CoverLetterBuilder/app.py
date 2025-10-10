# Streamlit app for Cover Letter Generator

import streamlit as st
import plotly.graph_objects as go
from graph import run_cover_letter_generation
from config import DEFAULT_MAX_ITERATIONS, DEFAULT_QUALITY_THRESHOLD

# Page config
st.set_page_config(
    page_title="AI Cover Letter Generator",
    page_icon="📝",
    layout="wide"
)

st.title("📝 AI Cover Letter Generator with Reflection")
st.markdown("Generate tailored cover letters using AI agents with iterative refinement")

# Sidebar inputs
st.sidebar.header("📋 Inputs")

uploaded_file = st.sidebar.file_uploader(
    "Upload Resume (PDF)",
    type=['pdf'],
    help="Upload your resume in PDF format"
)

job_url = st.sidebar.text_input(
    "Job Posting URL",
    placeholder="https://company.com/careers/job-123",
    help="Paste the URL of the job posting"
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Settings")

max_iterations = st.sidebar.slider(
    "Max Reflection Loops",
    min_value=1,
    max_value=5,
    value=DEFAULT_MAX_ITERATIONS,
    help="Number of refinement iterations"
)

quality_threshold = st.sidebar.slider(
    "Quality Threshold",
    min_value=7.0,
    max_value=9.5,
    value=DEFAULT_QUALITY_THRESHOLD,
    step=0.5,
    help="Stop if score exceeds this"
)

st.sidebar.info(f"""
**Current Settings:**
- Max iterations: {max_iterations}
- Quality threshold: {quality_threshold}/10
- Agent will stop when either condition is met
""")

# Main area
if st.sidebar.button("🚀 Generate Cover Letter", type="primary", use_container_width=True):
    
    if not uploaded_file or not job_url:
        st.error("⚠️ Please upload resume and provide job URL")
    
    else:
        # Create containers for real-time updates
        status_container = st.empty()
        progress_bar = st.progress(0)
        
        col1, col2 = st.columns(2)
        with col1:
            resume_status = st.empty()
        with col2:
            job_status = st.empty()
        
        results_container = st.container()
        
        try:
            # Show initial status
            status_container.info("🔄 Starting cover letter generation...")
            
            # Run the workflow
            with st.spinner("Processing..."):
                final_state = run_cover_letter_generation(
                    uploaded_file,
                    job_url,
                    max_iterations,
                    quality_threshold
                )
            
            progress_bar.progress(100)
            status_container.success("✅ Cover letter generation complete!")
            
            # Display extraction results
            resume_status.success(f"✅ Resume extracted")
            job_status.success(f"✅ Job description fetched")
            
            # Display results
            with results_container:
                st.markdown("---")
                st.header("📊 Results")
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Total Iterations",
                        final_state['current_iteration']
                    )
                
                with col2:
                    initial_score = final_state['critiques'][0]['overall_score']
                    final_score = final_state['critiques'][-1]['overall_score']
                    improvement = final_score - initial_score
                    
                    st.metric(
                        "Final Score",
                        f"{final_score}/10",
                        f"+{improvement:.1f}",
                        delta_color="normal"
                    )
                
                with col3:
                    st.metric(
                        "Stop Reason",
                        "Threshold" if final_state['stop_reason'] == 'quality_threshold' else "Max Iterations"
                    )
                
                # Score progression chart
                st.subheader("📈 Quality Score Progression")
                
                scores = [c['overall_score'] for c in final_state['critiques']]
                iterations = list(range(1, len(scores) + 1))
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=iterations,
                    y=scores,
                    mode='lines+markers',
                    name='Quality Score',
                    line=dict(color='green', width=3),
                    marker=dict(size=10)
                ))
                
                fig.add_hline(
                    y=quality_threshold,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Threshold: {quality_threshold}"
                )
                
                fig.update_layout(
                    xaxis_title="Iteration",
                    yaxis_title="Score (out of 10)",
                    yaxis_range=[0, 10],
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show all iterations in tabs
                st.subheader("📝 All Versions")
                
                tabs = st.tabs([f"Iteration {i+1}" for i in range(len(final_state['drafts']))])
                
                for i, tab in enumerate(tabs):
                    with tab:
                        draft = final_state['drafts'][i]
                        critique = final_state['critiques'][i]
                        
                        # Show draft
                        st.markdown("**Cover Letter:**")
                        st.text_area(
                            f"Draft {i+1}",
                            draft,
                            height=300,
                            key=f"draft_{i}",
                            label_visibility="collapsed"
                        )
                        
                        st.markdown(f"**Word Count:** {len(draft.split())}")
                        
                        # Show critique
                        st.markdown("---")
                        st.markdown("**Critique:**")
                        
                        # Scores
                        score_cols = st.columns(5)
                        score_names = [
                            "Job Alignment",
                            "Skill Highlight",
                            "Prof. Tone",
                            "Examples",
                            "Length"
                        ]
                        
                        for j, (col, name) in enumerate(zip(score_cols, score_names)):
                            score_key = list(critique['scores'].keys())[j]
                            score_val = critique['scores'][score_key]
                            col.metric(name, f"{score_val}/10")
                        
                        st.metric("Overall Score", f"{critique['overall_score']}/10")
                        
                        # Issues and suggestions
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Issues Found:**")
                            for issue in critique['issues']:
                                st.markdown(f"- {issue}")
                        
                        with col2:
                            st.markdown("**Suggestions:**")
                            for suggestion in critique['suggestions']:
                                st.markdown(f"- {suggestion}")
                
                # Final download
                st.markdown("---")
                st.subheader("💾 Download Final Version")
                
                final_letter = final_state['drafts'][-1]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📄 Download as TXT",
                        final_letter,
                        file_name="cover_letter.txt",
                        mime="text/plain"
                    )
                
                with col2:
                    st.button("📋 Copy to Clipboard", help="Click to copy")
        
        except Exception as e:
            status_container.error(f"❌ Error: {str(e)}")
            st.exception(e)

else:
    # Show instructions
    st.info("""
    ### How to use:
    1. Upload your resume (PDF format)
    2. Paste the job posting URL
    3. Adjust settings if needed (optional)
    4. Click "Generate Cover Letter"
    5. Watch the AI agents work in real-time!
    
    ### What happens:
    - **Step 1:** Extract resume & job description (parallel)
    - **Step 2:** Producer Agent generates initial draft
    - **Step 3:** Critic Agent evaluates and scores it
    - **Step 4:** Refiner Agent improves based on feedback
    - **Repeat:** Process continues until quality threshold or max iterations
    """)
    
    st.markdown("---")
    st.markdown("**Built with:** LangGraph + Snowflake Cortex + Streamlit")