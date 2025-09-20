import streamlit as st
from snowflake_connection import call_cortex_complete
from agent_prompts import *

# Model configuration for each agent type
AGENT_MODELS = {
    'code_generation': 'claude-3-5-sonnet',    # Best for code generation
    'test_generation': 'llama4-maverick',    # Excellent for testing
    'requirements': 'mixtral-8x7b',          # Good for requirements analysis
    'documentation': 'reka-flash',             # Great for documentation
    'validation': 'mistral-7b'               # Fast and efficient validation
}

class CodeGenerationAgent:
    def __init__(self):
        self.name = "Code Generation Agent"
        self.icon = "💻"
        self.model = AGENT_MODELS['code_generation']
        self.description = "Generates production-ready Python code"
    
    def execute(self, user_requirement: str, show_backend: bool = False):
        st.write(f"{self.icon} **{self.name}** (using {self.model})")
        prompt = get_code_generation_prompt(user_requirement)
        
        with st.spinner(f"{self.name} is working with {self.model}..."):
            result = call_cortex_complete(prompt, self.model)
        
        if show_backend:
            with st.expander(f"Backend: {self.name}", expanded=False):
                st.write(f"**Model Used:** `{self.model}`")
                st.code(prompt, language="text")
                st.code(result[:200] + "...", language="text")
        
        st.success(f"✅ {self.name} completed")
        return result

class TestGenerationAgent:
    def __init__(self):
        self.name = "Test Generation Agent"
        self.icon = "🧪"
        self.model = AGENT_MODELS['test_generation']
        self.description = "Creates comprehensive test suites"
    
    def execute(self, main_code: str, show_backend: bool = False):
        st.write(f"{self.icon} **{self.name}** (using {self.model})")
        prompt = get_test_generation_prompt(main_code)
        
        with st.spinner(f"{self.name} is working with {self.model}..."):
            result = call_cortex_complete(prompt, self.model)
        
        if show_backend:
            with st.expander(f"Backend: {self.name}", expanded=False):
                st.write(f"**Model Used:** `{self.model}`")
                st.code(prompt, language="text")
                st.code(result[:200] + "...", language="text")
        
        st.success(f"✅ {self.name} completed")
        return result

class RequirementsAgent:
    def __init__(self):
        self.name = "Requirements Agent"
        self.icon = "📦"
        self.model = AGENT_MODELS['requirements']
        self.description = "Analyzes dependencies and creates requirements.txt"
    
    def execute(self, main_code: str, test_code: str, show_backend: bool = False):
        st.write(f"{self.icon} **{self.name}** (using {self.model})")
        prompt = get_requirements_prompt(main_code, test_code)
        
        with st.spinner(f"{self.name} is working with {self.model}..."):
            result = call_cortex_complete(prompt, self.model)
        
        if show_backend:
            with st.expander(f"Backend: {self.name}", expanded=False):
                st.write(f"**Model Used:** `{self.model}`")
                st.code(prompt, language="text")
                st.code(result[:200] + "...", language="text")
        
        st.success(f"✅ {self.name} completed")
        return result

class DocumentationAgent:
    def __init__(self):
        self.name = "Documentation Agent"
        self.icon = "📚"
        self.model = AGENT_MODELS['documentation']
        self.description = "Writes comprehensive documentation"
    
    def execute(self, main_code: str, test_code: str, requirements: str, show_backend: bool = False):
        st.write(f"{self.icon} **{self.name}** (using {self.model})")
        prompt = get_readme_prompt(main_code, test_code, requirements)
        
        with st.spinner(f"{self.name} is working with {self.model}..."):
            result = call_cortex_complete(prompt, self.model)
        
        if show_backend:
            with st.expander(f"Backend: {self.name}", expanded=False):
                st.write(f"**Model Used:** `{self.model}`")
                st.code(prompt, language="text")
                st.code(result[:200] + "...", language="text")
        
        st.success(f"✅ {self.name} completed")
        return result

class ValidationAgent:
    def __init__(self):
        self.name = "Validation Agent"
        self.icon = "✅"
        self.model = AGENT_MODELS['validation']
        self.description = "Reviews and validates the complete project"
    
    def execute(self, main_code: str, test_code: str, requirements: str, readme: str, show_backend: bool = False):
        st.write(f"{self.icon} **{self.name}** (using {self.model})")
        prompt = get_validation_prompt(main_code, test_code, requirements, readme)
        
        with st.spinner(f"{self.name} is working with {self.model}..."):
            result = call_cortex_complete(prompt, self.model)
        
        if show_backend:
            with st.expander(f"Backend: {self.name}", expanded=False):
                st.write(f"**Model Used:** `{self.model}`")
                st.code(prompt, language="text")
                st.code(result[:200] + "...", language="text")
        
        st.success(f"✅ {self.name} completed")
        return result

def get_agent_model(agent_type: str) -> str:
    """Get the recommended model for an agent type"""
    return AGENT_MODELS.get(agent_type, 'claude-3-5-sonnet')