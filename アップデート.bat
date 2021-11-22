rem @echo off
for /f "usebackq delims=" %%A in (`python -c "import os; print(os.getcwd().split(os.sep)[-1])"`) do set dirname=%%A
if not exist .git (
    cd ..
    git clone https://github.com/yas-sim/openvino-auto-thermometer clone-temp
    xcopy /E /H clone-temp %dirname%
    cd %dirname%
)
git pull
git checkout excel_operation
pause

:end