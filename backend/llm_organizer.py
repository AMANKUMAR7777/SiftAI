import json
import re
import requests
from typing import List, Dict, Any
from backend.config import OLLAMA_BASE_URL, DEFAULT_MODEL, BATCH_SIZE, OLLAMA_TIMEOUT


SYSTEM_PROMPT = """You are an expert file organizer.
Group files into specific, granular, and descriptive folders.

RULES:
1. NEVER use generic buckets like "documents", "archives", "images", "files", "downloads", "others", or "miscellaneous".
2. Create DETAILED folder names based on the filename and preview (e.g. "Financial Records/Invoices 2024", "Software Development/Python Scripts", "Academic Papers/Machine Learning", "System Utilities/Installers").
3. DO NOT use hyphens anywhere in folder names or reasons. Use spaces or forward slashes.
4. Return ONLY a valid JSON array of objects with keys:
   - "filename": exact original filename
   - "folder": detailed folder path
   - "reason": brief reason without hyphens
"""


def clean_no_hyphens(text: str) -> str:
    """Ensure no hyphens exist in generated names or reasons."""
    return text.replace("-", " ").replace("  ", " ").strip()


def sanitize_folder_path(path_str: str) -> str:
    """Sanitize folder path for Windows filesystem without hyphens or invalid characters."""
    cleaned = clean_no_hyphens(path_str)
    cleaned = cleaned.replace("\\", "/")
    cleaned = re.sub(r'[*?:"<>|]', "", cleaned)
    parts = [p.strip() for p in cleaned.split("/") if p.strip()]
    if not parts:
        return "General Records"
    return "/".join(parts)


def query_ollama_batch(model: str, files_batch: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Query Ollama with a batch of files and request structured JSON output."""
    chosen_model = model or DEFAULT_MODEL
    if not chosen_model:
        return generate_fallback_categories(files_batch)

    file_descriptions = []
    for f in files_batch:
        item = f"File: {f['name']} ({f['extension']})"
        if f.get("sample"):
            item += f" | Preview: {f['sample'][:140]}"
        file_descriptions.append(item)

    user_prompt = "Categorize these files into detailed folders. Return JSON array:\n" + "\n".join(file_descriptions)

    payload = {
        "model": chosen_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "top_p": 0.85
        }
    }

    try:
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=OLLAMA_TIMEOUT)
        if resp.status_code == 200:
            result = resp.json()
            content = result.get("message", {}).get("content", "")
            parsed = parse_llm_json_response(content, files_batch)
            if parsed:
                return parsed
    except Exception as e:
        print(f"Ollama query timeout or error: {e}. Using fast detailed categorization.")

    return generate_fallback_categories(files_batch)


def parse_llm_json_response(content: str, files_batch: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Parse and validate JSON response from the LLM."""
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            if "filename" in parsed or "name" in parsed:
                parsed = [parsed]
            else:
                for key in ("files", "data", "results", "items"):
                    if key in parsed and isinstance(parsed[key], list):
                        parsed = parsed[key]
                        break
                else:
                    list_items = []
                    for k, v in parsed.items():
                        if isinstance(v, dict):
                            list_items.append({
                                "filename": k,
                                "folder": v.get("folder", "General"),
                                "reason": v.get("reason", "Categorized")
                            })
                        elif isinstance(v, str):
                            list_items.append({
                                "filename": k,
                                "folder": v,
                                "reason": "Categorized"
                            })
                    if list_items:
                        parsed = list_items

        if isinstance(parsed, list):
            results = []
            # Create a lookup for quick mapping
            batch_map = {f["name"].lower(): f["name"] for f in files_batch}
            
            for item in parsed:
                if isinstance(item, dict):
                    fn = item.get("filename", "")
                    matched_name = batch_map.get(fn.lower(), fn)
                    folder = sanitize_folder_path(item.get("folder", "Detailed Records"))
                    reason = clean_no_hyphens(item.get("reason", "Semantic context match"))
                    results.append({
                        "filename": matched_name,
                        "folder": folder,
                        "reason": reason
                    })

            if results:
                return results
    except Exception as e:
        print(f"Error parsing LLM response: {e}")

    return generate_fallback_categories(files_batch)


def generate_fallback_categories(files_batch: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Intelligent detailed fallback when Ollama is busy or initializing.
    Provides detailed categories rather than generic names.
    """
    results = []
    for f in files_batch:
        name_lower = f["name"].lower()
        ext = f["extension"].lower()
        sample = f.get("sample", "").lower()

        folder = "General Media and Assets"
        reason = "File attributes and naming pattern"

        if "invoice" in name_lower or "receipt" in name_lower or "tax" in name_lower:
            folder = "Financial Records/Invoices and Receipts"
            reason = "Financial transaction keywords"
        elif "statement" in name_lower or "bank" in name_lower or "bill" in name_lower:
            folder = "Financial Records/Banking and Statements"
            reason = "Banking and accounting documents"
        elif "resume" in name_lower or "cv" in name_lower or "portfolio" in name_lower:
            folder = "Career and Professional/Resumes"
            reason = "Career application documents"
        elif "ticket" in name_lower or "boarding" in name_lower or "flight" in name_lower or "booking" in name_lower:
            folder = "Travel and Transportation/Bookings"
            reason = "Travel reservation records"
        elif ext in ["py", "js", "ts", "html", "css", "cpp", "java", "rs"]:
            folder = "Software Engineering/Source Code"
            reason = "Programming language script"
        elif ext in ["json", "csv", "sql", "parquet", "tsv"]:
            folder = "Data Engineering/Datasets and Tables"
            reason = "Structured data storage format"
        elif ext in ["exe", "msi", "pkg", "iso"]:
            folder = "Software Installers/Application Setup"
            reason = "Executable system package"
        elif ext in ["zip", "rar", "7z", "tar", "gz"]:
            folder = "Compressed Packages/Project Archives"
            reason = "Bundled archive asset"
        elif ext in ["pdf"]:
            if "research" in sample or "abstract" in sample or "paper" in name_lower:
                folder = "Academic and Research/Scientific Papers"
                reason = "Academic article content preview"
            elif "manual" in name_lower or "guide" in name_lower or "documentation" in name_lower:
                folder = "Documentation and Manuals/User Guides"
                reason = "Reference documentation"
            else:
                folder = "Business Documents/PDF Publications"
                reason = "Publication document"
        elif ext in ["png", "jpg", "jpeg", "webp"]:
            if "screenshot" in name_lower:
                folder = "Screen Captures/Desktop Screenshots"
                reason = "Visual screenshot capture"
            elif "icon" in name_lower or "logo" in name_lower:
                folder = "Brand Assets/Logos and Icons"
                reason = "Graphic identity asset"
            else:
                folder = "Photography and Creative/Image Assets"
                reason = "Visual media image"
        elif ext in ["mp4", "mov", "mkv"]:
            folder = "Video Production/Clips and Recordings"
            reason = "Digital video file"
        elif ext in ["mp3", "wav", "aac"]:
            folder = "Audio Production/Sound Tracks and Audio"
            reason = "Digital sound track"

        results.append({
            "filename": f["name"],
            "folder": sanitize_folder_path(folder),
            "reason": clean_no_hyphens(reason)
        })

    return results


def check_ollama_status() -> Dict[str, Any]:
    """Check if Ollama server is active and get available models."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name") for m in data.get("models", [])]
            default_m = DEFAULT_MODEL if (DEFAULT_MODEL and DEFAULT_MODEL in models) else (models[0] if models else "")
            return {
                "online": True,
                "models": models,
                "default_model": default_m
            }
    except Exception:
        pass

    return {
        "online": False,
        "models": [],
        "default_model": DEFAULT_MODEL or ""
    }


def categorize_files_stream(files: List[Dict[str, Any]], model: str = DEFAULT_MODEL):
    """
    Generator yielding categorization results in batches so frontend can stream progress.
    """
    total = len(files)
    processed = 0

    for i in range(0, total, BATCH_SIZE):
        batch = files[i:i + BATCH_SIZE]
        batch_results = query_ollama_batch(model, batch)
        processed += len(batch)

        result_dict = {item["filename"]: item for item in batch_results}
        enriched_batch = []
        for f in batch:
            res = result_dict.get(f["name"], {
                "filename": f["name"],
                "folder": "Categorized Assets",
                "reason": "Analyzed file"
            })
            enriched_batch.append({
                "id": f["id"],
                "name": f["name"],
                "path": f["path"],
                "extension": f["extension"],
                "size_formatted": f["size_formatted"],
                "suggested_folder": res["folder"],
                "reason": res["reason"],
                "selected": True
            })

        yield {
            "processed": processed,
            "total": total,
            "percentage": int((processed / total) * 100) if total > 0 else 100,
            "items": enriched_batch
        }
