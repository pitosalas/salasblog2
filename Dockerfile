# Multi-stage build for Salasblog2 FastAPI app
FROM python:3.11-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy Python files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/
COPY content/ ./content/
COPY themes/ ./themes/
COPY templates/ ./templates/

# Install dependencies
RUN uv sync --frozen

# Generate the static site
RUN uv run python -m salasblog2.cli generate

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8080

# Run the FastAPI server
CMD ["uv", "run", "salasblog2", "server", "--port", "8080"]