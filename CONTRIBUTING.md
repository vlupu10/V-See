# Contributing to V-See

Thanks for your interest in contributing.

## Development setup

1. Clone the repo (include `vio-python` if you need music support — it should be a sibling folder).
2. Create the conda environment:

   ```bash
   conda env create -f environment.yml
   conda activate v-see
   ```

3. Optional (music playback): `pip install -e "../vio-python[qt]"` (from Project-photo-viewer directory).
4. Run the app: `./run.sh` (macOS/Linux) or `python main.py` (Windows).

## Building for distribution

- **macOS/Linux:** `./scripts/build-and-zip.sh`
- **Windows:** `scripts\build-and-zip.bat`

For music support in the built app, ensure `vio-python` is a sibling folder of `Project-photo-viewer` before building. The build script installs `mp3-player[qt]` automatically when possible.

## Project structure

- `src/photo_viewer/` — main application code
- `docs/` — architecture and setup documentation
- `scripts/` — build and packaging scripts

## Submitting changes

1. Fork the repo and create a branch.
2. Make your changes, keeping the style consistent.
3. Open a pull request with a clear description of the change.
