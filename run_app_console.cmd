@echo off
@chcp 65001 >nul
echo Запуск приложения...
call venv\Scripts\activate
python app_console.py
pause