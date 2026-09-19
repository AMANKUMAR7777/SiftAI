import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "history.db"

# Default target directory (Windows Downloads folder)
DEFAULT_TARGET_DIR = str(Path.home() / "Downloads")

# Ollama API Configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "")

# Safe Processing Settings
BATCH_SIZE = 18
OLLAMA_TIMEOUT = 14
MAX_SAMPLE_CHARS = 300
MAX_PREVIEW_FILES = 500
