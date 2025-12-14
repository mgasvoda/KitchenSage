#!/usr/bin/env python3
"""
Add missing updated_at column to pending_recipes table.
"""

import sqlite3
import os

def add_updated_at_column():
    """Add updated_at column to pending_recipes table if it doesn't exist."""
    
    # Get database path from environment or use default
    db_path = os.getenv('DATABASE_URL', 'sqlite:///kitchen_crew.db').replace('sqlite:///', '')
    
    print(f"Updating database at: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if updated_at column exists
        cursor.execute("PRAGMA table_info(pending_recipes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'updated_at' not in columns:
            print("Adding updated_at column to pending_recipes table...")
            cursor.execute('''
                ALTER TABLE pending_recipes 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ''')
            print("Column added successfully!")
        else:
            print("updated_at column already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Commit changes and close connection
        conn.commit()
        conn.close()
        print("Database update completed!")

if __name__ == "__main__":
    add_updated_at_column()