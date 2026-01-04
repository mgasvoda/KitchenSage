#!/usr/bin/env python3
"""
Database migration script to convert date-based meal plans to dateless, reusable plans.

Changes:
1. Add is_active column to meal_plans
2. Add day_number column to meals (calculated from meal_date - start_date + 1)
3. Remove start_date, end_date from meal_plans
4. Remove meal_date from meals

This migration preserves all existing data while transforming the schema.
"""

import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path


def backup_database(conn):
    """Create a backup of the database before migration."""
    db_path = os.getenv('DATABASE_URL', 'sqlite:///kitchen_crew.db').replace('sqlite:///', '')
    backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')

    print(f"Creating backup at: {backup_path}")

    # SQLite backup
    backup_conn = sqlite3.connect(backup_path)
    conn.backup(backup_conn)
    backup_conn.close()

    print(f"Backup created successfully: {backup_path}")
    return backup_path


def migrate_database():
    """Migrate database to dateless meal plan schema."""

    # Get database path
    db_path = os.getenv('DATABASE_URL', 'sqlite:///kitchen_crew.db').replace('sqlite:///', '')

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Nothing to migrate.")
        return

    print(f"Migrating database at: {db_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Create backup first
        backup_path = backup_database(conn)

        print("\n--- Phase 1: Adding new columns ---")

        # Add is_active column to meal_plans (default FALSE)
        print("Adding is_active column to meal_plans...")
        try:
            cursor.execute("ALTER TABLE meal_plans ADD COLUMN is_active BOOLEAN DEFAULT FALSE")
            print("✓ is_active column added")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ is_active column already exists")
            else:
                raise

        # Add day_number column to meals
        print("Adding day_number column to meals...")
        try:
            cursor.execute("ALTER TABLE meals ADD COLUMN day_number INTEGER")
            print("✓ day_number column added")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ day_number column already exists")
            else:
                raise

        conn.commit()

        print("\n--- Phase 2: Migrating data ---")

        # Get all meal plans with their start dates
        cursor.execute("SELECT id, name, start_date FROM meal_plans")
        meal_plans = cursor.fetchall()

        print(f"Found {len(meal_plans)} meal plans to migrate")

        for plan in meal_plans:
            plan_id = plan['id']
            start_date_str = plan['start_date']

            if not start_date_str:
                print(f"  Plan {plan_id} ({plan['name']}): No start_date, skipping meal migration")
                continue

            # Parse start_date
            try:
                start_date = datetime.fromisoformat(start_date_str).date()
            except (ValueError, AttributeError):
                print(f"  Plan {plan_id} ({plan['name']}): Invalid start_date '{start_date_str}', skipping")
                continue

            # Get all meals for this plan
            cursor.execute("SELECT id, meal_date FROM meals WHERE meal_plan_id = ?", (plan_id,))
            meals = cursor.fetchall()

            migrated_count = 0
            for meal in meals:
                meal_id = meal['id']
                meal_date_str = meal['meal_date']

                if not meal_date_str:
                    print(f"    Meal {meal_id}: No meal_date, setting day_number to 1")
                    day_number = 1
                else:
                    try:
                        meal_date = datetime.fromisoformat(meal_date_str).date()
                        # Calculate day number (1-based)
                        day_number = (meal_date - start_date).days + 1

                        # Validate day_number is reasonable (1-30)
                        if day_number < 1:
                            day_number = 1
                        elif day_number > 30:
                            day_number = 30
                    except (ValueError, AttributeError):
                        print(f"    Meal {meal_id}: Invalid meal_date '{meal_date_str}', setting day_number to 1")
                        day_number = 1

                # Update meal with day_number
                cursor.execute("UPDATE meals SET day_number = ? WHERE id = ?", (day_number, meal_id))
                migrated_count += 1

            print(f"  Plan {plan_id} ({plan['name']}): Migrated {migrated_count} meals")

        conn.commit()

        print("\n--- Phase 3: Removing old columns ---")

        # SQLite doesn't support DROP COLUMN, so we need to recreate tables
        # This is safe because we have a backup

        # 1. Create new meal_plans table
        print("Recreating meal_plans table without date columns...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meal_plans_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT FALSE,
                people_count INTEGER,
                dietary_restrictions TEXT,
                description TEXT,
                budget_target REAL,
                calories_per_day_target INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Copy data (excluding start_date, end_date)
        cursor.execute('''
            INSERT INTO meal_plans_new (id, name, is_active, people_count, dietary_restrictions,
                                       description, budget_target, calories_per_day_target,
                                       created_at, updated_at)
            SELECT id, name, is_active, people_count, dietary_restrictions,
                   description, budget_target, calories_per_day_target,
                   created_at, updated_at
            FROM meal_plans
        ''')

        # Drop old table and rename new one
        cursor.execute("DROP TABLE meal_plans")
        cursor.execute("ALTER TABLE meal_plans_new RENAME TO meal_plans")
        print("✓ meal_plans table recreated")

        # 2. Create new meals table
        print("Recreating meals table without meal_date column...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meals_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_plan_id INTEGER,
                recipe_id INTEGER,
                meal_type TEXT,
                day_number INTEGER,
                servings_override INTEGER,
                notes TEXT,
                FOREIGN KEY (meal_plan_id) REFERENCES meal_plans (id),
                FOREIGN KEY (recipe_id) REFERENCES recipes (id)
            )
        ''')

        # Copy data (excluding meal_date)
        cursor.execute('''
            INSERT INTO meals_new (id, meal_plan_id, recipe_id, meal_type, day_number,
                                  servings_override, notes)
            SELECT id, meal_plan_id, recipe_id, meal_type, day_number,
                   servings_override, notes
            FROM meals
        ''')

        # Drop old table and rename new one
        cursor.execute("DROP TABLE meals")
        cursor.execute("ALTER TABLE meals_new RENAME TO meals")
        print("✓ meals table recreated")

        conn.commit()

        print("\n--- Migration Complete ---")
        print(f"✓ All date fields removed")
        print(f"✓ is_active field added to meal_plans")
        print(f"✓ day_number field added to meals")
        print(f"✓ All existing data preserved")
        print(f"\nBackup saved to: {backup_path}")
        print("\nMigration successful!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Database was backed up before migration started.")
        print(f"Restore from backup: {backup_path}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("KitchenSage: Dateless Meal Plans Migration")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Backup your database")
    print("  2. Add is_active column to meal_plans")
    print("  3. Add day_number column to meals")
    print("  4. Calculate day_number from existing dates")
    print("  5. Remove all date columns")
    print("\n⚠️  This operation modifies your database schema.")
    print("    A backup will be created automatically.\n")

    # Check for --yes or -y flag for non-interactive mode
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    if auto_confirm:
        print("Auto-confirming migration (--yes flag provided)")
        migrate_database()
    else:
        response = input("Continue with migration? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            migrate_database()
        else:
            print("Migration cancelled.")
