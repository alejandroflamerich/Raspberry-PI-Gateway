#!/bin/sh
# Run this from the repository root to add, commit and show the commit created.
# Usage: ./scripts/do-commit.sh

MSG_FILE="COMMIT_MESSAGE.txt"
if [ ! -f "$MSG_FILE" ]; then
  echo "Create $MSG_FILE with the commit message before running this script." >&2
  exit 1
fi

git add .
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  git commit -F "$MSG_FILE" || (echo "No changes to commit" && exit 0)
else
  git commit -m "$(cat "$MSG_FILE")"
fi

echo "Commit created. Run: git push -u origin main"