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
                           max_prep_time: Optional[int] = None) -> Task:
        """
        Task to search for recipes from external sources.
        
        Args:
            cuisine: Type of cuisine to search for
            dietary_restrictions: List of dietary restrictions
            ingredients: Available ingredients to use
            max_prep_time: Maximum preparation time in minutes
            
        Returns:
            CrewAI Task object
        """
        criteria = []
        if cuisine:
            criteria.append(f"Cuisine: {cuisine}")
        if dietary_restrictions:
            criteria.append(f"Dietary restrictions: {', '.join(dietary_restrictions)}")
        if ingredients:
            criteria.append(f"Must use ingredients: {', '.join(ingredients)}")
        if max_prep_time:
            criteria.append(f"Maximum prep time: {max_prep_time} minutes")
        
        criteria_text = "\n".join(criteria) if criteria else "No specific criteria"
        
        return Task(
            description=f"""
            Search for recipes from external sources with the following criteria:
            {criteria_text}
            
            Your search should:
            1. Query multiple recipe APIs and databases
            2. Scrape relevant cooking websites if needed
            3. Filter results based on the specified criteria
            4. Ensure recipe quality and completeness
            5. Gather at least 10-20 relevant recipes
            6. Include recipe metadata (prep time, difficulty, ratings)
            
            Return a comprehensive list of recipes that match the search criteria.
            """,
            expected_output="List of recipes with complete information including ingredients, instructions, and metadata",
            async_execution=False
        ) 