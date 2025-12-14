"""
Main KitchenCrew class that orchestrates all cooking-related AI agents.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
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
        
        # Debug logging
        self.logger.debug(f"Parameters received: cuisine={cuisine}, dietary_restrictions={dietary_restrictions}, "
                         f"ingredients={ingredients}, max_prep_time={max_prep_time}, original_query={original_query}")
        
        try:
            # Create the search task with proper agent assignment
            search_task = self.discovery_tasks.search_recipes_task(
                cuisine=cuisine,
                dietary_restrictions=dietary_restrictions,
                ingredients=ingredients,
                max_prep_time=max_prep_time,
                original_query=original_query,
                agent=self.recipe_scout.agent
            )
            
            self.logger.debug("Search task created successfully")
            
            # Create the validation task with proper agent assignment
            validation_task = self.recipe_tasks.validate_and_store_recipes_task()
            validation_task.agent = self.recipe_manager.agent
            
            self.logger.debug("Validation task created successfully")
            
            # Create discovery crew
            discovery_crew = Crew(
                agents=[self.recipe_scout.agent, self.recipe_manager.agent],
                tasks=[search_task, validation_task],
                process=Process.sequential,
                verbose=True
            )
            
            self.logger.debug("Discovery crew created successfully")
            
            result = discovery_crew.kickoff()
            return result
            
        except Exception as e:
            self.logger.error(f"Error in find_recipes: {e}")
            self.logger.error(f"Error type: {type(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
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
    
    def create_meal_plan_with_callbacks(
        self,
        days: int = 7,
        people: int = 2,
        dietary_restrictions: Optional[List[str]] = None,
        budget: Optional[float] = None,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Create a meal plan with real-time callbacks for agent activity.
        
        Args:
            days: Number of days for the meal plan
            people: Number of people the plan should serve
            dietary_restrictions: List of dietary restrictions
            budget: Optional budget constraint
            event_callback: Callback function to receive agent activity events
            
        Returns:
            Dictionary containing the meal plan
        """
        self.logger.info(f"Creating meal plan with callbacks for {days} days, {people} people")
        
        def step_callback(step_output):
            """Callback for each agent step."""
            if event_callback is None:
                return
            
            try:
                # Get the class name to understand what type of output this is
                class_name = type(step_output).__name__
                
                # Handle different CrewAI output types
                if class_name == 'AgentFinish':
                    # Agent finished thinking - extract the output
                    output = getattr(step_output, 'output', None) or getattr(step_output, 'return_values', {})
                    if isinstance(output, dict):
                        output_text = output.get('output', str(output))
                    else:
                        output_text = str(output) if output else "Processing complete"
                    # Clean up the output for display
                    output_text = output_text[:150] if len(str(output_text)) > 150 else str(output_text)
                    event_callback({
                        "type": "agent_thinking",
                        "agent": "Meal Planning Expert",
                        "content": f"Completed analysis: {output_text}",
                    })
                    
                elif class_name == 'ToolResult' or hasattr(step_output, 'result'):
                    # Tool returned a result
                    result = getattr(step_output, 'result', str(step_output))
                    tool_name = getattr(step_output, 'tool', 'Tool')
                    # Parse result if it's a string that looks like JSON
                    if isinstance(result, str):
                        try:
                            import json
                            parsed = json.loads(result.replace("'", '"'))
                            if parsed.get('status') == 'success':
                                summary = parsed.get('message', 'Completed successfully')
                            else:
                                summary = parsed.get('message', result[:100])
                        except:
                            summary = result[:100] if len(result) > 100 else result
                    else:
                        summary = str(result)[:100]
                    event_callback({
                        "type": "tool_result",
                        "tool": tool_name,
                        "summary": summary,
                    })
                    
                elif hasattr(step_output, 'tool') and step_output.tool:
                    # Tool is being invoked
                    tool_input = getattr(step_output, 'tool_input', '')
                    if isinstance(tool_input, dict):
                        # Extract meaningful info from the tool input
                        input_summary = ', '.join([f"{k}: {str(v)[:30]}" for k, v in list(tool_input.items())[:3]])
                    else:
                        input_summary = str(tool_input)[:80]
                    event_callback({
                        "type": "tool_start",
                        "agent": "Meal Planning Expert",
                        "tool": step_output.tool,
                        "input_summary": input_summary,
                    })
                    
                elif hasattr(step_output, 'log') or hasattr(step_output, 'thought'):
                    # Agent is thinking
                    thought = getattr(step_output, 'log', None) or getattr(step_output, 'thought', '')
                    if thought:
                        # Clean up thought for display
                        thought_clean = str(thought).strip()[:150]
                        event_callback({
                            "type": "agent_thinking",
                            "agent": "Meal Planning Expert", 
                            "content": thought_clean,
                        })
                        
            except Exception as e:
                self.logger.error(f"Error in step callback: {e}")
        
        def task_callback(task_output):
            """Callback for task completion."""
            if event_callback is None:
                return
            
            try:
                # Get a meaningful task name
                task_desc = getattr(task_output, 'description', None)
                if task_desc:
                    # Extract first line or first 50 chars
                    task_name = task_desc.split('\n')[0][:50]
                else:
                    task_name = "Task"
                
                # Get a meaningful summary from the output
                raw_output = getattr(task_output, 'raw', None) or getattr(task_output, 'output', None)
                if raw_output:
                    # Get first meaningful line
                    lines = [l.strip() for l in str(raw_output).split('\n') if l.strip()]
                    summary = lines[0][:100] if lines else "Completed"
                else:
                    summary = "Completed successfully"
                
                event_callback({
                    "type": "task_complete",
                    "task": task_name,
                    "summary": summary,
                })
            except Exception as e:
                self.logger.error(f"Error in task callback: {e}")
        
        # Send initial planning events
        if event_callback:
            event_callback({
                "type": "agent_thinking",
                "agent": "Meal Planning Expert",
                "content": f"Analyzing requirements: {days} days, {people} people" + 
                          (f", restrictions: {', '.join(dietary_restrictions)}" if dietary_restrictions else ""),
            })
        
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
        
        if event_callback:
            event_callback({
                "type": "tool_start",
                "agent": "Meal Planning Expert",
                "tool": "Recipe Search Tool",
                "input_summary": "Searching for recipes matching criteria...",
            })
        
        # Create meal planning crew with callbacks
        planning_crew = Crew(
            agents=[self.meal_planner.agent, self.recipe_manager.agent],
            tasks=[meal_plan_task, recipe_fetch_task],
            process=Process.sequential,
            verbose=True,
            step_callback=step_callback,
            task_callback=task_callback,
        )
        
        result = planning_crew.kickoff()
        
        if event_callback:
            event_callback({
                "type": "task_complete",
                "task": "Meal Plan Generation",
                "summary": "Successfully created meal plan",
            })
        
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