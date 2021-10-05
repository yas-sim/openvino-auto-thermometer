@echo off
set cwd=%~dp0
if "%INTEL_OPENVINO_DIR%" == "" (
    call "%PROGRAMFILES(X86)%\intel\openvino_2021\bin\setupvars.bat"
)
python "%cwd%thermometer.py"
pause
