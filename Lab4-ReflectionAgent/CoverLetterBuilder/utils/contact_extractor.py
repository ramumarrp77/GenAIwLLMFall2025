# Contact Information Extractor
# Extract candidate info from resume using LLM

from utils.snowflake_connection import call_llm
import json
import re

def extract_contact_info(resume_text):
    """
    Extract contact information from resume text
    Returns dict with name, address, phone, email
    """
    print("👤 Extracting contact information from resume...")
    
    prompt = f"""Extract the candidate's contact information from this resume.

Resume:
{resume_text}

Extract:
1. Full name
2. Address (full address or city, state)
3. Phone number
4. Email address

Return ONLY a JSON object in this exact format:
{{
  "name": "Full Name",
  "address": "City, State or Full Address",
  "phone": "Phone Number",
  "email": "email@example.com"
}}

If any field is not found, use "Not Found" as the value.
Return ONLY the JSON, nothing else."""

    response = call_llm(prompt)
    
    # Parse JSON from response
    try:
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            contact_info = json.loads(json_match.group())
        else:
            contact_info = json.loads(response)
        
        # Ensure all fields exist
        required_fields = ['name', 'address', 'phone', 'email']
        for field in required_fields:
            if field not in contact_info:
                contact_info[field] = "Not Found"
        
        print(f"✓ Extracted contact info:")
        print(f"   Name: {contact_info['name']}")
        print(f"   Email: {contact_info['email']}")
        
        return contact_info
    
    except Exception as e:
        print(f"⚠️ Failed to parse contact info: {e}")
        
        # Fallback - use default values
        return {
            'name': '[Your Name]',
            'address': '[Your Address]',
            'phone': '[Your Phone]',
            'email': '[Your Email]'
        }