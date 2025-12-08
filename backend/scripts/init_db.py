#!/usr/bin/env python3
"""
Database initialization script for KitchenCrew.
Creates the SQLite database and tables.
"""

import sqlite3
import os
from pathlib import Path


def create_database():
    """Create the KitchenCrew database and tables."""
    
    # Get database path from environment or use default
    db_path = os.getenv('DATABASE_URL', 'sqlite:///kitchen_crew.db').replace('sqlite:///', '')
    
    print(f"Creating database at: {db_path}")
    
    # Create database directory if it doesn't exist
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database (creates file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    print("Creating tables...")
    
    # Recipes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            prep_time INTEGER,
            cook_time INTEGER,
            servings INTEGER,
            difficulty TEXT,
            cuisine TEXT,
            dietary_tags TEXT,
            instructions TEXT,
            notes TEXT,
            source TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Ingredients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            common_unit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Recipe ingredients junction table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient_id INTEGER,
            quantity REAL,
            unit TEXT,
            notes TEXT,
            optional BOOLEAN DEFAULT FALSE,
            substitutes TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
        )
    ''')
    
    # Meal plans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date DATE,
            end_date DATE,
            people_count INTEGER,
            dietary_restrictions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Meals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_plan_id INTEGER,
            recipe_id INTEGER,
            meal_type TEXT,
            meal_date DATE,
            FOREIGN KEY (meal_plan_id) REFERENCES meal_plans (id),
            FOREIGN KEY (recipe_id) REFERENCES recipes (id)
        )
    ''')
    
    # Grocery lists table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grocery_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_plan_id INTEGER,
            estimated_cost REAL,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meal_plan_id) REFERENCES meal_plans (id)
        )
    ''')
    
    # Grocery items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grocery_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grocery_list_id INTEGER,
            ingredient_id INTEGER,
            quantity REAL,
            unit TEXT,
            estimated_price REAL,
            purchased BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (grocery_list_id) REFERENCES grocery_lists (id),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
        )
    ''')
    
    # User preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preference_key TEXT UNIQUE NOT NULL,
            preference_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database created successfully!")
    print(f"Database location: {os.path.abspath(db_path)}")


if __name__ == "__main__":
    create_database() 