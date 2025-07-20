# Multi-stage build for Salasblog2 FastAPI app
FROM python:3.11-slim

# Accept GIT_BRANCH as build argument (defaults to main)
ARG GIT_BRANCH=main

# Install system dependencies including git, rsync, ripgrep, and nano
RUN apt-get update && \
    apt-get install -y git rsync ripgrep nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Clone the repository from specified branch
RUN git clone -b ${GIT_BRANCH} https://github.com/pitosalas/salasblog2.git /tmp/repo && \
    cp -r /tmp/repo/* . && \
    cp -r /tmp/repo/.git . && \
    cp /tmp/repo/.gitignore . 2>/dev/null || true && \
    rm -rf /tmp/repo && \
    git config user.email "pitosalas@gmail.com" && \
    git config user.name "pitosalas"

# Install dependencies
RUN uv sync --frozen

# Generate the static site
RUN uv run python -m salasblog2.cli generate --theme test

# Copy and setup startup script
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8080

# Run the startup script
CMD ["/startup.sh"]