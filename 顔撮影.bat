@echo off
echo WebCamで顔写真を撮影し、'face_images'フォルダに格納します
echo IDは出席番号、nameは氏名を入力してください。
echo 氏名は英文字と'_'だけ使用してください(日本語不可, 例：Yamada_Taro)
echo カメラ画像のウインドウ('Cam')が選択されてないとキーを受け付けません。カメラ画像ウインドウをアクティブにしてください。
echo;
set cwd=%~dp0
if "%INTEL_OPENVINO_DIR%" == "" (
    call "%PROGRAMFILES(X86)%\intel\openvino_2021\bin\setupvars.bat"
)
python "%cwd%capture_image.py"
pause
