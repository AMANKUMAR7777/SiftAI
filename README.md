# SiftAI Universal File Organizer

SiftAI is an intelligent desktop application designed to organize cluttered folders, drives, and directories containing hundreds of unorganized files. Powered by local LLM models of your choice via Ollama, it categorizes files with granular semantic detail instead of generic buckets.

## Key Capabilities

* Detailed Semantic Organization: Replaces vague folders like documents or images with specific contextual structures such as Financial Records/Invoices 2024, Software Engineering/Python Scripts, Academic Papers/Machine Learning, or Design Assets/Vector Graphics.
* Any Local Model of Your Choice: Fully flexible. Run any Ollama model you prefer such as 1B, 3B, 7B, 8B, or custom fine tuned models. The software automatically detects whatever models you have installed. It also includes fast semantic heuristics if no model is loaded.
* Universal Folder Support: Easily organize any directory on your computer including Downloads, Desktop, Documents, external drives, or USB media. Includes an optional toggle to inspect deeply nested subfolders.
* Absolute Safety and Zero Deletions:
  * Files are strictly moved with collision renaming protection such as (1), (2) so no data is ever overwritten.
  * No file deletion commands exist in the codebase.
  * Interactive Dry Run preview lets you inspect and edit proposed folder names before applying.
  * One click safe Undo restores every file in a batch back to its original location using an SQLite audit ledger.
* Geex Inspired Soft Aesthetics:
  * Soft pastel palette with clean rounded cards and subtle diffused shadows.
  * Strictly no emojis, no hyphens, and no gradients.

## Quick Start

1. Start Ollama with any model of your choice:
   ```bash
   ollama serve
   ```

2. Run the application:
   ```bash
   python run.py
   ```
   or double click start.bat.

3. The application will launch at http://127.0.0.1:5000 and automatically list all your local Ollama models in the dropdown.
