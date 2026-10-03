import os
import shutil
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import json
import threading

# ================= CONFIGURATION =================
MAPPING = {
    ".pdf": "PDFs", ".doc": "Documents", ".docx": "Documents", ".txt": "Documents",
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
    ".mp4": "Videos", ".avi": "Videos", ".mkv": "Videos",
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
    ".exe": "Installers", ".msi": "Installers",
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    ".py": "Scripts", ".js": "Scripts", ".ps1": "Scripts",
}

SKIP_PATTERNS = ["organize_gui.py", "organize-log-", "desktop.ini", "thumbs.db"]

SIZE_CATEGORIES = {
    "Tiny": 1024 * 1024,
    "Small": 10 * 1024 * 1024,
    "Medium": 50 * 1024 * 1024,
    "Large": 100 * 1024 * 1024,
    "Huge": float("inf"),
}

# ================= HELPER FUNCTIONS =================
def write_log(log_file: Path, message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    log_text.insert(tk.END, line + "\n")
    log_text.see(tk.END)

def get_unique_path(dest_path: Path) -> Path:
    if not dest_path.exists():
        return dest_path
    base = dest_path.stem
    ext = dest_path.suffix
    parent = dest_path.parent
    counter = 1
    while True:
        new_name = f"{base}({counter}){ext}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def get_file_hash(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_size_category(size_bytes: int) -> str:
    for category, threshold in SIZE_CATEGORIES.items():
        if size_bytes < threshold:
            return category
    return "Huge"

def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

# ================= ORGANIZATION LOGIC =================
def organize_folder_thread():
    folder_path = Path(folder_var.get())
    log_file = folder_path / f"organize-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    
    stats = {
        "total_files": 0, "moved_files": 0, "skipped_files": 0,
        "duplicate_files": 0, "error_files": 0, "total_size": 0,
    }
    
    duplicate_hashes = {} if duplicate_var.get() else None
    action_log = []  # For undo feature
    
    write_log(log_file, f"Starting organization of: {folder_path}", "INFO")
    
    for file_path in folder_path.iterdir():
        if not file_path.is_file():
            continue
        
        stats["total_files"] += 1
        file_size = file_path.stat().st_size
        stats["total_size"] += file_size
        
        if file_path.name in SKIP_PATTERNS or any(file_path.name.startswith(p) for p in SKIP_PATTERNS):
            stats["skipped_files"] += 1
            continue
        
        try:
            ext = file_path.suffix.lower()

            # Duplicate detection
            if duplicate_var.get():
                file_hash = get_file_hash(file_path)
                if file_hash in duplicate_hashes:
                    stats["duplicate_files"] += 1
                    duplicates_folder = folder_path / "_DUPLICATES"
                    if not duplicates_folder.exists():
                        duplicates_folder.mkdir()
                    dest_path = get_unique_path(duplicates_folder / file_path.name)
                    action_log.append(("duplicate", str(file_path), str(dest_path)))
                    shutil.move(str(file_path), str(dest_path))
                    write_log(log_file, f"Moved duplicate: {file_path.name}", "INFO")
                    continue
                duplicate_hashes[file_hash] = file_path

            if ext in MAPPING:
                folder_name = MAPPING[ext]

                if date_var.get():
                    date_folder = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m")
                    folder_name = f"{folder_name}/{date_folder}"

                if size_var.get():
                    size_cat = get_size_category(file_size)
                    folder_name = f"{folder_name}/{size_cat}"

                folder_path_dest = folder_path / folder_name
                if not folder_path_dest.exists():
                    folder_path_dest.mkdir(parents=True)

                dest_path = get_unique_path(folder_path_dest / file_path.name)
                action_log.append(("move", str(file_path), str(dest_path)))
                shutil.move(str(file_path), str(dest_path))
                stats["moved_files"] += 1
                write_log(log_file, f"Moved: {file_path.name} -> {folder_name}", "INFO")
            else:
                stats["skipped_files"] += 1
        
        except Exception as e:
            stats["error_files"] += 1
            write_log(log_file, f"ERROR: {file_path.name}: {str(e)}", "ERROR")
    
    # Save action log for undo
    if action_log:
        undo_file = folder_path / f"organize-undo-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(undo_file, "w", encoding="utf-8") as f:
            json.dump(action_log, f, indent=2)
        write_log(log_file, f"Undo log saved: {undo_file.name}", "INFO")
    
    # Save stats
    stats_file = folder_path / f"organize-stats-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    
    write_log(log_file, f"Complete! Moved: {stats['moved_files']}, Errors: {stats['error_files']}", "SUMMARY")
    
    # Update UI
    progress_var.set(100)
    status_label.config(text=f"✅ Complete! Files moved: {stats['moved_files']}")
    start_button.config(state=tk.NORMAL)
    
    messagebox.showinfo("Complete", f"Organization finished!\n\nFiles moved: {stats['moved_files']}\nDuplicates: {stats['duplicate_files']}\nErrors: {stats['error_files']}")

def start_organization():
    if not folder_var.get():
        messagebox.showwarning("Warning", "Please select a folder first!")
        return
    
    if not messagebox.askyesno("Confirm", "Start organizing files?"):
        return
    
    start_button.config(state=tk.DISABLED)
    status_label.config(text="⏳ Organizing...")
    progress_var.set(0)
    
    # Run in thread to keep GUI responsive
    thread = threading.Thread(target=organize_folder_thread, daemon=True)
    thread.start()

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def undo_last_organization():
    folder_path = Path(folder_var.get())
    if not folder_path.exists():
        messagebox.showerror("Error", "Folder not found!")
        return
    
    # Find latest undo file
    undo_files = list(folder_path.glob("organize-undo-*.json"))
    if not undo_files:
        messagebox.showinfo("Info", "No undo log found!")
        return
    
    latest_undo = max(undo_files, key=lambda p: p.stat().st_mtime)
    
    if not messagebox.askyesno("Confirm Undo", f"Undo last organization?\n\nFile: {latest_undo.name}"):
        return
    
    with open(latest_undo, "r", encoding="utf-8") as f:
        actions = json.load(f)
    
    undone = 0
    for action_type, src, dest in reversed(actions):
        try:
            if os.path.exists(dest):
                shutil.move(dest, src)
                undone += 1
        except:
            pass
    
    messagebox.showinfo("Undo Complete", f"Restored {undone} files!")

# ================= GUI SETUP =================
root = tk.Tk()
root.title("🗂️ Advanced Folder Organizer Pro")
root.geometry("700x600")
root.resizable(True, True)

# Title
title_label = tk.Label(root, text="🗂️ Advanced Folder Organizer Pro", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

# Folder selection
folder_frame = ttk.Frame(root)
folder_frame.pack(pady=10, fill=tk.X, padx=20)

folder_var = tk.StringVar()
folder_entry = ttk.Entry(folder_frame, textvariable=folder_var, width=50)
folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

browse_button = ttk.Button(folder_frame, text="Browse...", command=browse_folder)
browse_button.pack(side=tk.LEFT, padx=10)

# Options
options_frame = ttk.LabelFrame(root, text="Options", padding=10)
options_frame.pack(pady=10, fill=tk.X, padx=20)

date_var = tk.BooleanVar()
date_check = ttk.Checkbutton(options_frame, text="Create date-based subfolders (e.g., PDFs/2026-10)", variable=date_var)
date_check.pack(anchor=tk.W)

size_var = tk.BooleanVar()
size_check = ttk.Checkbutton(options_frame, text="Create size-based subfolders (e.g., Images/Large)", variable=size_var)
size_check.pack(anchor=tk.W)

duplicate_var = tk.BooleanVar()
duplicate_check = ttk.Checkbutton(options_frame, text="Detect and move duplicate files", variable=duplicate_var)
duplicate_check.pack(anchor=tk.W)

# Progress
progress_frame = ttk.Frame(root)
progress_frame.pack(pady=10, fill=tk.X, padx=20)

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
progress_bar.pack(fill=tk.X)

status_label = tk.Label(progress_frame, text="Ready")
status_label.pack(pady=5)

# Buttons
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

start_button = ttk.Button(button_frame, text="🚀 Start Organization", command=start_organization)
start_button.pack(side=tk.LEFT, padx=5)

undo_button = ttk.Button(button_frame, text="↩️ Undo Last", command=undo_last_organization)
undo_button.pack(side=tk.LEFT, padx=5)

# Log window
log_frame = ttk.LabelFrame(root, text="Activity Log", padding=10)
log_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)

log_text = tk.Text(log_frame, height=15, wrap=tk.WORD)
log_text.pack(fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(log_text, command=log_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_text.config(yscrollcommand=scrollbar.set)

# Footer
footer_label = tk.Label(root, text="Built with Python + Tkinter", font=("Arial", 8))
footer_label.pack(pady=5)

root.mainloop()