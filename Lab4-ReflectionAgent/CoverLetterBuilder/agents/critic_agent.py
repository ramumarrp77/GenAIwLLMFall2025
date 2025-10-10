# Critic Agent - Evaluates cover letters
# Uses Snowflake Cortex

from utils.snowflake_connection import call_llm
import json
import re

def critique_cover_letter(cover_letter, resume_text, job_description):
    """
    Evaluate cover letter
    Returns dict with scores and feedback
    """
    print("🔍 Critic: Evaluating cover letter...")
    
    word_count = len(cover_letter.split())
    
    prompt = f"""You are a senior HR professional evaluating a cover letter.

Job Description:
{job_description}

Candidate Resume:
{resume_text}

Cover Letter ({word_count} words):
{cover_letter}

Evaluate on these 5 criteria (score 1-10 each):
1. Job Alignment: Does it address specific job requirements?
2. Skill Highlighting: Does it showcase relevant resume skills?
3. Professional Tone: Is the language appropriate?
4. Specific Examples: Does it include concrete achievements?
5. Length: Is it concise (300-400 words)?

Respond in this EXACT JSON format:
{{
  "scores": {{
    "job_alignment": X,
    "skill_highlighting": X,
    "professional_tone": X,
    "specific_examples": X,
    "length": X
  }},
  "overall_score": X.X,
  "issues": ["issue 1", "issue 2"],
  "suggestions": ["suggestion 1", "suggestion 2"]
}}

Be specific and actionable."""

    response = call_llm(prompt)
    
    # Parse JSON from response
    try:
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            critique = json.loads(json_match.group())
        else:
            critique = json.loads(response)
        
        # Calculate overall if missing
        if 'overall_score' not in critique or critique['overall_score'] == 0:
            scores = critique['scores']
            overall = sum(scores.values()) / len(scores)
            critique['overall_score'] = round(overall, 1)
        
        print(f"✓ Score: {critique['overall_score']}/10")
        
        return critique
    
    except Exception as e:
        print(f"⚠️ JSON parsing failed: {e}")
        print("Using fallback critique...")
        
        # Fallback critique
        return {
            'scores': {
                'job_alignment': 7,
                'skill_highlighting': 7,
                'professional_tone': 8,
                'specific_examples': 6,
                'length': 8
            },
            'overall_score': 7.2,
            'issues': ['Could not parse detailed feedback'],
            'suggestions': ['Review manually']
        }