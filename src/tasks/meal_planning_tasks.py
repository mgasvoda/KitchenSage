"""
Meal planning task definitions for CrewAI agents.
"""

from crewai import Task
from typing import List, Dict, Any, Optional


class MealPlanningTasks:
    """Task definitions for meal planning operations."""
    
    def create_meal_plan_task(self,
                             days: int = 7,
                             people: int = 2,
                             dietary_restrictions: Optional[List[str]] = None,
                             budget: Optional[float] = None) -> Task:
        """
        Task to create a comprehensive meal plan.
        
        Args:
            days: Number of days for the meal plan
            people: Number of people the plan should serve
            dietary_restrictions: List of dietary restrictions
            budget: Optional budget constraint
            
        Returns:
            CrewAI Task object
        """
        restrictions_text = ", ".join(dietary_restrictions) if dietary_restrictions else "None"
        budget_text = f"${budget:.2f}" if budget else "No budget limit"
        
        return Task(
            description=f"""
            Create a {days}-day meal plan for {people} people with the following requirements:
            - Dietary restrictions: {restrictions_text}
            - Budget constraint: {budget_text}
            
            The meal plan should include:
            1. Breakfast, lunch, and dinner for each day
            2. Nutritionally balanced meals across the period
            3. Variety in cuisines and ingredients
            4. Consideration of preparation time and complexity
            5. Seasonal ingredient preferences
            6. Cost optimization within budget constraints
            
            Ensure meals complement each other and ingredients can be efficiently used
            across multiple recipes to minimize waste.
            """,
            expected_output="Complete meal plan with recipes assigned to each meal, nutritional summary, and cost estimate",
            async_execution=False
        )
    
    def rank_recipe_suggestions_task(self) -> Task:
        """
        Task to rank recipe suggestions based on various criteria.
        
        Returns:
            CrewAI Task object
        """
        return Task(
            description="""
            Rank the provided recipe suggestions based on multiple criteria:
            
            1. Ingredient availability and usage efficiency
            2. Nutritional balance and health benefits
            3. Preparation complexity and time requirements
            4. Cost effectiveness
            5. Variety and flavor profile diversity
            6. Seasonal appropriateness
            7. User preference alignment (if available)
            
            Provide a scored ranking with explanations for each recommendation.
            Consider how recipes work together as a cohesive meal plan.
            """,
            expected_output="Ranked list of recipe suggestions with scores and explanations",
            async_execution=False
        ) 