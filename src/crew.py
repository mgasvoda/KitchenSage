"""
Main KitchenCrew class that orchestrates all cooking-related AI agents.
"""

import logging
from typing import List, Dict, Any, Optional
from crewai import Crew, Process
from src.agents.recipe_manager import RecipeManagerAgent
from src.agents.meal_planner import MealPlannerAgent
from src.agents.recipe_scout import RecipeScoutAgent
from src.agents.grocery_list import GroceryListAgent
from src.tasks.recipe_tasks import RecipeTasks
from src.tasks.meal_planning_tasks import MealPlanningTasks
from src.tasks.discovery_tasks import DiscoveryTasks
from src.tasks.grocery_tasks import GroceryTasks


class KitchenCrew:
    """
    Main orchestrator for the KitchenCrew AI cooking assistant system.
    
    This class manages multiple specialized agents to handle:
    - Recipe management and storage
    - Meal planning and nutrition
    - Recipe discovery from external sources
    - Grocery list generation and optimization
    """
    
    def __init__(self):
        """Initialize the KitchenCrew with all agents and tasks."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize agents
        self.recipe_manager = RecipeManagerAgent()
        self.meal_planner = MealPlannerAgent()
        self.recipe_scout = RecipeScoutAgent()
        self.grocery_list_agent = GroceryListAgent()
        
        # Initialize task managers
        self.recipe_tasks = RecipeTasks()
        self.meal_planning_tasks = MealPlanningTasks()
        self.discovery_tasks = DiscoveryTasks()
        self.grocery_tasks = GroceryTasks()
        
        self.logger.info("KitchenCrew initialized with all agents")
    
    def find_recipes(self, 
                    cuisine: Optional[str] = None,
                    dietary_restrictions: Optional[List[str]] = None,
                    ingredients: Optional[List[str]] = None,
                    max_prep_time: Optional[int] = None,
                    original_query: Optional[str] = None,
                    **kwargs) -> Dict[str, Any]:
        """
        Find recipes based on specified criteria.
        
        Args:
            cuisine: Type of cuisine (e.g., "italian", "mexican")
            dietary_restrictions: List of dietary restrictions
            ingredients: Available ingredients to use
            max_prep_time: Maximum preparation time in minutes
            original_query: Original user query for context
            
        Returns:
            Dictionary containing found recipes and metadata
        """
        self.logger.info(f"Finding recipes with criteria: cuisine={cuisine}, "
                        f"dietary_restrictions={dietary_restrictions}")
        
        # Create the search task with proper agent assignment
        search_task = self.discovery_tasks.search_recipes_task(
            cuisine=cuisine,
            dietary_restrictions=dietary_restrictions,
            ingredients=ingredients,
            max_prep_time=max_prep_time,
            original_query=original_query,
            agent=self.recipe_scout.agent
        )
        
        # Create the validation task with proper agent assignment
        validation_task = self.recipe_tasks.validate_and_store_recipes_task()
        validation_task.agent = self.recipe_manager.agent
        
        # Create discovery crew
        discovery_crew = Crew(
            agents=[self.recipe_scout.agent, self.recipe_manager.agent],
            tasks=[search_task, validation_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = discovery_crew.kickoff()
        return result
    
    def create_meal_plan(self,
                        days: int = 7,
                        people: int = 2,
                        dietary_restrictions: Optional[List[str]] = None,
                        budget: Optional[float] = None) -> Dict[str, Any]:
        """
        Create a meal plan for specified parameters.
        
        Args:
            days: Number of days for the meal plan
            people: Number of people the plan should serve
            dietary_restrictions: List of dietary restrictions
            budget: Optional budget constraint
            
        Returns:
            Dictionary containing the meal plan
        """
        self.logger.info(f"Creating meal plan for {days} days, {people} people")
        
        # Create meal planning task with proper agent assignment
        meal_plan_task = self.meal_planning_tasks.create_meal_plan_task(
            days=days,
            people=people,
            dietary_restrictions=dietary_restrictions,
            budget=budget
        )
        meal_plan_task.agent = self.meal_planner.agent
        
        # Create recipe fetching task with proper agent assignment
        recipe_fetch_task = self.recipe_tasks.fetch_recipes_for_plan_task()
        recipe_fetch_task.agent = self.recipe_manager.agent
        
        # Create meal planning crew
        planning_crew = Crew(
            agents=[self.meal_planner.agent, self.recipe_manager.agent],
            tasks=[meal_plan_task, recipe_fetch_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = planning_crew.kickoff()
        return result
    
    def generate_grocery_list(self, meal_plan_id: int) -> Dict[str, Any]:
        """
        Generate a grocery list from a meal plan.
        
        Args:
            meal_plan_id: ID of the meal plan to generate list from
            
        Returns:
            Dictionary containing the optimized grocery list
        """
        self.logger.info(f"Generating grocery list for meal plan {meal_plan_id}")
        
        # Create ingredient extraction task with proper agent assignment
        extract_task = self.grocery_tasks.extract_ingredients_task(meal_plan_id)
        extract_task.agent = self.recipe_manager.agent
        
        # Create grocery optimization task with proper agent assignment
        optimize_task = self.grocery_tasks.optimize_grocery_list_task()
        optimize_task.agent = self.grocery_list_agent.agent
        
        # Create grocery list crew
        grocery_crew = Crew(
            agents=[self.grocery_list_agent.agent, self.recipe_manager.agent],
            tasks=[extract_task, optimize_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = grocery_crew.kickoff()
        return result
    
    def add_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new recipe to the database.
        
        Args:
            recipe_data: Dictionary containing recipe information
            
        Returns:
            Dictionary with the result of the operation
        """
        self.logger.info(f"Adding new recipe: {recipe_data.get('name', 'Unknown')}")
        
        # Create recipe addition task with proper agent assignment
        add_task = self.recipe_tasks.add_recipe_task(recipe_data)
        add_task.agent = self.recipe_manager.agent
        
        # Create recipe addition crew
        addition_crew = Crew(
            agents=[self.recipe_manager.agent],
            tasks=[add_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = addition_crew.kickoff()
        return result
    
    def get_recipe_suggestions(self, available_ingredients: List[str]) -> Dict[str, Any]:
        """
        Get recipe suggestions based on available ingredients.
        
        Args:
            available_ingredients: List of ingredients currently available
            
        Returns:
            Dictionary containing suggested recipes
        """
        self.logger.info(f"Getting suggestions for ingredients: {available_ingredients}")
        
        # Create ingredient-based recipe search task with proper agent assignment
        search_task = self.recipe_tasks.find_recipes_by_ingredients_task(available_ingredients)
        search_task.agent = self.recipe_manager.agent
        
        # Create recipe ranking task with proper agent assignment
        ranking_task = self.meal_planning_tasks.rank_recipe_suggestions_task()
        ranking_task.agent = self.meal_planner.agent
        
        # Create suggestion crew
        suggestion_crew = Crew(
            agents=[self.recipe_manager.agent, self.meal_planner.agent],
            tasks=[search_task, ranking_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = suggestion_crew.kickoff()
        return result
    
    def search_stored_recipes(self, 
                             cuisine: Optional[str] = None,
                             dietary_restrictions: Optional[List[str]] = None,
                             ingredients: Optional[List[str]] = None,
                             max_prep_time: Optional[int] = None) -> Dict[str, Any]:
        """
        Search recipes that are already stored in the database.
        
        Args:
            cuisine: Type of cuisine (e.g., "italian", "mexican")
            dietary_restrictions: List of dietary restrictions
            ingredients: Available ingredients to use
            max_prep_time: Maximum preparation time in minutes
            
        Returns:
            Dictionary containing found recipes from database
        """
        self.logger.info(f"Searching stored recipes with criteria: cuisine={cuisine}, "
                        f"dietary_restrictions={dietary_restrictions}")
        
        # Create database search task with proper agent assignment
        search_task = self.recipe_tasks.search_stored_recipes_task(
            cuisine=cuisine,
            dietary_restrictions=dietary_restrictions,
            ingredients=ingredients,
            max_prep_time=max_prep_time
        )
        search_task.agent = self.recipe_manager.agent
        
        # Create database search crew (only recipe manager, no scout)
        search_crew = Crew(
            agents=[self.recipe_manager.agent],
            tasks=[search_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = search_crew.kickoff()
        return result
    
    def discover_new_recipes(self, 
                            cuisine: Optional[str] = None,
                            dietary_restrictions: Optional[List[str]] = None,
                            ingredients: Optional[List[str]] = None,
                            max_prep_time: Optional[int] = None,
                            original_query: Optional[str] = None,
                            **kwargs) -> Dict[str, Any]:
        """
        Discover new recipes from external sources and optionally store them.
        
        Args:
            cuisine: Type of cuisine (e.g., "italian", "mexican")
            dietary_restrictions: List of dietary restrictions
            ingredients: Available ingredients to use
            max_prep_time: Maximum preparation time in minutes
            original_query: Original user query for context
            
        Returns:
            Dictionary containing newly discovered recipes
        """
        self.logger.info(f"Discovering new recipes with criteria: cuisine={cuisine}, "
                        f"dietary_restrictions={dietary_restrictions}")
        
        # Create the search task with proper agent assignment
        search_task = self.discovery_tasks.search_recipes_task(
            cuisine=cuisine,
            dietary_restrictions=dietary_restrictions,
            ingredients=ingredients,
            max_prep_time=max_prep_time,
            original_query=original_query,
            agent=self.recipe_scout.agent
        )
        
        # Create the validation task with proper agent assignment
        validation_task = self.recipe_tasks.validate_and_store_recipes_task()
        validation_task.agent = self.recipe_manager.agent
        
        # Create discovery crew (scout + manager for validation/storage)
        discovery_crew = Crew(
            agents=[self.recipe_scout.agent, self.recipe_manager.agent],
            tasks=[search_task, validation_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = discovery_crew.kickoff()
        return result 