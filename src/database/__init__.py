"""
Database operations package for KitchenCrew.

This package contains all database-related functionality including:
- Connection management
- Repository pattern implementations
- CRUD operations for all entities
- Data mapping between models and database
"""

from .connection import (
    get_db_connection,
    get_db_session,
    check_database_exists,
    initialize_database,
    DatabaseError,
    RecordNotFoundError,
    ValidationError
)

from .base_repository import BaseRepository

from .recipe_repository import (
    RecipeRepository,
    IngredientRepository
)

from .meal_plan_repository import MealPlanRepository

from .grocery_repository import GroceryRepository

__all__ = [
    # Connection utilities
    "get_db_connection",
    "get_db_session", 
    "check_database_exists",
    "initialize_database",
    
    # Exceptions
    "DatabaseError",
    "RecordNotFoundError",
    "ValidationError",
    
    # Base repository
    "BaseRepository",
    
    # Repository classes
    "RecipeRepository",
    "IngredientRepository",
    "MealPlanRepository",
    "GroceryRepository",
]


# Convenience function to get all repositories
def get_repositories():
    """
    Get instances of all repository classes.
    
    Returns:
        Dictionary with repository instances
    """
    return {
        'recipes': RecipeRepository(),
        'ingredients': IngredientRepository(),
        'meal_plans': MealPlanRepository(),
        'grocery_lists': GroceryRepository(),
    } 