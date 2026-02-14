# PyInstaller spec for V-See. Run from project root: pyinstaller v-see.spec
# Build on each target OS/arch (macOS M1, Windows x64, Linux ARM/x64) to get that install kit.
# Result: macOS -> V-See.app (double-clickable); Windows/Linux -> dist/V-See/ with executable.
# Requires mp3-player[qt] in the build env for music support. Run scripts/build-and-zip.sh
# (macOS/Linux) or scripts/build-and-zip.bat (Windows) to install deps and build.

import os
import sys

block_cipher = None

# Add vio-python path (sibling of Project-photo-viewer) so mp3_player is found
# Run pyinstaller from project root; cwd is Project-photo-viewer
_vio_python = os.path.normpath(os.path.join(os.getcwd(), "..", "vio-python"))
_pathex = ["src"]
if os.path.isdir(_vio_python):
    _pathex.append(_vio_python)

a = Analysis(
    ['main.py'],
    pathex=_pathex,
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'mp3_player',
        'mp3_player.mp3_player',
        'mp3_player.qt_player_widget',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='V-See',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='V-See',
)

# On macOS, wrap the folder in a .app bundle so the user can double-click it like any app.
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='V-See.app',
        icon=None,
        bundle_identifier='com.vsee.photo-viewer',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'CFBundleName': 'V-See',
            'CFBundleDisplayName': 'V-See',
            'CFBundleGetInfoString': 'V-See Photo Viewer',
        },
    )
