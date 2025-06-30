# Multi-stage build for Salasblog2 FastAPI app
FROM python:3.11-slim

# Install system dependencies including git and rsync
RUN apt-get update && \
    apt-get install -y git rsync && \
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
    rm -rf /app/content && \
    mkdir -p /app/content

# Install dependencies
RUN uv sync --frozen

# Generate the static site
RUN uv run python -m salasblog2.cli generate

# Create startup script for git authentication and initial sync
RUN echo '#!/bin/bash\n\
# Setup git authentication if token provided\n\
if [ -n "$GIT_TOKEN" ]; then\n\
    echo "Setting up git authentication..."\n\
    git config --global credential.helper store\n\
    echo "https://oauth2:${GIT_TOKEN}@github.com" > ~/.git-credentials\n\
    git remote set-url origin "https://oauth2:${GIT_TOKEN}@github.com/pitosalas/salasblog2.git"\n\
    echo "Git authentication configured"\n\
fi\n\
\n\
# Ensure /app/content is a real directory, not a symlink\n\
if [ -L "/app/content" ]; then\n\
    echo "Removing symlink at /app/content..."\n\
    rm -f /app/content\n\
fi\n\
mkdir -p /app/content\n\
\n\
# Sync content from volume if it exists (initial setup)\n\
if [ -d "/data/content" ] && [ "$(ls -A /data/content 2>/dev/null)" ]; then\n\
    echo "Found existing content in volume, syncing to /app/content..."\n\
    rsync -av --update /data/content/ /app/content/\n\
    echo "Initial sync from volume completed"\n\
else\n\
    echo "No existing content in volume found"\n\
fi\n\
\n\
# Start the server\n\
exec uv run salasblog2 server --port 8080' > /startup.sh && \
chmod +x /startup.sh

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8080

# Run the startup script
CMD ["/startup.sh"]