@echo off
setlocal
cd /d "%~dp0\.."
py -3.12 -m venv .venv-build
if errorlevel 1 goto failed
.venv-build\Scripts\python -m pip install -r windows\requirements-build.txt
if errorlevel 1 goto failed
.venv-build\Scripts\python -m PyInstaller --noconfirm --clean --onefile --windowed --name KeyToFolder --paths . --paths windows --add-data "ui.html:." --icon windows\AppIcon.ico windows\desktop.py
if errorlevel 1 goto failed
echo Built dist\KeyToFolder.exe
exit /b 0
:failed
echo Windows build failed.
exit /b 1
