@echo off
setlocal
pushd "%~dp0"
python -m pip install -r desktop_app\requirements.txt
popd
pause
