@echo off
REM Build a single-file, windowed executable using PyInstaller
REM Bundles all source code, assets, CSV seed data, and dependencies.
REM Uses Python 3.13 directly to avoid NumPy/matplotlib DLL incompatibilities with Python 3.14+

C:\Users\Calvyn\AppData\Local\Programs\Python\Python313\python.exe -m PyInstaller --noconfirm --onefile --windowed ^
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
    --hidden-import "numpy" ^
    --hidden-import "customtkinter" ^
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
