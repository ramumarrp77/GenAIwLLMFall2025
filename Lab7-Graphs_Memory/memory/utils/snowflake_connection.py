"""
Snowflake connection and Cortex LLM wrapper
"""

import snowflake.connector
from typing import Any, List, Optional, Mapping
from langchain_core.language_models.llms import BaseLLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import LLMResult, Generation
import config


def get_snowflake_connection():
    """Get Snowflake connection"""
    return snowflake.connector.connect(
        account=config.SNOWFLAKE_ACCOUNT,
        user=config.SNOWFLAKE_USER,
        password=config.SNOWFLAKE_PASSWORD,
        database=config.SNOWFLAKE_DATABASE,
        schema=config.SNOWFLAKE_SCHEMA,
        warehouse=config.SNOWFLAKE_WAREHOUSE,
        role=config.SNOWFLAKE_ROLE
    )


class SnowflakeCortexLLM(BaseLLM):
    """Snowflake Cortex LLM wrapper for LangChain"""
    
    model_name: str = config.LLM_MODEL
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, model_name: str = None, **kwargs):
        if model_name is None:
            model_name = config.LLM_MODEL
        super().__init__(model_name=model_name, **kwargs)
        object.__setattr__(self, '_conn', None)
    
    def _get_connection(self):
        if self._conn is None:
            object.__setattr__(self, '_conn', get_snowflake_connection())
        return self._conn
    
    @property
    def _llm_type(self) -> str:
        return "snowflake_cortex"
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        generations = []
        for prompt in prompts:
            text = self._call_cortex(prompt)
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)
    
    def _call_cortex(self, prompt: str) -> str:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            escaped = prompt.replace("'", "''")
            sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{self.model_name}', '{escaped}')"
            cursor.execute(sql)
            result = cursor.fetchone()
            return result[0] if result else ""
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            cursor.close()
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        return self._call_cortex(prompt)
    
    def __call__(self, prompt: str) -> str:
        return self._call_cortex(prompt)
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model_name": self.model_name}
    
    def __del__(self):
        try:
            if hasattr(self, '_conn') and self._conn:
                self._conn.close()
        except:
            pass