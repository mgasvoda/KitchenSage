"""
Grocery list task definitions for CrewAI agents.
"""

from crewai import Task
from typing import List, Dict, Any, Optional


class GroceryTasks:
    """Task definitions for grocery list operations."""
    
    def extract_ingredients_task(self, meal_plan_id: int) -> Task:
        """
        Task to extract all ingredients from a meal plan.
        
        Args:
            meal_plan_id: ID of the meal plan to extract ingredients from
            
        Returns:
            CrewAI Task object
        """
        return Task(
            description=f"""
            Extract all ingredients from meal plan ID {meal_plan_id}:
            
            1. Retrieve all recipes associated with the meal plan
            2. Extract ingredients from each recipe
            3. Consolidate duplicate ingredients
            4. Calculate total quantities needed
            5. Account for the number of people and servings
            6. Consider any existing inventory to subtract
            
            Return a comprehensive list of ingredients with quantities needed for shopping.
            """,
            expected_output="Consolidated list of ingredients with quantities, units, and categories",
            async_execution=False,
            context=[]  # Explicitly set context to empty list to prevent _NotSpecified error
        )
    
    def optimize_grocery_list_task(self) -> Task:
        """
        Task to optimize the grocery list for efficient shopping.
        
        Returns:
            CrewAI Task object
        """
        return Task(
            description="""
            Optimize the extracted grocery list for efficient shopping:
            
            1. Group ingredients by store sections (produce, dairy, meat, etc.)
            2. Suggest bulk purchasing opportunities for cost savings
            3. Identify ingredient substitutions if items are unavailable
            4. Calculate estimated costs based on average prices
            5. Suggest optimal shopping route through store
            6. Flag seasonal items that might be expensive or unavailable
            7. Recommend store brands vs name brands for cost optimization
            
            Return an optimized grocery list with cost estimates and shopping strategy.
            """,
            expected_output="Optimized grocery list organized by store sections with cost estimates and shopping tips",
            async_execution=False,
            context=[]  # Explicitly set context to empty list to prevent _NotSpecified error
        ) 