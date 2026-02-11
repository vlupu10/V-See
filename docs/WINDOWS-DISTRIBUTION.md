# Smarter Windows distribution: zip, single .exe, installer

This note clarifies how to ship V-See on Windows so a **normal user** can run it without installing Python or using the terminal.

## Important: we don’t install dependencies on the user’s PC

The only way to avoid asking users to install Python/PyQt6 is to **ship a pre-built app**. So:

- **You** (or CI) build once on Windows with PyInstaller; the output is either a folder (`V-See.exe` + DLLs) or a single `.exe`.
- **The user** gets a zip or an installer that contains that pre-built app. Nothing runs `pip install` or conda on their machine.

So: no “.bat that installs dependencies and runs the app from source.” The .bat (if any) only **launches** the already-built `V-See.exe`.

## No real “autorun” from a zip

- Windows does **not** auto-run scripts when a user extracts a zip. There is no standard “.autorun” that runs when you unzip.
- So we can’t rely on “user extracts zip → something runs automatically.” The user must **double-click** something: either `V-See.exe` or a launcher script.

## Options (pick one or combine)

### Option A: Zip of the built app + launcher .bat

1. On Windows, build as usual: `pyinstaller v-see.spec --noconfirm` → you get `dist\V-See\` (folder with `V-See.exe` and all DLLs).
2. Add a launcher batch file **inside** that folder, e.g. `Run V-See.bat`, that starts the exe (see below).
3. Zip the **contents** of `dist\V-See` (so `V-See.exe`, the `.bat`, and the rest are at the root of the zip).
4. Distribute `V-See-Windows.zip`. User: **Extract** the zip somewhere (e.g. Desktop or `C:\Users\<name>\V-See`), then **double-click `Run V-See.bat`** or **double-click `V-See.exe`**.

The .bat is just a convenience (same folder, clear name); it doesn’t install anything.

**Example `Run V-See.bat`** (must sit next to `V-See.exe`):

```batch
@echo off
cd /d "%~dp0"
start "" "V-See.exe"
```

### Option B: Single .exe (PyInstaller onefile)

- Build with **onefile**: one `V-See.exe` that extracts to a temp folder and runs. User downloads one file and double-clicks it; no zip, no folder.
- Trade-off: first start can be a bit slower (extraction). To enable onefile, change the spec so the EXE gets all binaries/datas and `onefile=True` (no COLLECT, or see PyInstaller docs for onefile spec).

### Option C: Self-extracting “installer” .exe (e.g. 7-Zip SFX)

- Build as now (onedir) → `dist\V-See\`.
- Zip that folder. Use **7-Zip SFX** (or similar) to turn the zip into `V-See-Setup.exe`.
- User runs `V-See-Setup.exe` → chooses (or default) extract folder → files are unpacked → optionally run `V-See.exe`. Feels like a small installer; no dependency install, just unpack + optional launch.

### Option D: “Install and run” .bat for **source** (not for normal users)

- A .bat that runs `conda env create`, `pip install`, `python main.py` is only suitable for developers or power users who already have (or will install) Miniconda. Normal users should get Option A, B, or C instead.

## Recommended for you

- **Simplest for users:** Option A (zip with built app + `Run V-See.bat`) or Option B (single .exe).
- **More “installer-like”:** Option C (SFX .exe).

Use the launcher `.bat` from the `packaging/` folder when you create the zip for Option A.
