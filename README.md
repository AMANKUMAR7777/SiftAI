# SiftAI Universal File Organizer

SiftAI is an intelligent desktop application designed to organize cluttered folders, drives, and directories containing hundreds of unorganized files. Powered by local 3B LLM models via Ollama (`qwen2.5:3b`), it categorizes files with granular semantic detail instead of generic buckets.

## Core Features

- **Detailed Organization**: Replaces vague folders like "documents" or "images" with specific, contextual structures (e.g. `Financial Records/Invoices 2024`, `Software Engineering/Python Scripts`, `Academic Papers/Machine Learning`).
- **Local 3B LLM Intelligence**: Connects to your local Ollama instance with zero external cloud dependencies. Analyzes filenames, extensions, and content previews (including text from PDFs and source code).
- **Absolute Safety (Zero Deletions)**:
  - Files are moved safely with collision protection (renaming duplicates `(1)`, `(2)` so nothing is ever overwritten).
  - No deletion logic exists anywhere in the software.
  - Interactive Dry Run preview lets you inspect and edit proposed folder names before applying.
  - One-click safe Undo restores every file in a batch back to its original path.
- **Geex-Inspired Soft Aesthetics**:
  - Soft pastel palette with clean rounded cards and subtle diffused shadows.
  - Strictly no emojis, no hyphens, and no gradients.

## Quick Start

1. Ensure Ollama is running and has a 3B model:
   ```bash
   ollama run qwen2.5:3b
   ```

2. Run the application:
   ```bash
   python run.py
   ```
   or double-click `start.bat`.

3. The application will open in your browser at `http://127.0.0.1:5000`.
