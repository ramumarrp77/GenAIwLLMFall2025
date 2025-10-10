# Producer Agent - Generates and refines cover letters
# Uses Snowflake Cortex

from utils.snowflake_connection import call_llm

def generate_cover_letter(resume_text, job_description):
    """
    Generate initial cover letter
    Takes resume and job description, returns cover letter
    """
    print("✍️ Producer: Generating initial cover letter...")
    
    prompt = f"""You are an expert cover letter writer.

Job Description:
{job_description}

Candidate Resume:
{resume_text}

Write a compelling cover letter (300-400 words) that:
1. Addresses specific job requirements
2. Highlights relevant skills from the resume
3. Uses professional tone
4. Includes concrete examples
5. Shows enthusiasm for the role

Write ONLY the cover letter, no extra commentary."""

    cover_letter = call_llm(prompt)
    word_count = len(cover_letter.split())
    
    print(f"✓ Generated {word_count} words")
    
    return cover_letter


def refine_cover_letter(draft, critique, resume_text, job_description):
    """
    Refine cover letter based on critique
    Takes previous draft + feedback, returns improved version
    """
    print("♻️ Refiner: Improving based on critique...")
    
    # Format the critique for the prompt
    critique_text = f"""Overall Score: {critique['overall_score']}/10

Issues Found:
{chr(10).join('- ' + issue for issue in critique['issues'])}

Suggestions:
{chr(10).join('- ' + suggestion for suggestion in critique['suggestions'])}"""

    prompt = f"""You are refining a cover letter based on expert feedback.

Previous Draft:
{draft}

Critique:
{critique_text}

Job Description:
{job_description}

Candidate Resume:
{resume_text}

Improve the cover letter by addressing ALL the issues mentioned.
Keep what's good, fix what's not.
Write ONLY the improved cover letter."""

    refined = call_llm(prompt)
    word_count = len(refined.split())
    
    print(f"✓ Refined version: {word_count} words")
    
    return refined