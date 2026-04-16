#!/bin/bash
set -e

echo "Starting salasblog2..."

# Setup git authentication if token provided
if [ -n "$GIT_TOKEN" ]; then
    echo "Setting up git authentication..."
    git config --global credential.helper store
    echo "https://oauth2:${GIT_TOKEN}@github.com" > ~/.git-credentials
    if git remote get-url origin &>/dev/null; then
        git remote set-url origin "https://oauth2:${GIT_TOKEN}@github.com/pitosalas/salasblog2.git"
    else
        git remote add origin "https://oauth2:${GIT_TOKEN}@github.com/pitosalas/salasblog2.git"
    fi
    echo "Git authentication configured"

    # Fetch remote history so the local repo has a valid commit to push from.
    # The Dockerfile excludes .git, so the container starts with a bare `git init`.
    # Without at least one commit in the history, `git push origin HEAD:main` fails.
    # timeout 20 prevents a hung GitHub connection from blocking the entire startup.
    echo "Fetching git history from remote..."
    if timeout 20 git fetch --depth=1 origin main 2>/dev/null; then
        git checkout -f -B main origin/main
        echo "Git repository synced with remote ($(git rev-parse --short HEAD))"
    else
        echo "Warning: Could not fetch from remote — scheduler git sync may fail"
    fi
fi

# Configure git if credentials are provided
if [ -n "$GIT_EMAIL" ]; then
    echo "Setting git user email to: $GIT_EMAIL"
    git config user.email "$GIT_EMAIL"
fi

if [ -n "$GIT_NAME" ]; then
    echo "Setting git user name to: $GIT_NAME"
    git config user.name "$GIT_NAME"
fi

# Show current git configuration
echo "Current git user: $(git config user.name) <$(git config user.email)>"

# Ensure /app/content is a real directory, not a symlink
if [ -L "/app/content" ]; then
    echo "Removing symlink at /app/content..."
    rm -f /app/content
fi
mkdir -p /app/content

# Volume-first architecture - /data/content is source of truth
# Initialize /data/content from repository if it's empty (first deployment)
if [ ! -d "/data/content" ] || [ ! "$(ls -A /data/content 2>/dev/null)" ]; then
    echo "Initializing empty /data/content from repository..."
    mkdir -p /data/content
    cp -r /app/content/* /data/content/ 2>/dev/null || true
    echo "Initialized /data/content from repository content"
else
    echo "Using existing /data/content as source of truth"
fi

# Set excerpt environment variables if not already set
export EXCERPT_LENGTH=${EXCERPT_LENGTH:-80}
export EXCERPT_SMART_THRESHOLD=${EXCERPT_SMART_THRESHOLD:-30}
echo "Using excerpt settings: length=${EXCERPT_LENGTH}, smart_threshold=${EXCERPT_SMART_THRESHOLD}"

# Set scheduler environment variables if not already set
export SCHED_GITSYNC_HRS=${SCHED_GITSYNC_HRS:-6.0}
export SCHED_RAINSYNC_HRS=${SCHED_RAINSYNC_HRS:-2.0}
echo "Using scheduler settings: git_sync=${SCHED_GITSYNC_HRS}h, raindrop_sync=${SCHED_RAINSYNC_HRS}h"

# Set logging level if not already set (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=${LOG_LEVEL:-INFO}
echo "Using log level: ${LOG_LEVEL}"

# Always sync pages from image to volume so page edits in the repo take effect on deploy
if [ -d "/app/content/pages" ] && [ -d "/data/content" ]; then
    echo "Syncing pages from image to volume..."
    mkdir -p /data/content/pages
    rsync -a --update /app/content/pages/ /data/content/pages/
    echo "Pages sync completed"
fi

echo "Starting server..."
exec uv run bg server --port 8080