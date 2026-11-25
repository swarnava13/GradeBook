"""
file_handler.py  -  Component 4: Files and error handling
Owner: Sinchana G (25BTRDC048)
Marks are stored in data/marks.csv, settings in data/settings.json.
Every file is opened with `with open()` and errors are handled with try/except.
"""
import csv
import json
import os
from datetime import datetime

DATA_DIR = "data" if os.path.isdir("data") else "."
MARKS_FILE = os.path.join(DATA_DIR, "marks.csv")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

DEFAULT_SETTINGS = {"class_name": "B.Tech CSE (Data Science) - Sem III",
                    "subjects": {"Maths": 4, "Python": 4, "Physics": 3,
                                 "English": 2, "Electronics": 3},
                    "pass_mark": 40}


def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        print("  settings.json not found - using default settings.")
        return DEFAULT_SETTINGS
    except json.JSONDecodeError:
        print("  settings.json is damaged - using default settings.")
        return DEFAULT_SETTINGS


def load_marks():
    """Return a list of (usn, name, subject, mark) tuples. Bad rows are skipped."""
    rows, skipped = [], 0
    try:
        with open(MARKS_FILE, newline="") as f:
            for row in csv.DictReader(f):
                try:
                    mark = int(row["mark"]) if row["mark"].strip() else None
                    if mark is not None and not 0 <= mark <= 100:
                        raise ValueError("mark out of range")
                    rows.append((row["usn"].strip(), row["name"].strip(),
                                 row["subject"].strip(), mark))
                except (ValueError, KeyError, AttributeError):
                    skipped += 1
    except FileNotFoundError:
        print("  marks.csv not found - starting with an empty class.")
    if skipped:
        print(f"  Warning: skipped {skipped} invalid row(s) in marks.csv.")
    return rows


def save_marks(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(MARKS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["usn", "name", "subject", "mark"])
            for usn, name, subject, mark in rows:
                writer.writerow([usn, name, subject, "" if mark is None else mark])
        stamp = datetime.now().strftime("%d-%m-%Y %H:%M")
        print(f"  Saved {len(rows)} records to {MARKS_FILE} at {stamp}.")
    except PermissionError:
        print("  Error: marks.csv is open in another program. Close it and try again.")
    finally:
        pass  
