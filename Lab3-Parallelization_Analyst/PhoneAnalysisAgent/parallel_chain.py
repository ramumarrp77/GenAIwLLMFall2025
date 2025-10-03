import streamlit as st
import time
from langchain.schema.runnable import RunnableParallel, RunnableLambda
from agents.sentiment_agent import SentimentAgent
from agents.feature_agent import FeatureAgent
from agents.news_agent import NewsAgent
from agents.quality_agent import QualityAgent
from aggregator.report_aggregator import ReportAggregator

class ParallelChain:
    def __init__(self):
        self.sentiment_agent = SentimentAgent()
        self.feature_agent = FeatureAgent()
        self.news_agent = NewsAgent()
        self.quality_agent = QualityAgent()
        self.aggregator = ReportAggregator()
        
    def execute_analysis(self, user_query: str, is_parallel: bool = True, show_backend: bool = False):
        """Execute analysis in parallel or sequential mode"""
        
        agent_times = {}
        
        if is_parallel:
            return self._execute_parallel(user_query, show_backend, agent_times)
        else:
            return self._execute_sequential(user_query, show_backend, agent_times)
    
    def _execute_parallel(self, user_query: str, show_backend: bool, agent_times: dict):
        """Execute all agents in parallel using LangChain RunnableParallel"""
        
        st.write("🔀 **Running 4 agents in parallel...**")
        
        # Create progress placeholders
        progress_cols = st.columns(4)
        status_placeholders = {}
        for i, agent_name in enumerate(['Sentiment', 'Features', 'News', 'Quality']):
            with progress_cols[i]:
                status_placeholders[agent_name] = st.empty()
                status_placeholders[agent_name].info(f"⏳ {agent_name} Agent")
        
        # Create LangChain RunnableParallel
        parallel_runnable = RunnableParallel(
            sentiment=RunnableLambda(lambda x: self._run_with_timing(
                self.sentiment_agent, x, 'Sentiment', status_placeholders, agent_times, show_backend
            )),
            features=RunnableLambda(lambda x: self._run_with_timing(
                self.feature_agent, x, 'Features', status_placeholders, agent_times, show_backend
            )),
            news=RunnableLambda(lambda x: self._run_with_timing(
                self.news_agent, x, 'News', status_placeholders, agent_times, show_backend
            )),
            quality=RunnableLambda(lambda x: self._run_with_timing(
                self.quality_agent, x, 'Quality', status_placeholders, agent_times, show_backend
            ))
        )
        
        # Execute all agents in parallel
        parallel_start = time.time()
        parallel_results = parallel_runnable.invoke({"query": user_query})
        parallel_time = time.time() - parallel_start
        
        # Update all statuses to complete
        for agent_name in ['Sentiment', 'Features', 'News', 'Quality']:
            status_placeholders[agent_name].success(f"✅ {agent_name} ({agent_times.get(agent_name, 0):.2f}s)")
        
        st.write(f"⚡ **All agents completed in {parallel_time:.2f} seconds**")
        
        # Sequential aggregation step
        st.markdown("---")
        st.write("📊 **Step 5: Aggregating Results**")
        
        agg_start = time.time()
        final_report = self.aggregator.aggregate(parallel_results, user_query, show_backend)
        agg_time = time.time() - agg_start
        
        st.success(f"✅ Aggregator completed in {agg_time:.2f}s")
        
        return {
            'sentiment': parallel_results['sentiment'],
            'features': parallel_results['features'],
            'news': parallel_results['news'],
            'quality': parallel_results['quality'],
            'final_report': final_report,
            'agent_times': agent_times,
            'total_time': parallel_time + agg_time
        }
    
    def _execute_sequential(self, user_query: str, show_backend: bool, agent_times: dict):
        """Execute all agents sequentially for comparison"""
        
        st.write("🔄 **Running agents sequentially...**")
        
        results = {}
        
        # Agent 1: Sentiment
        st.write("**Step 1: Sentiment Analysis Agent**")
        start = time.time()
        results['sentiment'] = self.sentiment_agent.execute(user_query, show_backend)
        agent_times['Sentiment'] = time.time() - start
        st.success(f"✅ Sentiment Agent completed ({agent_times['Sentiment']:.2f}s)")
        
        # Agent 2: Features
        st.write("**Step 2: Feature Extraction Agent**")
        start = time.time()
        results['features'] = self.feature_agent.execute(user_query, show_backend)
        agent_times['Features'] = time.time() - start
        st.success(f"✅ Feature Agent completed ({agent_times['Features']:.2f}s)")
        
        # Agent 3: News
        st.write("**Step 3: News Context Agent**")
        start = time.time()
        results['news'] = self.news_agent.execute(user_query, show_backend)
        agent_times['News'] = time.time() - start
        st.success(f"✅ News Agent completed ({agent_times['News']:.2f}s)")
        
        # Agent 4: Quality
        st.write("**Step 4: Quality Analysis Agent**")
        start = time.time()
        results['quality'] = self.quality_agent.execute(user_query, show_backend)
        agent_times['Quality'] = time.time() - start
        st.success(f"✅ Quality Agent completed ({agent_times['Quality']:.2f}s)")
        
        # Aggregation
        st.markdown("---")
        st.write("**Step 5: Aggregating Results**")
        start = time.time()
        final_report = self.aggregator.aggregate(results, user_query, show_backend)
        agg_time = time.time() - start
        st.success(f"✅ Aggregator completed ({agg_time:.2f}s)")
        
        total_time = sum(agent_times.values()) + agg_time
        st.write(f"🔄 **Total sequential time: {total_time:.2f} seconds**")
        
        return {
            **results,
            'final_report': final_report,
            'agent_times': agent_times,
            'total_time': total_time
        }
    
    def _run_with_timing(self, agent, input_data, agent_name, status_placeholders, agent_times, show_backend):
        """Execute agent with timing and status updates"""
        status_placeholders[agent_name].warning(f"⏳ {agent_name} Running...")
        
        start = time.time()
        result = agent.execute(input_data['query'], show_backend)
        execution_time = time.time() - start
        
        agent_times[agent_name] = execution_time
        return result

if __name__ == "__main__":
    main()