"""
TruLens manager for Snowflake AI Observability
"""

from trulens.apps.app import TruApp
from trulens.connectors.snowflake import SnowflakeConnector
from trulens.core.run import RunConfig
from datetime import datetime

class TruLensManager:
    """Manage TruLens evaluations for Snowflake AI Observability"""
    
    def __init__(self, session, app):
        self.session = session
        self.connector = SnowflakeConnector(snowpark_session=session)
        self.app = app
        
        # Register application
        self.tru_app = TruApp(
            app=self.app,
            app_name="safe_ai_monitor",
            app_version="v1.0",
            connector=self.connector,
            main_method=self.app.answer_query
        )
    
    def run_evaluation(
        self,
        dataset_name: str,
        metrics: list = None,
        judge_model: str = "llama3.1-70b"
    ):
        """Run evaluation on a dataset"""
        
        if metrics is None:
            metrics = ["context_relevance", "groundedness", "answer_relevance"]
        
        run_config = RunConfig(
            run_name=f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Evaluation run from Streamlit app",
            label="streamlit_evaluation",
            source_type="TABLE",
            dataset_name=dataset_name,
            dataset_spec={
                "RETRIEVAL.QUERY_TEXT": "query",
                "RECORD_ROOT.INPUT": "query",
            },
            llm_judge_name=judge_model
        )
        
        # Start evaluation
        run = self.tru_app.add_run(run_config=run_config)
        run.start()
        
        # Compute metrics
        results = run.compute_metrics(metrics)
        
        return {
            "run_name": run_config.run_name,
            "dataset": dataset_name,
            "metrics": results,
            "status": "complete"
        }