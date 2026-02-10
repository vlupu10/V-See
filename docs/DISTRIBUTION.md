# Distributing V-See (install kits)

This document describes how to build install kits (standalone executables or installers) for V-See on different machines and operating systems.

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

```bash
# From Project-photo-viewer/
pyinstaller v-see.spec
```

Output (double-clickable like a normal app):

- **macOS:** `dist/V-See.app` — double-click to open, or drag to Applications. The spec builds a proper .app bundle.
- **Windows:** `dist/V-See/V-See.exe` — double-click the exe (or create a shortcut on Desktop/Start Menu).
- **Linux:** `dist/V-See/V-See` — run the binary; to get an icon in the application menu, use the `.desktop` file (see below).

Build **on each target OS (and architecture)** to get the right install kit. The same `v-see.spec` is used everywhere.

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
