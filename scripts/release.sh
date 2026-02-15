#!/usr/bin/env bash
# V-See: commit, push develop and release branch, build, and optionally deploy.
#
# Usage:
#   ./scripts/release.sh [commit message]     # commit, push, build, deploy
#   ./scripts/release.sh --no-deploy          # skip GitHub release upload
#   VERSION=v1.0.1 ./scripts/release.sh       # use specific version for release tag
#
# Requires: git, conda (v-see env), and optionally gh (GitHub CLI) for deploy.
# Changes are in V-See (Project-photo-viewer) only; vio-python is not touched.

set -e
cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"

# Parse args
DEPLOY=true
COMMIT_MSG=""
for arg in "$@"; do
  if [[ "$arg" == "--no-deploy" ]]; then
    DEPLOY=false
  else
    COMMIT_MSG="$arg"
  fi
done

# Version for GitHub release tag (default from release branch or v1.0.0)
VERSION="${VERSION:-v1.0.0}"

echo "=== V-See Release ==="
echo "Commit message: ${COMMIT_MSG:-<auto>}"
echo "Release version: $VERSION"
echo "Deploy to GitHub: $DEPLOY"
echo ""

# --- 1. Commit and push develop ---
if [[ "$(git branch --show-current)" != "develop" ]]; then
  echo "Error: Must be on branch 'develop'. Current: $(git branch --show-current)" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  if [[ -z "$COMMIT_MSG" ]]; then
    COMMIT_MSG="Fix slideshow crash, suppress Qt multimedia logs"
  fi
  echo ">>> Committing changes..."
  git add -A
  git commit -m "$COMMIT_MSG"
else
  echo ">>> No uncommitted changes; skipping commit."
fi

echo ">>> Pushing develop..."
git push origin develop

# --- 2. Update and push release/v1.0.0 ---
echo ">>> Updating release/v1.0.0..."
git checkout release/v1.0.0
git merge develop -m "Merge develop into release/v1.0.0"
git push origin release/v1.0.0
git checkout develop

# --- 3. Build ---
echo ">>> Building..."
./scripts/build-and-zip.sh

# --- 4. Deploy (GitHub release) ---
ZIP_NAME=""
if [[ "$(uname)" == "Darwin" ]]; then
  ZIP_NAME="V-See-macOS.zip"
elif [[ "$(uname)" == "Linux" ]]; then
  ZIP_NAME="V-See-Linux.zip"
fi

if [[ "$DEPLOY" == "true" ]] && [[ -n "$ZIP_NAME" ]] && [[ -f "$PROJECT_ROOT/$ZIP_NAME" ]]; then
  if command -v gh &>/dev/null; then
    echo ">>> Creating/updating GitHub release $VERSION..."
    if gh release view "$VERSION" &>/dev/null; then
      gh release upload "$VERSION" "$ZIP_NAME" --clobber
      echo "Updated release $VERSION with $ZIP_NAME"
    else
      gh release create "$VERSION" "$ZIP_NAME" --title "V-See $VERSION" --notes "See changelog for details."
      echo "Created release $VERSION with $ZIP_NAME"
    fi
  else
    echo ">>> gh CLI not found; skipping deploy. Upload $ZIP_NAME manually to GitHub Releases."
  fi
elif [[ "$DEPLOY" == "true" ]] && [[ -z "$ZIP_NAME" ]]; then
  echo ">>> Deploy skipped: build zip not produced on this platform (e.g. Windows)."
fi

echo ""
echo "=== Done ==="
