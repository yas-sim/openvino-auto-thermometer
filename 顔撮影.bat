@echo off
echo WebCam�Ŋ�ʐ^���B�e���A'face_images'�t�H���_�Ɋi�[���܂�
echo ID�͏o�Ȕԍ��Aname�͎�������͂��Ă��������B
echo �����͉p������'_'�����g�p���Ă�������(���{��s��, ��FYamada_Taro)
echo �J�����摜�̃E�C���h�E('Cam')���I������ĂȂ��ƃL�[���󂯕t���܂���B�J�����摜�E�C���h�E���A�N�e�B�u�ɂ��Ă��������B
echo;
set cwd=%~dp0
if "%INTEL_OPENVINO_DIR%" == "" (
    call "%PROGRAMFILES(X86)%\intel\openvino_2021\bin\setupvars.bat"
)
python "%cwd%capture_image.py"
pause
