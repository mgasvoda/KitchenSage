#!/usr/bin/env python3
"""
Main entry point for KitchenCrew AI Assistant.

This script provides easy access to the KitchenCrew chat interface.
Run from the backend directory: python main.py chat
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables from project root or backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv()  # Also check current directory

# Add the backend directory to the Python path for src imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Initialize Phoenix tracing before importing other modules
from src.utils.telemetry import initialize_phoenix_tracing

# Initialize telemetry
tracer_provider = initialize_phoenix_tracing(project_name="kitchencrew")

from src.cli_orchestrated import cli

if __name__ == "__main__":
    cli() 