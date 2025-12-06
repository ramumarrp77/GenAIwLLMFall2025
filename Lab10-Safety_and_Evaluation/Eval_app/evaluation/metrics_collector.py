"""
Metrics collection for LLM performance
"""

import time

class MetricsCollector:
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start(self):
        """Start timing"""
        self.start_time = time.time()
    
    def end(self, input_text: str, output_text: str):
        """Calculate metrics"""
        latency = time.time() - self.start_time
        input_tokens = int(len(input_text.split()) * 1.3)
        output_tokens = int(len(output_text.split()) * 1.3)
        cost = (input_tokens * 0.0001 + output_tokens * 0.0003) / 1000
        
        self.metrics = {
            "latency_seconds": round(latency, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_cost": round(cost, 6)
        }
        return self.metrics