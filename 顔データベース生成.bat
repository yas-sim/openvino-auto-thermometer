@echo off
echo 'face_images'�t�H���_�̊�摜���������ʃf�[�^�x�[�X���쐬���܂�
echo �쐬���ꂽ������ʃt�@�C����'face_db'�t�H���_�ɕۑ�����܂�
echo ��x�f�[�^�x�[�X���쐬���ꂽ�猳�̊�ʐ^�͕s�v�ł��i�폜�j
echo;
pause
set cwd=%~dp0
echo %cwd%
if "%INTEL_OPENVINO_DIR%" == "" (
    call "%PROGRAMFILES(X86)%\intel\openvino_2021\bin\setupvars.bat"
)
python "%cwd%register_faces.py"
pause
