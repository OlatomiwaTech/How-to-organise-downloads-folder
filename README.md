# Folder Organiser

A simple Python script that helps you clean up a folder by sorting files into organised groups based on file type.

## What it does

This tool can:

- sort files into folders such as `PDFs`, `Documents`, `Images`, `Videos`, `Audio`, and more
- create date-based subfolders (for example `PDFs/2026-10`)
- create size-based subfolders (for example `Images/Large`)
- detect duplicate files and move them to a `_DUPLICATES` folder
- generate a JSON summary report and a text log
- preview changes in dry-run mode before actually moving files

## Requirements

- Python 3.x installed on your system

## How to use it

1. Download or copy `organize-downloads.py` into your project folder.
2. Open a terminal or command prompt.
3. Run:

```bash
python organize-downloads.py
```

4. Enter the full path of the folder you want to organise when prompted.
5. Choose the options you want, such as:
   - move files or scan only
   - create date-based folders
   - create size-based folders
   - detect duplicates
   - generate a report
   - use dry-run mode
6. Confirm the action to begin.

## Example

If your downloads folder contains:

- `report.pdf`
- `photo.jpg`
- `video.mp4`
- `notes.txt`

The script can organise them into folders like:

```text
Downloads/
├── PDFs/
│   └── report.pdf
├── Images/
│   └── photo.jpg
├── Videos/
│   └── video.mp4
├── Documents/
│   └── notes.txt
```

## Notes

- The script skips its own log files and system-related files.
- If a file already exists in the destination folder, a numbered copy is created automatically to avoid overwriting it.
- The generated log and JSON report can help you review what was organised.

## Customising file categories

The script includes a built-in `MAPPING` dictionary near the top of the file. You can edit it to change which file extensions are assigned to which folders.
