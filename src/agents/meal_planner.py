"""
Meal Planner Agent - Handles meal planning and nutritional analysis.
"""

import os
from crewai import Agent
from src.tools.meal_planning_tools import MealPlanningTool, NutritionAnalysisTool, CalendarTool
from src.tools.database_tools import RecipeSearchTool


class MealPlannerAgent:
    """
    Agent responsible for creating optimal meal plans.
    
    This agent handles:
    - Creating balanced meal plans
    - Nutritional analysis and optimization
    - Scheduling meals across time periods
    - Considering dietary restrictions and preferences
    """
    
    def __init__(self):
        """Initialize the Meal Planner agent with necessary tools."""
        self.tools = [
            MealPlanningTool(),
            NutritionAnalysisTool(),
            CalendarTool(),
            RecipeSearchTool()
        ]
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key.startswith('sk-placeholder'):
            print("Warning: OpenAI API key not available - meal planner will use basic functionality only")
            llm_config = {}
        else:
            from langchain_openai import ChatOpenAI
            llm_config = {"llm": ChatOpenAI(model="gpt-4", temperature=0.3)}
        
        self.agent = Agent(
            role="Certified Nutritionist and Meal Planning Expert",
            goal="Create optimal meal plans based on nutritional needs, preferences, and constraints",
            backstory="""You are a certified nutritionist and meal planning expert with 
            extensive knowledge of dietary requirements, nutritional balance, and meal 
            optimization. You understand how to create varied, healthy, and appealing 
            meal plans that meet specific dietary restrictions, budget constraints, and 
            time limitations. Your expertise includes macro and micronutrient balance, 
            portion control, and seasonal ingredient planning.""",
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
            **llm_config
        ) 