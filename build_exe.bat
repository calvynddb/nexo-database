@echo off
REM Build a single-file, windowed executable using PyInstaller
REM Bundles all source code, assets, CSV seed data, and dependencies.

pyinstaller --noconfirm --onefile --windowed ^
    --icon "assets/nexo.ico" ^
    --add-data "assets;assets" ^
    --add-data "config.py;." ^
    --add-data "students.csv;." ^
    --add-data "programs.csv;." ^
    --add-data "colleges.csv;." ^
    --add-data "users.csv;." ^
    --add-data "backend;backend" ^
    --add-data "frontend_ui;frontend_ui" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "matplotlib" ^
    --hidden-import "matplotlib.backends.backend_tkagg" ^
    --hidden-import "numpy" ^
    --hidden-import "customtkinter" ^
    --collect-all "customtkinter" ^
    --exclude-module "PyQt5" ^
    --exclude-module "PyQt6" ^
    --exclude-module "PySide2" ^
    --exclude-module "PySide6" ^
    --exclude-module "scipy" ^
    --exclude-module "pandas" ^
    --exclude-module "pytest" ^
    --exclude-module "setuptools" ^
    --exclude-module "unittest" ^
    --name nexo ^
    main.py

echo.
echo Build completed. Check the "dist" directory for "nexo.exe".
pause
