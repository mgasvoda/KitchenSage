"""
Recipe Scout Agent - Discovers and retrieves recipes from external sources.
"""

import os
from crewai import Agent
from src.tools.web_tools import WebSearchTool, WebScrapingTool, RecipeAPITool, ContentFilterTool


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
            WebSearchTool(),
            WebScrapingTool(),
            RecipeAPITool(),
            ContentFilterTool()
        ]
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key.startswith('sk-placeholder'):
            print("Warning: OpenAI API key not available - recipe scout will use basic functionality only")
            llm_config = {}
        else:
            from langchain_openai import ChatOpenAI
            llm_config = {"llm": ChatOpenAI(model="gpt-4.1-mini", temperature=0.4)}
        
        self.agent = Agent(
            role="Culinary Researcher and Recipe Discovery Specialist",
            goal="Find and retrieve relevant recipes from various external sources including web search, APIs, and cooking websites, always respecting the user's specific search terms and preferences",
            backstory="""You are a culinary researcher with access to global recipe 
            databases, cooking websites, and food blogs. You have an eye for quality 
            recipes and can quickly identify reliable sources. Your expertise includes 
            understanding different cuisine traditions, seasonal ingredients, and trending 
            food movements. You excel at finding recipes that match specific criteria 
            while ensuring they come from trustworthy sources. 
            
            IMPORTANT: You always pay close attention to the user's exact search terms 
            and preferences. When a user asks for a specific ingredient or dish (like 
            "pork tenderloin recipe"), you prioritize finding recipes that feature that 
            exact ingredient or dish prominently. You never ignore the user's specific 
            request in favor of generic searches. You use web search tools to discover 
            the latest and most popular recipes online that match the user's exact needs.""",
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
            **llm_config
        ) 