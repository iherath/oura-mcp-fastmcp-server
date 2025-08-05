FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Set environment variables
ENV MCP_SERVER_NAME=oura-mcp-server
ENV MCP_SERVER_VERSION=1.0.0
ENV MCP_PROTOCOL_VERSION=2025-06-18
ENV HOST=0.0.0.0
ENV PORT=3000

# Expose the port
EXPOSE 3000

# Run the server
CMD ["python", "server.py"] 