# Multi-stage build for Salasblog2 FastAPI app
FROM python:3.11-slim

# Install system dependencies including git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Clone the repository directly from persistent-volume branch
RUN git clone -b persistent-volume https://github.com/pitosalas/salasblog2.git /tmp/repo && \
    cp -r /tmp/repo/* . && \
    cp -r /tmp/repo/.git . && \
    cp /tmp/repo/.gitignore . 2>/dev/null || true && \
    rm -rf /tmp/repo && \
    git config user.email "blog-api@salasblog2.com" && \
    git config user.name "Salasblog2 Server" && \
    chmod +x scripts/setup-git.sh

# Install dependencies
RUN uv sync --frozen

# Generate the static site
RUN uv run python -m salasblog2.cli generate

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8080

# Run the FastAPI server with git setup
CMD ["sh", "-c", "./scripts/setup-git.sh && uv run salasblog2 server --port 8080"]