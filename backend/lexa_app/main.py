#!/usr/bin/env python3
"""
LexaAI Main Entry Point for lexa_app module.
This module imports the FastAPI app from the parent backend directory.
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path so we can import app
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import the FastAPI app from the parent backend directory
from app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8601)