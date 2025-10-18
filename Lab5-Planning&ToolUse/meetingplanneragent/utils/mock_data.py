# Mock calendar data for team members - UPDATED EMAIL ADDRESSES

from datetime import datetime, timedelta

# Mock team member calendars - October 19, 2025
MOCK_CALENDARS = {
    'ramkumarrp16077@gmail.com': {
        'name': 'Ram',
        'busy_slots': [
            {'start': '2025-10-19T09:00:00', 'end': '2025-10-19T10:00:00'},  # 9-10am
            {'start': '2025-10-19T14:00:00', 'end': '2025-10-19T15:00:00'},  # 2-3pm
        ]
    },
    'ramasamypandiaraj.r@northeastern.edu': {
        'name': 'Saliba',
        'busy_slots': [
            {'start': '2025-10-19T10:00:00', 'end': '2025-10-19T11:00:00'},  # 10-11am
            {'start': '2025-10-19T15:00:00', 'end': '2025-10-19T16:00:00'},  # 3-4pm
        ]
    },
    'ramgeon243@gmail.com': {
        'name': 'Gabriel',
        'busy_slots': [
            {'start': '2025-10-19T11:00:00', 'end': '2025-10-19T12:00:00'},  # 11am-12pm
        ]
    }
}


def get_mock_calendar_data(email):
    """Get mock calendar for a team member"""
    return MOCK_CALENDARS.get(email.lower(), {'name': email, 'busy_slots': []})


def find_common_slots(attendee_emails, date_str, duration_hours=1):
    """
    Find common free time slots for all attendees
    
    Args:
        attendee_emails: List of email addresses
        date_str: Date string like "2025-10-19" or "October 19"
        duration_hours: Meeting duration in hours
        
    Returns:
        Dict with individual and common availability
    """
    
    # Get each person's calendar
    individual_availability = {}
    for email in attendee_emails:
        cal_data = get_mock_calendar_data(email)
        individual_availability[email] = {
            'name': cal_data['name'],
            'busy_slots': cal_data['busy_slots']
        }
    
    # Common free slots (hardcoded based on above busy times)
    # Everyone is free: 11am-12pm, 12pm-1pm, 1pm-2pm
    common_slots = [
        {'start_time': '11:00 AM', 'end_time': '12:00 PM', 'duration': '1 hour'},
        {'start_time': '12:00 PM', 'end_time': '1:00 PM', 'duration': '1 hour'},
        {'start_time': '1:00 PM', 'end_time': '2:00 PM', 'duration': '1 hour'},
    ]
    
    return {
        'individual_availability': individual_availability,
        'common_slots': common_slots,
        'recommended_slot': common_slots[1] if len(common_slots) > 1 else common_slots[0]  # Recommend 12-1pm
    }