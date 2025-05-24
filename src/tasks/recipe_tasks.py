"""
Recipe-related task definitions for CrewAI agents.
"""

from crewai import Task
from typing import List, Dict, Any, Optional


class RecipeTasks:
    """Task definitions for recipe management operations."""
    
    def add_recipe_task(self, recipe_data: Dict[str, Any]) -> Task:
        """
        Task to add a new recipe to the database.
        
        Args:
            recipe_data: Dictionary containing recipe information
            
        Returns:
            CrewAI Task object
        """
        return Task(
            description=f"""
            Add the following recipe to the database:
            {recipe_data}
            
            Ensure the recipe data is properly validated, including:
            - Required fields are present (name, ingredients, instructions)
            - Ingredients have proper units and quantities
            - Instructions are clear and properly formatted
            - Nutritional information is calculated if missing
            - Dietary tags are assigned based on ingredients
            
            Store the recipe in the database and return the assigned recipe ID.
            """,
            expected_output="Recipe ID and confirmation of successful storage",
            async_execution=False
        )
    
    def validate_and_store_recipes_task(self) -> Task:
        """
        Task to validate and store recipes from external sources.
        
        Returns:
            CrewAI Task object
        """
        return Task(
            description="""
            Take the recipes found by the Recipe Scout and validate them before storage:
            
            1. Validate recipe format and completeness
            2. Standardize ingredient names and units
            3. Calculate nutritional information where missing
            4. Assign appropriate dietary tags
            5. Check for duplicates in the database
            6. Store valid, unique recipes
            
            Return a summary of recipes processed, stored, and any validation issues.
            """,
            expected_output="Summary of validated and stored recipes with any issues noted",
            async_execution=False
        )
    
    def fetch_recipes_for_plan_task(self) -> Task:
        """
        Task to fetch recipes that match meal plan requirements.
        
        Returns:
            CrewAI Task object
        """
        return Task(
            description="""
            Retrieve recipes from the database that match the meal plan requirements:
            
            1. Consider dietary restrictions and preferences
            2. Match cuisine preferences if specified
            3. Ensure variety across the meal plan period
            4. Consider preparation time constraints
            5. Balance nutritional requirements
            6. Account for ingredient availability and seasonality
            
            Return a curated list of recipes suitable for the meal plan.
            """,
            expected_output="List of recipes with nutritional information and suitability scores",
            async_execution=False
        )
    
    def find_recipes_by_ingredients_task(self, available_ingredients: List[str]) -> Task:
        """
        Task to find recipes based on available ingredients.
        
        Args:
            available_ingredients: List of ingredients currently available
            
        Returns:
            CrewAI Task object
        """
        return Task(
            description=f"""
            Find recipes that can be made with the available ingredients:
            Available ingredients: {', '.join(available_ingredients)}
            
            1. Search for recipes that use these ingredients
            2. Prioritize recipes that use most of the available ingredients
            3. Consider recipes that need only 1-2 additional ingredients
            4. Rank recipes by ingredient match percentage
            5. Include recipe difficulty and preparation time
            
            Return ranked list of suitable recipes with ingredient match analysis.
            """,
            expected_output="Ranked list of recipes with ingredient match percentages and analysis",
            async_execution=False
        ) 