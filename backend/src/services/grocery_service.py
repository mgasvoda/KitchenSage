"""
Grocery service - business logic layer for grocery list operations.
"""

import logging
from typing import Optional, Dict, Any, List

from src.database import GroceryRepository, RecipeRepository, MealPlanRepository, DatabaseError, RecordNotFoundError
from src.crew import KitchenCrew
from src.services.consolidation_service import GroceryConsolidationService

logger = logging.getLogger(__name__)


class GroceryService:
    """
    Service layer for grocery list operations.
    
    Handles business logic and coordinates between API layer,
    database repositories, and AI agents.
    """
    
    def __init__(self):
        self._grocery_repo = None
        self._recipe_repo = None
        self._meal_plan_repo = None
        self._kitchen_crew = None
        self._consolidation_service = None
    
    @property
    def grocery_repo(self) -> GroceryRepository:
        """Lazy initialization of grocery repository."""
        if self._grocery_repo is None:
            self._grocery_repo = GroceryRepository()
        return self._grocery_repo
    
    @property
    def recipe_repo(self) -> RecipeRepository:
        """Lazy initialization of recipe repository."""
        if self._recipe_repo is None:
            self._recipe_repo = RecipeRepository()
        return self._recipe_repo
    
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

    @property
    def consolidation_service(self) -> GroceryConsolidationService:
        """Lazy initialization of consolidation service."""
        if self._consolidation_service is None:
            self._consolidation_service = GroceryConsolidationService()
        return self._consolidation_service

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
    
    def get_or_create_default_list(self) -> Dict[str, Any]:
        """
        Get the default grocery list, creating one if it doesn't exist.
        
        Returns:
            Dictionary with grocery list data
        """
        try:
            grocery_list = self.grocery_repo.get_or_create_default_list()
            list_dict = grocery_list.model_dump() if hasattr(grocery_list, 'model_dump') else dict(grocery_list)
            
            return {
                "status": "success",
                "grocery_list": list_dict,
            }
            
        except Exception as e:
            logger.error(f"Error getting/creating default grocery list: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def add_recipe_ingredients(
        self,
        recipe_id: int,
        servings: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add ingredients from a recipe to the grocery list.

        Gets or creates the default grocery list, consolidates ingredients
        using LLM, then merges them into the list.

        Args:
            recipe_id: ID of the recipe
            servings: Number of servings (uses recipe default if not provided)

        Returns:
            Dictionary with result and updated grocery list
        """
        try:
            # Get the recipe with ingredients
            recipe = self.recipe_repo.get_recipe_with_ingredients(recipe_id)
            if not recipe:
                return {
                    "status": "error",
                    "message": f"Recipe with ID {recipe_id} not found",
                }

            # Get or create the grocery list
            grocery_list = self.grocery_repo.get_or_create_default_list()

            # Calculate serving multiplier
            recipe_servings = recipe.servings or 1
            target_servings = servings or recipe_servings
            multiplier = target_servings / recipe_servings

            # Collect raw items first
            raw_items: List[Dict[str, Any]] = []
            for recipe_ingredient in recipe.ingredients:
                if not recipe_ingredient.ingredient_id:
                    continue

                adjusted_quantity = recipe_ingredient.quantity * multiplier
                unit_value = recipe_ingredient.unit.value if hasattr(recipe_ingredient.unit, 'value') else str(recipe_ingredient.unit)

                raw_items.append({
                    'name': recipe_ingredient.ingredient.name if recipe_ingredient.ingredient else 'Unknown',
                    'quantity': adjusted_quantity,
                    'unit': unit_value,
                    'ingredient_id': recipe_ingredient.ingredient_id
                })

            # Consolidate using LLM (gracefully falls back to raw items on error)
            consolidated_items = self.consolidation_service.consolidate_ingredients(raw_items)

            # Add consolidated items to the list
            items_added = 0
            for item in consolidated_items:
                ingredient_id = item.get('ingredient_id')
                if not ingredient_id:
                    continue

                self.grocery_repo.add_or_merge_item(
                    grocery_list_id=grocery_list.id,
                    ingredient_id=ingredient_id,
                    quantity=item.get('quantity', 0),
                    unit=item.get('unit', 'piece')
                )
                items_added += 1

            # Get updated list
            updated_list = self.grocery_repo.get_or_create_default_list()
            list_dict = updated_list.model_dump() if hasattr(updated_list, 'model_dump') else dict(updated_list)

            return {
                "status": "success",
                "message": f"Added {items_added} ingredients from '{recipe.name}' to grocery list",
                "grocery_list": list_dict,
            }

        except Exception as e:
            logger.error(f"Error adding recipe ingredients: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def add_meal_plan_ingredients(self, meal_plan_id: int) -> Dict[str, Any]:
        """
        Add all ingredients from a meal plan to the grocery list.

        Gets or creates the default grocery list, consolidates all ingredients
        using LLM, then merges them into the list.

        Args:
            meal_plan_id: ID of the meal plan

        Returns:
            Dictionary with result and updated grocery list
        """
        try:
            # Get the meal plan with meals and recipes
            meal_plan = self.meal_plan_repo.get_meal_plan_with_meals(meal_plan_id)
            if not meal_plan:
                return {
                    "status": "error",
                    "message": f"Meal plan with ID {meal_plan_id} not found",
                }

            # Get or create the grocery list
            grocery_list = self.grocery_repo.get_or_create_default_list()

            # Collect all raw items from all meals first
            raw_items: List[Dict[str, Any]] = []

            for meal in meal_plan.meals:
                if not meal.recipe or not meal.recipe.ingredients:
                    continue

                # Calculate serving multiplier for this meal
                effective_servings = meal.get_effective_servings() if hasattr(meal, 'get_effective_servings') else (meal.servings_override or meal.recipe.servings)
                recipe_servings = meal.recipe.servings or 1
                multiplier = effective_servings / recipe_servings

                # Collect each ingredient
                for recipe_ingredient in meal.recipe.ingredients:
                    if not recipe_ingredient.ingredient_id:
                        continue

                    adjusted_quantity = recipe_ingredient.quantity * multiplier
                    unit_value = recipe_ingredient.unit.value if hasattr(recipe_ingredient.unit, 'value') else str(recipe_ingredient.unit)

                    raw_items.append({
                        'name': recipe_ingredient.ingredient.name if recipe_ingredient.ingredient else 'Unknown',
                        'quantity': adjusted_quantity,
                        'unit': unit_value,
                        'ingredient_id': recipe_ingredient.ingredient_id
                    })

            # Consolidate using LLM (gracefully falls back to raw items on error)
            consolidated_items = self.consolidation_service.consolidate_ingredients(raw_items)

            # Add consolidated items to the list
            items_added = 0
            for item in consolidated_items:
                ingredient_id = item.get('ingredient_id')
                if not ingredient_id:
                    continue

                self.grocery_repo.add_or_merge_item(
                    grocery_list_id=grocery_list.id,
                    ingredient_id=ingredient_id,
                    quantity=item.get('quantity', 0),
                    unit=item.get('unit', 'piece')
                )
                items_added += 1

            # Get updated list
            updated_list = self.grocery_repo.get_or_create_default_list()
            list_dict = updated_list.model_dump() if hasattr(updated_list, 'model_dump') else dict(updated_list)
            
            return {
                "status": "success",
                "message": f"Added {items_added} ingredients from meal plan '{meal_plan.name}' to grocery list",
                "grocery_list": list_dict,
            }
            
        except Exception as e:
            logger.error(f"Error adding meal plan ingredients: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def clear_checked_items(self, grocery_list_id: int) -> Dict[str, Any]:
        """
        Remove all checked/purchased items from a grocery list.
        
        Args:
            grocery_list_id: ID of the grocery list
            
        Returns:
            Dictionary with result
        """
        try:
            # Verify list exists
            grocery_list = self.grocery_repo.get_by_id(grocery_list_id)
            if grocery_list is None:
                return {
                    "status": "error",
                    "message": f"Grocery list with ID {grocery_list_id} not found",
                }
            
            deleted_count = self.grocery_repo.delete_checked_items(grocery_list_id)
            
            return {
                "status": "success",
                "message": f"Removed {deleted_count} checked items",
                "deleted_count": deleted_count,
            }
            
        except Exception as e:
            logger.error(f"Error clearing checked items: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def clear_all_items(self, grocery_list_id: int) -> Dict[str, Any]:
        """
        Remove all items from a grocery list.
        
        Args:
            grocery_list_id: ID of the grocery list
            
        Returns:
            Dictionary with result
        """
        try:
            # Verify list exists
            grocery_list = self.grocery_repo.get_by_id(grocery_list_id)
            if grocery_list is None:
                return {
                    "status": "error",
                    "message": f"Grocery list with ID {grocery_list_id} not found",
                }
            
            deleted_count = self.grocery_repo.delete_all_items(grocery_list_id)
            
            return {
                "status": "success",
                "message": f"Removed all {deleted_count} items from list",
                "deleted_count": deleted_count,
            }
            
        except Exception as e:
            logger.error(f"Error clearing all items: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

