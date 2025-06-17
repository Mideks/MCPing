@echo off
@chcp 65001 >nul
echo Запуск проекта...
call venv\Scripts\activate
python app.py
pause