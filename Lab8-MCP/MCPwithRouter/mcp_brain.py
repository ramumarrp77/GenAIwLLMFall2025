"""
MCP Brain - Decision Making Layer
Uses Snowflake Cortex LLM to make ALL routing decisions
"""

import json
from utils.snowflake_connection import execute_cortex_query

class MCPBrain:
    """
    The Brain - Uses Snowflake Cortex to make ALL decisions
    Decides which server and which tool to use
    """
    
    def __init__(self):
        self.model = "mistral-large2"
        print("\n[MCP BRAIN] Initialized with Snowflake Cortex")
        print(f"[MCP BRAIN] Model: {self.model}")
    
    def decide_tool(self, user_query: str, available_tools: list) -> dict:
        """
        Use Snowflake Cortex to decide which tool to use
        This is where ALL routing decisions are made
        """
        print("\n" + "="*70)
        print("[MCP BRAIN] 🧠 DECISION PHASE")
        print("="*70)
        print(f"[MCP BRAIN] User Query: '{user_query}'")
        print(f"[MCP BRAIN] Available tools: {len(available_tools)}")
        
        # Build detailed tool descriptions
        tools_text = "\n\n".join([
            f"Server: {t['server']}\n"
            f"Tool: {t['name']}\n"
            f"Description: {t['description']}\n"
            f"Parameters: {json.dumps(t['parameters'], indent=2)}"
            for t in available_tools
        ])
        
        prompt = f"""
You are an intelligent routing agent for a multi-server MCP system.

Available MCP Servers and Tools (discovered at runtime):
{tools_text}

User Query: {user_query}

Your task:
1. Analyze what the user is asking for
2. Match the query to the BEST tool based on tool descriptions
3. Determine the required arguments

Think about:
- Database queries, reviews, sentiment → database-server tools
- News, updates, announcements → news-server tools
- Locations, stores, directions → location-server tools

Respond with ONLY a JSON object (no markdown):
{{
    "server": "server-name",
    "tool_name": "tool_name",
    "arguments": {{"param": "value"}},
    "reasoning": "why this tool matches the query"
}}

Base your decision ONLY on the tool descriptions provided.
"""
        
        try:
            print(f"[MCP BRAIN] Calling Snowflake Cortex LLM...")
            
            # Call Cortex LLM
            response = execute_cortex_query(prompt, self.model)
            
            print(f"[MCP BRAIN] LLM response received")
            
            # Clean up response
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            # Parse JSON
            decision = json.loads(response.strip())
            
            print(f"\n[MCP BRAIN] 🎯 DECISION MADE:")
            print(f"[MCP BRAIN]    Server: {decision.get('server')}")
            print(f"[MCP BRAIN]    Tool: {decision.get('tool_name')}")
            print(f"[MCP BRAIN]    Arguments: {decision.get('arguments')}")
            print(f"[MCP BRAIN]    Reasoning: {decision.get('reasoning', 'N/A')}")
            print("="*70)
            
            return decision
            
        except json.JSONDecodeError as e:
            print(f"[MCP BRAIN] ❌ Failed to parse LLM response")
            print(f"[MCP BRAIN] Error: {e}")
            print(f"[MCP BRAIN] Raw response: {response[:200]}...")
            
            # Fallback decision
            return {
                "server": "database-server",
                "tool_name": "get_table_info",
                "arguments": {},
                "reasoning": "Error parsing LLM response, using fallback"
            }
        except Exception as e:
            print(f"[MCP BRAIN] ❌ Error in LLM decision: {str(e)}")
            return {
                "server": "database-server",
                "tool_name": "get_table_info",
                "arguments": {},
                "reasoning": f"Error occurred: {str(e)}"
            }
    
    def generate_final_response(self, user_query: str, tool_result: dict, decision: dict) -> str:
        """
        Generate natural language response from tool results
        """
        print("\n" + "="*70)
        print("[MCP BRAIN] 💬 GENERATING FINAL RESPONSE")
        print("="*70)
        
        prompt = f"""
User asked: {user_query}

We used: {decision.get('tool_name')} from {decision.get('server')}

Tool returned:
{json.dumps(tool_result, indent=2, default=str)[:500]}

Generate a natural, conversational response to the user's question based on this data.
Be concise but informative. If there's an error, explain it clearly.
"""
        
        try:
            print(f"[MCP BRAIN] Calling Cortex to format response...")
            response = execute_cortex_query(prompt, self.model)
            
            print(f"[MCP BRAIN] ✅ Final response generated")
            print(f"[MCP BRAIN] Response preview: {response[:100]}...")
            print("="*70)
            
            return response.strip()
        except Exception as e:
            print(f"[MCP BRAIN] ❌ Error generating response: {e}")
            return f"I processed your request using {decision.get('tool_name')}, but encountered an error formatting the response."