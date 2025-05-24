"""
Recipe Scout Agent - Discovers and retrieves recipes from external sources.
"""

import os
from crewai import Agent
from src.tools.web_tools import WebScrapingTool, RecipeAPITool, ContentFilterTool
from src.tools.database_tools import DatabaseTool, RecipeValidatorTool


class RecipeScoutAgent:
    """
    Agent responsible for discovering new recipes from various sources.
    
    This agent handles:
    - Searching external recipe databases and APIs
    - Web scraping from cooking websites
    - Filtering and validating external content
    - Discovering trending and seasonal recipes
    """
    
    def __init__(self):
        """Initialize the Recipe Scout agent with necessary tools."""
        self.tools = [
            WebScrapingTool(),
            RecipeAPITool(),
            ContentFilterTool(),
            DatabaseTool(),
            RecipeValidatorTool()
        ]
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key.startswith('sk-placeholder'):
            print("Warning: OpenAI API key not available - recipe scout will use basic functionality only")
            llm_config = {}
        else:
            from langchain_openai import ChatOpenAI
            llm_config = {"llm": ChatOpenAI(model="gpt-4", temperature=0.4)}
        
        self.agent = Agent(
            role="Culinary Researcher and Recipe Discovery Specialist",
            goal="Find and retrieve relevant recipes from various external sources",
            backstory="""You are a culinary researcher with access to global recipe 
            databases, cooking websites, and food blogs. You have an eye for quality 
            recipes and can quickly identify reliable sources. Your expertise includes 
            understanding different cuisine traditions, seasonal ingredients, and trending 
            food movements. You excel at finding recipes that match specific criteria 
            while ensuring they come from trustworthy sources.""",
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
            **llm_config
        ) 