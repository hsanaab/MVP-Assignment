#!/usr/bin/env python3
import os
import shutil
import sys
import time
from datetime import datetime, timedelta

TRASH_DIR = os.path.expanduser("~/.trashcan")
METADATA_FILE = os.path.join(TRASH_DIR, ".metadata")

def init_trash():
    os.makedirs(TRASH_DIR, exist_ok=True)
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w") as f:
            pass  # Create empty metadata file

def move_to_trash(filepath):
    if not os.path.exists(filepath):
        print(f"Error: '{filepath}' not found.")
        return
    init_trash()
    basename = os.path.basename(filepath)
    timestamp = datetime.now().isoformat()
    new_name = f"{basename}.{int(time.time())}"
    dest_path = os.path.join(TRASH_DIR, new_name)
    shutil.move(filepath, dest_path)
    with open(METADATA_FILE, "a") as f:
        f.write(f"{new_name}|{filepath}|{timestamp}\n")
    print(f"Moved '{filepath}' to trash.")

def list_trash():
    if not os.path.exists(METADATA_FILE):
        print("Trash is empty.")
        return
    with open(METADATA_FILE) as f:
        for line in f:
            name, original, timestamp = line.strip().split("|")
            print(f"{name} -> {original} (deleted {timestamp})")

def restore(filename):
    init_trash()
    found = False
    new_lines = []
    with open(METADATA_FILE) as f:
        for line in f:
            name, original, timestamp = line.strip().split("|")
            if name == filename:
                shutil.move(os.path.join(TRASH_DIR, name), original)
                print(f"Restored '{original}'")
                found = True
            else:
                new_lines.append(line)
    with open(METADATA_FILE, "w") as f:
        f.writelines(line + "\n" for line in new_lines)
    if not found:
        print("File not found in trash.")

def purge_trash(days=7):
    init_trash()
    threshold = datetime.now() - timedelta(days=days)
    new_lines = []
    with open(METADATA_FILE) as f:
        for line in f:
            name, original, timestamp = line.strip().split("|")
            deletion_time = datetime.fromisoformat(timestamp)
            path = os.path.join(TRASH_DIR, name)
            if deletion_time < threshold:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Purged '{name}' (deleted {timestamp})")
            else:
                new_lines.append(line)
    with open(METADATA_FILE, "w") as f:
        f.writelines(line + "\n" for line in new_lines)

def show_help():
    print("""TrashCan - Safer Deletes for Linux
Usage:
  trashcan.py delete <file>       Move file to trash
  trashcan.py list                Show trashed files
  trashcan.py restore <filename>  Restore from trash
  trashcan.py purge [days]        Purge files older than days (default: 7)
  trashcan.py help                Show this help
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
    else:
        cmd = sys.argv[1]
        if cmd == "delete" and len(sys.argv) == 3:
            move_to_trash(sys.argv[2])
        elif cmd == "list":
            list_trash()
        elif cmd == "restore" and len(sys.argv) == 3:
            restore(sys.argv[2])
        elif cmd == "purge":
            days = int(sys.argv[2]) if len(sys.argv) == 3 else 7
            purge_trash(days)
        else:
            show_help()
