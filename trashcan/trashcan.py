#!/usr/bin/env python3

import os
import sys
import shutil
import sqlite3
from datetime import datetime, timedelta

TRASH_DIR = os.path.expanduser("~/.trashcan")
DB_NAME = os.path.join(TRASH_DIR, "trashcan.db")
AUTO_PURGE_DAYS = 7  # Files older than this will be auto-deleted


def init():
    os.makedirs(TRASH_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trash (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT,
            trashed_path TEXT,
            deleted_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def log_action(original_path, trashed_path):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO trash (original_path, trashed_path, deleted_at) VALUES (?, ?, ?)',
              (original_path, trashed_path, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def delete_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return
    base_name = os.path.basename(file_path)
    trashed_name = f"{base_name}_{int(datetime.now().timestamp())}"
    trashed_path = os.path.join(TRASH_DIR, trashed_name)
    shutil.move(file_path, trashed_path)
    log_action(file_path, trashed_path)
    print(f"Moved '{file_path}' to TrashCan.")


def list_trash():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, original_path, trashed_path, deleted_at FROM trash')
    rows = c.fetchall()
    if not rows:
        print("TrashCan is empty.")
    else:
        print("TrashCan contents:")
        for row in rows:
            print(f"[ID: {row[0]}] {row[1]} (Deleted: {row[3]})")
    conn.close()


def restore_file(file_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, original_path, trashed_path FROM trash WHERE id = ?', (file_id,))
    row = c.fetchone()
    if not row:
        print("Error: File ID not found in TrashCan.")
        conn.close()
        return

    try:
        shutil.move(row[2], row[1])
        c.execute('DELETE FROM trash WHERE id = ?', (file_id,))
        conn.commit()
        print(f"Restored '{row[1]}' successfully.")
    except Exception as e:
        print(f"Error restoring file: {e}")
    conn.close()


def purge_trash():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT trashed_path FROM trash')
    rows = c.fetchall()
    for row in rows:
        try:
            os.remove(row[0])
        except FileNotFoundError:
            pass  # Already removed
    c.execute('DELETE FROM trash')
    conn.commit()
    conn.close()
    print("TrashCan purged.")


def auto_purge():
    cutoff = datetime.now() - timedelta(days=AUTO_PURGE_DAYS)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, trashed_path, deleted_at FROM trash')
    rows = c.fetchall()
    for row in rows:
        deleted_time = datetime.fromisoformat(row[2])
        if deleted_time < cutoff:
            try:
                os.remove(row[1])
            except FileNotFoundError:
                pass
            c.execute('DELETE FROM trash WHERE id = ?', (row[0],))
    conn.commit()
    conn.close()


def show_help():
    print("""
TrashCan - Enhanced Recycle Bin

Usage:
  trashcan.py delete <file>     Move a file to trash
  trashcan.py list              List trashed files
  trashcan.py restore <id>      Restore a file by ID
  trashcan.py purge             Empty the trash completely
  trashcan.py help              Show this help message
""")


if __name__ == "__main__":
    init()
    auto_purge()

    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "delete" and len(sys.argv) == 3:
        delete_file(sys.argv[2])
    elif command == "list":
        list_trash()
    elif command == "restore" and len(sys.argv) == 3:
        restore_file(sys.argv[2])
    elif command == "purge":
        purge_trash()
    else:
        show_help()
