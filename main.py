#!/usr/bin/env python3
"""
Main entry point for KitchenCrew AI Assistant.

This script provides easy access to the KitchenCrew chat interface.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli import cli

if __name__ == "__main__":
    cli() 