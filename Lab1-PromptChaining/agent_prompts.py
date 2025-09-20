def get_code_generation_prompt(user_requirement: str) -> str:
    """Prompt for Code Generation Agent"""
    return f"""You are a Senior Python Developer. Generate ONLY the Python code, no explanations.

USER REQUIREMENT: {user_requirement}

Requirements:
- Complete, working Python script
- Proper error handling and logging
- Docstrings and comments
- Main function with if __name__ == "__main__"
- Follow PEP 8 standards

Return ONLY the Python code, nothing else."""

def get_test_generation_prompt(main_code: str) -> str:
    """Prompt for Test Generation Agent"""
    return f"""You are a QA Testing Specialist. Generate ONLY the test code, no explanations.

MAIN CODE TO TEST:
{main_code}

Requirements:
- Complete pytest test file
- Unit tests for all functions
- Edge cases and error handling tests
- Mock objects where appropriate
- High test coverage

Return ONLY the test code as a complete test_*.py file, nothing else."""

def get_requirements_prompt(main_code: str, test_code: str) -> str:
    """Prompt for Requirements Generation Agent"""
    return f"""You are a DevOps Engineer. Generate ONLY the requirements.txt content, no explanations.

ANALYZE THIS CODE:
Main Code: {main_code}
Test Code: {test_code}

Requirements:
- List all required packages with specific versions
- Include development/testing dependencies
- One package per line

Return ONLY the requirements.txt content, nothing else."""

def get_readme_prompt(main_code: str, test_code: str, requirements: str) -> str:
    """Prompt for README Generation Agent"""
    return f"""You are a Technical Readme Writer. Generate ONLY the README.md content, no explanations and strictly no thinking process.

PROJECT FILES:
Main Code: {main_code}
Test Code: {test_code}
Requirements: {requirements}

Requirements:
- Professional README.md in markdown format
- Project overview and features
- Installation instructions
- Usage examples with code snippets
- Testing instructions

Return ONLY the complete README.md content, nothing else."""

def get_validation_prompt(main_code: str, test_code: str, requirements: str, readme: str) -> str:
    """Prompt for Final Validation Agent"""
    return f"""You are a Senior Software Architect. Provide ONLY the assessment, no extra text.

COMPLETE PROJECT REVIEW:
Main Code: {main_code}
Test Code: {test_code}
Requirements: {requirements}
README: {readme}

Provide structured assessment with:
- Overall Quality Score: X/10
- Code Quality: [assessment]
- Test Coverage: [assessment]  
- Documentation: [assessment]
- Production Readiness: [Ready/Not Ready]
- Top 3 Strengths: [list]
- Top 3 Improvements: [list]

Return ONLY the structured assessment, nothing else."""