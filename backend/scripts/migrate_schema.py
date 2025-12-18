#!/usr/bin/env python3
"""
Comprehensive database migration script for KitchenSage.

This script ensures an existing database matches the expected schema defined
in init_db.py. It can be run multiple times safely (idempotent).

Run this after pulling new code to ensure your local database has all required columns.
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Set, Tuple


# Expected schema for all tables
# Format: {table_name: [(column_name, column_definition), ...]}
EXPECTED_SCHEMA: Dict[str, List[Tuple[str, str]]] = {
    "recipes": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("name", "TEXT NOT NULL"),
        ("description", "TEXT"),
        ("prep_time", "INTEGER"),
        ("cook_time", "INTEGER"),
        ("servings", "INTEGER"),
        ("difficulty", "TEXT"),
        ("cuisine", "TEXT"),
        ("dietary_tags", "TEXT"),
        ("instructions", "TEXT"),
        ("notes", "TEXT"),
        ("source", "TEXT"),
        ("image_url", "TEXT"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "ingredients": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("name", "TEXT UNIQUE NOT NULL"),
        ("category", "TEXT"),
        ("common_unit", "TEXT"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "recipe_ingredients": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("recipe_id", "INTEGER"),
        ("ingredient_id", "INTEGER"),
        ("quantity", "REAL"),
        ("unit", "TEXT"),
        ("notes", "TEXT"),
        ("optional", "BOOLEAN DEFAULT FALSE"),
        ("substitutes", "TEXT"),
    ],
    "meal_plans": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("name", "TEXT NOT NULL"),
        ("is_active", "BOOLEAN DEFAULT FALSE"),
        ("people_count", "INTEGER"),
        ("dietary_restrictions", "TEXT"),
        ("description", "TEXT"),
        ("budget_target", "REAL"),
        ("calories_per_day_target", "INTEGER"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "meals": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("meal_plan_id", "INTEGER"),
        ("recipe_id", "INTEGER"),
        ("meal_type", "TEXT"),
        ("day_number", "INTEGER"),
        ("servings_override", "INTEGER"),
        ("notes", "TEXT"),
    ],
    "grocery_lists": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("meal_plan_id", "INTEGER"),
        ("name", "TEXT"),
        ("estimated_total", "REAL"),
        ("actual_total", "REAL"),
        ("budget_limit", "REAL"),
        ("store_preferences", "TEXT"),
        ("completed", "BOOLEAN DEFAULT FALSE"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("completed_at", "TIMESTAMP"),
    ],
    "grocery_items": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("grocery_list_id", "INTEGER"),
        ("ingredient_id", "INTEGER"),
        ("quantity", "REAL"),
        ("unit", "TEXT"),
        ("estimated_price", "REAL"),
        ("actual_price", "REAL"),
        ("status", "TEXT DEFAULT 'needed'"),
        ("store_section", "TEXT"),
        ("preferred_brand", "TEXT"),
        ("substitutes", "TEXT"),
        ("notes", "TEXT"),
        ("purchased", "BOOLEAN DEFAULT FALSE"),
    ],
    "user_preferences": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("preference_key", "TEXT UNIQUE NOT NULL"),
        ("preference_value", "TEXT"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "pending_recipes": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("name", "TEXT NOT NULL"),
        ("description", "TEXT"),
        ("prep_time", "INTEGER"),
        ("cook_time", "INTEGER"),
        ("servings", "INTEGER"),
        ("difficulty", "TEXT"),
        ("cuisine", "TEXT"),
        ("dietary_tags", "TEXT"),
        ("ingredients", "TEXT"),
        ("instructions", "TEXT"),
        ("notes", "TEXT"),
        ("image_url", "TEXT"),
        ("nutritional_info", "TEXT"),
        ("source_url", "TEXT"),
        ("discovery_query", "TEXT"),
        ("status", "TEXT DEFAULT 'pending'"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
}


def backup_database(conn: sqlite3.Connection, db_path: str) -> str:
    """Create a backup of the database before migration."""
    backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')

    print(f"Creating backup at: {backup_path}")

    backup_conn = sqlite3.connect(backup_path)
    conn.backup(backup_conn)
    backup_conn.close()

    print(f"Backup created successfully")
    return backup_path


def get_existing_columns(cursor: sqlite3.Cursor, table_name: str) -> Set[str]:
    """Get set of existing column names for a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def add_column_if_missing(cursor: sqlite3.Cursor, table_name: str, column_name: str, column_def: str) -> bool:
    """Add a column to a table if it doesn't exist. Returns True if column was added."""
    # Extract just the type/default from the definition (skip PRIMARY KEY, etc.)
    # For ALTER TABLE, we need a simpler definition
    simple_def = column_def

    # Handle common cases
    if "PRIMARY KEY" in column_def:
        return False  # Can't add primary key columns

    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {simple_def}")
        return True
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            return False
        raise


def migrate_table(cursor: sqlite3.Cursor, table_name: str, expected_columns: List[Tuple[str, str]]) -> int:
    """Migrate a single table to match expected schema. Returns count of columns added."""
    existing_columns = get_existing_columns(cursor, table_name)
    added_count = 0

    for column_name, column_def in expected_columns:
        if column_name not in existing_columns:
            if add_column_if_missing(cursor, table_name, column_name, column_def):
                print(f"  + Added column: {column_name}")
                added_count += 1

    return added_count


def check_table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def migrate_database():
    """Run the full database migration."""
    # Get database path
    db_path = os.getenv('DATABASE_URL', 'sqlite:///kitchen_crew.db').replace('sqlite:///', '')

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Run 'uv run python scripts/init_db.py' to create a new database.")
        return

    print(f"Migrating database at: {db_path}")
    print("=" * 60)

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Create backup first
        backup_path = backup_database(conn, db_path)

        total_added = 0
        missing_tables = []

        print("\nChecking tables...")
        print("-" * 40)

        for table_name, expected_columns in EXPECTED_SCHEMA.items():
            if not check_table_exists(cursor, table_name):
                missing_tables.append(table_name)
                print(f"\n[!] Table '{table_name}' does not exist")
                continue

            print(f"\n[{table_name}]")
            existing = get_existing_columns(cursor, table_name)
            expected_names = {col[0] for col in expected_columns}
            missing = expected_names - existing

            if not missing:
                print(f"  All {len(expected_names)} columns present")
            else:
                print(f"  Missing columns: {missing}")
                added = migrate_table(cursor, table_name, expected_columns)
                total_added += added

        conn.commit()

        print("\n" + "=" * 60)
        print("Migration Summary")
        print("-" * 40)
        print(f"Total columns added: {total_added}")

        if missing_tables:
            print(f"\nMissing tables: {missing_tables}")
            print("Run 'uv run python scripts/init_db.py' to create missing tables.")

        if total_added > 0:
            print(f"\nBackup saved at: {backup_path}")
            print("You can delete the backup once you've verified everything works.")
        else:
            print("\nNo changes were needed. Database schema is up to date.")
            # Clean up unnecessary backup
            if os.path.exists(backup_path):
                os.remove(backup_path)
                print("Removed unnecessary backup file.")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR during migration: {e}")
        print("Database has been rolled back. No changes were made.")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()
