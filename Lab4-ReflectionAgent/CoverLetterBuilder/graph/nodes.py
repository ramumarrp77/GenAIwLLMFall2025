# LangGraph node functions

from concurrent.futures import ThreadPoolExecutor
import time

from utils import extract_resume, fetch_job, extract_contact_info
from agents import generate_cover_letter, refine_cover_letter, critique_cover_letter


def extract_data_node(state):
    """
    Node 1: Extract resume and job description in parallel
    Then extract contact information from resume
    """
    print("\n" + "="*70)
    print("STEP 1: PARALLEL DATA EXTRACTION")
    print("="*70)
    
    start = time.time()
    
    # Run both in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        resume_future = executor.submit(extract_resume, state['uploaded_file'])
        job_future = executor.submit(fetch_job, state['job_url'])
        
        resume_result = resume_future.result()
        job_result = job_future.result()
    
    elapsed = time.time() - start
    print(f"\n✓ Parallel extraction done in {elapsed:.2f}s\n")
    
    if not resume_result['success']:
        raise Exception(f"Resume extraction failed: {resume_result['error']}")
    
    if not job_result['success']:
        raise Exception(f"Job fetch failed: {job_result['error']}")
    
    state['resume_text'] = resume_result['text']
    state['job_text'] = job_result['text']
    
    # Extract contact information from resume
    print("Extracting contact information from resume...")
    contact_info = extract_contact_info(resume_result['text'])
    state['contact_info'] = contact_info
    
    print()
    return state


def generate_node(state):
    """
    Node 2: Generate initial draft
    """
    print("\n" + "="*70)
    print(f"STEP 2: GENERATE DRAFT (Iteration 1)")
    print("="*70)
    
    cover_letter = generate_cover_letter(state['resume_text'], state['job_text'])
    
    state['drafts'].append(cover_letter)
    state['current_iteration'] = 1
    
    print()
    return state


def critique_node(state):
    """
    Node 3: Critique current draft
    """
    print("\n" + "="*70)
    print(f"STEP 3: CRITIQUE DRAFT (Iteration {state['current_iteration']})")
    print("="*70)
    
    current_draft = state['drafts'][-1]
    critique = critique_cover_letter(current_draft, state['resume_text'], state['job_text'])
    
    state['critiques'].append(critique)
    
    print()
    return state


def refine_node(state):
    """
    Node 4: Refine draft based on critique
    """
    print("\n" + "="*70)
    print(f"STEP 4: REFINE DRAFT (Iteration {state['current_iteration'] + 1})")
    print("="*70)
    
    prev_draft = state['drafts'][-1]
    prev_critique = state['critiques'][-1]
    
    refined = refine_cover_letter(prev_draft, prev_critique, state['resume_text'], state['job_text'])
    
    state['drafts'].append(refined)
    state['current_iteration'] += 1
    
    print()
    return state