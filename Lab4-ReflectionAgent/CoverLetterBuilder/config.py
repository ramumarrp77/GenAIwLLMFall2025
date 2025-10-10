# Configuration for Cover Letter Generator
# Loads credentials and settings from .env file
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Snowflake credentials (loaded from .env)
SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'database': os.getenv('SNOWFLAKE_DATABASE'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA'),
    'role' : os.getenv('SNOWFLAKE_ROLE'),
}

# LLM settings (loaded from .env)
LLM_MODEL = os.getenv('LLM_MODEL')

# App defaults (hardcoded)
DEFAULT_MAX_ITERATIONS = 3
DEFAULT_QUALITY_THRESHOLD = 8.5