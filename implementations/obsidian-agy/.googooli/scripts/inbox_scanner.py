#!/usr/bin/env python3
import os
import json
import sys

def scan_inbox(inbox_dir):
    """
    Scans the inbox directory and groups files into logical processing units.
    - Subdirectories are grouped together as single task units.
    - Root-level files are treated as individual task units.
    - Excludes hidden files and system directories like '.bin'.
    """
    if not os.path.exists(inbox_dir):
        print(json.dumps({"error": f"Inbox directory not found: {inbox_dir}"}))
        return

    task_units = []
    
    # Scan root files and subdirectories
    for entry in os.scandir(inbox_dir):
        if entry.name.startswith('.') or entry.name == 'TODO.md':
            continue
            
        if entry.is_dir():
            if entry.name == '.bin':
                continue
            # Group all files inside the subdirectory together
            sub_files = []
            for root, _, files in os.walk(entry.path):
                for f in files:
                    if not f.startswith('.'):
                        sub_files.append(os.path.relpath(os.path.join(root, f), start=inbox_dir))
            if sub_files:
                task_units.append({
                    "type": "directory",
                    "name": entry.name,
                    "path": os.path.relpath(entry.path, start=inbox_dir),
                    "files": sorted(sub_files)
                })
        elif entry.is_file():
            # Individual root file task unit
            task_units.append({
                "type": "file",
                "name": entry.name,
                "path": os.path.relpath(entry.path, start=inbox_dir),
                "files": [os.path.relpath(entry.path, start=inbox_dir)]
            })

    print(json.dumps({"task_units": task_units}, indent=2))

if __name__ == "__main__":
    # Vault base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    inbox_path = os.path.join(base_dir, "00-Inbox")
    scan_inbox(inbox_path)
