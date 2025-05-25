"""
Recipe discovery task definitions for CrewAI agents.
"""

from crewai import Task
from typing import List, Dict, Any, Optional


class DiscoveryTasks:
    """Task definitions for recipe discovery operations."""
    
    def search_recipes_task(self,
                           cuisine: Optional[str] = None,
                           dietary_restrictions: Optional[List[str]] = None,
                           ingredients: Optional[List[str]] = None,
                           max_prep_time: Optional[int] = None,
                           agent=None) -> Task:
        """
        Task to search for recipes from external sources.
        
        Args:
            cuisine: Type of cuisine to search for
            dietary_restrictions: List of dietary restrictions
            ingredients: Available ingredients to use
            max_prep_time: Maximum preparation time in minutes
            agent: The agent to assign this task to
            
        Returns:
            CrewAI Task object
        """
        criteria = []
        search_query_parts = []
        
        if cuisine:
            criteria.append(f"Cuisine: {cuisine}")
            search_query_parts.append(cuisine)
        if dietary_restrictions:
            criteria.append(f"Dietary restrictions: {', '.join(dietary_restrictions)}")
            search_query_parts.extend(dietary_restrictions)
        if ingredients:
            criteria.append(f"Must use ingredients: {', '.join(ingredients)}")
            search_query_parts.extend(ingredients)
        if max_prep_time:
            criteria.append(f"Maximum prep time: {max_prep_time} minutes")
            if max_prep_time <= 30:
                search_query_parts.append("quick")
        
        criteria_text = "\n".join(criteria) if criteria else "No specific criteria"
        
        # Build search query for web search
        search_query = " ".join(search_query_parts + ["recipes"])
        if not search_query_parts:
            search_query = "healthy dinner recipes"
        
        task = Task(
            description=f"""
            Search for recipes from external sources with the following criteria:
            {criteria_text}
            
            Use the following approach:
            1. Start with a web search using query: "{search_query}"
            2. Use the Web Search Tool to find relevant recipes online
            3. If needed, use Recipe API Tool to get additional recipes from recipe databases
            4. Filter and validate the results using Content Filter Tool
            5. Ensure recipe quality and completeness
            6. Gather at least 5-10 relevant recipes
            7. Include recipe metadata (prep time, difficulty, ratings, nutrition)
            
            Focus on finding recipes that are:
            - Complete with ingredients and instructions
            - From reliable sources
            - Match the specified criteria
            - Have good ratings or reviews when available
            
            Return a comprehensive list of recipes that match the search criteria.
            """,
            expected_output="List of 5-10 recipes with complete information including ingredients, instructions, prep time, and source metadata",
            async_execution=False
        )
        
        # Assign agent if provided
        if agent:
            task.agent = agent
            
        return task
    
    def web_search_recipes_task(self, search_query: str, max_results: int = 10, agent=None) -> Task:
        """
        Task specifically for web searching recipes.
        
        Args:
            search_query: The search query to use
            max_results: Maximum number of results to return
            agent: The agent to assign this task to
            
        Returns:
            CrewAI Task object
        """
        task = Task(
            description=f"""
            Perform a web search for recipes using the query: "{search_query}"
            
            Steps to follow:
            1. Use the Web Search Tool with the provided query
            2. Analyze the search results for recipe quality and relevance
            3. Extract key information from each recipe found
            4. Ensure recipes have complete ingredients and instructions
            5. Include source information and ratings when available
            6. Return up to {max_results} of the best matching recipes
            
            Focus on finding recipes that are:
            - Complete and well-structured
            - From reputable cooking websites
            - Have clear instructions and ingredient lists
            - Include timing and serving information
            """,
            expected_output=f"List of up to {max_results} recipes with complete details from web search",
            async_execution=False
        )
        
        # Assign agent if provided
        if agent:
            task.agent = agent
            
        return task 