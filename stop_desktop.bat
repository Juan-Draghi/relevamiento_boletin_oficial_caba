@echo off
setlocal
set "BOCABA_PORT=7862"

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%BOCABA_PORT% .*LISTENING"') do (
  taskkill /PID %%P /F >nul 2>nul
)

exit /b
