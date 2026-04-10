@echo off
REM Build a single-file, windowed executable using PyInstaller.
REM Bundles source code, assets, SQLite support, and theme-specific logo assets.
SETLOCAL ENABLEDELAYEDEXPANSION

set PYTHON=C:\Users\Calvyn\AppData\Local\Programs\Python\Python313\python.exe
if not exist "%PYTHON%" set PYTHON=%~dp0.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=python

%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements for build environment.
    pause
    exit /b 1
)

%PYTHON% -m PyInstaller --noconfirm --onefile --windowed ^
    --icon "assets/nexo.ico" ^
    --add-data "assets;assets" ^
    --add-data "config.py;." ^
    --add-data "nexo.db;." ^
    --add-data "backend;backend" ^
    --add-data "frontend_ui;frontend_ui" ^
    --hidden-import "sqlalchemy" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "numpy" ^
    --hidden-import "customtkinter" ^
    --collect-all "sqlalchemy" ^
    --collect-all "customtkinter" ^
    --collect-all "matplotlib" ^
    --exclude-module "PyQt5" ^
    --exclude-module "PyQt6" ^
    --exclude-module "PySide2" ^
    --exclude-module "PySide6" ^
    --exclude-module "scipy" ^
    --exclude-module "pandas" ^
    --exclude-module "pytest" ^
    --exclude-module "setuptools" ^
    --name nexo ^
    main.py

echo.
echo Build completed. Check the "dist" directory for "nexo.exe".
pause
