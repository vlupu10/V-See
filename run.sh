#!/usr/bin/env bash
# Start V-See photo viewer from the project root.
# Uses only the isolated conda env "v-see" (no interference with other projects).
# One-time setup: conda env create -f environment.yml

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
exec python main.py "$@"
