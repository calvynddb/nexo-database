<p align="center">
  <img src="assets/banner.png" alt="nexo banner" width="600"/>
</p>

<h1 align="center">nexo</h1>

<p align="center">
  <b>A Simple Student Information System</b><br/>
  Built with Python &amp; CustomTkinter
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white" alt="Python 3.13"/>
  <img src="https://img.shields.io/badge/UI-CustomTkinter-purple" alt="CustomTkinter"/>
  <img src="https://img.shields.io/badge/data-CSV-green" alt="CSV Storage"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT License"/>
</p>

<p align="center">
  <img src="screenshots/dashboard.png" alt="nexo dashboard" width="800"/>
</p>

> **Default login** — username: `admin` &nbsp;·&nbsp; password: `admin`

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Default Credentials](#default-credentials)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [Building the Executable](#building-the-executable)

---

## Overview

nexo is a desktop student information system built with Python and CustomTkinter. It manages students, academic programs, and colleges through a dark-themed GUI backed entirely by CSV flat files — no database setup required. The app is structured around a strict backend/frontend split: the `backend/` package handles all data access, validation, and business logic with zero UI dependencies, while `frontend_ui/` is responsible solely for presentation.

The interface opens on a dashboard with three views — Students, Programs, and Colleges. Each view provides full **CRUDL** (Create, Read, Update, Delete, List) operations: records can be added individually or imported in bulk via CSV, edited in place through a detail popup, and deleted with a set-null cascade that keeps related records consistent. Tables support **search by fields** — a real-time filter that narrows results across all visible columns as you type — and **sort** on any column header, toggling ascending/descending order with numeric-aware comparison for year and ID fields. The Programs view also displays a donut chart (via matplotlib) showing enrollment distribution by college alongside a top-enrolled sidebar.

All write operations are gated behind admin authentication. Credentials are stored as SHA-256 hashes with per-user random salts — passwords are never written to disk in plaintext. Additional administrators can be registered through the gear icon in the dashboard header after logging in. Logging out returns to a read-only guest view without redirecting to the login screen. The app packages into a single portable `.exe` via PyInstaller, seeding its CSV data files on first run.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.13+ |
| UI Framework | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Charts | Matplotlib + NumPy |
| Image Loading | Pillow (PIL) |
| Data Storage | CSV (flat file) |
| Packaging | PyInstaller |

---

## Getting Started

### Prerequisites

- Python **3.13** or later (Python 3.14 has a known NumPy/PyInstaller incompatibility)
- `customtkinter`, `Pillow`, `matplotlib`, `numpy` — install via `pip install -r requirements.txt`
- `pyinstaller` — only required for building the executable

### Installation

```bash
# clone the repository
git clone https://github.com/calvynddb/Simple-Student-Information-System.git
cd Simple-Student-Information-System

# (recommended) create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate  # windows
# source .venv/bin/activate  # mac/linux

# install dependencies
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

The app opens at **1400 × 940** in dark mode. CSV data files are created automatically on first launch.

---

## Default Credentials

| Username | Password |
|---|---|
| `admin` | `admin` |

> The default admin account is created automatically on first launch with its password stored as a SHA-256 hash — not in plaintext. Additional administrators can be registered via the gear icon in the dashboard header (visible when logged in).

---

## Project Structure

```
nexo/
├── main.py                          # Entry point — App class, frame management, custom dialogs
├── config.py                        # Colors, fonts, file paths, ThemeManager, path helpers
├── requirements.txt                 # Python dependencies
├── build_exe.bat                    # PyInstaller build script
│
├── assets/
│   ├── Main Logo.png                # App logo
│   └── icons/                       # 58 PNG icons (18/22/28/36 px sizes)
│
├── backend/                         # Data layer (no UI dependencies)
│   ├── __init__.py                  # Public API — init_files, load_csv, save_csv, hash_password, verify_password
│   ├── storage.py                   # CSV file I/O (init, load, save, backup, seed copy)
│   ├── auth.py                      # Password hashing — SHA-256 with per-user random salt
│   ├── validators.py                # Field-level validation for all entities
│   ├── crud/
│   │   ├── students.py              # StudentCRUD — create / read / update / delete / list
│   │   ├── programs.py              # ProgramCRUD
│   │   └── colleges.py              # CollegeCRUD
│   ├── search/
│   │   ├── students.py              # StudentSearch — by_id, by_name, by_field, by_any_field
│   │   ├── programs.py              # ProgramSearch
│   │   └── colleges.py              # CollegeSearch
│   └── sort/
│       ├── students.py              # StudentSort — by_id, by_name, by_year, by_program, etc.
│       ├── programs.py              # ProgramSort
│       └── colleges.py              # CollegeSort
│
├── frontend_ui/                     # Presentation layer
│   ├── auth/
│   │   └── login.py                 # LoginFrame — sign in, guest access
│   ├── dashboard/
│   │   └── main.py                  # DashboardFrame — topbar, nav tabs, settings modal
│   ├── views/
│   │   ├── students.py              # StudentsView — table, profile, add/edit/import
│   │   ├── programs.py              # ProgramsView — table, donut chart, top enrolled sidebar
│   │   └── colleges.py              # CollegesView — table, add/edit/import
│   └── ui/
│       ├── cards.py                 # DepthCard, StatCard components
│       ├── inputs.py                # SearchableComboBox, StyledComboBox, SmartSearchEntry
│       └── utils.py                 # Icon/logo loader, Treeview styling, animations
│
├── students.csv                     # Student records
├── programs.csv                     # 59 pre-seeded programs
├── colleges.csv                     # 7 pre-seeded colleges
└── users.csv                        # Admin credentials (username, salt, SHA-256 hash)
```

---

## Architecture

The project follows a **layered architecture** with clear separation between data and presentation:

```
┌──────────────────────────────────────────────┐
│                  main.py                     │
│          App shell, frame switching          │
├──────────────┬───────────────────────────────┤
│  frontend_ui │          config.py            │
│  ┌─────────┐ │   Colors, fonts, paths,       │
│  │  auth/  │ │   ThemeManager                │
│  │dashboard│ │                               │
│  │ views/  │ │                               │
│  │  ui/    │ │                               │
│  └────┬────┘ │                               │
│       │      │                               │
├───────┴──────┴───────────────────────────────┤
│                 backend/                     │
│   storage ← crud / search / sort            │
│   validators                                │
├──────────────────────────────────────────────┤
│              CSV flat files                  │
│   students.csv  programs.csv  colleges.csv   │
└──────────────────────────────────────────────┘
```

**Key design decisions:**

1. 𝗕𝗮𝗰𝗸𝗲𝗻𝗱 / 𝗙𝗿𝗼𝗻𝗴𝗲𝗻𝗱 𝘀𝗽𝗹𝗶𝗴 — The `backend/` package has zero UI imports; it only deals with CSV data, validation, and business logic.
2. 𝗖𝗥𝗨𝗗, 𝗦𝗲𝗮𝗿𝗰𝗵, 𝗦𝗼𝗿𝗴 𝗰𝗹𝗮𝘀𝘀𝗲𝘀 — Each entity (Student, Program, College) has its own dedicated class for each operation type.
3. 𝗖𝗲𝗻𝗴𝗿𝗮𝗹𝗶𝘇𝗲𝗱 𝗰𝗼𝗻𝗳𝗶𝗴 — All colors, fonts, file paths, and theme state live in `config.py`.
4. 𝗖𝘂𝘀𝗴𝗼𝗺 𝗱𝗶𝗮𝗹𝗼𝗴 𝘀𝘆𝘀𝗴𝗲𝗺 — A single `show_custom_dialog()` replaces all native message boxes with themed modal windows.
5. 𝗣𝗮𝗴𝗵 𝗵𝗲𝗹𝗽𝗲𝗿𝘀 — `resource_path()` and `data_path()` enable seamless PyInstaller bundling.
6. 𝗔𝗱𝗺𝗶𝗻 𝗺𝗮𝗻𝗮𝗴𝗲𝗺𝗲𝗻𝗴 — Administrators are registered and credentials changed via a gear-icon panel in the dashboard header, visible only when logged in.
7. 𝗦𝗲𝗰𝘂𝗿𝗲 𝗰𝗿𝗲𝗱𝗲𝗻𝘁𝗶𝗮𝗹𝘀 — Passwords are hashed with SHA-256 and a per-user random salt using Python's stdlib `hashlib` + `secrets`. Plain-text passwords are never written to disk.

---

## Data Model

### Students

| Field | Description |
|---|---|
| `id` | Unique student ID (e.g. `2023-0001`) — no letters allowed |
| `firstname` | First name — alphabetic only |
| `lastname` | Last name — alphabetic only |
| `gender` | Male / Female / Other |
| `year` | Year level (numeric) |
| `program` | Program code (foreign key to Programs) |

### Programs

| Field | Description |
|---|---|
| `code` | Unique program code (e.g. `BSCS`) |
| `name` | Full program name — no digits allowed |
| `college` | College code (foreign key to Colleges) |

### Colleges

| Field | Description |
|---|---|
| `code` | Unique college code (e.g. `CCS`) |
| `name` | Full college name — no digits allowed |

**Relationships:** Student → Program → College — deleting a program clears the `program` field on enrolled students; deleting a college clears the `college` field on affected programs (set-null cascade).

---

## Building the Executable

### Prerequisites

Before building, make sure the following are in place:

- **Python 3.13** — Python 3.14 has a known NumPy DLL incompatibility with PyInstaller; stick to 3.13.
- **PyInstaller** — install into your virtual environment:
  ```bash
  pip install pyinstaller
  ```
- **All runtime dependencies installed** — run `pip install -r requirements.txt` first if you haven't already.
- **Assets present** — the `assets/` folder (logo + icons) must exist before building. The batch script assumes it is at the project root.
- **PyQt5 must not be installed** — it conflicts with matplotlib's TkAgg backend. If it is present, uninstall it:
  ```bash
  pip uninstall PyQt5
  ```

### Build

The simplest way is to use the included batch script:

```bash
.\build_exe.bat
```

Or run PyInstaller manually:

```bash
python -m PyInstaller --noconfirm --onefile --windowed ^
    --icon "assets/nexo.ico" ^
    --add-data "assets;assets" ^
    --add-data "config.py;." ^
    --add-data "students.csv;." --add-data "programs.csv;." ^
    --add-data "colleges.csv;." --add-data "users.csv;." ^
    --add-data "backend;backend" --add-data "frontend_ui;frontend_ui" ^
    --hidden-import PIL --hidden-import matplotlib ^
    --hidden-import numpy --hidden-import customtkinter ^
    --collect-all customtkinter --exclude-module PyQt5 ^
    --name nexo main.py
```

The output at `dist/nexo.exe` (~38 MB) is fully self-contained. On first run it writes its CSV data files next to itself.

---

<p align="center">
  Made with ❤️ using Python and CustomTkinter
</p>
