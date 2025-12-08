"""
Recipe service - business logic layer for recipe operations.
"""

import logging
from typing import Optional, List, Dict, Any

from src.models import Recipe, RecipeCreate, RecipeUpdate, CuisineType, DietaryTag, DifficultyLevel
from src.database import RecipeRepository, DatabaseError, RecordNotFoundError
from src.crew import KitchenCrew

logger = logging.getLogger(__name__)


class RecipeService:
    """
    Service layer for recipe operations.
    
    Handles business logic and coordinates between API layer,
    database repositories, and AI agents.
    """
    
    def __init__(self):
        self._recipe_repo = None
        self._kitchen_crew = None
    
    @property
    def recipe_repo(self) -> RecipeRepository:
        """Lazy initialization of recipe repository."""
        if self._recipe_repo is None:
            self._recipe_repo = RecipeRepository()
        return self._recipe_repo
    
    @property
    def kitchen_crew(self) -> KitchenCrew:
        """Lazy initialization of kitchen crew."""
        if self._kitchen_crew is None:
            self._kitchen_crew = KitchenCrew()
        return self._kitchen_crew
    
    def search_recipes(
        self,
        search_term: Optional[str] = None,
        cuisine: Optional[CuisineType] = None,
        dietary_tags: Optional[List[DietaryTag]] = None,
        difficulty: Optional[DifficultyLevel] = None,
        max_prep_time: Optional[int] = None,
        max_cook_time: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search recipes in the database.
        
        Args:
            search_term: Text to search in recipe name
            cuisine: Filter by cuisine type
            dietary_tags: Filter by dietary tags
            difficulty: Filter by difficulty level
            max_prep_time: Maximum prep time in minutes
            max_cook_time: Maximum cook time in minutes
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Dictionary with recipes and metadata
        """
        try:
            recipes = self.recipe_repo.search_recipes(
                search_term=search_term,
                cuisine=cuisine.value if cuisine else None,
                dietary_tags=[tag.value for tag in dietary_tags] if dietary_tags else None,
                difficulty=difficulty.value if difficulty else None,
                max_prep_time=max_prep_time,
                max_cook_time=max_cook_time,
                limit=limit,
            )
            
            # Convert to dictionaries
            recipe_dicts = []
            for recipe in recipes:
                if hasattr(recipe, 'model_dump'):
                    recipe_dicts.append(recipe.model_dump())
                else:
                    recipe_dicts.append(dict(recipe))
            
            return {
                "status": "success",
                "recipes": recipe_dicts[offset:offset + limit],
                "total": len(recipe_dicts),
                "limit": limit,
                "offset": offset,
            }
            
        except DatabaseError as e:
            logger.error(f"Database error searching recipes: {e}")
            return {
                "status": "error",
                "message": str(e),
                "recipes": [],
            }
        except Exception as e:
            logger.error(f"Unexpected error searching recipes: {e}")
            return {
                "status": "error",
                "message": "An unexpected error occurred",
                "recipes": [],
            }
    
    def get_recipe(self, recipe_id: int) -> Dict[str, Any]:
        """
        Get a recipe by ID with full details.
        
        Args:
            recipe_id: Recipe ID
            
        Returns:
            Dictionary with recipe data or error
        """
        try:
            recipe = self.recipe_repo.get_recipe_with_ingredients(recipe_id)
            
            if recipe is None:
                return {
                    "status": "error",
                    "message": f"Recipe with ID {recipe_id} not found",
                }
            
            recipe_dict = recipe.model_dump() if hasattr(recipe, 'model_dump') else dict(recipe)
            
            return {
                "status": "success",
                "recipe": recipe_dict,
            }
            
        except RecordNotFoundError:
            return {
                "status": "error",
                "message": f"Recipe with ID {recipe_id} not found",
            }
        except Exception as e:
            logger.error(f"Error getting recipe {recipe_id}: {e}")
            return {
                "status": "error",
                "message": "An unexpected error occurred",
            }
    
    def create_recipe(self, recipe_data: RecipeCreate) -> Dict[str, Any]:
        """
        Create a new recipe.
        
        Args:
            recipe_data: Recipe creation data
            
        Returns:
            Dictionary with created recipe or error
        """
        try:
            # Extract ingredients if present
            ingredients = []
            if hasattr(recipe_data, 'ingredients'):
                ingredients = recipe_data.ingredients
            
            recipe = self.recipe_repo.create_recipe(recipe_data, ingredients)
            
            return {
                "status": "success",
                "message": "Recipe created successfully",
                "recipe_id": recipe.id,
                "recipe": recipe.model_dump() if hasattr(recipe, 'model_dump') else dict(recipe),
            }
            
        except Exception as e:
            logger.error(f"Error creating recipe: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def update_recipe(self, recipe_id: int, recipe_data: RecipeUpdate) -> Dict[str, Any]:
        """
        Update an existing recipe.
        
        Args:
            recipe_id: Recipe ID to update
            recipe_data: Updated recipe data
            
        Returns:
            Dictionary with update result
        """
        try:
            # Get only the fields that are set
            update_data = recipe_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return {
                    "status": "error",
                    "message": "No fields to update",
                }
            
            success = self.recipe_repo.update(recipe_id, update_data)
            
            if success:
                return {
                    "status": "success",
                    "message": "Recipe updated successfully",
                    "recipe_id": recipe_id,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Recipe with ID {recipe_id} not found",
                }
                
        except RecordNotFoundError:
            return {
                "status": "error",
                "message": f"Recipe with ID {recipe_id} not found",
            }
        except Exception as e:
            logger.error(f"Error updating recipe {recipe_id}: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def delete_recipe(self, recipe_id: int) -> Dict[str, Any]:
        """
        Delete a recipe.
        
        Args:
            recipe_id: Recipe ID to delete
            
        Returns:
            Dictionary with deletion result
        """
        try:
            success = self.recipe_repo.delete(recipe_id)
            
            if success:
                return {
                    "status": "success",
                    "message": "Recipe deleted successfully",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Recipe with ID {recipe_id} not found",
                }
                
        except Exception as e:
            logger.error(f"Error deleting recipe {recipe_id}: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def discover_recipes(
        self,
        cuisine: Optional[str] = None,
        dietary_restrictions: Optional[List[str]] = None,
        ingredients: Optional[List[str]] = None,
        max_prep_time: Optional[int] = None,
        original_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Discover new recipes using AI agents.
        
        Args:
            cuisine: Cuisine type to search for
            dietary_restrictions: Dietary restrictions
            ingredients: Available ingredients
            max_prep_time: Maximum prep time
            original_query: Natural language query
            
        Returns:
            Dictionary with discovered recipes
        """
        try:
            result = self.kitchen_crew.discover_new_recipes(
                cuisine=cuisine,
                dietary_restrictions=dietary_restrictions,
                ingredients=ingredients,
                max_prep_time=max_prep_time,
                original_query=original_query,
            )
            
            # Extract the result from CrewOutput if needed
            if hasattr(result, 'raw'):
                result_text = result.raw
            else:
                result_text = str(result)
            
            return {
                "status": "success",
                "result": result_text,
            }
            
        except Exception as e:
            logger.error(f"Error discovering recipes: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

