#!/usr/bin/env python3
"""
Run the KitchenSage API server.

Usage:
    python run_api.py
    
Or with uvicorn directly:
    uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Ensure the backend directory is in the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Load environment variables
load_dotenv(os.path.join(backend_dir, '..', '.env'))
load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

