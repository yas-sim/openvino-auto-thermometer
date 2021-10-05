@echo off
echo 'face_images'フォルダの顔画像から顔特徴量データベースを作成します
echo 作成された顔特徴量ファイルは'face_db'フォルダに保存されます
echo 一度データベースが作成されたら元の顔写真は不要です（削除可）
echo;
pause
set cwd=%~dp0
echo %cwd%
if "%INTEL_OPENVINO_DIR%" == "" (
    call "%PROGRAMFILES(X86)%\intel\openvino_2021\bin\setupvars.bat"
)
python "%cwd%register_faces.py"
pause
