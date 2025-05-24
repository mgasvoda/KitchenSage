"""
Custom tools for KitchenCrew agents.

This module contains all the tools used by the KitchenCrew agents for:
- Database operations
- Recipe management and validation
- Meal planning and nutrition analysis
- Grocery list generation and optimization
- External data integration
"""

from .database_tools import DatabaseTool, RecipeValidatorTool, RecipeSearchTool
from .meal_planning_tools import MealPlanningTool, NutritionAnalysisTool, CalendarTool
from .grocery_tools import InventoryTool, PriceComparisonTool, ListOptimizationTool
from .web_tools import WebScrapingTool, RecipeAPITool, ContentFilterTool

__all__ = [
    # Database and recipe tools
    "DatabaseTool",
    "RecipeValidatorTool", 
    "RecipeSearchTool",
    
    # Meal planning tools
    "MealPlanningTool",
    "NutritionAnalysisTool",
    "CalendarTool",
    
    # Grocery and shopping tools
    "InventoryTool",
    "PriceComparisonTool",
    "ListOptimizationTool",
    
    # External integration tools
    "WebScrapingTool",
    "RecipeAPITool",
    "ContentFilterTool",
]


def get_recipe_tools():
    """Get all tools related to recipe management."""
    return [
        DatabaseTool(),
        RecipeValidatorTool(),
        RecipeSearchTool()
    ]


def get_meal_planning_tools():
    """Get all tools related to meal planning."""
    return [
        MealPlanningTool(),
        NutritionAnalysisTool(),
        CalendarTool()
    ]


def get_grocery_tools():
    """Get all tools related to grocery shopping."""
    return [
        InventoryTool(),
        PriceComparisonTool(),
        ListOptimizationTool()
    ]


def get_web_tools():
    """Get all tools related to external data sources."""
    return [
        WebScrapingTool(),
        RecipeAPITool(),
        ContentFilterTool()
    ]


def get_all_tools():
    """Get all available tools for KitchenCrew agents."""
    return (
        get_recipe_tools() +
        get_meal_planning_tools() +
        get_grocery_tools() +
        get_web_tools()
    ) 