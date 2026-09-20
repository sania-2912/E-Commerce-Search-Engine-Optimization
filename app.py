"""
Multimodal E-Commerce Search Engine - Main Application Entry Point
Starts Uvicorn server hosting the FastAPI backend on port 8000.
"""
import uvicorn
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"Starting Multimodal E-Commerce Search Engine on http://{host}:{port} ...")
    uvicorn.run("backend.app:app", host=host, port=port, reload=False)
