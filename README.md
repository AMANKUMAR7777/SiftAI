# SiftAI Universal File Organizer

SiftAI is an intelligent local desktop application designed to organize cluttered folders, drives, and directories containing hundreds of unorganized files. Powered by your choice of local language models via Ollama, it groups files with granular semantic detail instead of generic bucket folders.

SiftAI is completely private, operates locally without cloud dependencies, guarantees zero file deletions, and features a soft modern user interface.

***

## Key Capabilities

* Detailed Semantic Organization: Replaces vague folders like documents or images with specific contextual structures such as Financial Records/Invoices 2024, Software Engineering/Python Scripts, Academic Papers/Machine Learning, or Design Assets/Vector Graphics.
* Model Agnostic: Connects to your local Ollama instance with zero external cloud dependencies. You can run any model of your preference including 1B, 3B, 7B, 8B, or custom fine tuned models. It automatically detects installed models on your computer.
* Built In Heuristic Fallback: Even if Ollama is not running or no model is loaded, SiftAI continues to organize files accurately using an intelligent semantic rule engine.
* Universal Directory Support: Seamlessly organize any location on your machine including Downloads, Desktop, Documents, external hard drives, or USB media. Includes an optional toggle to inspect deeply nested subfolders.
* Absolute Safety and Zero Deletions:
  * Files are strictly moved with collision renaming protection like (1), (2) so no data is ever overwritten.
  * No file deletion commands exist in the codebase.
  * An interactive preview lets you inspect and edit proposed folder names before applying moves.
  * One click safe Undo restores every file in a batch back to its original location using an SQLite audit ledger.
* Geex Inspired Soft Aesthetics:
  * Soft pastel palette with clean rounded cards and subtle diffused shadows.
  * Strictly no emojis, no hyphens in text, and no gradients.

***

## Prerequisites

Before setting up SiftAI, ensure you have the following installed on your machine:

1. Python (version 3.10 or newer)
2. Git
3. Ollama (optional but recommended for local intelligence)

***

## Installation and Setup

Follow these steps to copy and set up the project on your local machine:

### Step 1: Copy or Clone the Repository

Open your terminal or command prompt and clone the repository:

```bash
git clone https://github.com/AMANKUMAR7777/SiftAI.git
cd SiftAI
```

Alternatively, you can download the repository as a ZIP archive directly from GitHub, extract the contents to a folder of your choice, and navigate inside that folder.

### Step 2: Install Required Dependencies

Install the necessary Python packages using pip:

```bash
pip install flask requests pymupdf pillow
```

You can also install using the provided requirements file:

```bash
pip install -r requirements.txt
```

### Step 3: Setup Ollama (Optional)

If you wish to use local language models:

1. Download and install Ollama from the official website.
2. Start the Ollama service:
   ```bash
   ollama serve
   ```
3. Pull any model of your choice. Some great examples:
   ```bash
   ollama pull qwen2.5:3b
   ```
   or
   ```bash
   ollama pull llama3.2:1b
   ```
   or
   ```bash
   ollama pull llama3:8b
   ```

SiftAI automatically detects whatever models are present in your Ollama library when the application starts.

***

## Running SiftAI

### On Windows

Double click the included launcher script:
```text
start.bat
```

Or run directly from your terminal:
```bash
python run.py
```

### On macOS or Linux

Execute the launcher using Python:
```bash
python run.py
```

Once launched, the application will automatically open in your default browser at:
```text
http://127.0.0.1:5000
```

***

## How to Use SiftAI

SiftAI features a simplified two step workflow:

### 1. Select Your Target Directory
* When launched, SiftAI defaults to your standard Downloads directory and automatically lists all loose files.
* Use the quick location dropdown to jump instantly between Downloads, Desktop, Documents, Pictures, Videos, and Music.
* Click Browse to pick any custom folder or external drive on your computer using the native system folder selector.
* You can also drag and drop any folder directly from your file manager onto the folder display bar.
* If your folder has messy nested subdirectories, check the Include Subfolders box.

### 2. Organize and Move
* Select your preferred local model from the dropdown.
* Click the purple Organize Files button. SiftAI will stream progress in real time as files are analyzed and classified into detailed topics.
* Review the suggested folder destinations in the table. You can edit any folder path directly inside the table row if you want to tweak a name.
* When satisfied, click Move Files Now. All files are safely moved into their detailed subfolders with zero deletions.

### 3. Reversing a Move (Undo)
* Navigate to the Safety and History tab in the left navigation sidebar.
* Click Undo Batch Move on any past run. Every file from that run will immediately return to its original location.

***

## Project Architecture

```text
SiftAI/
* backend/
  * config.py          Configuration constants and directory paths
  * scanner.py         Directory scanner with text and PDF preview extractors
  * llm_organizer.py   Ollama streaming query handler and semantic rule engine
  * mover.py           Non destructive file mover with collision renaming
  * ledger.py          SQLite audit logger for one click rollback tracking
  * app.py             Flask application with streaming endpoints
* frontend/
  * index.html         Geex inspired soft dashboard layout
  * styles.css         Custom soft UI styling with solid pastel tokens
  * app.js             Frontend controller with live streaming updates
* tests/
  * test_system.py     Automated tests for scanner, mover, and rollback
* data/                Directory storing the SQLite history ledger
* run.py               Python launcher with browser auto launch
* start.bat            Windows double click launcher script
* requirements.txt     Python package dependencies list
* README.md            Documentation guide
```

***

## Safety Guarantees

* Zero Deletions: No files are ever deleted or destroyed.
* Collision Resolution: If a file with an identical name already exists in a destination folder, a numbered suffix like (1) or (2) is automatically created so no data is overwritten.
* Complete Rollback: All moves are recorded with timestamps, source paths, and target paths in an SQLite database so you can reverse any organization batch at any time.
