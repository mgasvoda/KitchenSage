"""
Grocery service - business logic layer for grocery list operations.
"""

import logging
from typing import Optional, Dict, Any

from src.database import GroceryRepository, DatabaseError, RecordNotFoundError
from src.crew import KitchenCrew

logger = logging.getLogger(__name__)


class GroceryService:
    """
    Service layer for grocery list operations.
    
    Handles business logic and coordinates between API layer,
    database repositories, and AI agents.
    """
    
    def __init__(self):
        self._grocery_repo = None
        self._kitchen_crew = None
    
    @property
    def grocery_repo(self) -> GroceryRepository:
        """Lazy initialization of grocery repository."""
        if self._grocery_repo is None:
            self._grocery_repo = GroceryRepository()
        return self._grocery_repo
    
    @property
    def kitchen_crew(self) -> KitchenCrew:
        """Lazy initialization of kitchen crew."""
        if self._kitchen_crew is None:
            self._kitchen_crew = KitchenCrew()
        return self._kitchen_crew
    
    def list_grocery_lists(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List all grocery lists.
        
        Args:
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Dictionary with grocery lists and metadata
        """
        try:
            grocery_lists = self.grocery_repo.get_all()
            
            # Convert to dictionaries
            list_dicts = []
            for grocery_list in grocery_lists:
                if hasattr(grocery_list, 'model_dump'):
                    list_dicts.append(grocery_list.model_dump())
                elif hasattr(grocery_list, '__dict__'):
                    list_dicts.append(grocery_list.__dict__)
                else:
                    list_dicts.append(dict(grocery_list))
            
            return {
                "status": "success",
                "grocery_lists": list_dicts[offset:offset + limit],
                "total": len(list_dicts),
                "limit": limit,
                "offset": offset,
            }
            
        except DatabaseError as e:
            logger.error(f"Database error listing grocery lists: {e}")
            return {
                "status": "error",
                "message": str(e),
                "grocery_lists": [],
            }
        except Exception as e:
            logger.error(f"Unexpected error listing grocery lists: {e}")
            return {
                "status": "error",
                "message": "An unexpected error occurred",
                "grocery_lists": [],
            }
    
    def get_grocery_list(self, grocery_list_id: int) -> Dict[str, Any]:
        """
        Get a grocery list by ID with full details.
        
        Args:
            grocery_list_id: Grocery list ID
            
        Returns:
            Dictionary with grocery list data or error
        """
        try:
            grocery_list = self.grocery_repo.get_by_id(grocery_list_id)
            
            if grocery_list is None:
                return {
                    "status": "error",
                    "message": f"Grocery list with ID {grocery_list_id} not found",
                }
            
            list_dict = grocery_list.model_dump() if hasattr(grocery_list, 'model_dump') else dict(grocery_list)
            
            return {
                "status": "success",
                "grocery_list": list_dict,
            }
            
        except RecordNotFoundError:
            return {
                "status": "error",
                "message": f"Grocery list with ID {grocery_list_id} not found",
            }
        except Exception as e:
            logger.error(f"Error getting grocery list {grocery_list_id}: {e}")
            return {
                "status": "error",
                "message": "An unexpected error occurred",
            }
    
    def generate_grocery_list(self, meal_plan_id: int) -> Dict[str, Any]:
        """
        Generate a grocery list from a meal plan using AI agents.
        
        Args:
            meal_plan_id: Meal plan ID to generate list from
            
        Returns:
            Dictionary with generated grocery list or error
        """
        try:
            result = self.kitchen_crew.generate_grocery_list(meal_plan_id)
            
            # Extract the result from CrewOutput if needed
            if hasattr(result, 'raw'):
                result_text = result.raw
            else:
                result_text = str(result)
            
            return {
                "status": "success",
                "message": "Grocery list generated successfully",
                "result": result_text,
            }
            
        except Exception as e:
            logger.error(f"Error generating grocery list: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def update_item(
        self,
        grocery_list_id: int,
        item_id: int,
        checked: bool,
    ) -> Dict[str, Any]:
        """
        Update a grocery list item.
        
        Args:
            grocery_list_id: Grocery list ID
            item_id: Item ID to update
            checked: Whether the item is checked
            
        Returns:
            Dictionary with update result
        """
        try:
            # First verify the grocery list exists
            grocery_list = self.grocery_repo.get_by_id(grocery_list_id)
            if grocery_list is None:
                return {
                    "status": "error",
                    "message": f"Grocery list with ID {grocery_list_id} not found",
                }
            
            # Update the item
            success = self.grocery_repo.update_item(item_id, {"checked": checked})
            
            if success:
                return {
                    "status": "success",
                    "message": "Item updated successfully",
                    "item_id": item_id,
                    "checked": checked,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Item with ID {item_id} not found",
                }
                
        except Exception as e:
            logger.error(f"Error updating item {item_id}: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def delete_grocery_list(self, grocery_list_id: int) -> Dict[str, Any]:
        """
        Delete a grocery list.
        
        Args:
            grocery_list_id: Grocery list ID to delete
            
        Returns:
            Dictionary with deletion result
        """
        try:
            success = self.grocery_repo.delete(grocery_list_id)
            
            if success:
                return {
                    "status": "success",
                    "message": "Grocery list deleted successfully",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Grocery list with ID {grocery_list_id} not found",
                }
                
        except Exception as e:
            logger.error(f"Error deleting grocery list {grocery_list_id}: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

