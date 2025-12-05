"""Configuration management for Lab 8 MCP Integration."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class SnowflakeConfig:
    """Snowflake MCP server configuration."""
    
    user: str
    password: str  # PAT token
    account: str
    warehouse: str
    database: str
    schema: str
    role: str
    mcp_server_name: str
    
    @property
    def mcp_endpoint(self) -> str:
        """Generate MCP server endpoint URL."""
        return (
            f"https://{self.account}.snowflakecomputing.com"
            f"/api/v2/databases/{self.database}/schemas/{self.schema}"
            f"/mcp-servers/{self.mcp_server_name}"
        )
    
    @classmethod
    def from_env(cls) -> 'SnowflakeConfig':
        """Load configuration from environment variables."""
        return cls(
            user=os.getenv('SNOWFLAKE_USER', ''),
            password=os.getenv('SNOWFLAKE_PASSWORD', ''),  # PAT token
            account=os.getenv('SNOWFLAKE_ACCOUNT', ''),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
            database=os.getenv('SNOWFLAKE_DATABASE', 'LAB_DB'),
            schema=os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC'),
            role=os.getenv('SNOWFLAKE_ROLE', 'LAB_ROLE'),
            mcp_server_name=os.getenv('MCP_SERVER_NAME', 'nutrition_mcp_server')
        )
    
    def validate(self) -> bool:
        """Validate required configuration."""
        if not self.account:
            raise ValueError("SNOWFLAKE_ACCOUNT is required in .env")
        if not self.password:
            raise ValueError("SNOWFLAKE_PASSWORD (PAT token) is required in .env")
        if not self.user:
            raise ValueError("SNOWFLAKE_USER is required in .env")
        return True


# Global config instance
snowflake_config = SnowflakeConfig.from_env()