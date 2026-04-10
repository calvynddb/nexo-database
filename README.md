<p align="center">
  <img src="assets/banner.png" alt="nexo banner" width="600"/>
</p>

<h1 align="center">nexo</h1>

<p align="center">
  <b>A Simple Student Information System</b><br/>
  Built with Python, CustomTkinter, and SQLite
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white" alt="Python 3.13"/>
  <img src="https://img.shields.io/badge/UI-CustomTkinter-4f46e5" alt="CustomTkinter"/>
  <img src="https://img.shields.io/badge/database-SQLite-16a34a" alt="SQLite"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT License"/>
</p>

<p align="center">
  <img src="assets/screenshots/dashboard.png" alt="nexo dashboard"/>
</p>

---

## Overview

Nexo is a desktop student information system with full CRUDL operations for Students, Programs, and Colleges.
The app is fully SQLite-backed through SQLAlchemy.

Key features:

- Streamlined access flow with a single Proceed as Administrator entry action
- Theme management with Light/Dark mode plus 4 accent presets (Purple, Blue, Orange, Pink)
- Theme preference persistence across app restarts
- CRUDL for Students, Programs, Colleges
- Search, sort, and pagination in each table view
- Dashboard analytics and enrollment visuals
- Packaged desktop executable via PyInstaller

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.13+ |
| UI Framework | CustomTkinter |
| Database | SQLite + SQLAlchemy |
| Charts | Matplotlib + NumPy |
| Packaging | PyInstaller |

---

## Getting Started

### Prerequisites

- Python 3.13+
- Dependencies from requirements.txt

### Installation

```bash
git clone https://github.com/calvynddb/Simple-Student-Information-System.git
cd Simple-Student-Information-System

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

On first launch, the app initializes the SQLite schema in nexo.db if needed.

---

## Project Structure

```text
nexo/
|- main.py
|- config.py
|- requirements.txt
|- build_exe.bat
|- nexo.spec
|- nexo.db
|- backend/
|  |- __init__.py
|  |- students/
|  |  |- controller.py
|  |  |- service.py
|  |  |- repository.py
|  |  |- validators.py
|  |  |- queries.py
|  |  |- sorts.py
|  |- programs/
|  |  |- controller.py
|  |  |- service.py
|  |  |- repository.py
|  |  |- validators.py
|  |  |- queries.py
|  |  |- sorts.py
|  |- colleges/
|  |  |- controller.py
|  |  |- service.py
|  |  |- repository.py
|  |  |- validators.py
|  |  |- queries.py
|  |  |- sorts.py
|  |- controllers/      (compatibility wrappers)
|  |- services/         (compatibility wrappers + shared services)
|  |- repositories/     (compatibility wrappers)
|  |- auth.py
|  |- database.py
|  |- models.py
|  |- storage.py
|  |- validators.py
|  |- search/
|  |- sort/
|- frontend_ui/
|  |- students/
|  |  |- list_view.py
|  |- programs/
|  |  |- list_view.py
|  |- colleges/
|  |  |- list_view.py
|  |- auth/
|  |- dashboard/
|  |- views/            (compatibility wrappers)
|  |- ui/
|- assets/
```

### CRUDL Navigation Guide

Use the feature packages first when navigating code:

- Student CRUDL:
  - backend/students/controller.py
  - backend/students/service.py
  - backend/students/repository.py
- Program CRUDL:
  - backend/programs/controller.py
  - backend/programs/service.py
  - backend/programs/repository.py
- College CRUDL:
  - backend/colleges/controller.py
  - backend/colleges/service.py
  - backend/colleges/repository.py

Frontend list views are feature-oriented as well (canonical implementation paths):

- frontend_ui/students/list_view.py
- frontend_ui/programs/list_view.py
- frontend_ui/colleges/list_view.py

Legacy layer-first folders are still present as compatibility wrappers during migration.

---

## Build Executable

```bash
./build_exe.bat
```

Or use the spec directly:

```bash
pyinstaller nexo.spec
```

The packaged app uses SQLite persistence.
