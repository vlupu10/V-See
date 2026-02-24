#!/usr/bin/env bash
#
# Build and deploy V-See from the develop branch to the applications folder.
# Run from project root: ./deploy.sh
#
# Build: uses scripts/build-and-zip.sh (conda env v-see, PyInstaller).
# Deploy: copies dist/V-See.app (macOS) or dist/V-See (Linux) into APPLICATIONS_FOLDER.
#
# Optional: set APPLICATIONS_FOLDER to override deploy target (default: project root/Applications).
# Optional: set SKIP_BRANCH_CHECK=1 to build from current branch without checking develop.
#
# Author: Viorel LUPU
# Date: 2026-02-17
# Purpose: One-step build and deploy for V-See photo viewer

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Optional: require develop branch
if [[ "${SKIP_BRANCH_CHECK}" != "1" ]] && git rev-parse --is-inside-work-tree &>/dev/null; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [[ "$BRANCH" != "develop" ]]; then
    echo "Warning: current branch is '$BRANCH', not 'develop'. Set SKIP_BRANCH_CHECK=1 to build anyway." >&2
    exit 1
  fi
fi

# Build (creates dist/V-See.app or dist/V-See and zip)
echo "=== Building V-See ==="
bash "$PROJECT_ROOT/scripts/build-and-zip.sh"

# Deploy target: default is project root/Applications
APPLICATIONS_FOLDER="${APPLICATIONS_FOLDER:-$PROJECT_ROOT/Applications}"
mkdir -p "$APPLICATIONS_FOLDER"

if [[ "$(uname)" == "Darwin" ]]; then
  SRC="$PROJECT_ROOT/dist/V-See.app"
  DST="$APPLICATIONS_FOLDER/V-See.app"
  if [[ ! -d "$SRC" ]]; then
    echo "Error: build artifact not found: $SRC" >&2
    exit 1
  fi
  echo "=== Deploying to $APPLICATIONS_FOLDER ==="
  rm -rf "$DST"
  cp -R "$SRC" "$DST"
  echo "Deployed: $DST"
elif [[ "$(uname)" == "Linux" ]]; then
  SRC="$PROJECT_ROOT/dist/V-See"
  DST="$APPLICATIONS_FOLDER/V-See"
  if [[ ! -d "$SRC" ]]; then
    echo "Error: build artifact not found: $SRC" >&2
    exit 1
  fi
  echo "=== Deploying to $APPLICATIONS_FOLDER ==="
  rm -rf "$DST"
  cp -R "$SRC" "$DST"
  echo "Deployed: $DST"
else
  echo "Deploy is supported on macOS and Linux only. Build output is in dist/." >&2
  exit 1
fi

echo "Done. Run the app from: $DST"
