import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import scanner, llm_organizer, mover, ledger
from backend.config import BASE_DIR

TEST_DIR = BASE_DIR / "test_sandbox"


def setup_test_files():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    # Create dummy files
    (TEST_DIR / "Stripe_Invoice_November_2024.csv").write_text("Invoice Date,Amount,Client\n2024-11-01,$450.00,Acme Corp")
    (TEST_DIR / "data_processor_helper.py").write_text("import pandas as pd\ndef clean_data():\n    pass")
    (TEST_DIR / "transformer_attention_mechanisms.txt").write_text("Abstract: We introduce self attention mechanisms for sequence modeling in natural language processing.")
    (TEST_DIR / "docker_desktop_installer_v4.exe").write_bytes(b"\x00" * 1024)
    (TEST_DIR / "company_logo_vector_assets.svg").write_text("<svg><circle r='10'/></svg>")


def run_all_tests():
    print("\n--- TEST 1: Database Initialization ---")
    ledger.init_db()
    print("Database initialized successfully.")

    print("\n--- TEST 2: Scanner Metadata Extraction ---")
    setup_test_files()
    scan_result = scanner.scan_directory(str(TEST_DIR))
    print(f"Scanned {scan_result['total_files']} files. Size: {scan_result['total_size_formatted']}")
    assert scan_result["total_files"] == 5, f"Expected 5 files, got {scan_result['total_files']}"
    for f in scan_result["files"]:
        print(f" - {f['name']} [{f['extension']}]: {f['sample']}")

    print("\n--- TEST 3: Ollama 3B Detailed Categorization ---")
    status = llm_organizer.check_ollama_status()
    print(f"Ollama Status: {status}")
    categories = llm_organizer.query_ollama_batch(status.get("default_model", "qwen2.5:3b"), scan_result["files"])
    print("Generated Categories:")
    for c in categories:
        print(f" - {c['filename']} -> Folder: '{c['folder']}' (Reason: {c['reason']})")
        assert "-" not in c["folder"], f"Found hyphen in folder: {c['folder']}"

    print("\n--- TEST 4: Safe Move Execution ---")
    plan_items = []
    cat_map = {c["filename"]: c for c in categories}
    for f in scan_result["files"]:
        cat = cat_map.get(f["name"], {"folder": "Miscellaneous Records", "reason": "General"})
        plan_items.append({
            "name": f["name"],
            "path": f["path"],
            "suggested_folder": cat["folder"],
            "selected": True
        })

    move_result = mover.execute_organization_plan(str(TEST_DIR), plan_items)
    print(f"Move result: {move_result}")
    assert move_result["success"] is True
    assert move_result["moved_count"] == 5

    # Verify no files in root
    remaining_loose = [p.name for p in TEST_DIR.iterdir() if p.is_file()]
    assert len(remaining_loose) == 0, f"Expected 0 loose files in root, found: {remaining_loose}"
    print("All files moved into detailed subdirectories.")

    print("\n--- TEST 5: One Click Safe Undo Rollback ---")
    batch_id = move_result["batch_id"]
    undo_result = mover.undo_batch(batch_id)
    print(f"Undo result: {undo_result}")
    assert undo_result["success"] is True
    assert undo_result["restored_count"] == 5

    # Verify files are restored back to root
    restored_files = [p.name for p in TEST_DIR.iterdir() if p.is_file()]
    print(f"Restored files in root: {restored_files}")
    assert len(restored_files) == 5, f"Expected 5 restored files, got {len(restored_files)}"

    print("\n--- TEST 6: Zero Deletion and Collision Renaming ---")
    dest_dir = TEST_DIR / "Financial Records"
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "duplicate.txt").write_text("Original content")
    
    # Simulate move of another file with same name
    src_file = TEST_DIR / "duplicate.txt"
    src_file.write_text("New content")

    safe_dest = mover.get_safe_destination_path(dest_dir, "duplicate.txt")
    print(f"Safe destination resolved to: {safe_dest.name}")
    assert safe_dest.name == "duplicate (1).txt"
    assert (dest_dir / "duplicate.txt").read_text() == "Original content"
    print("Collision avoided without overwriting or deleting existing files.")

    # Clean up test sandbox
    shutil.rmtree(TEST_DIR)
    print("\nAll Automated Tests Passed Successfully!")


if __name__ == "__main__":
    run_all_tests()
