import streamlit as st
import time
from datetime import datetime
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
        
        st.write("⚡ **Running 4 agents in parallel...**")
        
        execution_tracking = {
            'Sentiment': {'start': None, 'end': None, 'duration': 0},
            'Features': {'start': None, 'end': None, 'duration': 0},
            'News': {'start': None, 'end': None, 'duration': 0},
            'Quality': {'start': None, 'end': None, 'duration': 0}
        }
        
        progress_cols = st.columns(4)
        status_placeholders = {}
        for i, agent_name in enumerate(['Sentiment', 'Features', 'News', 'Quality']):
            with progress_cols[i]:
                status_placeholders[agent_name] = st.empty()
                status_placeholders[agent_name].info(f"⏳ {agent_name}")
        
        parallel_runnable = RunnableParallel(
            sentiment=RunnableLambda(lambda x: self._run_agent_with_tracking(
                self.sentiment_agent, x, 'Sentiment', execution_tracking, show_backend
            )),
            features=RunnableLambda(lambda x: self._run_agent_with_tracking(
                self.feature_agent, x, 'Features', execution_tracking, show_backend
            )),
            news=RunnableLambda(lambda x: self._run_agent_with_tracking(
                self.news_agent, x, 'News', execution_tracking, show_backend
            )),
            quality=RunnableLambda(lambda x: self._run_agent_with_tracking(
                self.quality_agent, x, 'Quality', execution_tracking, show_backend
            ))
        )
        
        parallel_start = time.time()
        parallel_results = parallel_runnable.invoke({"query": user_query})
        parallel_time = time.time() - parallel_start
        
        st.write("**Agent Execution Timeline:**")
        timing_cols = st.columns(4)
        
        for i, agent_name in enumerate(['Sentiment', 'Features', 'News', 'Quality']):
            tracking = execution_tracking[agent_name]
            with timing_cols[i]:
                status_placeholders[agent_name].success(f"✅ {agent_name}")
                st.metric(
                    label="Duration",
                    value=f"{tracking['duration']:.2f}s"
                )
                if tracking['start'] and tracking['end']:
                    st.caption(f"Start: {tracking['start']}")
                    st.caption(f"End: {tracking['end']}")
        
        st.write(f"⚡ **Total parallel execution: {parallel_time:.2f} seconds**")
        
        st.markdown("---")
        st.write("📊 **Step 5: Aggregating Results**")
        
        agg_start = time.time()
        final_report = self.aggregator.aggregate(parallel_results, user_query, show_backend)
        agg_time = time.time() - agg_start
        
        st.success(f"✅ Aggregator completed in {agg_time:.2f}s")
        
        for agent_name, tracking in execution_tracking.items():
            agent_times[agent_name] = tracking['duration']
        
        return {
            'sentiment': parallel_results['sentiment'],
            'features': parallel_results['features'],
            'news': parallel_results['news'],
            'quality': parallel_results['quality'],
            'final_report': final_report,
            'agent_times': agent_times,
            'execution_tracking': execution_tracking,
            'total_time': parallel_time + agg_time
        }
    
    def _execute_sequential(self, user_query: str, show_backend: bool, agent_times: dict):
        """Execute all agents sequentially for comparison"""
        
        st.write("🔄 **Running agents sequentially...**")
        
        results = {}
        execution_tracking = {}
        
        st.write("**Step 1: Sentiment Analysis Agent**")
        start = time.time()
        start_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        results['sentiment'] = self.sentiment_agent.execute(user_query, show_backend)
        end_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        duration = time.time() - start
        agent_times['Sentiment'] = duration
        execution_tracking['Sentiment'] = {'start': start_time, 'end': end_time, 'duration': duration}
        st.success(f"✅ Sentiment: {start_time} → {end_time} ({duration:.2f}s)")
        
        st.write("**Step 2: Feature Extraction Agent**")
        start = time.time()
        start_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        results['features'] = self.feature_agent.execute(user_query, show_backend)
        end_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        duration = time.time() - start
        agent_times['Features'] = duration
        execution_tracking['Features'] = {'start': start_time, 'end': end_time, 'duration': duration}
        st.success(f"✅ Features: {start_time} → {end_time} ({duration:.2f}s)")
        
        st.write("**Step 3: News Context Agent**")
        start = time.time()
        start_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        results['news'] = self.news_agent.execute(user_query, show_backend)
        end_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        duration = time.time() - start
        agent_times['News'] = duration
        execution_tracking['News'] = {'start': start_time, 'end': end_time, 'duration': duration}
        st.success(f"✅ News: {start_time} → {end_time} ({duration:.2f}s)")
        
        st.write("**Step 4: Quality Analysis Agent**")
        start = time.time()
        start_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        results['quality'] = self.quality_agent.execute(user_query, show_backend)
        end_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        duration = time.time() - start
        agent_times['Quality'] = duration
        execution_tracking['Quality'] = {'start': start_time, 'end': end_time, 'duration': duration}
        st.success(f"✅ Quality: {start_time} → {end_time} ({duration:.2f}s)")
        
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
            'execution_tracking': execution_tracking,
            'total_time': total_time
        }
    
    def _run_agent_with_tracking(self, agent, input_data, agent_name, execution_tracking, show_backend):
        """Execute agent with start/end time tracking - NO Streamlit UI calls"""
        start = time.time()
        start_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        result = agent.execute(input_data['query'], show_backend)
        
        end_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        duration = time.time() - start
        
        execution_tracking[agent_name] = {
            'start': start_time,
            'end': end_time,
            'duration': duration
        }
        
        return result