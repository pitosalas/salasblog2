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

# Copy Python files
COPY pyproject.toml uv.lock* ./
COPY .gitignore ./
COPY src/ ./src/
COPY content/ ./content/
COPY themes/ ./themes/
COPY templates/ ./templates/
COPY scripts/ ./scripts/

# Install dependencies
RUN uv sync --frozen

# Generate the static site
RUN uv run python -m salasblog2.cli generate

# Initialize git repository and configure
RUN chmod +x scripts/setup-git.sh && \
    git init && \
    git config user.email "blog-api@salasblog2.com" && \
    git config user.name "Salasblog2 Server" && \
    git add . && \
    git commit -m "Initial commit from Docker build"

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8080

# Run the FastAPI server with git setup
CMD ["sh", "-c", "./scripts/setup-git.sh && uv run salasblog2 server --port 8080"]