@echo off
@chcp 65001 >nul
echo [*] Активация виртуального окружения...
call venv\Scripts\activate

echo [*] Очистка старых сборок...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
del /q *.spec 2>nul

echo [*] Сборка консольной версии...
pyinstaller --onefile app_console.py --name mcping_console

echo [*] Сборка веб-версии...
pyinstaller --onefile ^
 --add-data "templates;templates" ^
 --add-data "static;static" ^
 app_web.py --name mcping_web

echo [*] Подготовка папки release_builds...
mkdir release_builds 2>nul
copy dist\mcping_console.exe release_builds\
copy dist\mcping_web.exe release_builds\

echo [✓] Сборка завершена. Файлы:
echo     release_builds\mcping_console.exe
echo     release_builds\mcping_web.exe
pause