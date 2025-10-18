# Configuration for Meeting Planner

import os
from dotenv import load_dotenv

load_dotenv()

# Snowflake
SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'database': os.getenv('SNOWFLAKE_DATABASE'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA'),
    'role': os.getenv('SNOWFLAKE_ROLE'),
}

# LLM
LLM_MODEL = os.getenv('LLM_MODEL', 'llama3.1-8b')

# External APIs - Google Maps (used for both directions AND places/venues)
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Weather API
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Email
GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')