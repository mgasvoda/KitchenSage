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
    
    # Debug: Check if environment variables are loaded
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        logger.info(f"OpenAI API key loaded: {api_key[:10]}..." if len(api_key) > 10 else "OpenAI API key loaded (short)")
    else:
        logger.warning("OpenAI API key not found in environment variables")
        logger.info("Available environment variables starting with OPENAI:")
        for key, value in os.environ.items():
            if key.startswith('OPENAI'):
                logger.info(f"  {key}: {value[:10]}..." if len(value) > 10 else f"  {key}: {value}")
    
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