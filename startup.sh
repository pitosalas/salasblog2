#!/bin/bash
set -e

echo "Starting salasblog2..."

# Setup git authentication if token provided
if [ -n "$GIT_TOKEN" ]; then
    echo "Setting up git authentication..."
    git config --global credential.helper store
    echo "https://oauth2:${GIT_TOKEN}@github.com" > ~/.git-credentials
    git remote set-url origin "https://oauth2:${GIT_TOKEN}@github.com/pitosalas/salasblog2.git"
    echo "Git authentication configured"
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

# Repository-first sync - use repository as base, add only newer content from volume
if [ -d "/data/content" ] && [ "$(ls -A /data/content 2>/dev/null)" ]; then
    echo "Found existing content in volume, performing repository-first sync..."
    
    # Repository content is authoritative - only sync files from volume that are newer
    # This ensures deleted repository content stays deleted, but allows new dynamic content
    echo "Repository content takes precedence, syncing only newer volume content..."
    
    # Use --update flag to only copy files that are newer in the source
    # This preserves all repository content while adding new volume content
    rsync -av --update /data/content/ /app/content/
    
    echo "Repository-first sync completed - repository is authoritative, newer volume content added"
else
    echo "No existing content in volume found - using pure repository content"
fi

# Set excerpt environment variables if not already set
export EXCERPT_LENGTH=${EXCERPT_LENGTH:-80}
export EXCERPT_SMART_THRESHOLD=${EXCERPT_SMART_THRESHOLD:-30}
echo "Using excerpt settings: length=${EXCERPT_LENGTH}, smart_threshold=${EXCERPT_SMART_THRESHOLD}"

# Set scheduler environment variables if not already set
export SCHED_GITSYNC_HRS=${SCHED_GITSYNC_HRS:-6.0}
export SCHED_RAINSYNC_HRS=${SCHED_RAINSYNC_HRS:-2.0}
echo "Using scheduler settings: git_sync=${SCHED_GITSYNC_HRS}h, raindrop_sync=${SCHED_RAINSYNC_HRS}h"

echo "Regenerating site with current environment variables..."
uv run salasblog2 generate
echo "Site regeneration completed"

exec uv run salasblog2 server --port 8080