# Streamlit app for Cover Letter Generator

import streamlit as st
import plotly.graph_objects as go
from graph import run_cover_letter_generation
from agents import format_cover_letter
from utils import create_docx, create_pdf
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
- Contact info will be extracted automatically from resume
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
        
        contact_info_display = st.container()
        extraction_display = st.container()
        results_container = st.container()
        
        try:
            # Show initial status
            status_container.info("🔄 Starting cover letter generation...")
            progress_bar.progress(10)
            
            # Run the workflow
            with st.spinner("Processing..."):
                final_state = run_cover_letter_generation(
                    uploaded_file,
                    job_url,
                    max_iterations,
                    quality_threshold
                )
            
            progress_bar.progress(90)
            
            # Display extraction results
            resume_status.success(f"✅ Resume extracted")
            job_status.success(f"✅ Job description fetched")
            
            # Get contact info from state
            contact_info = final_state['contact_info']
            
            # Display extracted contact information
            with contact_info_display:
                st.markdown("---")
                st.subheader("👤 Extracted Contact Information")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Name", contact_info['name'])
                
                with col2:
                    st.metric("Email", contact_info['email'])
                
                with col3:
                    st.metric("Phone", contact_info['phone'])
                
                with col4:
                    address_display = contact_info['address'][:30] + "..." if len(contact_info['address']) > 30 else contact_info['address']
                    st.metric("Address", address_display)
                
                # Allow manual override if extraction failed
                with st.expander("✏️ Edit Contact Information (Optional)"):
                    st.info("If the extracted information is incorrect, you can edit it here:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        override_name = st.text_input("Name", value=contact_info['name'], key="edit_name")
                        override_phone = st.text_input("Phone", value=contact_info['phone'], key="edit_phone")
                    with col2:
                        override_email = st.text_input("Email", value=contact_info['email'], key="edit_email")
                        override_address = st.text_input("Address", value=contact_info['address'], key="edit_address")
                    
                    if st.button("Update Contact Info"):
                        contact_info = {
                            'name': override_name,
                            'email': override_email,
                            'phone': override_phone,
                            'address': override_address
                        }
                        st.success("✓ Contact information updated")
            
            # Format the final cover letter with extracted contact info
            status_container.info("📝 Formatting final cover letter...")
            formatted_letter = format_cover_letter(
                final_state['drafts'][-1],
                contact_info['name'],
                contact_info['address'],
                contact_info['phone'],
                contact_info['email']
            )
            
            progress_bar.progress(100)
            status_container.success("✅ Cover letter generation complete!")
            
            # Display extracted content
            with extraction_display:
                st.markdown("---")
                st.header("📄 Extracted Content")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    with st.expander("📝 Resume Content", expanded=False):
                        st.markdown(f"**Word Count:** {len(final_state['resume_text'].split())} words")
                        st.text_area(
                            "Resume Text",
                            final_state['resume_text'],
                            height=300,
                            key="resume_display",
                            label_visibility="collapsed"
                        )
                
                with col2:
                    with st.expander("🌐 Job Description", expanded=False):
                        st.markdown(f"**Word Count:** {len(final_state['job_text'].split())} words")
                        st.text_area(
                            "Job Description",
                            final_state['job_text'],
                            height=300,
                            key="job_display",
                            label_visibility="collapsed"
                        )
            
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
                
                # Display formatted final version
                st.markdown("---")
                st.header("📄 Final Formatted Cover Letter")
                
                st.text_area(
                    "Professionally Formatted",
                    formatted_letter,
                    height=400,
                    key="formatted_final",
                    label_visibility="collapsed"
                )
                
                # Download options
                st.subheader("💾 Download Options")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        "📄 Download as TXT",
                        formatted_letter,
                        file_name="cover_letter.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col2:
                    # Create DOCX
                    docx_buffer = create_docx(formatted_letter)
                    st.download_button(
                        "📝 Download as DOCX",
                        docx_buffer,
                        file_name="cover_letter.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                
                with col3:
                    # Create PDF
                    pdf_bytes = create_pdf(formatted_letter)
                    st.download_button(
                        "📕 Download as PDF",
                        pdf_bytes,
                        file_name="cover_letter.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        
        except Exception as e:
            status_container.error(f"❌ Error: {str(e)}")
            st.exception(e)

else:
    # Show instructions
    st.info("""
    ### How to use:
    1. Upload your resume (PDF format) - contact info will be extracted automatically
    2. Paste the job posting URL
    3. Adjust settings if needed (optional)
    4. Click "Generate Cover Letter"
    5. Download in TXT, DOCX, or PDF format!
    
    ### What happens:
    - **Step 1:** Extract resume, job description, and contact info (parallel)
    - **Step 2:** Producer Agent generates initial draft
    - **Step 3:** Critic Agent evaluates and scores it
    - **Step 4:** Refiner Agent improves based on feedback
    - **Step 5:** Formatter Agent adds professional structure with your contact info
    - **Repeat:** Steps 2-4 continue until quality threshold or max iterations
    """)
    
    st.markdown("---")
    st.markdown("**Built with:** LangGraph + Snowflake Cortex + Streamlit")