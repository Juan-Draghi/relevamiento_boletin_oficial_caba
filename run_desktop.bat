@echo off
setlocal
pushd "%~dp0"

set "BOCABA_PORT=7862"

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%BOCABA_PORT% .*LISTENING"') do (
  taskkill /PID %%P /F >nul 2>nul
)

where pythonw.exe >nul 2>nul
if %ERRORLEVEL%==0 (
  start "" pythonw.exe "%CD%\desktop_app\app.py"
) else (
  start "" /min python "%CD%\desktop_app\app.py"
)

popd
exit /b
