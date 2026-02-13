FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Expose SSE port
EXPOSE 8080

# Run the MCP server
CMD ["python", "-m", "src.server"]
