#!/bin/bash
# Install git hooks from the repo into .git/hooks/
# Run once after cloning: bash Programs/hooks/install.sh

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK_SRC="$REPO_ROOT/Programs/hooks/pre-commit"
HOOK_DST="$REPO_ROOT/.git/hooks/pre-commit"

if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "Error: not a git repository"
    exit 1
fi

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"
echo "Installed pre-commit hook to .git/hooks/pre-commit"
