@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto check_py
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto check_py
".venv\Scripts\python.exe" app.py
goto finished
:check_py
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto check_python
py -3 app.py
goto finished
:check_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto missing_python
python app.py
goto finished
:missing_python
echo Python 3.10 or newer is required.
echo Install it from https://www.python.org/downloads/ and launch again.
pause
exit /b 1
:finished
if not errorlevel 1 exit /b 0
echo The app stopped with an error. Please read the message above.
pause
exit /b 1
