# Formatter Agent - Formats cover letter professionally
# Uses Snowflake Cortex to add proper business letter structure

from utils.snowflake_connection import call_llm
from datetime import date

def format_cover_letter(cover_letter_content, candidate_name="[Your Name]", candidate_address="[Your Address]", candidate_phone="[Your Phone]", candidate_email="[Your Email]"):
    """
    Format cover letter with proper business letter structure
    Uses LLM to intelligently add formatting while preserving content
    """
    print("📝 Formatter: Structuring cover letter...")
    
    today = date.today().strftime("%B %d, %Y")
    
    prompt = f"""You are a professional document formatter. Format this cover letter content into a proper business letter structure.

Cover Letter Content:
{cover_letter_content}

Instructions:
1. Add proper business letter header with:
   - Candidate name: {candidate_name}
   - Address: {candidate_address}
   - Phone: {candidate_phone}
   - Email: {candidate_email}
   - Date: {today}

2. Add appropriate salutation (use "Dear Hiring Manager," if no specific name in content)

3. Keep the main content EXACTLY as provided

4. Add professional closing:
   - "Sincerely," or "Best regards,"
   - {candidate_name}

5. Format with proper spacing and paragraphs

Return ONLY the formatted letter, no explanations.

Example format:
{candidate_name}
{candidate_address}
{candidate_phone} | {candidate_email}

{today}

Dear Hiring Manager,

[Content goes here, preserved exactly]

Sincerely,
{candidate_name}
"""

    formatted_letter = call_llm(prompt)
    
    print("✓ Letter formatted")
    
    return formatted_letter