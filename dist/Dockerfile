FROM python:3.12-alpine

WORKDIR /app

# Install only necessary system dependencies
RUN apk add --no-cache gcc musl-dev sqlite

# Install Python dependencies
COPY governor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt aiohttp

# Copy entire governor service directory
COPY governor/ ./

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create data directories
RUN mkdir -p /data/reports/memo /data/reports/traces /data/reports/full

# Expose ports: 9090 for MCP, 9091 for Web Viewer
EXPOSE 9090 9091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9090/health')" || exit 1

ENTRYPOINT ["bash", "entrypoint.sh"]
