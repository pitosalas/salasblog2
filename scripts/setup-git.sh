#!/bin/bash

# Setup git authentication and remote
if [ -n "$GIT_TOKEN" ]; then
    echo "Setting up git with GitHub token authentication"
    git config --global credential.helper store
    echo "https://oauth2:${GIT_TOKEN}@github.com" > ~/.git-credentials
    git remote set-url origin "https://oauth2:${GIT_TOKEN}@github.com/pitosalas/salasblog2.git"
    echo "Git authentication configured successfully"
else
    echo "No GIT_TOKEN found, git push operations will not work"
    git remote add origin https://github.com/pitosalas/salasblog2.git 2>/dev/null || true
fi

# Update git user config from environment if available
if [ -n "$GIT_EMAIL" ]; then
    git config user.email "$GIT_EMAIL"
fi

if [ -n "$GIT_NAME" ]; then
    git config user.name "$GIT_NAME"
fi

echo "Git setup completed"