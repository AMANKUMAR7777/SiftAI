import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.app import app
from backend.llm_organizer import check_ollama_status


def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("=" * 60)
    print("  SiftAI Local File Organizer")
    print("  Zero Deletions | Detailed Categorization | 3B Model")
    print("=" * 60)

    ollama_info = check_ollama_status()
    if ollama_info.get("online"):
        models = ollama_info.get("models", [])
        print(f"  Ollama Status: Online")
        print(f"  Detected Models: {', '.join(models) if models else 'None'}")
    else:
        print("  Notice: Ollama server was not detected at http://localhost:11434")
        print("  Please ensure Ollama is running (`ollama serve`)")

    print("\n  Launching SiftAI interface at: http://127.0.0.1:5000\n")

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
