# iPhone Assistant - Routing Agent with RAG Patterns

This code repository is created as part of DAMG 7374 Gen AI w/ LLM Fall 2025 semester - Lab session

A Streamlit application demonstrating routing agents, RAG (Retrieval-Augmented Generation), and agentic patterns using Snowflake Cortex with external API integrations.

## Overview

This application creates an intelligent iPhone customer support system using routing agents and specialized tools:

1. **Router Agent** (Claude-3.5-Sonnet) - Classifies user queries and routes to appropriate tool
2. **RAG Agent** (Claude-3.5-Sonnet) - Analyzes iPhone reviews using vector similarity search  
3. **News Agent** (Mixtral-8x7b) - Fetches latest iPhone news using SerpAPI
4. **Maps Agent** (Llama4-Maverick) - Finds Apple Store locations using Google Maps API
5. **Response Synthesizer** (Claude-3.5-Sonnet) - Generates natural language responses

## Project Structure

```
routing_agent_app/
├── app.py                          # Main Streamlit application
├── routing_chain.py                # Orchestrates router → tool → synthesizer
├── router_agent.py                 # Router agent that classifies queries
├── tools/
│   ├── rag_agent.py               # RAG agent for Snowflake reviews
│   ├── news_agent.py              # SerpAPI news retrieval
│   └── map_agent.py               # Google Maps store locator
├── utils/
│   └── snowflake_connection.py    # Snowflake Cortex connection
├── requirements.txt               # Dependencies
├── .env                          # API keys and Snowflake credentials
└── README.md                     # This file
```

## Prerequisites

- Python 3.8+
- Snowflake account with Cortex access
- iPhone reviews table with embeddings (`LAB_DB.PUBLIC.IPHONE_TABLE`)
- SerpAPI account for news search
- Google Maps API key for location services

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Snowflake Configuration
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_pat_token_here
SNOWFLAKE_ACCOUNT=your_account_identifier  
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=LAB_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=YOUR_ROLE

# External APIs
SERPAPI_API_KEY=your_serpapi_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_key_here
```

### 3. Setup iPhone Reviews Table

Ensure the iPhone reviews table exists with embeddings:

```sql
-- Verify table exists
SELECT COUNT(*) FROM LAB_DB.PUBLIC.IPHONE_TABLE;

-- Check embeddings column exists and is populated
SELECT COUNT(*) FROM LAB_DB.PUBLIC.IPHONE_TABLE 
WHERE REVIEW_EMBEDDINGS IS NOT NULL;
```

### 4. API Key Setup

**SerpAPI Key:**
1. Sign up at https://serpapi.com/
2. Get your API key from dashboard
3. Add to `.env` file

**Google Maps API Key:**
1. Go to Google Cloud Console
2. Enable Places API and Directions API
3. Create API key and add to `.env` file

### 5. Run the Application

```bash
streamlit run app.py
```

## Architecture

### Routing Agent Flow

```
User Query → Router Agent → Tool Selection → Specialized Processing → Response Synthesis
```

**Router Agent:** Analyzes query intent and selects ONE specialized tool

**Three Specialized Tools:**
- **RAG Agent**: Vector similarity search on Snowflake iPhone reviews
- **News Agent**: Real-time iPhone news via SerpAPI
- **Maps Agent**: Apple Store locations and transit via Google Maps API

**Response Synthesizer:** Converts technical outputs to natural language

### Query Examples

| User Query | Router Decision | Tool Used | Data Source |
|------------|----------------|-----------|-------------|
| "iPhone 15 battery reviews" | RAG Agent | Vector similarity search | Snowflake Reviews |
| "Latest iPhone 16 news" | News Agent | Web search | SerpAPI |
| "Apple Store near Northeastern" | Maps Agent | Location search | Google Maps |

### Agent Specialization

| Agent | Model | Data Source | Processing Type |
|-------|-------|-------------|----------------|
| Router | Claude-3.5-Sonnet | User query | Query classification |
| RAG Agent | Claude-3.5-Sonnet | Snowflake reviews | Vector similarity + analysis |
| News Agent | Mixtral-8x7b | SerpAPI | Web search + summarization |
| Maps Agent | Llama4-Maverick | Google Maps | Location + transit planning |
| Synthesizer | Claude-3.5-Sonnet | Tool outputs | Natural language generation |