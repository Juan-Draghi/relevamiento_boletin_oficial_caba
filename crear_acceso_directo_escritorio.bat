@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "TARGET=%PROJECT_DIR%run_desktop_silencioso.vbs"
set "ICON=%PROJECT_DIR%desktop_app\static\app-icon-ciudad.ico"
set "SHORTCUT=%USERPROFILE%\Desktop\Relevamiento BO CABA.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$shell = New-Object -ComObject WScript.Shell; " ^
  "$shortcut = $shell.CreateShortcut('%SHORTCUT%'); " ^
  "$shortcut.TargetPath = '%TARGET%'; " ^
  "$shortcut.WorkingDirectory = '%PROJECT_DIR%'; " ^
  "$shortcut.IconLocation = '%ICON%'; " ^
  "$shortcut.Description = 'Relevamiento Boletin Oficial CABA - Biblioteca CPAU'; " ^
  "$shortcut.Save();"

echo Acceso directo creado en el Escritorio:
echo %SHORTCUT%
pause
