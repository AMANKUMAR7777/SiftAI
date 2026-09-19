import shutil
import uuid
from pathlib import Path
from typing import List, Dict, Any
from backend import ledger


def get_safe_destination_path(target_dir: Path, original_filename: str) -> Path:
    """
    Ensure no files are overwritten.
    If a file with the same name already exists in target_dir,
    append (1), (2), etc.
    """
    original_path = Path(original_filename)
    stem = original_path.stem
    suffix = original_path.suffix

    destination = target_dir / original_filename
    counter = 1

    while destination.exists():
        new_name = f"{stem} ({counter}){suffix}"
        destination = target_dir / new_name
        counter += 1

    return destination


def execute_organization_plan(source_directory: str, plan_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Safely move selected files into their designated detailed folders.
    Guarantees:
    - Never deletes any file.
    - Never overwrites existing files.
    - Records all operations in SQLite ledger for instant one click undo.
    """
    source_root = Path(source_directory)
    batch_id = str(uuid.uuid4())[:8]

    # Initialize batch in ledger
    ledger.create_batch(batch_id, str(source_root), len(plan_items))

    moved_count = 0
    skipped_count = 0
    errors: List[str] = []

    for item in plan_items:
        if not item.get("selected", True):
            skipped_count += 1
            continue

        src_path = Path(item["path"])
        folder_category = item.get("suggested_folder", "").strip() or "Organized Items"

        if not src_path.exists() or not src_path.is_file():
            errors.append(f"File not found: {item.get('name', 'Unknown')}")
            continue

        try:
            # Construct target directory
            target_dir = source_root / folder_category
            target_dir.mkdir(parents=True, exist_ok=True)

            # Resolve safe target path to avoid overwriting
            dest_path = get_safe_destination_path(target_dir, src_path.name)

            # Perform safe move
            shutil.move(str(src_path), str(dest_path))

            # Record in audit ledger
            ledger.record_move(
                batch_id=batch_id,
                original_path=str(src_path.resolve()),
                new_path=str(dest_path.resolve()),
                folder_category=folder_category
            )
            moved_count += 1
        except Exception as e:
            errors.append(f"Failed to move {src_path.name}: {str(e)}")

    return {
        "batch_id": batch_id,
        "moved_count": moved_count,
        "skipped_count": skipped_count,
        "errors": errors,
        "success": moved_count > 0 or len(errors) == 0
    }


def undo_batch(batch_id: str) -> Dict[str, Any]:
    """
    Safely restore all files from a batch to their exact original locations.
    Never deletes files. If destination collision occurs, uses safe naming.
    """
    moves = ledger.get_batch_moves(batch_id)
    if not moves:
        return {"success": False, "message": "Batch not found or already reverted."}

    restored_count = 0
    errors: List[str] = []

    for move in moves:
        if move.get("reverted", 0) == 1:
            continue

        current_path = Path(move["new_path"])
        orig_path = Path(move["original_path"])

        if not current_path.exists():
            errors.append(f"Moved file not found at: {current_path.name}")
            continue

        try:
            # Ensure original directory exists
            orig_path.parent.mkdir(parents=True, exist_ok=True)

            # Check for collision at original path
            safe_orig_path = orig_path
            if safe_orig_path.exists() and safe_orig_path != current_path:
                safe_orig_path = get_safe_destination_path(orig_path.parent, orig_path.name)

            shutil.move(str(current_path), str(safe_orig_path))
            restored_count += 1
        except Exception as e:
            errors.append(f"Error restoring {current_path.name}: {str(e)}")

    # Mark batch as reverted
    ledger.mark_batch_status(batch_id, "reverted")

    return {
        "success": restored_count > 0 or len(errors) == 0,
        "restored_count": restored_count,
        "errors": errors
    }
