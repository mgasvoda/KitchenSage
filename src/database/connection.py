"""
Database connection management for KitchenCrew.

Provides connection pooling, context management, and transaction support.
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Optional, Generator
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration settings."""
    
    def __init__(self):
        """Initialize database configuration from environment."""
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///kitchen_crew.db')
        self.connection_timeout = 30
        self.check_same_thread = False  # Allow multi-threading
        
        # Extract SQLite file path from URL
        if self.database_url.startswith('sqlite:///'):
            self.db_path = self.database_url[10:]  # Remove 'sqlite:///'
        else:
            self.db_path = 'kitchen_crew.db'
        
        # Ensure directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Database configured: {self.db_path}")


# Global configuration instance
config = DatabaseConfig()


def get_db_connection() -> sqlite3.Connection:
    """
    Get a new database connection.
    
    Returns:
        sqlite3.Connection: Database connection with proper settings
    """
    try:
        conn = sqlite3.connect(
            config.db_path,
            timeout=config.connection_timeout,
            check_same_thread=config.check_same_thread
        )
        
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Set row factory for easier access to columns
        conn.row_factory = sqlite3.Row
        
        return conn
        
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


@contextmanager
def get_db_session() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database sessions with automatic commit/rollback.
    
    Yields:
        sqlite3.Connection: Database connection within transaction
        
    Example:
        with get_db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO recipes ...")
            # Automatically commits on success, rolls back on error
    """
    conn = None
    try:
        conn = get_db_connection()
        yield conn
        conn.commit()
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database session error: {e}")
        raise
        
    finally:
        if conn:
            conn.close()


def execute_script(script_path: str) -> None:
    """
    Execute a SQL script file.
    
    Args:
        script_path: Path to the SQL script file
        
    Raises:
        FileNotFoundError: If script file doesn't exist
        sqlite3.Error: If SQL execution fails
    """
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"SQL script not found: {script_path}")
    
    with open(script_path, 'r', encoding='utf-8') as file:
        script_content = file.read()
    
    with get_db_session() as conn:
        conn.executescript(script_content)
        logger.info(f"Successfully executed SQL script: {script_path}")


def check_database_exists() -> bool:
    """
    Check if the database file exists and has tables.
    
    Returns:
        bool: True if database exists and has tables
    """
    if not os.path.exists(config.db_path):
        return False
    
    try:
        with get_db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='recipes'"
            )
            return cursor.fetchone() is not None
            
    except sqlite3.Error:
        return False


def initialize_database() -> None:
    """
    Initialize the database if it doesn't exist.
    
    This will run the initialization script to create all tables.
    """
    if check_database_exists():
        logger.info("Database already exists and is initialized")
        return
    
    logger.info("Initializing database...")
    
    # Look for the initialization script
    script_paths = [
        "scripts/init_db.py",
        "../scripts/init_db.py", 
        "../../scripts/init_db.py"
    ]
    
    for script_path in script_paths:
        if os.path.exists(script_path):
            # Import and run the initialization
            import sys
            sys.path.append(os.path.dirname(script_path))
            
            try:
                import init_db
                init_db.create_tables()
                logger.info("Database initialized successfully")
                return
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
    
    logger.warning("Could not find database initialization script")


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class RecordNotFoundError(DatabaseError):
    """Raised when a requested record is not found."""
    pass


class ValidationError(DatabaseError):
    """Raised when data validation fails."""
    pass 