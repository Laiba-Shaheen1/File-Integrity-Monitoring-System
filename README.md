# 🛡️ File Integrity Monitoring System (FIM)

A complete cybersecurity tool for monitoring file and folder integrity
using SHA-256 hashing and real-time change detection.

---

## Features

| Feature | Description |
|---------|-------------|
| SHA-256 Baseline | Hash all monitored files and store as a security baseline |
| Real-time Monitoring | Watchdog-powered instant detection of changes |
| Change Detection | Detects modified, deleted, and newly created files |
| Alerts Dashboard | Live alerts with severity levels (HIGH / MEDIUM / LOW) |
| Full Audit Logs | Every event logged with timestamp, path, type, and status |
| Security Reports | Export to CSV: full report, alerts, logs, or baseline |
| SQLite Storage | All data persisted in a local `fim_data.db` database |
| Modern GUI | CustomTkinter dark UI with 6 pages |

---

## Installation

### Requirements
- Python 3.8 or higher
- Windows / macOS / Linux

### Steps

```bash
# 1. Navigate to the project folder
cd fim_system

# 2. Run setup (installs dependencies)
python setup.py

# 3. Launch the app
python main.py
```

### Manual install (if setup.py fails)
```bash
pip install customtkinter watchdog Pillow
```

---

## Usage Guide

### 1. Add files or folders to monitor
- Go to **Monitoring** page
- Click **+ Add File** or **+ Add Folder**
- Select the files/directories you want to watch

### 2. Create a baseline
- Click **🔒 Create Baseline**
- The system hashes every monitored file with SHA-256
- This baseline is the "known good" state

### 3. Start real-time monitoring
- Click **▶ Start Monitoring**
- The system watches for changes in real time using the `watchdog` library
- Any modification, deletion, or new file triggers an alert

### 4. Run a full scan (optional)
- Click **🔎 Run Full Scan** to manually check all files against the baseline
- Useful for periodic checks even without real-time monitoring

### 5. View alerts
- Go to **Alerts** page
- Filter by MODIFIED / DELETED / CREATED / UNREAD
- Double-click a row to acknowledge it

### 6. View logs
- Go to **Logs** page
- Full audit trail with search/filter

### 7. Generate reports
- Go to **Reports** page
- Generate Full Report, Alerts, Logs, or Baseline Snapshot as CSV files

---

## Project Structure

```
fim_system/
├── main.py                   ← Entry point
├── setup.py                  ← Install script
├── requirements.txt
├── fim_data.db               ← Created on first run
├── config.json               ← Created on first run
├── reports/                  ← Generated CSV reports
│
├── core/
│   ├── __init__.py
│   ├── database.py           ← SQLite + config operations
│   ├── hash_engine.py        ← SHA-256 hashing, baseline, scan
│   ├── file_watcher.py       ← Watchdog real-time monitor
│   └── report_generator.py  ← CSV export
│
└── gui/
    ├── __init__.py
    ├── app.py                ← Main window + controller
    ├── theme.py              ← Colors, fonts, constants
    ├── widgets.py            ← Reusable components
    └── pages/
        ├── __init__.py
        ├── dashboard.py
        ├── monitoring.py
        ├── alerts.py
        ├── logs.py
        ├── reports.py
        └── settings.py
```

---

## Database Schema

### `baseline` table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| file_path | TEXT UNIQUE | Absolute file path |
| sha256_hash | TEXT | 64-char hex hash |
| file_size | INTEGER | Bytes |
| last_modified | REAL | Unix timestamp |
| baseline_created | TEXT | Datetime string |

### `alerts` table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| timestamp | TEXT | Alert datetime |
| file_path | TEXT | Affected file |
| event_type | TEXT | MODIFIED/DELETED/CREATED |
| old_hash | TEXT | Hash before change |
| new_hash | TEXT | Hash after change |
| severity | TEXT | HIGH/MEDIUM/LOW |
| acknowledged | INTEGER | 0=unread, 1=read |

### `logs` table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| timestamp | TEXT | |
| file_path | TEXT | |
| event_type | TEXT | |
| status | TEXT | OK/ALERT/ERROR/WARNING |
| details | TEXT | Human-readable note |

### `watch_paths` table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| path | TEXT UNIQUE | |
| path_type | TEXT | file/dir |
| added_on | TEXT | |
| active | INTEGER | 1=active |

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Python 3.8+ | Language |
| CustomTkinter | Modern GUI framework |
| watchdog | Real-time filesystem events |
| hashlib (stdlib) | SHA-256 hashing |
| sqlite3 (stdlib) | Local database |
| csv (stdlib) | Report export |
| threading (stdlib) | Background monitoring |

---

## Notes for Evaluation

- All hashing uses Python's built-in `hashlib` — no external crypto deps
- Files are hashed in 64 KB chunks so large files don't block the GUI
- Real-time events are debounced (1.5s) to prevent duplicate alerts
- All database writes are committed immediately (no data loss on crash)
- The GUI uses `after()` for all cross-thread updates (thread-safe)
