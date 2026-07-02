#!/usr/bin/env python3
"""Initialize SQLite database for Googooli Research Assistant state tracking."""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "research_state.db")


def main():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Suggestions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        source TEXT NOT NULL,
        description TEXT,
        prerequisites TEXT, -- JSON string array
        metric TEXT,
        created_date TEXT NOT NULL, -- YYYY-MM-DD
        status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'rejected'
        processed INTEGER DEFAULT 0, -- 0 = false, 1 = true
        user_notes TEXT
    )
    """)

    # 2. Background topics table (prerequisites)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS background_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'unknown', -- 'unknown', 'known', 'learning'
        updated_date TEXT NOT NULL
    )
    """)

    # 3. User selections logging
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_selections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        suggestion_id INTEGER,
        user_response TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (suggestion_id) REFERENCES suggestions (id)
    )
    """)

    # 4. Pending keyword changes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pending_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        changes_json TEXT NOT NULL, -- JSON representation of keywords/conferences changes
        created_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending' -- 'pending', 'accepted', 'rejected'
    )
    """)

    # Run migration to add user_notes column if not exists
    try:
        cursor.execute("ALTER TABLE suggestions ADD COLUMN user_notes TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    main()
