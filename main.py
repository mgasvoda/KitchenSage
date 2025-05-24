#!/usr/bin/env python3
"""
KitchenCrew - AI-Powered Cooking Assistant
Main entry point for the application.
"""

import os
import logging
from dotenv import load_dotenv
from src.crew import KitchenCrew
from src.utils.logging_config import setup_logging


def main():
    """Main application entry point."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting KitchenCrew application")
    
    try:
        # Initialize the crew
        crew = KitchenCrew()
        
        # Example usage - this will be replaced with proper CLI or API
        logger.info("KitchenCrew initialized successfully")
        
        # Demo: Find some Italian vegetarian recipes
        print("=== KitchenCrew Demo ===")
        print("Finding Italian vegetarian recipes...")
        
        # This is a placeholder for actual functionality
        print("System ready! Use the API endpoints or CLI commands to interact with KitchenCrew.")
        
    except Exception as e:
        logger.error(f"Error starting KitchenCrew: {e}")
        raise


if __name__ == "__main__":
    main() 