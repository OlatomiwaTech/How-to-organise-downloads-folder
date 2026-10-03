import os
import shutil
from datetime import datetime
from pathlib import Path

# ================= CONFIGURATION =================
DOWNLOADS_DIR = Path(r"C:\Users\Olatomiwa\Downloads")
LOG_FILE = DOWNLOADS_DIR / f"organize-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"

# Extension → Folder mapping (customize as needed)
MAPPING = {
    ".pdf": "PDFs",
    ".doc": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".rtf": "Documents",
    ".xls": "Spreadsheets",
    ".xlsx": "Spreadsheets",
    ".csv": "Spreadsheets",
    ".ppt": "Presentations",
    ".pptx": "Presentations",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".bmp": "Images",
    ".webp": "Images",
    ".mp4": "Videos",
    ".avi": "Videos",
    ".mov": "Videos",
    ".wmv": "Videos",
    ".mkv": "Videos",
    ".mp3": "Audio",
    ".wav": "Audio",
    ".flac": "Audio",
    ".aac": "Audio",
    ".exe": "Installers",
    ".msi": "Installers",
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    ".ps1": "Scripts",
    ".py": "Scripts",
    ".js": "Scripts",
    ".bat": "Scripts",
    ".sh": "Scripts",
    ".apk": "Android",
}

# Files to skip (script + logs)
SKIP_PATTERNS = ["organize_downloads.py", "organize-log-"]

# ================= HELPER FUNCTIONS =================
def write_log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_unique_path(dest_path: Path) -> Path:
    """If file exists, add (1), (2), etc. before extension."""
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

# ================= MAIN LOGIC =================
def organize_downloads():
    write_log(f"Starting organization of: {DOWNLOADS_DIR}")
    
    if not DOWNLOADS_DIR.exists():
        write_log(f"ERROR: Downloads folder not found: {DOWNLOADS_DIR}")
        return
    
    moved_count = 0
    error_count = 0
    
    for file_path in DOWNLOADS_DIR.iterdir():
        # Skip directories
        if not file_path.is_file():
            continue
        
        # Skip script and log files
        if file_path.name in SKIP_PATTERNS or any(file_path.name.startswith(p) for p in SKIP_PATTERNS):
            continue
        
        try:
            ext = file_path.suffix.lower()
            
            if ext in MAPPING:
                folder_name = MAPPING[ext]
                folder_path = DOWNLOADS_DIR / folder_name
                
                # Create folder if it doesn't exist
                if not folder_path.exists():
                    folder_path.mkdir(parents=True)
                    write_log(f"Created folder: {folder_name}")
                
                # Build destination path (handle duplicates)
                dest_path = get_unique_path(folder_path / file_path.name)
                
                # Move file
                shutil.move(str(file_path), str(dest_path))
                write_log(f"Moved: {file_path.name} -> {folder_name}")
                moved_count += 1
            else:
                write_log(f"Skipped (no mapping): {file_path.name}")
        
        except Exception as e:
            write_log(f"ERROR moving {file_path.name}: {str(e)}")
            error_count += 1
    
    write_log(f"Organization complete. Files moved: {moved_count}, Errors: {error_count}")
    write_log(f"Log saved to: {LOG_FILE}")

if __name__ == "__main__":
    organize_downloads()