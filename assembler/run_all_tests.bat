@echo off
cd /d "%~dp0"

echo Running MLASM built-in self-test...
python MLASM.py --self-test
if errorlevel 1 exit /b %errorlevel%

echo.
echo Running all assembly/simulator tests...
python verify_all_tests.py
exit /b %errorlevel%
