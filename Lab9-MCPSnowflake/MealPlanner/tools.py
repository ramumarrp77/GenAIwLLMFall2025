"""Tool definitions and mappings for MCP tools."""

from typing import Dict, Any
from enum import Enum
import re

class ToolIntent(Enum):
    """User intent categories."""
    SEARCH = "search"
    CALCULATE = "calculate"
    SCORE = "score"
    FILTER = "filter"
    ANALYZE = "analyze"
    SQL = "sql"
    UNKNOWN = "unknown"

class ToolMapper:
    """Map user intents to MCP tool names."""
    
    # Intent to tool mapping
    INTENT_TO_TOOL = {
        ToolIntent.SEARCH: "meal-search",
        ToolIntent.CALCULATE: "macro-calculator",
        ToolIntent.SCORE: "meal-scorer",
        ToolIntent.FILTER: "diet-filter",
        ToolIntent.ANALYZE: "nutrition-analyst",
        ToolIntent.SQL: "sql-query"
    }
    
    # Keywords for intent detection
    INTENT_KEYWORDS = {
        ToolIntent.SEARCH: ["find", "search", "show", "list", "get", "looking for", "what"],
        ToolIntent.CALCULATE: ["calculate", "compute", "macro", "breakdown", "calories from"],
        ToolIntent.SCORE: ["score", "rate", "evaluate", "compare", "match", "fit", "against"],
        ToolIntent.FILTER: ["filter", "vegetarian", "vegan", "low-carb", "high-protein", "diet"],
        ToolIntent.ANALYZE: ["analyze", "insight", "trend"],
        ToolIntent.SQL: ["sql", "query", "select", "database"]
    }
    
    @classmethod
    def detect_intent(cls, query: str) -> ToolIntent:
        """
        Detect user intent from query string.
        
        Args:
            query: User query text
            
        Returns:
            Detected intent
        """
        query_lower = query.lower()
        
        # Check each intent's keywords
        for intent, keywords in cls.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return intent
        
        return ToolIntent.SEARCH  # Default to search
    
    @classmethod
    def get_tool_name(cls, intent: ToolIntent) -> str:
        """Get tool name for intent."""
        return cls.INTENT_TO_TOOL.get(intent, "meal-search")
    
    @classmethod
    def extract_search_params(cls, query: str) -> Dict[str, Any]:
        """Extract parameters for meal-search tool."""
        return {
            "query": query,
            "columns": ["FOOD_NAME", "MEAL_DESCRIPTION", "PROTEIN", "CALORIES"],
            "limit": 5
        }
    
    @classmethod
    def extract_macro_params(cls, query: str) -> Dict[str, Any]:
        """Extract parameters for macro-calculator tool."""
        protein = re.search(r'(\d+\.?\d*)\s*g?\s*protein', query, re.I)
        carbs = re.search(r'(\d+\.?\d*)\s*g?\s*carb', query, re.I)
        fat = re.search(r'(\d+\.?\d*)\s*g?\s*fat', query, re.I)
        
        return {
            "protein": float(protein.group(1)) if protein else 30.0,
            "carbs": float(carbs.group(1)) if carbs else 50.0,
            "fat": float(fat.group(1)) if fat else 15.0
        }
    
    @classmethod
    def extract_score_params(cls, query: str) -> Dict[str, Any]:
        """Extract parameters for meal-scorer tool."""
        calories = re.search(r'(\d+\.?\d*)\s*cal', query, re.I)
        protein = re.search(r'(\d+\.?\d*)\s*g?\s*protein', query, re.I)
        carbs = re.search(r'(\d+\.?\d*)\s*g?\s*carb', query, re.I)
        target_cal = re.search(r'target.*?(\d+\.?\d*)\s*cal', query, re.I)
        target_protein = re.search(r'target.*?(\d+\.?\d*)\s*g?\s*protein', query, re.I)
        
        return {
            "calories": float(calories.group(1)) if calories else 400.0,
            "protein": float(protein.group(1)) if protein else 30.0,
            "carbs": float(carbs.group(1)) if carbs else 50.0,
            "target_calories": float(target_cal.group(1)) if target_cal else 400.0,
            "target_protein": float(target_protein.group(1)) if target_protein else 30.0
        }
    
    @classmethod
    def extract_filter_params(cls, query: str) -> Dict[str, Any]:
        """Extract parameters for diet-filter tool."""
        query_lower = query.lower()
        
        diet_type = "vegetarian"  # default
        
        if "high protein" in query_lower or "high-protein" in query_lower:
            diet_type = "high_protein"
        elif "low carb" in query_lower or "low-carb" in query_lower:
            diet_type = "low_carb"
        elif "low sodium" in query_lower or "low-sodium" in query_lower:
            diet_type = "low_sodium"
        elif "low fat" in query_lower or "low-fat" in query_lower:
            diet_type = "low_fat"
        
        return {"diet_type": diet_type}