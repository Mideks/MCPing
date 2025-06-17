@echo off
@chcp 65001 >nul
echo Установка зависимостей...
python -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
echo.
echo ✅ Установка завершена.
pause