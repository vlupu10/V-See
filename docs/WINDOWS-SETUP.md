# V-See on Windows: Setup and Distribution

This document covers both **installing V-See as an end user** (no build required) and **building V-See from source** (for developers).

---

## Installing V-See (End Users – No Build Required)

If you have **V-See-Windows.zip**, you can run V-See without installing Python or any developer tools.

### Step 1: Download and extract

1. Download **V-See-Windows.zip** (from a release page, shared link, or project folder).
2. **Extract the zip file:**
   - Right-click the zip file → **Extract All…**
   - Choose a folder (e.g. Desktop, Documents, or `C:\Users\YourName\V-See`)
   - Click **Extract**

### Step 2: Run V-See

1. Open the extracted folder.
2. Double-click **V-See.exe** (or **Run V-See.bat**) to start the app.

That’s it. No installation wizard, no Python, no terminal.

### Optional: Create a shortcut

To start V-See from your Desktop:

1. Right-click **V-See.exe** → **Create shortcut**
2. Cut the shortcut (Ctrl+X) and paste it on your Desktop (Ctrl+V)
3. You can rename it to “V-See” if you like

### System requirements

- Windows 10 or 11 (64-bit)
- No other software required

---

## Building V-See from Source (Developers)

The following sections are for developers who want to run V-See from source or create distribution packages.

---

## Phase 1: Install Python / Conda

### 1. Install Miniconda for Windows

1. Download Miniconda from: https://docs.conda.io/en/latest/miniconda.html  
2. Choose the **Windows 64-bit** installer.  
3. Run the installer:
   - Use the default install location.
   - Optionally check "Add Miniconda to PATH" (or use Anaconda Prompt).
   - Complete the installation.

### 2. Verify conda

1. Open **Anaconda Prompt (Miniconda3)** from the Start Menu.  
2. Run: `conda --version`  
3. You should see something like `conda 24.x.x`.

---

## Phase 2: Run V-See from Source

### 3. Navigate to the project folder

```powershell
cd C:\projects\Project-V-See
```

(Adjust the path if your project lives elsewhere.)

### 4. Create the conda environment

```powershell
conda env create -f environment.yml
```

This creates the `v-see` environment with Python, Pillow, and PyQt6.

### 5. Activate the environment

```powershell
conda activate v-see
```

### 6. Run the application

```powershell
python main.py
```

**Note:** The `run.sh` script is for Unix/macOS. On Windows, use `python main.py` directly.

### 7. (Optional) Install music playback for slideshow

For background music during slideshow, install the mp3-player package with the Qt widget. From the Project-photo-viewer directory:

```powershell
pip install -e "..\vio-python[qt]"
```

(Adjust the path if `vio-python` is not a sibling folder. Requires [ffmpeg](https://ffmpeg.org/) on Windows.)

### 8. Verify it works

- The main window should show the folder tree, thumbnail grid, and preview pane.
- Double-clicking an image should open the viewer window.
- The slideshow button and Configure Slideshow should work. With `mp3-player[qt]` installed, the left panel shows Photos and Music folder trees; music can be selected and auto-starts with the slideshow.

---

## Phase 3: Create a Windows Build (Installer / Distributable)

### 9. Install PyInstaller

With the `v-see` environment activated:

```powershell
pip install pyinstaller
```

### 10. Build the application

From the project root (same folder as `main.py` and `v-see.spec`):

```powershell
pyinstaller v-see.spec --noconfirm
```

### 11. Test the built application

- Navigate to `dist\V-See\`
- Double-click **V-See.exe**

The first run creates `config\state.db` next to the exe. The app should behave the same as when run from source.

### 12. Distribution options

From `docs/WINDOWS-DISTRIBUTION.md`:

| Option | Description |
|--------|-------------|
| **Zip** | Zip the contents of `dist\V-See` and include `packaging/Run V-See.bat`. User extracts and double-clicks the .bat or exe. |
| **Single .exe** | Build with PyInstaller onefile mode (`onefile=True` in the spec). One file to distribute; slower first start. |
| **Installer (7-Zip SFX)** | Use 7-Zip SFX to turn the zip into `V-See-Setup.exe` that extracts and optionally launches the app. |

Use the launcher `.bat` from `packaging/Run V-See.bat` when creating the zip for the first option.

---

## Quick Reference Checklist

| Step | Action |
|------|--------|
| 1 | Install Miniconda for Windows |
| 2 | Open Anaconda Prompt, navigate to project folder |
| 3 | `conda env create -f environment.yml` |
| 4 | `conda activate v-see` |
| 5 | `python main.py` (run from source) |
| 6 | *(Optional)* `pip install -e "..\vio-python[qt]"` for slideshow music |
| 7 | `pip install pyinstaller` |
| 8 | `pyinstaller v-see.spec --noconfirm` |
| 9 | Test `dist\V-See\V-See.exe` |
| 10 | Package for distribution (zip / single exe / SFX installer) |

---

## Troubleshooting

### PyInstaller build fails or exe won't start

- PyQt6 may need to be fully collected. Check PyInstaller docs and the PyQt6 hook (e.g. `--collect-all PyQt6` or adding a hook in the spec).
- If you see a Qt platform plugin error, the Qt libraries may not be fully bundled.

### Antivirus flags the built .exe

- PyInstaller executables are sometimes flagged by antivirus software. This is common; you may need to add an exception or sign the executable for distribution.

### Git / path issues

- If you use Git for Windows and SSH keys, ensure `C:\Program Files\Git\usr\bin` is in your PATH for `ssh` and `ssh-add` to work. See your SSH setup documentation.

---

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — Application design and structure  
- [DISTRIBUTION.md](DISTRIBUTION.md) — Build and distribution overview (all platforms)  
- [WINDOWS-DISTRIBUTION.md](WINDOWS-DISTRIBUTION.md) — Windows packaging options in detail  
