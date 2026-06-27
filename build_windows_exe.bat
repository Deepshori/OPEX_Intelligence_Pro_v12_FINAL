@echo off
cd /d "%~dp0"
echo Building OPEX Intelligence Pro v12.1...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pyinstaller --onefile --windowed --name "OPEX Intelligence Pro" --version-file version_info.txt --add-data "config;config" main.py
if exist "dist\OPEX Intelligence Pro.exe" (
  echo Done: dist\OPEX Intelligence Pro.exe
) else (
  echo Build failed. Check messages above.
)
pause
