#!/usr/bin/env python3
"""
Main entry point for KitchenCrew AI Assistant.

This script provides easy access to the KitchenCrew chat interface.
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Initialize Phoenix tracing before importing other modules
from src.utils.telemetry import initialize_phoenix_tracing

# Initialize telemetry
tracer_provider = initialize_phoenix_tracing(project_name="kitchencrew")

from src.cli_orchestrated import cli

if __name__ == "__main__":
    cli() 