import streamlit as st
from agents import *

class AgentChain:
    def __init__(self):
        self.agents = {
            'code': CodeGenerationAgent(),
            'test': TestGenerationAgent(),
            'requirements': RequirementsAgent(),
            'docs': DocumentationAgent(),
            'validation': ValidationAgent()
        }
    
    def execute_chain(self, user_requirement: str, show_backend: bool = False):
        """Execute the complete agent chain"""
        
        st.subheader("🔗 Agent Chain Execution")
        progress_bar = st.progress(0)
        
        results = {}
        
        # Step 1: Code Generation
        progress_bar.progress(0.2)
        results['code'] = self.agents['code'].execute(user_requirement, show_backend)
        
        # Step 2: Test Generation
        progress_bar.progress(0.4)
        results['test'] = self.agents['test'].execute(results['code'], show_backend)
        
        # Step 3: Requirements
        progress_bar.progress(0.6)
        results['requirements'] = self.agents['requirements'].execute(
            results['code'], results['test'], show_backend
        )
        
        # Step 4: Documentation
        progress_bar.progress(0.8)
        results['docs'] = self.agents['docs'].execute(
            results['code'], results['test'], results['requirements'], show_backend
        )
        
        # Step 5: Validation
        progress_bar.progress(1.0)
        results['validation'] = self.agents['validation'].execute(
            results['code'], results['test'], results['requirements'], results['docs'], show_backend
        )
        
        st.success("🎉 Agent chain completed!")
        return results