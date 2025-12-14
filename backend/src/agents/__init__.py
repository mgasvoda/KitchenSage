"""
KitchenCrew Agents

This module contains all the specialized agents for the KitchenCrew AI cooking assistant:
- RecipeManagerAgent: Handles recipe database operations and management
- MealPlannerAgent: Creates and optimizes meal plans with nutritional analysis
- GroceryListAgent: Generates and optimizes grocery shopping lists
- RecipeScoutAgent: Discovers and validates recipes from external sources
"""

from .recipe_manager import RecipeManagerAgent
from .meal_planner import MealPlannerAgent
from .grocery_list import GroceryListAgent
from .recipe_scout import RecipeScoutAgent
from .orchestrator import OrchestratorAgent

__all__ = [
    "RecipeManagerAgent",
    "MealPlannerAgent", 
    "GroceryListAgent",
    "RecipeScoutAgent",
    "OrchestratorAgent"
]


def get_all_agents():
    """Get instances of all KitchenCrew agents."""
    return {
        'recipe_manager': RecipeManagerAgent(),
        'meal_planner': MealPlannerAgent(),
        'grocery_list': GroceryListAgent(),
        'recipe_scout': RecipeScoutAgent()
    }


def get_core_agents():
    """Get instances of core agents (recipe manager, meal planner, grocery list)."""
    return {
        'recipe_manager': RecipeManagerAgent(),
        'meal_planner': MealPlannerAgent(),
        'grocery_list': GroceryListAgent()
    }


def get_recipe_agents():
    """Get agents related to recipe management."""
    return {
        'recipe_manager': RecipeManagerAgent(),
        'recipe_scout': RecipeScoutAgent()
    } 