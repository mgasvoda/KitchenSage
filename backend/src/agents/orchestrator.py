"""
Orchestrator Agent - Handles natural language processing and task routing.
"""

import os
from crewai import Agent
from typing import List, Optional, Dict, Any
from src.tools.web_tools import WebSearchTool


class OrchestratorAgent:
    """
    Agent responsible for understanding user queries and orchestrating appropriate responses.
    
    This agent handles:
    - Natural language understanding of user requests
    - Extracting intent and parameters from user input
    - Determining which agents and tasks are needed
    - Gathering additional information when needed
    - Routing requests to appropriate specialized agents
    """
    
    def __init__(self):
        """Initialize the Orchestrator agent with necessary tools."""
        # Tools for gathering additional information when needed
        self.tools = [
            WebSearchTool()  # For when we need to clarify cooking terms or ingredients
        ]
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key.startswith('sk-placeholder'):
            print("Warning: OpenAI API key not available - agent will use basic functionality only")
            llm_config = {}
        else:
            from langchain_openai import ChatOpenAI
            llm_config = {"llm": ChatOpenAI(model="gpt-4.1-mini", temperature=0.1)}
        
        self.agent = Agent(
            role="KitchenCrew Query Orchestrator",
            goal="Understand user cooking requests and coordinate the appropriate AI agents to fulfill them",
            backstory="""You are an expert culinary assistant and project manager with deep 
            knowledge of cooking, recipes, meal planning, and grocery shopping. You excel at 
            understanding what people want when they ask cooking-related questions, even when 
            they're not perfectly clear. You know how to break down complex requests into 
            actionable tasks and coordinate multiple specialists to get the best results.
            
            You have experience with:
            - Recipe discovery and management
            - Meal planning for various dietary needs and constraints
            - Grocery shopping optimization
            - Understanding cooking terminology and techniques
            - Clarifying ambiguous requests through intelligent questioning
            
            Your role is to be the intelligent interface between users and the specialized 
            cooking agents, ensuring every request is properly understood and routed to 
            the right experts.""",
            tools=self.tools,
            verbose=True,
            allow_delegation=True,  # This agent can delegate to other agents
            **llm_config
        ) 