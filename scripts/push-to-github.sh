#!/bin/sh
# Simple helper to prepare and show how to push this workspace to GitHub.
# Usage: ./scripts/push-to-github.sh https://github.com/alejandroflamerich/Raspberry-PI-Gateway.git main
REMOTE_URL=${1:-"https://github.com/alejandroflamerich/Raspberry-PI-Gateway.git"}
BRANCH=${2:-main}

echo "Preparing repository to push to $REMOTE_URL (branch: $BRANCH)"

if [ ! -d .git ]; then
  echo "Initializing git repository..."
  git init
else
  echo ".git already exists"
fi

echo "Adding files and creating commit..."
git add .
# create commit if none exists
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Repository has commits; creating update commit if needed"
  git commit -m "Update: sync workspace" || echo "No changes to commit"
else
  git commit -m "Initial commit from local workspace"
fi

echo "Setting branch name to $BRANCH"
git branch -M $BRANCH 2>/dev/null || true

# set remote
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE_URL"

cat <<EOF
Repository prepared. To push, run one of the commands below depending on your auth method:

1) If using HTTPS and Git will prompt for credentials (recommended interactive):
   git push -u origin $BRANCH

2) If using a Personal Access Token non-interactively (NOT recommended to store in shell history):
   git push https://<YOUR_TOKEN>@github.com/alejandroflamerich/Raspberry-PI-Gateway.git -u origin $BRANCH

3) If using SSH:
   git remote set-url origin git@github.com:alejandroflamerich/Raspberry-PI-Gateway.git
   git push -u origin $BRANCH

EOF

echo "Done."
