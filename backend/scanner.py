import os
import time
import zipfile
from pathlib import Path
from typing import List, Dict, Any
from backend.config import MAX_SAMPLE_CHARS, MAX_PREVIEW_FILES

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

TEXT_EXTENSIONS = {
    ".txt", ".md", ".json", ".csv", ".tsv", ".py", ".js", ".jsx",
    ".ts", ".tsx", ".html", ".css", ".xml", ".yaml", ".yml", ".sql",
    ".log", ".sh", ".bat", ".ini", ".cfg", ".conf", ".env", ".rtf"
}

ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".7z", ".rar"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".bmp", ".ico", ".tiff"}
MEDIA_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".mp3", ".wav", ".aac", ".flac", ".ogg"}
INSTALLER_EXTENSIONS = {".exe", ".msi", ".pkg", ".dmg", ".iso", ".apk"}


def format_file_size(size_in_bytes: int) -> str:
    """Format bytes into a clean human readable string without hyphens."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"


def extract_content_sample(file_path: Path) -> str:
    """Extract a brief text preview to give LLM high context for categorization."""
    ext = file_path.suffix.lower()
    sample = ""

    try:
        if ext == ".pdf" and HAS_PYMUPDF:
            with fitz.open(file_path) as doc:
                if len(doc) > 0:
                    text = doc[0].get_text("text")
                    clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
                    sample = " ".join(clean_lines)[:MAX_SAMPLE_CHARS]
        elif ext in TEXT_EXTENSIONS:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(MAX_SAMPLE_CHARS * 2)
                clean_lines = [line.strip() for line in content.splitlines() if line.strip()]
                sample = " ".join(clean_lines)[:MAX_SAMPLE_CHARS]
        elif ext == ".zip":
            try:
                with zipfile.ZipFile(file_path, "r") as zf:
                    namelist = zf.namelist()[:4]
                    sample = "Contains: " + ", ".join(namelist)
            except Exception:
                sample = "Compressed archive"
        elif ext in INSTALLER_EXTENSIONS:
            sample = "Application or system setup installer"
        elif ext in IMAGE_EXTENSIONS:
            sample = "Graphic or visual image file"
        elif ext in MEDIA_EXTENSIONS:
            sample = "Audio or video multimedia file"
    except Exception:
        sample = ""

    return sample.strip()


def scan_directory(directory_path: str, include_subfolders: bool = False) -> Dict[str, Any]:
    """
    Scan the target directory for unorganized files.
    Never modifies or deletes anything. Returns metadata for preview.
    """
    folder = Path(directory_path)
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Directory does not exist: {directory_path}")

    files: List[Dict[str, Any]] = []
    total_bytes = 0

    SKIP_DIRS = {".git", ".svn", "node_modules", "venv", ".venv", "__pycache__", "$recycle.bin"}

    if include_subfolders:
        entry_list = []
        for root, dirs, filenames in os.walk(folder):
            # Modify dirs in-place to skip build/system folders
            dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in SKIP_DIRS]
            for fn in filenames:
                if len(entry_list) >= MAX_PREVIEW_FILES:
                    break
                entry_list.append(Path(root) / fn)
            if len(entry_list) >= MAX_PREVIEW_FILES:
                break
    else:
        try:
            entry_list = [p for p in folder.iterdir() if p.is_file()]
        except PermissionError:
            raise PermissionError(f"Permission denied accessing: {directory_path}")

    for entry in entry_list:
        if len(files) >= MAX_PREVIEW_FILES:
            break

        # Skip hidden and system files
        if entry.name.startswith(".") or entry.name.lower() in {"desktop.ini", "thumbs.db", "ntuser.dat"}:
            continue

        try:
            stat = entry.stat()
            file_size = stat.st_size
            mod_time = time.strftime("%Y/%m/%d %H:%M", time.localtime(stat.st_mtime))
            total_bytes += file_size

            ext = entry.suffix.lower()
            clean_ext = ext[1:] if ext.startswith(".") else ext

            files.append({
                "id": str(len(files) + 1),
                "name": entry.name,
                "path": str(entry.resolve()),
                "extension": clean_ext if clean_ext else "file",
                "size": file_size,
                "size_formatted": format_file_size(file_size),
                "modified": mod_time,
                "sample": extract_content_sample(entry),
                "selected": True,
                "suggested_folder": "",
                "reason": ""
            })
        except (PermissionError, FileNotFoundError):
            continue

    return {
        "directory": str(folder.resolve()),
        "total_files": len(files),
        "total_size": total_bytes,
        "total_size_formatted": format_file_size(total_bytes),
        "files": files
    }
