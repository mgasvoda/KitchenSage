"""
Recipe Manager Agent - Handles database operations and recipe management.
"""

from crewai import Agent
from langchain_openai import ChatOpenAI
from typing import List
from src.tools.database_tools import DatabaseTool
from src.tools.recipe_tools import RecipeValidatorTool, RecipeSearchTool


class RecipeManagerAgent:
    """
    Agent responsible for managing recipe data in the database.
    
    This agent handles:
    - Storing and retrieving recipes
    - Validating recipe data
    - Searching recipes by various criteria
    - Managing recipe metadata
    """
    
    def __init__(self):
        """Initialize the Recipe Manager agent with necessary tools."""
        self.tools = [
            DatabaseTool(),
            RecipeValidatorTool(),
            RecipeSearchTool()
        ]
        
        self.agent = Agent(
            role="Recipe Database Manager",
            goal="Efficiently store, retrieve, and organize recipe data in the database",
            backstory="""You are an expert data manager with deep knowledge of recipe 
            structures and database operations. You ensure that all recipe data is 
            properly validated, stored, and easily retrievable. You have years of 
            experience in culinary data management and understand the nuances of 
            recipe formatting, ingredient standardization, and nutritional data.""",
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4", temperature=0.1)
        ) 