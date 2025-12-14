"""
Pending recipe repository for database operations.

Handles pending recipes awaiting user approval.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.models import (
    PendingRecipe, PendingRecipeCreate, PendingRecipeUpdate,
    PendingRecipeStatus, PendingRecipeIngredient,
    RecipeCreate, DifficultyLevel, CuisineType, DietaryTag, IngredientCategory,
    MeasurementUnit
)
from .base_repository import BaseRepository
from .connection import get_db_session, RecordNotFoundError, ValidationError
from .recipe_repository import RecipeRepository


class PendingRecipeRepository(BaseRepository[PendingRecipe]):
    """Repository for pending recipe operations."""
    
    def __init__(self):
        super().__init__("pending_recipes", PendingRecipe)
        self._recipe_repo = None
    
    @property
    def recipe_repo(self) -> RecipeRepository:
        """Lazy initialization of recipe repository."""
        if self._recipe_repo is None:
            self._recipe_repo = RecipeRepository()
        return self._recipe_repo
    
    def _row_to_model(self, row: sqlite3.Row) -> PendingRecipe:
        """Convert database row to PendingRecipe model."""
        # Parse JSON fields
        dietary_tags = json.loads(row['dietary_tags']) if row['dietary_tags'] else []
        ingredients_raw = json.loads(row['ingredients']) if row['ingredients'] else []
        instructions = json.loads(row['instructions']) if row['instructions'] else []
        nutritional_info = json.loads(row['nutritional_info']) if row['nutritional_info'] else None
        
        # Convert ingredients to PendingRecipeIngredient objects
        ingredients = []
        for ing in ingredients_raw:
            if isinstance(ing, str):
                ingredients.append(PendingRecipeIngredient(name=ing))
            elif isinstance(ing, dict):
                ingredients.append(PendingRecipeIngredient(**ing))
        
        return PendingRecipe(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            prep_time=row['prep_time'],
            cook_time=row['cook_time'],
            servings=row['servings'],
            difficulty=row['difficulty'],
            cuisine=row['cuisine'],
            dietary_tags=dietary_tags,
            ingredients=ingredients,
            instructions=instructions,
            notes=row['notes'],
            image_url=row['image_url'],
            nutritional_info=nutritional_info,
            source_url=row['source_url'],
            discovery_query=row['discovery_query'],
            status=PendingRecipeStatus(row['status']) if row['status'] else PendingRecipeStatus.PENDING,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    def _model_to_dict(self, model: PendingRecipe, include_id: bool = True) -> Dict[str, Any]:
        """Convert PendingRecipe model to dictionary."""
        # Convert ingredients to serializable format
        ingredients_data = [
            ing.model_dump() if hasattr(ing, 'model_dump') else ing.__dict__
            for ing in model.ingredients
        ]
        
        data = {
            'name': model.name,
            'description': model.description,
            'prep_time': model.prep_time,
            'cook_time': model.cook_time,
            'servings': model.servings,
            'difficulty': model.difficulty,
            'cuisine': model.cuisine,
            'dietary_tags': json.dumps(model.dietary_tags),
            'ingredients': json.dumps(ingredients_data),
            'instructions': json.dumps(model.instructions),
            'notes': model.notes,
            'image_url': model.image_url,
            'nutritional_info': json.dumps(model.nutritional_info) if model.nutritional_info else None,
            'source_url': model.source_url,
            'discovery_query': model.discovery_query,
            'status': model.status.value if model.status else PendingRecipeStatus.PENDING.value,
        }
        
        if include_id and model.id is not None:
            data['id'] = model.id
        
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
            
        return data
    
    def create_pending(self, pending_create: PendingRecipeCreate) -> PendingRecipe:
        """
        Create a new pending recipe.
        
        Args:
            pending_create: Pending recipe creation data
            
        Returns:
            Created PendingRecipe instance
        """
        # Convert ingredients to serializable format
        ingredients_data = [
            ing.model_dump() if hasattr(ing, 'model_dump') else ing.__dict__
            for ing in pending_create.ingredients
        ]
        
        recipe_data = {
            'name': pending_create.name,
            'description': pending_create.description,
            'prep_time': pending_create.prep_time,
            'cook_time': pending_create.cook_time,
            'servings': pending_create.servings,
            'difficulty': pending_create.difficulty,
            'cuisine': pending_create.cuisine,
            'dietary_tags': json.dumps(pending_create.dietary_tags),
            'ingredients': json.dumps(ingredients_data),
            'instructions': json.dumps(pending_create.instructions),
            'notes': pending_create.notes,
            'image_url': pending_create.image_url,
            'nutritional_info': json.dumps(pending_create.nutritional_info) if pending_create.nutritional_info else None,
            'source_url': pending_create.source_url,
            'discovery_query': pending_create.discovery_query,
            'status': PendingRecipeStatus.PENDING.value,
            'created_at': datetime.now().isoformat()
        }
        
        pending_id = self.create(recipe_data)
        return self.get_by_id(pending_id)
    
    def update_pending(self, pending_id: int, pending_update: PendingRecipeUpdate) -> Optional[PendingRecipe]:
        """
        Update a pending recipe before approval.
        
        Args:
            pending_id: ID of the pending recipe
            pending_update: Update data
            
        Returns:
            Updated PendingRecipe instance, or None if not found
        """
        update_data = {}
        
        if pending_update.name is not None:
            update_data['name'] = pending_update.name
        if pending_update.description is not None:
            update_data['description'] = pending_update.description
        if pending_update.prep_time is not None:
            update_data['prep_time'] = pending_update.prep_time
        if pending_update.cook_time is not None:
            update_data['cook_time'] = pending_update.cook_time
        if pending_update.servings is not None:
            update_data['servings'] = pending_update.servings
        if pending_update.difficulty is not None:
            update_data['difficulty'] = pending_update.difficulty
        if pending_update.cuisine is not None:
            update_data['cuisine'] = pending_update.cuisine
        if pending_update.dietary_tags is not None:
            update_data['dietary_tags'] = json.dumps(pending_update.dietary_tags)
        if pending_update.ingredients is not None:
            ingredients_data = [
                ing.model_dump() if hasattr(ing, 'model_dump') else ing.__dict__
                for ing in pending_update.ingredients
            ]
            update_data['ingredients'] = json.dumps(ingredients_data)
        if pending_update.instructions is not None:
            update_data['instructions'] = json.dumps(pending_update.instructions)
        if pending_update.notes is not None:
            update_data['notes'] = pending_update.notes
        if pending_update.image_url is not None:
            update_data['image_url'] = pending_update.image_url
        if pending_update.nutritional_info is not None:
            update_data['nutritional_info'] = json.dumps(pending_update.nutritional_info)
        
        if update_data:
            updated = self.update(pending_id, update_data)
            if not updated:
                return None
        
        return self.get_by_id(pending_id)
    
    def get_pending_by_status(self, status: PendingRecipeStatus, limit: int = 50) -> List[PendingRecipe]:
        """
        Get all pending recipes with a specific status.
        
        Args:
            status: Status to filter by
            limit: Maximum number of results
            
        Returns:
            List of pending recipes
        """
        return self.find_by_criteria({'status': status.value}, limit=limit)
    
    def get_all_pending(self, limit: int = 50) -> List[PendingRecipe]:
        """
        Get all pending recipes (status = 'pending').
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of pending recipes awaiting review
        """
        return self.get_pending_by_status(PendingRecipeStatus.PENDING, limit)
    
    def approve(self, pending_id: int) -> Dict[str, Any]:
        """
        Approve a pending recipe and move it to the main recipes table.
        
        Args:
            pending_id: ID of the pending recipe to approve
            
        Returns:
            Dictionary with status and the new recipe ID
            
        Raises:
            RecordNotFoundError: If pending recipe not found
            ValidationError: If recipe data is invalid
        """
        # Get the pending recipe
        pending = self.get_by_id(pending_id)
        if not pending:
            raise RecordNotFoundError(f"Pending recipe with ID {pending_id} not found")
        
        # Validate and convert to RecipeCreate
        try:
            # Map difficulty to enum (or default)
            difficulty = DifficultyLevel.MEDIUM
            if pending.difficulty:
                try:
                    difficulty = DifficultyLevel(pending.difficulty.lower())
                except ValueError:
                    pass
            
            # Map cuisine to enum (or default)
            cuisine = CuisineType.OTHER
            if pending.cuisine:
                try:
                    cuisine = CuisineType(pending.cuisine.lower().replace(' ', '_'))
                except ValueError:
                    pass
            
            # Map dietary tags to enums
            dietary_tags = []
            for tag in pending.dietary_tags:
                try:
                    dietary_tags.append(DietaryTag(tag.lower().replace(' ', '_')))
                except ValueError:
                    pass  # Skip invalid tags
            
            # Validate we have minimum required fields
            if not pending.instructions:
                raise ValidationError("Recipe must have at least one instruction")
            
            # Create RecipeCreate model
            recipe_create = RecipeCreate(
                name=pending.name,
                description=pending.description,
                prep_time=pending.prep_time or 0,
                cook_time=pending.cook_time or 0,
                servings=pending.servings or 4,
                difficulty=difficulty,
                cuisine=cuisine,
                dietary_tags=dietary_tags,
                instructions=pending.instructions,
                notes=pending.notes,
                source=pending.source_url,
                image_url=pending.image_url
            )
            
            # Convert pending ingredients to format expected by recipe_repo
            ingredients_data = []
            for ing in pending.ingredients:
                ingredients_data.append({
                    'name': ing.name,
                    'quantity': ing.quantity or 1.0,
                    'unit': ing.unit or MeasurementUnit.ITEM.value,
                    'notes': ing.notes,
                    'category': IngredientCategory.OTHER
                })
            
            # Create the real recipe
            recipe = self.recipe_repo.create_recipe(recipe_create, ingredients_data)
            
            # Update pending status to approved
            self.update(pending_id, {'status': PendingRecipeStatus.APPROVED.value})
            
            # Delete the pending recipe (optional - could keep for audit)
            self.delete(pending_id)
            
            self.logger.info(f"Approved pending recipe {pending_id}, created recipe {recipe.id}")
            
            return {
                'status': 'success',
                'message': f'Recipe "{pending.name}" approved and added to collection',
                'recipe_id': recipe.id,
                'pending_id': pending_id
            }
            
        except Exception as e:
            self.logger.error(f"Error approving pending recipe {pending_id}: {e}")
            raise ValidationError(f"Failed to approve recipe: {str(e)}")
    
    def reject(self, pending_id: int) -> Dict[str, Any]:
        """
        Reject and delete a pending recipe.
        
        Args:
            pending_id: ID of the pending recipe to reject
            
        Returns:
            Dictionary with status message
            
        Raises:
            RecordNotFoundError: If pending recipe not found
        """
        pending = self.get_by_id(pending_id)
        if not pending:
            raise RecordNotFoundError(f"Pending recipe with ID {pending_id} not found")
        
        # Delete the pending recipe
        deleted = self.delete(pending_id)
        
        if deleted:
            self.logger.info(f"Rejected and deleted pending recipe {pending_id}")
            return {
                'status': 'success',
                'message': f'Pending recipe "{pending.name}" rejected and removed',
                'pending_id': pending_id
            }
        else:
            raise RecordNotFoundError(f"Failed to delete pending recipe {pending_id}")
    
    def check_duplicate(self, name: str, source_url: Optional[str] = None) -> Optional[PendingRecipe]:
        """
        Check if a pending recipe with the same name or source URL exists.
        
        Args:
            name: Recipe name to check
            source_url: Optional source URL to check
            
        Returns:
            Existing PendingRecipe if found, None otherwise
        """
        try:
            # Check by name first
            existing = self.find_by_criteria({'name': name.strip().title()})
            if existing:
                return existing[0]
            
            # Check by source URL if provided
            if source_url:
                query = """
                    SELECT * FROM pending_recipes 
                    WHERE source_url = ? AND status = ?
                    LIMIT 1
                """
                with get_db_session() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (source_url, PendingRecipeStatus.PENDING.value))
                    row = cursor.fetchone()
                    if row:
                        return self._row_to_model(row)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking for duplicate pending recipe: {e}")
            return None

