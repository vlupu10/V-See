#!/usr/bin/env bash
# Start V-See photo viewer from the project root.
# Uses only the isolated conda env "v-see" (no interference with other projects).
# One-time setup: conda env create -f environment.yml
# Optional (music): conda activate v-see && pip install -e "../vio-python[qt]"

set -e
cd "$(dirname "$0")"

if ! command -v conda &>/dev/null; then
  echo "Error: conda not found. This project must run in the 'v-see' conda env to avoid interfering with other Python projects." >&2
  echo "Install Miniconda/Anaconda, then run: conda env create -f environment.yml" >&2
  exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"
if ! conda env list | grep -qE '^v-see[\* ]'; then
  echo "Error: conda env 'v-see' not found. Create it with: conda env create -f environment.yml" >&2
  exit 1
fi

conda activate v-see

# PyPI PyQt6 loads the xcb platform plugin from the system/conda libs; Qt 6.5+
# needs libxcb-cursor. Conda provides it (see environment.yml) but does not
# put $CONDA_PREFIX/lib on the default linker path for subprocess-free Python.
if [[ "$(uname -s)" == "Linux" && -n "${CONDA_PREFIX:-}" ]]; then
  export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
fi

exec python main.py "$@"
