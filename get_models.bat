: get_model.bat
if "%INTEL_OPENVINO_DIR%" == "" (
    call "%PROGRAMFILES(X86)%\intel\openvino_2021\bin\setupvars.sh"
)

python "%INTEL_OPENVINO_DIR%\deployment_tools\open_model_zoo\tools\downloader\downloader.py" --list models.lst
python "%INTEL_OPENVINO_DIR%\deployment_tools\open_model_zoo\tools\downloader\converter.py" --list models.lst
