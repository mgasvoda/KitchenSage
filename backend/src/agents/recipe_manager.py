"""
Recipe Manager Agent - Handles database operations and recipe management.
"""

import os
from crewai import Agent
from typing import List, Optional
from src.config import settings, is_reasoning_model


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
        # Simplified version without database tools for now
        self.tools = []
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key.startswith('sk-placeholder'):
            print("Warning: OpenAI API key not available - agent will use basic functionality only")
            llm_config = {}
        else:
            from langchain_openai import ChatOpenAI
            model = settings.llm.recipe_manager_model
            llm_params = {"model": model}
            # Reasoning models don't support temperature or stop parameters
            if is_reasoning_model(model):
                llm_params["disabled_params"] = {"stop": None}
            else:
                llm_params["temperature"] = settings.llm.recipe_manager_temperature
            llm_config = {"llm": ChatOpenAI(**llm_params)}
        
        self.agent = Agent(
            role="Recipe Database Manager",
            goal="Efficiently store, retrieve, and organize recipe data in the database",
            backstory="""You are an expert data manager with deep knowledge of recipe 
            structures and database operations. You ensure that all recipe data is 
            properly validated, stored, and easily retrievable. You have years of 
            experience in culinary data management and understand the nuances of
            recipe formatting, ingredient standardization, and nutritional data.""",
            tools=self.tools,
            verbose=settings.llm.agent_verbose,
            allow_delegation=False,
            **llm_config
        ) 