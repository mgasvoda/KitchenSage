"""
Grocery List Agent - Generates and optimizes grocery shopping lists.
"""

import os
from crewai import Agent
from src.tools.grocery_tools import InventoryTool, PriceComparisonTool, ListOptimizationTool


class GroceryListAgent:
    """
    Agent responsible for generating optimized grocery lists.
    
    This agent handles:
    - Extracting ingredients from meal plans
    - Consolidating and optimizing quantities
    - Price comparison and cost optimization
    - Store location and availability checking
    """
    
    def __init__(self):
        """Initialize the Grocery List agent with necessary tools."""
        self.tools = [
            InventoryTool(),
            PriceComparisonTool(),
            ListOptimizationTool()
        ]
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key.startswith('sk-placeholder'):
            print("Warning: OpenAI API key not available - grocery list agent will use basic functionality only")
            llm_config = {}
        else:
            from langchain_openai import ChatOpenAI
            llm_config = {"llm": ChatOpenAI(model="gpt-4", temperature=0.2)}
        
        self.agent = Agent(
            role="Supply Chain Specialist and Shopping Optimization Expert",
            goal="Generate efficient and cost-optimized grocery lists from meal plans",
            backstory="""You are a supply chain specialist with deep knowledge of grocery 
            shopping patterns, seasonal availability, and cost optimization strategies. 
            You understand how to consolidate ingredients efficiently, find the best 
            prices across different stores, and organize shopping lists for maximum 
            efficiency. Your expertise includes inventory management, bulk purchasing 
            strategies, and understanding ingredient substitutions for cost savings.""",
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
            **llm_config
        ) 