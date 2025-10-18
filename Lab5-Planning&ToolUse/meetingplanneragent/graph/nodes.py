# LangGraph node functions for Meeting Planner
# Complete implementation with multi-tool support and intent-based controller

from langchain_core.messages import HumanMessage, AIMessage
from utils.snowflake_connection import call_llm
from tools import check_availability, get_weather_forecast, search_venues, send_meeting_invite
import json
import re


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _extract_user_message(messages):
    """Extract the last user message from conversation"""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    return ""


def _messages_to_text(messages, limit=6):
    """Convert LangChain messages to text for LLM prompt"""
    conversation_text = ""
    for msg in messages[-limit:]:
        if isinstance(msg, HumanMessage):
            conversation_text += f"User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            conversation_text += f"Assistant: {msg.content}\n"
    return conversation_text


# ============================================================
# CONTROLLER NODE
# ============================================================

def controller_node(state):
    """
    INTENT-BASED Controller:
    1. Analyzes user's message for explicit requests (like EventLens)
    2. Falls back to state-based logic
    3. Can return MULTIPLE tools to execute in one turn
    """
    
    print(f"\n[DEBUG] ===== CONTROLLER START =====")
    
    messages = state.get("messages", [])
    last_user_message = _extract_user_message(messages)
    
    # Get current state
    attendees = state.get('attendees')
    date_pref = state.get('date_preference')
    venue_pref = state.get('venue_preference')
    tools_already_called = state.get('tools_called') or []
    
    print(f"[DEBUG] State: Attendees={bool(attendees)}, Date={bool(date_pref)}, Venue={bool(venue_pref)}")
    print(f"[DEBUG] Tools already called: {tools_already_called}")
    print(f"[DEBUG] User message: {last_user_message[:80]}")
    
    # Check if we're continuing multi-tool execution
    tools_to_call_this_turn = state.get('tools_to_call') or []
    tools_done_this_turn = state.get('tools_done_this_turn') or []
    
    if tools_to_call_this_turn:
        remaining = [t for t in tools_to_call_this_turn if t not in tools_done_this_turn]
        if remaining:
            print(f"[DEBUG] Continuing multi-tool: {remaining}")
            return {
                "current_tool": remaining[0],
                "need_final_answer": False
            }
    
    # FRESH DECISION: What tools do we need this turn?
    tools_needed = []
    user_lower = last_user_message.lower()
    
    # ============================================================
    # 1. INTENT-BASED LOGIC (Check user's explicit requests)
    # ============================================================
    
    # User explicitly asks for weather
    if ('weather' in user_lower or 'forecast' in user_lower) and 'weather_tool' not in tools_already_called:
        print("[DEBUG] User explicitly asked for weather")
        tools_needed.append('weather_tool')
    
    # User explicitly asks for venues/places
    if ('venue' in user_lower or 'place' in user_lower or 'location' in user_lower or 
        'suggest' in user_lower or 'recommend' in user_lower) and 'places_tool' not in tools_already_called:
        print("[DEBUG] User explicitly asked for venues")
        tools_needed.append('places_tool')
    
    # Check for email/confirmation requests
    confirmation_keywords = ['send', 'email', 'invite', 'draft', 'finalize', 'confirm']
    user_requesting_email = any(keyword in user_lower for keyword in confirmation_keywords)
    
    # User explicitly asks to send invites
    if user_requesting_email and 'email_tool' not in tools_already_called:
        # Check if we have minimum required info
        if attendees and date_pref:
            print("[DEBUG] User asked to send invites")
            tools_needed.append('email_tool')
    
    # Auto-trigger email on confirmation words (after venues shown)
    confirmation_words = ['yes', 'sure', 'perfect', 'great', 'good', 'sounds good', 'looks good']
    user_confirming = any(word in user_lower for word in confirmation_words)
    
    if (user_confirming and 
        attendees and date_pref and 
        'places_tool' in tools_already_called and  # Venues already shown
        'email_tool' not in tools_already_called and
        'email_tool' not in tools_needed):
        print("[DEBUG] User confirmed - auto-triggering email")
        tools_needed.append('email_tool')
    
    # ============================================================
    # 2. STATE-BASED LOGIC (Fallback)
    # ============================================================
    
    # Have attendees, calendar not called
    if attendees and 'calendar_tool' not in tools_already_called:
        if 'calendar_tool' not in tools_needed:
            print("[DEBUG] State-based: Need calendar check")
            tools_needed.append('calendar_tool')
    
    # Have date, weather not called (only if user moved forward)
    if date_pref and 'weather_tool' not in tools_already_called:
        if 'weather_tool' not in tools_needed:
            # Only add if user has venue preference OR explicitly asked
            if venue_pref or 'weather' in user_lower:
                print("[DEBUG] State-based: Need weather check")
                tools_needed.append('weather_tool')
    
    # Have date, places not called (only if user moved forward)
    if date_pref and 'places_tool' not in tools_already_called:
        if 'places_tool' not in tools_needed:
            # Only add if user has venue preference OR explicitly asked
            if venue_pref or 'venue' in user_lower or 'place' in user_lower:
                print("[DEBUG] State-based: Need venue search")
                tools_needed.append('places_tool')
    
    # ============================================================
    # 3. RETURN DECISION
    # ============================================================
    
    if tools_needed:
        print(f"[DEBUG] Decision: Call {len(tools_needed)} tools: {tools_needed}")
        return {
            "tools_to_call": tools_needed,
            "tools_done_this_turn": [],
            "current_tool": tools_needed[0],
            "need_final_answer": False
        }
    
    # No tools needed
    print("[DEBUG] Decision: Generate final answer (no tools needed)")
    return {
        "tools_to_call": [],
        "need_final_answer": True
    }


# ============================================================
# ROUTING FUNCTIONS
# ============================================================

def _route_to_next_node(state):
    """Route based on current_tool or need_final_answer"""
    
    if state.get("need_final_answer"):
        print("[DEBUG] Routing → answer_generator")
        return "answer_generator"
    
    current_tool = state.get("current_tool")
    print(f"[DEBUG] Routing → {current_tool}")
    
    if current_tool == "calendar_tool":
        return "calendar_tool_node"
    elif current_tool == "weather_tool":
        return "weather_tool_node"
    elif current_tool == "places_tool":
        return "places_tool_node"
    elif current_tool == "email_tool":
        return "email_tool_node"
    else:
        return "answer_generator"


def _check_more_tools_this_turn(state):
    """
    After a tool executes, check if more tools needed THIS turn.
    Routes to next tool OR answer_generator.
    """
    tools_to_call = state.get('tools_to_call') or []
    tools_done = state.get('tools_done_this_turn') or []
    
    remaining = [t for t in tools_to_call if t not in tools_done]
    
    print(f"[DEBUG] Multi-tool check: Done={tools_done}, Remaining={remaining}")
    
    if remaining:
        next_tool = remaining[0]
        # Map tool name to node name
        tool_to_node = {
            'calendar_tool': 'calendar_tool_node',
            'weather_tool': 'weather_tool_node',
            'places_tool': 'places_tool_node',
            'email_tool': 'email_tool_node'
        }
        next_node = tool_to_node.get(next_tool, 'answer_generator')
        print(f"[DEBUG] → Next tool: {next_tool} → node: {next_node}")
        return next_node
    else:
        print("[DEBUG] → All done, generating answer")
        return "answer_generator"


# ============================================================
# TOOL NODES
# ============================================================

def calendar_tool_node(state):
    """Execute calendar tool - ALWAYS executes when routed here"""
    
    print("\n[DEBUG] ===== EXECUTING CALENDAR TOOL =====")
    
    messages = state.get("messages", [])
    last_user_message = _extract_user_message(messages)
    
    # Initialize tracking
    tools_called = list(state.get("tools_called") or [])
    tools_done_this_turn = list(state.get("tools_done_this_turn") or [])
    tool_results = dict(state.get("tool_results") or {})
    
    try:
        result = check_availability(last_user_message, state)
        
        if "calendar_tool" not in tools_called:
            tools_called.append("calendar_tool")
        
        if "calendar_tool" not in tools_done_this_turn:
            tools_done_this_turn.append("calendar_tool")
        
        tool_results["calendar_tool"] = result
        
        print(f"[DEBUG] Calendar DONE")
        
    except Exception as e:
        print(f"[ERROR] Calendar: {e}")
        import traceback
        traceback.print_exc()
        
        # Even on error, mark as done to avoid infinite loop
        if "calendar_tool" not in tools_called:
            tools_called.append("calendar_tool")
        if "calendar_tool" not in tools_done_this_turn:
            tools_done_this_turn.append("calendar_tool")
        tool_results["calendar_tool"] = {"error": str(e), "formatted": f"Error checking calendar: {str(e)}"}
    
    # ALWAYS return updated state
    return {
        "tools_called": tools_called,
        "tools_done_this_turn": tools_done_this_turn,
        "tool_results": tool_results
    }


def weather_tool_node(state):
    """Execute weather tool - ALWAYS executes when routed here"""
    
    print("\n[DEBUG] ===== EXECUTING WEATHER TOOL =====")
    
    messages = state.get("messages", [])
    last_user_message = _extract_user_message(messages)
    
    # Initialize tracking
    tools_called = list(state.get("tools_called") or [])
    tools_done_this_turn = list(state.get("tools_done_this_turn") or [])
    tool_results = dict(state.get("tool_results") or {})
    
    try:
        result = get_weather_forecast(last_user_message, state)
        
        if "weather_tool" not in tools_called:
            tools_called.append("weather_tool")
        
        if "weather_tool" not in tools_done_this_turn:
            tools_done_this_turn.append("weather_tool")
        
        tool_results["weather_tool"] = result
        
        print(f"[DEBUG] Weather DONE")
        
    except Exception as e:
        print(f"[ERROR] Weather: {e}")
        import traceback
        traceback.print_exc()
        
        # Even on error, mark as done
        if "weather_tool" not in tools_called:
            tools_called.append("weather_tool")
        if "weather_tool" not in tools_done_this_turn:
            tools_done_this_turn.append("weather_tool")
        tool_results["weather_tool"] = {"error": str(e), "formatted": f"Error getting weather: {str(e)}"}
    
    # ALWAYS return updated state
    return {
        "tools_called": tools_called,
        "tools_done_this_turn": tools_done_this_turn,
        "tool_results": tool_results
    }


def places_tool_node(state):
    """Execute places tool - ALWAYS executes when routed here"""
    
    print("\n[DEBUG] ===== EXECUTING PLACES TOOL =====")
    
    messages = state.get("messages", [])
    last_user_message = _extract_user_message(messages)
    
    # Initialize tracking
    tools_called = list(state.get("tools_called") or [])
    tools_done_this_turn = list(state.get("tools_done_this_turn") or [])
    tool_results = dict(state.get("tool_results") or {})
    
    try:
        result = search_venues(last_user_message, state)
        
        if "places_tool" not in tools_called:
            tools_called.append("places_tool")
        
        if "places_tool" not in tools_done_this_turn:
            tools_done_this_turn.append("places_tool")
        
        tool_results["places_tool"] = result
        
        print(f"[DEBUG] Places DONE")
        
    except Exception as e:
        print(f"[ERROR] Places: {e}")
        import traceback
        traceback.print_exc()
        
        # Even on error, mark as done
        if "places_tool" not in tools_called:
            tools_called.append("places_tool")
        if "places_tool" not in tools_done_this_turn:
            tools_done_this_turn.append("places_tool")
        tool_results["places_tool"] = {"error": str(e), "formatted": f"Error finding venues: {str(e)}"}
    
    # ALWAYS return updated state
    return {
        "tools_called": tools_called,
        "tools_done_this_turn": tools_done_this_turn,
        "tool_results": tool_results
    }


def email_tool_node(state):
    """Execute email tool - ALWAYS executes when routed here"""
    
    print("\n[DEBUG] ===== EXECUTING EMAIL TOOL =====")
    
    messages = state.get("messages", [])
    last_user_message = _extract_user_message(messages)
    
    # Initialize tracking
    tools_called = list(state.get("tools_called") or [])
    tools_done_this_turn = list(state.get("tools_done_this_turn") or [])
    tool_results = dict(state.get("tool_results") or {})
    
    try:
        result = send_meeting_invite(last_user_message, state)
        
        if "email_tool" not in tools_called:
            tools_called.append("email_tool")
        
        if "email_tool" not in tools_done_this_turn:
            tools_done_this_turn.append("email_tool")
        
        tool_results["email_tool"] = result
        
        print(f"[DEBUG] Email DONE")
        
    except Exception as e:
        print(f"[ERROR] Email: {e}")
        import traceback
        traceback.print_exc()
        
        # Even on error, mark as done
        if "email_tool" not in tools_called:
            tools_called.append("email_tool")
        if "email_tool" not in tools_done_this_turn:
            tools_done_this_turn.append("email_tool")
        tool_results["email_tool"] = {"error": str(e), "formatted": f"Error sending email: {str(e)}"}
    
    # ALWAYS return updated state
    return {
        "tools_called": tools_called,
        "tools_done_this_turn": tools_done_this_turn,
        "tool_results": tool_results
    }


# ============================================================
# ANSWER GENERATOR NODE
# ============================================================

def answer_generator_node(state):
    """
    Generate response using tool results.
    Handles email tool specially (success/failure/completion).
    """
    
    print("\n[DEBUG] ===== GENERATING ANSWER =====")
    
    messages = state.get("messages", [])
    tool_results = state.get("tool_results") or {}
    tools_called = state.get("tools_called") or []
    
    attendees = state.get('attendees')
    date_pref = state.get('date_preference')
    venue_pref = state.get('venue_preference')
    
    conversation_text = _messages_to_text(messages, limit=8)
    
    # ============================================================
    # SPECIAL HANDLING: Email Tool
    # ============================================================
    
    email_tool_result = None
    if 'email_tool' in tools_called:
        email_tool_result = tool_results.get('email_tool')
    
    if email_tool_result:
        email_raw = email_tool_result.get('raw', {})
        
        # Email sent successfully
        if email_raw.get('success'):
            prompt = f"""You are Meeting Planner Assistant. The meeting invitation was SUCCESSFULLY SENT.

Conversation:
{conversation_text}

Meeting Summary:
- Attendees: {', '.join(attendees) if attendees else 'N/A'}
- Date/Time: {date_pref or 'N/A'}
- Duration: {state.get('duration', '1 hour')}
- Venue: One Financial Center (mentioned in conversation)

Email Status: ✅ SENT to {', '.join(email_raw.get('sent_to', []))}

INSTRUCTIONS:
1. Confirm the email was sent successfully
2. Provide a brief meeting summary
3. Thank the user
4. DO NOT ask for more information - the meeting is scheduled!
5. Keep it brief and positive

Response:"""
            
            response_text = call_llm(prompt)
            print(f"[DEBUG] Email success response ({len(response_text)} chars)")
            return {"messages": [AIMessage(content=response_text)]}
        
        # Email failed
        else:
            error_msg = email_raw.get('error', 'Unknown error')
            
            # Check if it's a configuration issue
            if 'not configured' in error_msg.lower() or 'credentials' in error_msg.lower():
                response_text = """I don't have Gmail credentials configured to send emails. 

To enable email sending, you need to add these to your .env file:
- GMAIL_EMAIL=your.email@gmail.com
- GMAIL_APP_PASSWORD=your_app_password

For now, here's the meeting summary you can share manually:

📅 **Meeting Details:**
- Attendees: """ + f"{', '.join(attendees) if attendees else 'N/A'}" + f"""
- Date/Time: {date_pref or 'N/A'}
- Duration: {state.get('duration', '1 hour')}
- Venue: One Financial Center

Would you like me to help with anything else?"""
            else:
                response_text = f"I encountered an error while sending the email: {error_msg}\n\nWould you like me to try again?"
            
            print(f"[DEBUG] Email error response ({len(response_text)} chars)")
            return {"messages": [AIMessage(content=response_text)]}
    
    # ============================================================
    # NORMAL RESPONSE GENERATION (No email or email not yet triggered)
    # ============================================================
    
    # Build tool outputs
    tool_outputs = ""
    for tool_name, result in tool_results.items():
        if tool_name == 'email_tool':
            continue  # Skip email (handled above)
        if isinstance(result, dict) and result.get('formatted'):
            tool_outputs += f"\n=== {tool_name.upper()} ===\n{result['formatted']}\n"
    
    # Determine what's missing
    missing_info = []
    if not attendees:
        missing_info.append("attendees")
    if not date_pref:
        missing_info.append("date/time")
    if not venue_pref:
        missing_info.append("venue preference")
    
    prompt = f"""You are Meeting Planner Assistant.

Conversation:
{conversation_text}

Current Info:
- Attendees: {attendees or 'NOT SET'}
- Date: {date_pref or 'NOT SET'}
- Venue preference: {venue_pref or 'NOT SET'}

Tools Executed: {tools_called}

Tool Results:
{tool_outputs if tool_outputs else 'No tool results yet'}

INSTRUCTIONS:
1. Present tool results naturally and concisely
2. Missing info: {', '.join(missing_info) if missing_info else 'All info collected'}
3. If all info collected and venues shown, ask if user wants to finalize/send invites
4. If info missing, ask for next piece
5. Be brief and conversational
6. Don't repeat information already shown in previous messages

Response:"""
    
    response_text = call_llm(prompt)
    
    print(f"[DEBUG] Answer generated ({len(response_text)} chars)")
    
    return {"messages": [AIMessage(content=response_text)]}