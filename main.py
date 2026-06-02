@echo off
echo AI 기반 공부 계획 평가 시스템 실행파일을 생성합니다.
echo.

cd /d %~dp0\..

pip install -r src\requirements.txt
pip install pyinstaller

pyinstaller --onefile --windowed src\main.py --name study_manager

echo.
echo 실행파일 생성이 완료되었습니다.
echo dist 폴더 안의 study_manager.exe 파일을 확인하세요.
pause
