#!/bin/bash

# === CONFIG ===
REPO_NAME=$(basename "$PWD")
GITHUB_USERNAME="ghost-hub1"           # <<< Replace this
GIT_COMMIT_MESSAGE="second commit"
REMOTE_URL="git@github.com:$GITHUB_USERNAME/$REPO_NAME.git"

# === INIT IF NOT ALREADY ===
if [ ! -d ".git" ]; then
    git init
    git branch -M main
fi

# === ADD, COMMIT, AND PUSH ===
git add .
git commit -m "$GIT_COMMIT_MESSAGE"
git remote remove origin 2>/dev/null
git remote add origin "git@github.com:$GITHUB_USERNAME/Paysphere.git"
git push -u origin main
