# Email Tool - FIXED with Better Debugging

from utils.snowflake_connection import call_llm
from config import GMAIL_EMAIL, GMAIL_APP_PASSWORD
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import re

# STAGE 1: Parameter Extraction
def extract_email_parameters(user_query, context):
    """LLM extracts email recipients and content from query"""
    
    # Get meeting details from conversation
    attendees = context.get('attendees', [])
    date = context.get('date_preference', 'TBD')
    duration = context.get('duration', '1 hour')
    venue = "One Financial Center"  # Extract from conversation
    
    # Get weather info if available
    weather_info = ""
    weather_result = context.get('tool_results', {}).get('weather_tool', {})
    if weather_result.get('raw'):
        weather_data = weather_result['raw']
        weather_info = f"Weather: {weather_data.get('temperature')}°F, {weather_data.get('condition')}"
    
    # Build email body
    email_body = f"""Hello,

You are invited to a team meeting:

Date: {date}
Duration: {duration}
Venue: {venue}
{weather_info}

Please confirm your attendance.

Best regards,
Meeting Planner Assistant"""
    
    return {
        "to_emails": attendees,
        "subject": f"Team Meeting - {date}",
        "body": email_body
    }


# STAGE 2: API Call (Gmail SMTP)
def call_email_api(params):
    """
    Send email via Gmail SMTP with better error handling
    """
    
    print(f"[DEBUG] Email API Check:")
    print(f"  GMAIL_EMAIL loaded: {bool(GMAIL_EMAIL)}")
    print(f"  GMAIL_EMAIL value: {repr(GMAIL_EMAIL)[:50]}...")
    print(f"  GMAIL_APP_PASSWORD loaded: {bool(GMAIL_APP_PASSWORD)}")
    print(f"  GMAIL_APP_PASSWORD length: {len(GMAIL_APP_PASSWORD) if GMAIL_APP_PASSWORD else 0}")
    
    # Clean credentials (remove quotes if present)
    gmail_email = GMAIL_EMAIL.strip('"').strip("'") if GMAIL_EMAIL else None
    gmail_password = GMAIL_APP_PASSWORD.strip('"').strip("'") if GMAIL_APP_PASSWORD else None
    
    print(f"[DEBUG] After cleaning:")
    print(f"  Email: {gmail_email}")
    print(f"  Password length: {len(gmail_password) if gmail_password else 0}")
    
    if not gmail_email or not gmail_password:
        return {
            'success': False,
            'error': 'Gmail credentials not configured. Please check .env file has GMAIL_EMAIL and GMAIL_APP_PASSWORD'
        }
    
    to_emails = params.get('to_emails', [])
    subject = params.get('subject', 'Meeting Invitation')
    body = params.get('body', '')
    
    print(f"[DEBUG] Sending email to: {to_emails}")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"[DEBUG] Connecting to Gmail SMTP...")
        
        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as smtp:
            print(f"[DEBUG] Logging in as {gmail_email}...")
            smtp.login(gmail_email, gmail_password)
            
            print(f"[DEBUG] Sending message...")
            smtp.send_message(msg)
        
        print(f"[DEBUG] Email sent successfully!")
        
        return {
            'success': True,
            'sent_to': to_emails,
            'subject': subject
        }
    
    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] SMTP Authentication failed: {e}")
        return {
            'success': False,
            'error': f'Gmail authentication failed. Please check your GMAIL_EMAIL and GMAIL_APP_PASSWORD are correct. Error: {str(e)}'
        }
    
    except smtplib.SMTPException as e:
        print(f"[ERROR] SMTP error: {e}")
        return {
            'success': False,
            'error': f'Email sending failed: {str(e)}'
        }
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'Error: {str(e)}'
        }


# STAGE 3: Format Result
def format_email_result(api_response, user_query):
    """LLM formats email send confirmation"""
    
    if api_response.get('success'):
        return f"✅ Meeting invitations sent successfully to: {', '.join(api_response.get('sent_to', []))}"
    else:
        return f"❌ Failed to send email: {api_response.get('error', 'Unknown error')}"


# MAIN FUNCTION: Executes all 3 stages
def send_meeting_invite(user_query, context):
    """
    Complete 3-stage email send
    
    Stage 1: Extract params
    Stage 2: Send email via Gmail
    Stage 3: Format confirmation
    """
    
    print(f"\n[DEBUG] ===== EMAIL TOOL START =====")
    
    # Stage 1
    params = extract_email_parameters(user_query, context)
    print(f"[DEBUG] Email params: to={params['to_emails']}, subject={params['subject'][:30]}...")
    
    # Stage 2
    api_result = call_email_api(params)
    print(f"[DEBUG] Email API result: success={api_result.get('success')}")
    
    # Stage 3
    formatted_result = format_email_result(api_result, user_query)
    print(f"[DEBUG] ===== EMAIL TOOL END =====\n")
    
    return {
        'raw': api_result,
        'formatted': formatted_result,
        'params_used': params
    }