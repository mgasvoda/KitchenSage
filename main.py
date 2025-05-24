#!/usr/bin/env python3
"""
KitchenCrew - AI-Powered Cooking Assistant
Main entry point for the application.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from src.crew import KitchenCrew
from src.utils.logging_config import setup_logging


def main():
    """Main application entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='KitchenCrew - AI-Powered Cooking Assistant')
    parser.add_argument('--cli', action='store_true', help='Start CLI interface')
    parser.add_argument('--demo', action='store_true', help='Run demo mode')
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting KitchenCrew application")
    
    # Check environment setup
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key and not api_key.startswith('sk-placeholder'):
        logger.info(f"OpenAI API key loaded: {api_key[:10]}...")
    else:
        logger.warning("OpenAI API key not found or is placeholder - using basic functionality only")
    
    try:
        # Handle different modes
        if args.init_db:
            init_database()
        elif args.cli:
            start_cli_mode()
        elif args.demo:
            run_demo_mode()
        else:
            # Default: show help and available modes
            show_usage_help(parser)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting KitchenCrew: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


def start_cli_mode():
    """Start the CLI interface."""
    print("🍳 Starting KitchenCrew CLI...")
    print("Use --help to see available commands")
    
    # Import and run CLI
    try:
        from src.cli import cli
        cli()
    except ImportError as e:
        print(f"❌ CLI module not available: {e}")
        sys.exit(1)


def run_demo_mode():
    """Run the demo mode."""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize the crew
        crew = KitchenCrew()
        logger.info("KitchenCrew initialized successfully")
        
        print("=== KitchenCrew Demo Mode ===")
        print()
        
        # Check database status
        from src.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if we have recipes
            cursor.execute("SELECT COUNT(*) FROM recipes")
            recipe_count = cursor.fetchone()[0]
            
            print(f"📊 Database Status:")
            print(f"   Recipes: {recipe_count}")
            
            if recipe_count == 0:
                print("\n💡 No recipes found! Try:")
                print("   python main.py --cli")
                print("   python -m src.cli data import-samples --count 10")
                return
            
            # Show some sample recipes
            print(f"\n🍽️  Sample Recipes (first 5):")
            cursor.execute("SELECT id, name, cuisine, difficulty FROM recipes LIMIT 5")
            recipes = cursor.fetchall()
            
            for recipe_id, name, cuisine, difficulty in recipes:
                print(f"   {recipe_id}: {name} ({cuisine}, {difficulty})")
        
        print(f"\n✅ KitchenCrew is ready!")
        print(f"   🔧 Use CLI: python main.py --cli")
        print(f"   📖 See help: python -m src.cli --help")
        
    except Exception as e:
        logger.error(f"Error in demo mode: {e}")
        print(f"❌ Demo failed: {e}")


def init_database():
    """Initialize the database."""
    print("🔧 Initializing database...")
    
    try:
        # Run the database initialization script
        import subprocess
        result = subprocess.run([sys.executable, 'scripts/init_db.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database initialized successfully!")
            print(result.stdout)
        else:
            print("❌ Database initialization failed:")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


def show_usage_help(parser):
    """Show usage help and available commands."""
    print("🍳 KitchenCrew - AI-Powered Cooking Assistant")
    print("=" * 50)
    
    print("\n📋 Available Modes:")
    print("  --cli        Start interactive CLI interface")
    print("  --demo       Run demo mode to test functionality")
    print("  --init-db    Initialize/reset database")
    
    print("\n🚀 Quick Start:")
    print("  1. Initialize database:  python main.py --init-db")
    print("  2. Add sample recipes:   python main.py --cli data import-samples")
    print("  3. Start using CLI:      python main.py --cli")
    
    print("\n🔧 CLI Commands Preview:")
    print("  Recipe Management:")
    print("    python -m src.cli recipe add --interactive")
    print("    python -m src.cli recipe list")
    print("    python -m src.cli recipe search --cuisine italian")
    
    print("\n  Meal Planning:")
    print("    python -m src.cli meal plan --days 7 --people 2")
    
    print("\n  Grocery Lists:")
    print("    python -m src.cli grocery generate --meal-plan-id 1")
    
    print("\n  Data Management:")
    print("    python -m src.cli data status")
    print("    python -m src.cli data import-samples --count 10")
    
    print(f"\n💡 For detailed help: python -m src.cli --help")


if __name__ == "__main__":
    main() 