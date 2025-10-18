# 📅 Meeting Planner Agent

An intelligent, conversational AI assistant that schedules team meetings by checking attendee availability, analyzing weather conditions, recommending venues, and sending meeting invitations automatically. 

## 🎯 Features

- **Smart Calendar Management**: Checks attendee availability and finds common free time slots
- **Weather-Aware Planning**: Considers weather forecasts when suggesting indoor/outdoor venues
- **Venue Recommendations**: Searches for meeting halls, conference centers, and event spaces using Google Maps API
- **Automated Invitations**: Sends meeting invites via Gmail with complete meeting details
- **Multi-Tool Orchestration**: Executes multiple tools in a single conversation turn for efficiency
- **Intent-Based Understanding**: Recognizes user requests and adapts conversation flow dynamically
- **Stateful Conversations**: Maintains context across multiple turns using LangGraph

## 🏗️ Architecture

Built with:
- **LangGraph**: Stateful conversation workflow
- **Snowflake Cortex**: LLM for natural language understanding and generation
- **Google Maps API**: Geocoding, directions, and venue search
- **OpenWeatherMap API**: Weather forecasts
- **Gmail SMTP**: Email delivery
- **Streamlit**: Interactive web interface

## 📁 Project Structure

```
meetingplanneragent/
│
├── app.py                          # Streamlit web interface
├── config.py                       # Configuration and environment variables
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (not in repo)
│
├── graph/                         # LangGraph workflow
│   ├── __init__.py
│   ├── state.py                   # State definition with multi-tool support
│   ├── nodes.py                   # Controller, tool nodes, answer generator
│   ├── workflow.py                # LangGraph workflow creation
│   └── conditions.py              # Conditional routing logic
│
├── agents/                        # Agent logic
│   ├── __init__.py
│   ├── conversation_analyzer.py   # Extract information from messages
│   └── synthesizer.py             # Generate final recommendations
│
├── tools/                         # External API integrations
│   ├── __init__.py
│   ├── calendar_tool.py           # Mock calendar availability checker
│   ├── weather_tool.py            # OpenWeatherMap integration
│   ├── places_tool.py             # Google Maps Places API
│   └── email_tool.py              # Gmail SMTP integration
│
└── utils/                         # Utilities
    ├── __init__.py
    ├── snowflake_connection.py    # Snowflake Cortex LLM interface
    └── mock_data.py               # Mock calendar data for testing
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Snowflake account with Cortex access
- Google Cloud Platform account (for Maps API)
- OpenWeatherMap API key (free tier available)
- Gmail account with 2FA and App Password

### Installation

1. **Clone the repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials (see [Environment Variables](#environment-variables) below)

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the interface**
   
   Open your browser to `http://localhost:8501`

## 🔑 Environment Variables

Create a `.env` file with the following variables (without quotes):

```bash
# Snowflake Configuration (for LLM)
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_ROLE=your_role

# LLM Model
LLM_MODEL=llama3.1-8b

# Google Maps API (for directions and venue search)
GOOGLE_MAPS_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXX

# OpenWeatherMap API (for weather forecasts)
OPENWEATHER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

# Gmail SMTP (for sending invitations)
# Note: Use Gmail App Password, not your regular password
GMAIL_EMAIL=your.email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```