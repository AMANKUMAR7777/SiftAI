import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response
from backend.config import BASE_DIR, DEFAULT_TARGET_DIR, DEFAULT_MODEL
from backend import scanner, llm_organizer, mover, ledger

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "frontend"),
    static_url_path="/static"
)

# Initialize database
ledger.init_db()


@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR / "frontend"), "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(str(BASE_DIR / "frontend"), filename)


@app.route("/api/status", methods=["GET"])
def get_status():
    home = Path.home()
    ollama_info = llm_organizer.check_ollama_status()

    return jsonify({
        "status": "online",
        "default_folder": DEFAULT_TARGET_DIR,
        "quick_folders": {
            "Downloads": str(home / "Downloads"),
            "Desktop": str(home / "Desktop"),
            "Documents": str(home / "Documents"),
            "Pictures": str(home / "Pictures"),
            "Videos": str(home / "Videos"),
            "Music": str(home / "Music")
        },
        "ollama": ollama_info
    })


@app.route("/api/scan", methods=["POST"])
def scan_folder():
    data = request.get_json() or {}
    folder_path = data.get("directory", DEFAULT_TARGET_DIR)
    include_subfolders = data.get("include_subfolders", False)

    try:
        results = scanner.scan_directory(folder_path, include_subfolders=include_subfolders)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/categorize", methods=["POST"])
def categorize_files():
    data = request.get_json() or {}
    files = data.get("files", [])
    model = data.get("model", DEFAULT_MODEL)

    if not files:
        return jsonify({"success": False, "error": "No files provided"}), 400

    results = []
    # Process in batches using llm_organizer
    for update in llm_organizer.categorize_files_stream(files, model=model):
        results.extend(update["items"])

    return jsonify({"success": True, "items": results})


@app.route("/api/categorize_stream", methods=["POST"])
def categorize_stream():
    """SSE endpoint to stream categorized batches live to the frontend."""
    data = request.get_json() or {}
    files = data.get("files", [])
    model = data.get("model", DEFAULT_MODEL)

    def generate():
        for update in llm_organizer.categorize_files_stream(files, model=model):
            yield f"data: {json.dumps(update)}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/apply", methods=["POST"])
def apply_organization():
    data = request.get_json() or {}
    directory = data.get("directory", "")
    items = data.get("items", [])

    if not directory or not items:
        return jsonify({"success": False, "error": "Invalid directory or items payload"}), 400

    try:
        result = mover.execute_organization_plan(directory, items)
        return jsonify({"success": result["success"], "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        batches = ledger.get_batches()
        return jsonify({"success": True, "batches": batches})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/undo", methods=["POST"])
def undo_batch_action():
    data = request.get_json() or {}
    batch_id = data.get("batch_id", "")

    if not batch_id:
        return jsonify({"success": False, "error": "Batch ID required"}), 400

    try:
        result = mover.undo_batch(batch_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/pick_folder", methods=["POST"])
def pick_folder_dialog():
    """Trigger native Windows folder dialog using tkinter."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected_dir = filedialog.askdirectory(initialdir=DEFAULT_TARGET_DIR)
        root.destroy()

        if selected_dir:
            return jsonify({"success": True, "directory": selected_dir})
        else:
            return jsonify({"success": False, "message": "Selection cancelled"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print(f"Starting SiftAI Local Organizer on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
