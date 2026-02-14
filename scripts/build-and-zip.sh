#!/usr/bin/env bash
# Build V-See with PyInstaller and create a zip archive.
# Run from project root. Uses conda env "v-see" and requires pyinstaller.
# Output: dist/V-See.app (macOS) or dist/V-See/ (Windows/Linux) and V-See-<platform>.zip

set -e
cd "$(dirname "$0")/.."

if ! command -v conda &>/dev/null; then
  echo "Error: conda not found." >&2
  exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"
if ! conda env list | grep -qE '^v-see[\* ]'; then
  echo "Error: conda env 'v-see' not found. Run: conda env create -f environment.yml" >&2
  exit 1
fi

conda activate v-see

# Ensure PyInstaller, mp3-player (music), and deps for video support
pip install -q pyinstaller
pip install -q PyQt6-Multimedia PyQt6-MultimediaWidgets 2>/dev/null || true
if [[ -d "../vio-python" ]]; then
  echo "Installing mp3-player[qt] for music support..."
  pip install -q -e "../vio-python[qt]" || echo "Warning: mp3-player install failed; build continues without music support"
fi

echo "Building V-See..."
pyinstaller v-see.spec --noconfirm

# Create zip based on platform
if [[ "$(uname)" == "Darwin" ]]; then
  ZIP_NAME="V-See-macOS.zip"
  cd dist
  zip -r "../$ZIP_NAME" V-See.app
  cd ..
  echo "Created $ZIP_NAME"
elif [[ "$(uname)" == "Linux" ]]; then
  ZIP_NAME="V-See-Linux.zip"
  cd dist
  zip -r "../$ZIP_NAME" V-See
  cd ..
  echo "Created $ZIP_NAME"
else
  echo "For Windows: build with 'pyinstaller v-see.spec --noconfirm', then zip dist\\V-See (include packaging/Run V-See.bat) as V-See-Windows.zip"
fi
