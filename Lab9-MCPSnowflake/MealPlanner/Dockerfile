FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY config.py .
COPY mcp_client.py .
COPY llm.py .
COPY tools.py .
COPY graph.py .
COPY utils.py .
COPY app.py .

# Copy .env file into the image
COPY .env .

# Expose Streamlit port
EXPOSE 8510

# Set environment variable for Streamlit
ENV STREAMLIT_SERVER_PORT=8510
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run the application
CMD ["streamlit", "run", "app.py"]