# LangGraph workflow definition

from langgraph.graph import StateGraph, END
from .state import State
from .nodes import extract_data_node, generate_node, critique_node, refine_node
from .conditions import should_continue


def create_workflow():
    """
    Create LangGraph workflow
    """
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("extract", extract_data_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("critique", critique_node)
    workflow.add_node("refine", refine_node)
    
    # Define edges
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "generate")
    workflow.add_edge("generate", "critique")
    
    # Conditional edge after critique
    workflow.add_conditional_edges(
        "critique",
        should_continue,
        {
            "continue": "refine",
            "stop": END
        }
    )
    
    # Loop back from refine to critique
    workflow.add_edge("refine", "critique")
    
    return workflow.compile()


def run_cover_letter_generation(uploaded_file, job_url, max_iterations=3, quality_threshold=8.5):
    """
    Run the complete cover letter generation workflow
    """
    # Initialize state
    initial_state = {
        'uploaded_file': uploaded_file,
        'job_url': job_url,
        'max_iterations': max_iterations,
        'quality_threshold': quality_threshold,
        'resume_text': '',
        'job_text': '',
        'contact_info': {},  # Will be populated during extraction
        'drafts': [],
        'critiques': [],
        'current_iteration': 0,
        'stop_reason': ''
    }
    
    # Create and run workflow
    app = create_workflow()
    
    print("\n" + "="*70)
    print("STARTING COVER LETTER GENERATION WORKFLOW")
    print("="*70)
    
    # Run the workflow
    final_state = app.invoke(initial_state)
    
    print("\n" + "="*70)
    print("WORKFLOW COMPLETE")
    print("="*70)
    print(f"Total iterations: {final_state['current_iteration']}")
    print(f"Final score: {final_state['critiques'][-1]['overall_score']}/10")
    print(f"Stop reason: {final_state['stop_reason']}")
    print(f"Contact info extracted: {final_state['contact_info']['name']}")
    print("="*70 + "\n")
    
    return final_state