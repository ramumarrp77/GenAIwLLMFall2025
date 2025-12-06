"""
Instrumented application for TruLens observability
"""

import os
os.environ["TRULENS_OTEL_TRACING"] = "1"

from trulens.core.otel.instrument import instrument
from trulens.otel.semconv.trace import SpanAttributes
import sys
sys.path.append('utils')
from cortex_helpers import call_cortex

class InstrumentedSafeAI:
    """AI application instrumented with TruLens decorators"""
    
    def __init__(self, session):
        self.session = session
    
    @instrument(
        span_type=SpanAttributes.SpanType.RETRIEVAL,
        attributes={
            SpanAttributes.RETRIEVAL.QUERY_TEXT: "query",
            SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS: "return",
        }
    )
    def retrieve_context(self, query: str) -> list:
        """Retrieve relevant context for RAG pattern"""
        # For demo, return sample contexts
        # In production, this would query Cortex Search or vector DB
        contexts = [
            "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
            "Deep learning uses neural networks with multiple layers to process complex patterns."
        ]
        return contexts
    
    @instrument(span_type=SpanAttributes.SpanType.GENERATION)
    def generate_response(self, query: str, context: list) -> str:
        """Generate response using Cortex with context"""
        prompt = f"""Context information:
{chr(10).join(context)}

Question: {query}

Answer the question based on the context provided:"""
        
        return call_cortex(prompt, model="llama3.1-70b")
    
    @instrument(
        span_type=SpanAttributes.SpanType.RECORD_ROOT,
        attributes={
            SpanAttributes.RECORD_ROOT.INPUT: "query",
            SpanAttributes.RECORD_ROOT.OUTPUT: "return",
        }
    )
    def answer_query(self, query: str) -> str:
        """Main entry point - marked as RECORD_ROOT for TruLens"""
        context = self.retrieve_context(query)
        response = self.generate_response(query, context)
        return response