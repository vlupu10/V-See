# Distributing V-See (install kits)

This document describes how to build install kits (standalone executables or installers) for V-See on different machines and operating systems.

## Developer vs end user

- **Developer:** You build the app with PyInstaller. You need conda, Python, PyInstaller, and optionally vio-python (mp3-player) for music support. You run `build-and-zip.sh` or `build-and-zip.bat` to produce the zip.
- **End user:** Downloads the zip (e.g. V-See-macOS.zip or V-See-Windows.zip), extracts it, and double-clicks the app. No Python, conda, vio-python, or any developer tools required—everything needed to run is bundled in the zip.

## Why one build per platform?

V-See is a Python + PyQt6 app. To run it **without** requiring users to install Python, conda, or dependencies, you “freeze” the app into a standalone bundle. That bundle is **platform- and architecture-specific**:

- **macOS (Apple Silicon M1)** → build on an M1 Mac (or macOS ARM runner)
- **macOS (Intel)** → build on an Intel Mac
- **Windows (x64)** → build on Windows (e.g. your Dell Precision 5520)
- **Linux (x64)** → build on x64 Linux
- **Linux (ARM, e.g. Cubieboard)** → build on that ARM device or an ARM Linux runner

So you get one install kit per (OS, architecture) pair. There is no single universal binary.

## Target matrix (your machines)

| Machine           | OS      | Architecture | Build on              | Output (example)        |
|-------------------|--------|--------------|------------------------|-------------------------|
| MacBook Pro M1    | macOS  | arm64        | M1 Mac                 | `.app` or `.dmg`        |
| MacBook Air M1    | macOS  | arm64        | Same as above          | Same build works        |
| Dell Precision    | Windows| x64          | Windows                | `.exe` or folder        |
| Cubieboard        | Linux  | arm (e.g. armv7l/aarch64) | That device or Linux ARM | binary or directory |

## Option 1: PyInstaller (recommended to start)

PyInstaller bundles the Python interpreter, your code, and PyQt6 into a single folder or executable. No installer UI; you zip the output and ship it (or wrap it in a .dmg on macOS).

### One-time setup (on each build machine)

```bash
# Use the project’s conda env
conda activate v-see
pip install pyinstaller
```

### Build (run from project root)

**Recommended** – use the build script (installs mp3-player for music, then builds and zips):

- **macOS/Linux:** `./scripts/build-and-zip.sh`
- **Windows:** `scripts\build-and-zip.bat`

Or manually:

```bash
# From Project-photo-viewer/
conda activate v-see
pip install -e "../vio-python[qt]"   # optional, for music support
pip install pyinstaller
pyinstaller v-see.spec
```

Output (double-clickable like a normal app):

- **macOS:** `dist/V-See.app` — double-click to open, or install to Applications (see below).
- **Windows:** `dist/V-See/V-See.exe` — double-click the exe (or create a shortcut on Desktop/Start Menu).
- **Linux:** `dist/V-See/V-See` — run the binary; to get an icon in the application menu, use the `.desktop` file (see below).

Zip the output to distribute to end users (e.g. `V-See-macOS.zip`, `V-See-Windows.zip`). End users extract and run—no Python or developer tools required.

Build **on each target OS (and architecture)** to get the right install kit. The same `v-see.spec` is used everywhere.

### macOS: Install to Applications

To have V-See appear in the **Applications** folder (and in Launchpad / Spotlight like any other app):

**Option A — Finder**  
1. Open **Finder** and go to your project’s `dist` folder (where `V-See.app` is).  
2. In the Finder sidebar, click **Applications** (or open **Go → Applications**).  
3. **Drag** `V-See.app` into the Applications window.  
4. Confirm if macOS asks to replace an existing copy.  
5. You can then launch V-See from Launchpad, Spotlight (⌘Space), or Applications.

**Option B — Terminal** (from the project root):

```bash
cp -R dist/V-See.app /Applications/
```

After that, open **Applications** in Finder (or Launchpad) and click **V-See** to run it.

### Windows: Build and run (e.g. Dell Precision)

Do this on the Windows machine (Dell Precision 5520 or any x64 PC):

1. **Get the project**  
   Copy the project folder onto the Dell (e.g. clone the repo, or copy `Project-photo-viewer` from your Mac via USB/network/cloud). You need at least: `main.py`, `v-see.spec`, `environment.yml`, `requirements.txt`, and the `src/` tree.

2. **Install Python and dependencies**  
   - Install [Miniconda for Windows](https://docs.conda.io/en/latest/miniconda.html) (or use an existing Python 3.9+).  
   - Open **Command Prompt** or **PowerShell**, go to the project folder, then:
   ```cmd
   conda env create -f environment.yml
   conda activate v-see
   pip install pyinstaller
   ```

3. **Build the app**  
   From the project root (same folder as `main.py` and `v-see.spec`):
   ```cmd
   pyinstaller v-see.spec --noconfirm
   ```

4. **Run V-See**  
   - Open `dist\V-See\` in File Explorer and **double-click `V-See.exe`**.  
   - Optional: right‑click `V-See.exe` → **Create shortcut**, then move the shortcut to Desktop or pin it to the Start menu.

The first run creates `config\state.db` next to the exe (inside `dist\V-See\`). To “install” for daily use, copy the whole `dist\V-See` folder to e.g. `C:\Program Files\V-See\` or your user folder, then create a shortcut to `V-See.exe` where you like.

### Windows: Zip or single .exe for end users

To give users a **zip** or a **single .exe** (no Python/conda on their machine), see **docs/WINDOWS-DISTRIBUTION.md**. Summary: **Zip** — build, then zip contents of `dist\V-See` and include `packaging/Run V-See.bat`; user extracts and double-clicks .bat or exe. **Single .exe** — build PyInstaller onefile; distribute one file. **Installer-like** — use 7-Zip SFX to make `V-See-Setup.exe` that extracts and optionally runs the app.

### Linux: application menu icon

To have V-See appear in the application menu (so users can click an icon instead of opening a terminal):

1. Build as above; the executable is `dist/V-See/V-See`.
2. Copy the template: `cp packaging/v-see.desktop ~/.local/share/applications/` (or use the path where you installed V-See).
3. Edit the copy and set `Exec=` to the **full path** of the executable, e.g. `Exec=/home/username/dist/V-See/V-See`.
4. Optional: set `Icon=` to a full path to a PNG/icon if you add one.

After that, “V-See” will show up in the Graphics or Viewer menu and can be launched with a single click.

If the built app fails to start with a Qt platform plugin error, PyQt6’s libraries may need to be fully collected; see PyInstaller’s docs and the PyQt6 hook (e.g. `--collect-all PyQt6` or adding a hook to the spec).

### Optional: one-file bundle

For a single executable (slower startup, no extract folder), in `v-see.spec` set `EXE(..., onefile=True)` in the spec. Default here is `onefile=False` for faster startup and easier debugging.

## Option 2: Briefcase (native installers)

[Briefcase](https://briefcase.readthedocs.io/) (BeeWare) can produce **native installers**:

- **macOS:** `.dmg` or `.pkg`
- **Windows:** `.msi` or `.exe` installer
- **Linux:** `.deb`, `.rpm`, or AppImage

Setup and project layout differ from PyInstaller (e.g. `briefcase create`, `briefcase build`). Use this if you want proper “install kits” with installers rather than a portable folder/executable.

## Option 3: Keep using Python + conda on each machine

You can skip install kits and run from source on each machine:

1. Clone the repo (or copy the project).
2. `conda env create -f environment.yml`
3. `conda activate v-see` then `./run.sh` (or `python main.py`).

This is the same workflow you use now; no build step, but each machine needs Python and conda.

## Summary

- **Yes, you can create install kits** for macOS (M1), Windows (Dell), and Linux (Cubieboard).
- **You need a separate build per (OS, architecture)**; the same repo and spec are used, but the build must run on that OS/arch (or a matching CI runner).
- **PyInstaller + `v-see.spec`** gives you a portable app (`.app` on Mac, folder/exe on Windows, folder on Linux) with no installer. Add Briefcase later if you want .dmg/.msi/.deb-style installers.
