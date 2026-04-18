# Salasblog2 FastAPI app
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y git rsync ripgrep nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Configure git identity (needed for scheduler git sync)
RUN git init && \
    git config user.email "pitosalas@gmail.com" && \
    git config user.name "pitosalas"

# Install dependencies
RUN uv sync --frozen --no-dev

# Generate the static site
RUN uv run bg generate

# Copy and setup startup script
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app/src
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Expose port
EXPOSE 8080

# Run the startup script
CMD ["/startup.sh"]