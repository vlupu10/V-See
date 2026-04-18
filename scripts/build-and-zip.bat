@echo off
REM Build V-See with PyInstaller and create V-See-Windows.zip.
REM Run from project root. Uses conda env "v-see".
REM Requires: conda env create -f environment.yml

cd /d "%~dp0\.."

where conda >nul 2>&1
if errorlevel 1 (
  echo Error: conda not found.
  exit /b 1
)

call conda activate v-see
if errorlevel 1 (
  echo Error: conda env 'v-see' not found. Run: conda env create -f environment.yml
  exit /b 1
)

echo Ensuring PyInstaller, mp3-player, and video support are installed...
pip install -q pyinstaller
pip install -q "PyQt6>=6.7,<7"
if exist "..\vio-python" (
  echo Installing mp3-player[qt] for music support...
  pip install -q -e "..\vio-python[qt]"
  if errorlevel 1 echo Warning: mp3-player install failed; build continues without music support
)

echo Building V-See...
pyinstaller v-see.spec --noconfirm
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

echo Creating V-See-Windows.zip...
copy "packaging\Run V-See.bat" "dist\V-See\"
cd dist\V-See
powershell -Command "Compress-Archive -Path * -DestinationPath ..\..\V-See-Windows.zip -Force"
cd ..\..
echo Created V-See-Windows.zip
