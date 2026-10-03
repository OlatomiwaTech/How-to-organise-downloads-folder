import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import json

# ================= CONFIGURATION =================

# Extension → Folder mapping (customize as needed)
MAPPING = {
    ".pdf": "PDFs",
    ".doc": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".rtf": "Documents",
    ".odt": "Documents",
    ".xls": "Spreadsheets",
    ".xlsx": "Spreadsheets",
    ".csv": "Spreadsheets",
    ".ods": "Spreadsheets",
    ".ppt": "Presentations",
    ".pptx": "Presentations",
    ".odp": "Presentations",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".bmp": "Images",
    ".webp": "Images",
    ".svg": "Images",
    ".ico": "Images",
    ".tiff": "Images",
    ".tif": "Images",
    ".raw": "Images",
    ".cr2": "Images",
    ".nef": "Images",
    ".mp4": "Videos",
    ".avi": "Videos",
    ".mov": "Videos",
    ".wmv": "Videos",
    ".mkv": "Videos",
    ".flv": "Videos",
    ".webm": "Videos",
    ".m4v": "Videos",
    ".mp3": "Audio",
    ".wav": "Audio",
    ".flac": "Audio",
    ".aac": "Audio",
    ".ogg": "Audio",
    ".wma": "Audio",
    ".m4a": "Audio",
    ".exe": "Installers",
    ".msi": "Installers",
    ".dmg": "Installers",
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    ".bz2": "Archives",
    ".xz": "Archives",
    ".ps1": "Scripts",
    ".py": "Scripts",
    ".js": "Scripts",
    ".ts": "Scripts",
    ".bat": "Scripts",
    ".sh": "Scripts",
    ".cmd": "Scripts",
    ".apk": "Android",
    ".ipa": "iOS",
    ".lnk": "Shortcuts",
    ".url": "Shortcuts",
}

# Files to skip (this script + logs + system files)
SKIP_PATTERNS = [
    "organize_folder_pro.py",
    "organize-log-",
    "desktop.ini",
    "thumbs.db",
    ".gitignore",
]

# Size categories (in bytes)
SIZE_CATEGORIES = {
    "Tiny": 1024 * 1024,  # < 1 MB
    "Small": 10 * 1024 * 1024,  # < 10 MB
    "Medium": 50 * 1024 * 1024,  # < 50 MB
    "Large": 100 * 1024 * 1024,  # < 100 MB
    "Huge": float("inf"),  # > 100 MB
}

# ================= HELPER FUNCTIONS =================
def write_log(log_file: Path, message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
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

def get_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file for duplicate detection."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_size_category(size_bytes: int) -> str:
    """Categorize file by size."""
    for category, threshold in SIZE_CATEGORIES.items():
        if size_bytes < threshold:
            return category
    return "Huge"

def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

# ================= MAIN LOGIC =================
def organize_folder(
    folder_path: Path,
    log_file: Path,
    move_files: bool = True,
    create_subfolders_by_date: bool = False,
    create_subfolders_by_size: bool = False,
    detect_duplicates: bool = False,
    generate_report: bool = True,
    dry_run: bool = False
):
    write_log(log_file, f"Starting organization of: {folder_path}", "INFO")
    write_log(log_file, f"Mode: {'DRY RUN' if dry_run else 'LIVE'}", "INFO")
    
    if not folder_path.exists():
        write_log(log_file, f"ERROR: Folder not found: {folder_path}", "ERROR")
        return None
    
    if not folder_path.is_dir():
        write_log(log_file, f"ERROR: Path is not a folder: {folder_path}", "ERROR")
        return None
    
    # Statistics tracking
    stats = {
        "total_files": 0,
        "moved_files": 0,
        "skipped_files": 0,
        "duplicate_files": 0,
        "error_files": 0,
        "total_size": 0,
        "by_extension": defaultdict(int),
        "by_size_category": defaultdict(int),
    }
    
    # Duplicate tracking (hash → file path)
    duplicate_hashes = {} if detect_duplicates else None
    
    for file_path in folder_path.iterdir():
        # Skip directories
        if not file_path.is_file():
            continue
        
        stats["total_files"] += 1
        file_size = file_path.stat().st_size
        stats["total_size"] += file_size
        
        # Track by extension
        ext = file_path.suffix.lower()
        stats["by_extension"][ext if ext else "(no extension)"] += 1
        
        # Track by size category
        size_cat = get_size_category(file_size)
        stats["by_size_category"][size_cat] += 1
        
        # Skip script and log files
        if file_path.name in SKIP_PATTERNS or any(file_path.name.startswith(p) for p in SKIP_PATTERNS):
            write_log(log_file, f"Skipped (system/script): {file_path.name}", "SKIP")
            stats["skipped_files"] += 1
            continue
        
        try:
            # Duplicate detection by hash
            if detect_duplicates:
                file_hash = get_file_hash(file_path)
                if file_hash in duplicate_hashes:
                    write_log(log_file, f"DUPLICATE detected: {file_path.name} (same as {duplicate_hashes[file_hash].name})", "WARN")
                    stats["duplicate_files"] += 1
                    
                    # Move duplicates to a special folder
                    duplicates_folder = folder_path / "_DUPLICATES"
                    if not dry_run:
                        if not duplicates_folder.exists():
                            duplicates_folder.mkdir(parents=True)
                        dest_path = get_unique_path(duplicates_folder / file_path.name)
                        shutil.move(str(file_path), str(dest_path))
                        write_log(log_file, f"Moved duplicate to: _DUPLICATES/{dest_path.name}", "INFO")
                    else:
                        write_log(log_file, f"Would move duplicate to: _DUPLICATES/{file_path.name}", "INFO")
                    continue
                else:
                    duplicate_hashes[file_hash] = file_path
            
            # Get target folder based on extension
            if ext in MAPPING:
                folder_name = MAPPING[ext]
                
                # Optional: Add date-based subfolder (e.g., PDFs/2026-10)
                if create_subfolders_by_date:
                    date_folder = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m")
                    folder_name = f"{folder_name}/{date_folder}"
                
                # Optional: Add size-based subfolder (e.g., Images/Large)
                if create_subfolders_by_size:
                    size_cat = get_size_category(file_size)
                    folder_name = f"{folder_name}/{size_cat}"
                
                folder_path_dest = folder_path / folder_name
                
                # Create folder if it doesn't exist
                if not dry_run and not folder_path_dest.exists():
                    folder_path_dest.mkdir(parents=True)
                    write_log(log_file, f"Created folder: {folder_name}", "INFO")
                elif dry_run and not folder_path_dest.exists():
                    write_log(log_file, f"Would create folder: {folder_name}", "INFO")
                
                # Build destination path (handle duplicates by name)
                dest_path = get_unique_path(folder_path_dest / file_path.name) if move_files else folder_path_dest / file_path.name
                
                # Move file
                if move_files and not dry_run:
                    shutil.move(str(file_path), str(dest_path))
                    write_log(log_file, f"Moved: {file_path.name} -> {folder_name} ({format_size(file_size)})", "INFO")
                    stats["moved_files"] += 1
                elif move_files and dry_run:
                    write_log(log_file, f"Would move: {file_path.name} -> {folder_name} ({format_size(file_size)})", "INFO")
                    stats["moved_files"] += 1
                else:
                    write_log(log_file, f"Scanned: {file_path.name} ({format_size(file_size)})", "INFO")
            else:
                write_log(log_file, f"Skipped (no mapping): {file_path.name} [{ext or 'no extension'}]", "SKIP")
                stats["skipped_files"] += 1
        
        except Exception as e:
            write_log(log_file, f"ERROR moving {file_path.name}: {str(e)}", "ERROR")
            stats["error_files"] += 1
    
    # Generate summary report
    if generate_report:
        write_log(log_file, "=" * 60, "SUMMARY")
        write_log(log_file, f"Total files scanned: {stats['total_files']}", "SUMMARY")
        write_log(log_file, f"Files moved: {stats['moved_files']}", "SUMMARY")
        write_log(log_file, f"Files skipped: {stats['skipped_files']}", "SUMMARY")
        write_log(log_file, f"Duplicates found: {stats['duplicate_files']}", "SUMMARY")
        write_log(log_file, f"Errors: {stats['error_files']}", "SUMMARY")
        write_log(log_file, f"Total size: {format_size(stats['total_size'])}", "SUMMARY")
        
        write_log(log_file, "-" * 60, "SUMMARY")
        write_log(log_file, "By Extension:", "SUMMARY")
        for ext, count in sorted(stats["by_extension"].items(), key=lambda x: x[1], reverse=True):
            write_log(log_file, f"  {ext}: {count}", "SUMMARY")
        
        write_log(log_file, "-" * 60, "SUMMARY")
        write_log(log_file, "By Size Category:", "SUMMARY")
        for cat, count in sorted(stats["by_size_category"].items()):
            write_log(log_file, f"  {cat}: {count}", "SUMMARY")
        
        write_log(log_file, "=" * 60, "SUMMARY")
        
        # Save JSON report
        if not dry_run:
            report_path = folder_path / f"organize-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, default=str)
            write_log(log_file, f"JSON report saved to: {report_path.name}", "SUMMARY")
    
    write_log(log_file, f"Log saved to: {log_file}", "INFO")
    return stats

# ================= INTERACTIVE MENU =================
def show_menu():
    print("\n" + "=" * 60)
    print("🗂️  ADVANCED FOLDER ORGANIZER")
    print("=" * 60)
    print("\nFeatures:")
    print("  1. Organize files by extension")
    print("  2. Create date-based subfolders (e.g., PDFs/2026-10)")
    print("  3. Create size-based subfolders (e.g., Images/Large)")
    print("  4. Detect and move duplicate files")
    print("  5. Generate detailed JSON report")
    print("  6. Dry-run mode (preview without moving)")
    print("=" * 60)

# ================= ENTRY POINT =================
if __name__ == "__main__":
    show_menu()
    
    # Ask user for folder path
    folder_input = input("\n📁 Enter the full path of the folder to organize:\n> ").strip()
    
    # Remove quotes if user pasted with quotes
    folder_input = folder_input.strip('"').strip("'")
    
    folder_path = Path(folder_input)
    
    # Validate path
    if not folder_path.exists():
        print(f"\n❌ ERROR: Folder not found: {folder_path}")
        print("Please check the path and try again.")
        input("\nPress Enter to exit...")
        exit(1)
    
    if not folder_path.is_dir():
        print(f"\n❌ ERROR: Path is not a folder: {folder_path}")
        print("Please provide a valid folder path.")
        input("\nPress Enter to exit...")
        exit(1)
    
    # Configure options
    print(f"\n📁 Folder to organize: {folder_path}")
    print("\n⚙️  Configure options:")
    
    move_files = input("  Move files? (yes/no): ").strip().lower() in ["yes", "y"]
    create_by_date = input("  Create date-based subfolders? (yes/no): ").strip().lower() in ["yes", "y"]
    create_by_size = input("  Create size-based subfolders? (yes/no): ").strip().lower() in ["yes", "y"]
    detect_duplicates = input("  Detect duplicates? (yes/no): ").strip().lower() in ["yes", "y"]
    generate_report = input("  Generate JSON report? (yes/no): ").strip().lower() in ["yes", "y"]
    dry_run = input("  Dry-run mode (preview only)? (yes/no): ").strip().lower() in ["yes", "y"]
    
    if dry_run:
        print("\n⚠️  DRY-RUN MODE: No files will be moved.")
    
    # Confirm before proceeding
    confirm = input("\n✅ Proceed with organization? (yes/no): ").strip().lower()
    
    if confirm not in ["yes", "y"]:
        print("\n❌ Operation cancelled.")
        input("\nPress Enter to exit...")
        exit(0)
    
    # Create log file
    log_file = folder_path / f"organize-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    
    # Run organization
    print("\n" + "=" * 60)
    stats = organize_folder(
        folder_path=folder_path,
        log_file=log_file,
        move_files=move_files,
        create_subfolders_by_date=create_by_date,
        create_subfolders_by_size=create_by_size,
        detect_duplicates=detect_duplicates,
        generate_report=generate_report,
        dry_run=dry_run
    )
    print("=" * 60)
    
    if stats:
        print(f"\n✅ Organization complete!")
        print(f"   Files moved: {stats['moved_files']}")
        print(f"   Files skipped: {stats['skipped_files']}")
        print(f"   Duplicates found: {stats['duplicate_files']}")
        print(f"   Errors: {stats['error_files']}")
        print(f"   Total size: {format_size(stats['total_size'])}")
    
    input("\nPress Enter to exit...")