"""
Meal Plan service - business logic layer for meal plan operations.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator

from src.database import MealPlanRepository, DatabaseError, RecordNotFoundError
from src.crew import KitchenCrew

logger = logging.getLogger(__name__)


class MealPlanService:
    """
    Service layer for meal plan operations.
    
    Handles business logic and coordinates between API layer,
    database repositories, and AI agents.
    """
    
    def __init__(self):
        self._meal_plan_repo = None
        self._kitchen_crew = None
    
    @property
    def meal_plan_repo(self) -> MealPlanRepository:
        """Lazy initialization of meal plan repository."""
        if self._meal_plan_repo is None:
            self._meal_plan_repo = MealPlanRepository()
        return self._meal_plan_repo
    
    @property
    def kitchen_crew(self) -> KitchenCrew:
        """Lazy initialization of kitchen crew."""
        if self._kitchen_crew is None:
            self._kitchen_crew = KitchenCrew()
        return self._kitchen_crew
    
    def list_meal_plans(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List all meal plans.
        
        Args:
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Dictionary with meal plans and metadata
        """
        try:
            meal_plans = self.meal_plan_repo.get_all()
            
            # Convert to dictionaries
            plan_dicts = []
            for plan in meal_plans:
                if hasattr(plan, 'model_dump'):
                    plan_dicts.append(plan.model_dump())
                elif hasattr(plan, '__dict__'):
                    plan_dicts.append(plan.__dict__)
                else:
                    plan_dicts.append(dict(plan))
            
            return {
                "status": "success",
                "meal_plans": plan_dicts[offset:offset + limit],
                "total": len(plan_dicts),
                "limit": limit,
                "offset": offset,
            }
            
        except DatabaseError as e:
            logger.error(f"Database error listing meal plans: {e}")
            return {
                "status": "error",
                "message": str(e),
                "meal_plans": [],
            }
        except Exception as e:
            logger.error(f"Unexpected error listing meal plans: {e}")
            return {
                "status": "error",
                "message": "An unexpected error occurred",
                "meal_plans": [],
            }
    
    def get_meal_plan(self, meal_plan_id: int) -> Dict[str, Any]:
        """
        Get a meal plan by ID with full details including meals.

        Args:
            meal_plan_id: Meal plan ID

        Returns:
            Dictionary with meal plan data or error
        """
        try:
            meal_plan = self.meal_plan_repo.get_meal_plan_with_meals(meal_plan_id)
            
            if meal_plan is None:
                return {
                    "status": "error",
                    "message": f"Meal plan with ID {meal_plan_id} not found",
                }
            
            plan_dict = meal_plan.model_dump() if hasattr(meal_plan, 'model_dump') else dict(meal_plan)
            
            return {
                "status": "success",
                "meal_plan": plan_dict,
            }
            
        except RecordNotFoundError:
            return {
                "status": "error",
                "message": f"Meal plan with ID {meal_plan_id} not found",
            }
        except Exception as e:
            logger.error(f"Error getting meal plan {meal_plan_id}: {e}")
            return {
                "status": "error",
                "message": "An unexpected error occurred",
            }
    
    def create_meal_plan(
        self,
        days: int = 7,
        people: int = 2,
        dietary_restrictions: Optional[List[str]] = None,
        budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a new meal plan using AI agents.
        
        Args:
            days: Number of days for the meal plan
            people: Number of people to plan for
            dietary_restrictions: Dietary restrictions
            budget: Optional budget constraint
            
        Returns:
            Dictionary with created meal plan or error
        """
        try:
            result = self.kitchen_crew.create_meal_plan(
                days=days,
                people=people,
                dietary_restrictions=dietary_restrictions,
                budget=budget,
            )
            
            # Extract the result from CrewOutput if needed
            if hasattr(result, 'raw'):
                result_text = result.raw
            else:
                result_text = str(result)
            
            return {
                "status": "success",
                "message": "Meal plan created successfully",
                "result": result_text,
            }
            
        except Exception as e:
            logger.error(f"Error creating meal plan: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    async def create_meal_plan_stream(
        self,
        days: int = 7,
        people: int = 2,
        dietary_restrictions: Optional[List[str]] = None,
        budget: Optional[float] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Create a meal plan with streaming agent activity updates.
        
        Args:
            days: Number of days for the meal plan
            people: Number of people to plan for
            dietary_restrictions: Dietary restrictions
            budget: Optional budget constraint
            
        Yields:
            Agent activity events during meal plan creation
        """
        import queue
        import threading
        
        # Queue for events from callback thread
        event_queue: queue.Queue = queue.Queue()
        
        def run_crew():
            """Run the crew in a separate thread with callbacks."""
            try:
                result = self.kitchen_crew.create_meal_plan_with_callbacks(
                    days=days,
                    people=people,
                    dietary_restrictions=dietary_restrictions,
                    budget=budget,
                    event_callback=lambda event: event_queue.put(event),
                )
                
                # Extract final result
                if hasattr(result, 'raw'):
                    result_text = result.raw
                else:
                    result_text = str(result)
                
                event_queue.put({
                    "type": "complete",
                    "meal_plan": result_text,
                })
            except Exception as e:
                logger.error(f"Error in crew execution: {e}")
                event_queue.put({
                    "type": "error",
                    "content": str(e),
                })
            finally:
                event_queue.put(None)  # Signal completion
        
        # Start the crew in a thread
        thread = threading.Thread(target=run_crew)
        thread.start()
        
        # Send initial event
        yield {
            "type": "agent_thinking",
            "agent": "Meal Planning Expert",
            "content": f"Starting meal plan for {days} days, {people} people...",
        }
        
        # Stream events from the queue
        while True:
            try:
                # Check for events with timeout to allow async cooperation
                event = await asyncio.to_thread(event_queue.get, timeout=0.1)
                
                if event is None:
                    break
                    
                yield event
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error getting event from queue: {e}")
                break
        
        thread.join(timeout=5.0)
    
    def delete_meal_plan(self, meal_plan_id: int) -> Dict[str, Any]:
        """
        Delete a meal plan.
        
        Args:
            meal_plan_id: Meal plan ID to delete
            
        Returns:
            Dictionary with deletion result
        """
        try:
            success = self.meal_plan_repo.delete(meal_plan_id)
            
            if success:
                return {
                    "status": "success",
                    "message": "Meal plan deleted successfully",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Meal plan with ID {meal_plan_id} not found",
                }
                
        except Exception as e:
            logger.error(f"Error deleting meal plan {meal_plan_id}: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

