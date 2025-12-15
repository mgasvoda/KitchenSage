"""
Grocery list repository for database operations.

Handles grocery lists and their items with full CRUD operations.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.models import GroceryList, GroceryListCreate, GroceryItem, GroceryItemCreate
from src.models import GroceryItemStatus, MeasurementUnit, IngredientCategory
from .base_repository import BaseRepository
from .connection import get_db_session, RecordNotFoundError, ValidationError
from .recipe_repository import IngredientRepository
from .meal_plan_repository import MealPlanRepository


class GroceryRepository(BaseRepository[GroceryList]):
    """Repository for grocery list operations with item relationships."""
    
    def __init__(self):
        super().__init__("grocery_lists", GroceryList)
        self.ingredient_repo = IngredientRepository()
        self.meal_plan_repo = MealPlanRepository()
    
    def _row_to_model(self, row: sqlite3.Row) -> GroceryList:
        """Convert database row to GroceryList model."""
        grocery_list = GroceryList(
            id=row['id'],
            meal_plan_id=row['meal_plan_id'],
            name=row['name'],
            estimated_total=row['estimated_total'],
            actual_total=row['actual_total'],
            budget_limit=row['budget_limit'],
            store_preferences=json.loads(row['store_preferences']) if row['store_preferences'] else [],
            completed=bool(row['completed']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None
        )
        
        return grocery_list
    
    def _model_to_dict(self, model: GroceryList, include_id: bool = True) -> Dict[str, Any]:
        """Convert GroceryList model to dictionary."""
        data = {
            'meal_plan_id': model.meal_plan_id,
            'name': model.name,
            'estimated_total': model.estimated_total,
            'actual_total': model.actual_total,
            'budget_limit': model.budget_limit,
            'store_preferences': json.dumps(model.store_preferences),
            'completed': model.completed,
        }
        
        if include_id and model.id is not None:
            data['id'] = model.id
        
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
        if model.completed_at:
            data['completed_at'] = model.completed_at.isoformat()
            
        return data
    
    def create_grocery_list(self, grocery_list_create: GroceryListCreate) -> GroceryList:
        """
        Create a new grocery list.
        
        Args:
            grocery_list_create: Grocery list creation data
            
        Returns:
            Created GroceryList instance
        """
        try:
            grocery_list_data = {
                'meal_plan_id': grocery_list_create.meal_plan_id,
                'name': grocery_list_create.name,
                'budget_limit': grocery_list_create.budget_limit,
                'store_preferences': json.dumps(grocery_list_create.store_preferences),
                'completed': False,
            }
            
            grocery_list_id = self.create(grocery_list_data)
            return self.get_grocery_list_with_items(grocery_list_id)
            
        except Exception as e:
            self.logger.error(f"Error creating grocery list: {e}")
            raise
    
    def get_grocery_list_with_items(self, grocery_list_id: int) -> Optional[GroceryList]:
        """
        Get a grocery list with all its items loaded.
        
        Args:
            grocery_list_id: ID of the grocery list
            
        Returns:
            GroceryList instance with items, or None if not found
        """
        # Get base grocery list
        grocery_list = self.get_by_id(grocery_list_id)
        if not grocery_list:
            return None
        
        # Load items
        grocery_list.items = self._get_grocery_list_items(grocery_list_id)
        
        return grocery_list
    
    def _get_grocery_list_items(self, grocery_list_id: int) -> List[GroceryItem]:
        """Get all items for a grocery list."""
        try:
            query = """
                SELECT gi.*, i.name, i.category, i.common_unit
                FROM grocery_items gi
                JOIN ingredients i ON gi.ingredient_id = i.id
                WHERE gi.grocery_list_id = ?
                ORDER BY i.category, i.name
            """
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (grocery_list_id,))
                rows = cursor.fetchall()
                
                items = []
                for row in rows:
                    # Create ingredient instance
                    ingredient = self.ingredient_repo._row_to_model(row)
                    
                    # Create grocery item
                    grocery_item = GroceryItem(
                        id=row['id'],
                        grocery_list_id=row['grocery_list_id'],
                        ingredient_id=row['ingredient_id'],
                        ingredient=ingredient,
                        quantity=row['quantity'],
                        unit=MeasurementUnit(row['unit']),
                        estimated_price=row['estimated_price'],
                        actual_price=row['actual_price'],
                        status=GroceryItemStatus(row['status']) if row['status'] else GroceryItemStatus.NEEDED,
                        store_section=row['store_section'],
                        preferred_brand=row['preferred_brand'],
                        substitutes=json.loads(row['substitutes']) if row['substitutes'] else [],
                        notes=row['notes']
                    )
                    
                    items.append(grocery_item)
                
                return items
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting grocery list items: {e}")
            raise
    
    def add_item_to_list(self, grocery_list_id: int, grocery_item_create: GroceryItemCreate) -> GroceryItem:
        """
        Add an item to a grocery list.
        
        Args:
            grocery_list_id: ID of the grocery list
            grocery_item_create: Grocery item creation data
            
        Returns:
            Created GroceryItem instance
        """
        try:
            # Verify grocery list exists
            if not self.exists(grocery_list_id):
                raise RecordNotFoundError(f"Grocery list {grocery_list_id} not found")
            
            # Get or create ingredient if ingredient_id is not provided
            ingredient_id = grocery_item_create.ingredient_id
            if not ingredient_id:
                # This shouldn't happen in normal usage, but handle it gracefully
                raise ValidationError("Ingredient ID is required for grocery items")
            
            item_data = {
                'grocery_list_id': grocery_list_id,
                'ingredient_id': ingredient_id,
                'quantity': grocery_item_create.quantity,
                'unit': grocery_item_create.unit.value,
                'estimated_price': grocery_item_create.estimated_price,
                'status': GroceryItemStatus.NEEDED.value,
                'store_section': grocery_item_create.store_section,
                'preferred_brand': grocery_item_create.preferred_brand,
                'substitutes': json.dumps(grocery_item_create.substitutes),
                'notes': grocery_item_create.notes
            }
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO grocery_items 
                    (grocery_list_id, ingredient_id, quantity, unit, estimated_price, 
                     status, store_section, preferred_brand, substitutes, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_data['grocery_list_id'],
                    item_data['ingredient_id'],
                    item_data['quantity'],
                    item_data['unit'],
                    item_data['estimated_price'],
                    item_data['status'],
                    item_data['store_section'],
                    item_data['preferred_brand'],
                    item_data['substitutes'],
                    item_data['notes']
                ))
                
                item_id = cursor.lastrowid
                
                # Get ingredient
                ingredient = self.ingredient_repo.get_by_id(ingredient_id)
                
                # Create grocery item
                grocery_item = GroceryItem(
                    id=item_id,
                    grocery_list_id=grocery_list_id,
                    ingredient_id=ingredient_id,
                    ingredient=ingredient,
                    quantity=grocery_item_create.quantity,
                    unit=grocery_item_create.unit,
                    estimated_price=grocery_item_create.estimated_price,
                    status=GroceryItemStatus.NEEDED,
                    store_section=grocery_item_create.store_section,
                    preferred_brand=grocery_item_create.preferred_brand,
                    substitutes=grocery_item_create.substitutes,
                    notes=grocery_item_create.notes
                )
                
                self.logger.info(f"Added item to grocery list {grocery_list_id}: {ingredient.name if ingredient else 'Unknown'}")
                return grocery_item
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error adding item to grocery list: {e}")
            raise
    
    def update_item_status(self, item_id: int, status: GroceryItemStatus, actual_price: Optional[float] = None) -> bool:
        """
        Update the status of a grocery item.
        
        Args:
            item_id: ID of the grocery item
            status: New status
            actual_price: Actual price if item was purchased
            
        Returns:
            True if item was updated, False if not found
        """
        try:
            update_data = {'status': status.value}
            
            if actual_price is not None:
                update_data['actual_price'] = actual_price
            
            # Check if marking as completed and all items are done
            if status == GroceryItemStatus.PURCHASED:
                # We'll update the grocery list completion status separately
                pass
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                # Build update query
                set_clauses = [f"{column} = ?" for column in update_data.keys()]
                values = list(update_data.values()) + [item_id]
                
                query = f"""
                    UPDATE grocery_items
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Updated grocery item {item_id} status to {status.value}")
                    return True
                else:
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error updating grocery item status: {e}")
            raise
    
    def remove_item_from_list(self, item_id: int) -> bool:
        """
        Remove an item from a grocery list.
        
        Args:
            item_id: ID of the grocery item to remove
            
        Returns:
            True if item was removed, False if not found
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM grocery_items WHERE id = ?", (item_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Removed grocery item ID: {item_id}")
                    return True
                else:
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error removing grocery item: {e}")
            raise
    
    def generate_from_meal_plan(self, meal_plan_id: int, list_name: Optional[str] = None) -> GroceryList:
        """
        Generate a grocery list from a meal plan.
        
        Args:
            meal_plan_id: ID of the meal plan
            list_name: Optional name for the grocery list
            
        Returns:
            Created GroceryList with consolidated ingredients
        """
        try:
            # Get meal plan with meals
            meal_plan = self.meal_plan_repo.get_meal_plan_with_meals(meal_plan_id)
            if not meal_plan:
                raise RecordNotFoundError(f"Meal plan {meal_plan_id} not found")
            
            # Create grocery list
            if not list_name:
                list_name = f"Grocery List for {meal_plan.name}"
            
            grocery_list_create = GroceryListCreate(
                meal_plan_id=meal_plan_id,
                name=list_name,
                budget_limit=meal_plan.budget_target
            )
            
            grocery_list = self.create_grocery_list(grocery_list_create)
            
            # Consolidate ingredients from all meals
            ingredient_quantities = {}
            
            for meal in meal_plan.meals:
                if meal.recipe and meal.recipe.ingredients:
                    effective_servings = meal.get_effective_servings()
                    recipe_servings = meal.recipe.servings
                    serving_multiplier = effective_servings / recipe_servings if recipe_servings > 0 else 1
                    
                    for recipe_ingredient in meal.recipe.ingredients:
                        ingredient_id = recipe_ingredient.ingredient_id
                        if not ingredient_id:
                            continue
                            
                        adjusted_quantity = recipe_ingredient.quantity * serving_multiplier
                        unit = recipe_ingredient.unit
                        
                        # Create a key for consolidation (ingredient_id + unit)
                        key = (ingredient_id, unit.value)
                        
                        if key in ingredient_quantities:
                            ingredient_quantities[key]['quantity'] += adjusted_quantity
                            # Merge notes if different
                            existing_notes = ingredient_quantities[key].get('notes', '')
                            new_notes = recipe_ingredient.notes or ''
                            if new_notes and new_notes not in existing_notes:
                                combined_notes = f"{existing_notes}; {new_notes}" if existing_notes else new_notes
                                ingredient_quantities[key]['notes'] = combined_notes
                        else:
                            ingredient_quantities[key] = {
                                'ingredient_id': ingredient_id,
                                'quantity': adjusted_quantity,
                                'unit': unit,
                                'notes': recipe_ingredient.notes,
                                'substitutes': recipe_ingredient.substitutes,
                                'optional': recipe_ingredient.optional
                            }
            
            # Add consolidated items to grocery list
            for (ingredient_id, unit_value), item_data in ingredient_quantities.items():
                grocery_item_create = GroceryItemCreate(
                    ingredient_id=ingredient_id,
                    quantity=item_data['quantity'],
                    unit=item_data['unit'],
                    substitutes=item_data['substitutes'],
                    notes=item_data['notes']
                )
                
                self.add_item_to_list(grocery_list.id, grocery_item_create)
            
            # Return grocery list with items
            return self.get_grocery_list_with_items(grocery_list.id)
            
        except Exception as e:
            self.logger.error(f"Error generating grocery list from meal plan: {e}")
            raise
    
    def mark_list_completed(self, grocery_list_id: int) -> bool:
        """
        Mark a grocery list as completed.
        
        Args:
            grocery_list_id: ID of the grocery list
            
        Returns:
            True if list was marked completed, False if not found
        """
        try:
            # Calculate actual total from purchased items
            grocery_list = self.get_grocery_list_with_items(grocery_list_id)
            if not grocery_list:
                return False
            
            actual_total = grocery_list.calculate_actual_total()
            
            update_data = {
                'completed': True,
                'completed_at': datetime.now().isoformat(),
                'actual_total': actual_total
            }
            
            updated = self.update(grocery_list_id, update_data)
            if updated:
                self.logger.info(f"Marked grocery list {grocery_list_id} as completed")
            
            return updated
            
        except Exception as e:
            self.logger.error(f"Error marking grocery list completed: {e}")
            raise
    
    def get_lists_by_meal_plan(self, meal_plan_id: int) -> List[GroceryList]:
        """
        Get all grocery lists for a meal plan.
        
        Args:
            meal_plan_id: ID of the meal plan
            
        Returns:
            List of grocery lists
        """
        return self.find_by_criteria({'meal_plan_id': meal_plan_id})
    
    def search_grocery_lists(self, 
                           search_term: Optional[str] = None,
                           completed: Optional[bool] = None,
                           meal_plan_id: Optional[int] = None,
                           limit: int = 20) -> List[GroceryList]:
        """
        Search grocery lists with various filters.
        
        Args:
            search_term: Search in list name
            completed: Filter by completion status
            meal_plan_id: Filter by meal plan
            limit: Maximum number of results
            
        Returns:
            List of matching grocery lists
        """
        try:
            query_parts = ["SELECT * FROM grocery_lists WHERE 1=1"]
            params = []
            
            # Search term
            if search_term:
                query_parts.append("AND name LIKE ?")
                search_pattern = f"%{search_term}%"
                params.append(search_pattern)
            
            # Completion filter
            if completed is not None:
                query_parts.append("AND completed = ?")
                params.append(completed)
            
            # Meal plan filter
            if meal_plan_id is not None:
                query_parts.append("AND meal_plan_id = ?")
                params.append(meal_plan_id)
            
            query_parts.append("ORDER BY created_at DESC LIMIT ?")
            params.append(limit)
            
            query = " ".join(query_parts)
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_model(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error searching grocery lists: {e}")
            raise
    
    def delete_grocery_list(self, grocery_list_id: int) -> bool:
        """
        Delete a grocery list and all its items.
        
        Args:
            grocery_list_id: ID of the grocery list to delete
            
        Returns:
            True if grocery list was deleted, False if not found
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                # Delete grocery items first (foreign key constraint)
                cursor.execute("DELETE FROM grocery_items WHERE grocery_list_id = ?", (grocery_list_id,))
                
                # Delete grocery list
                cursor.execute("DELETE FROM grocery_lists WHERE id = ?", (grocery_list_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Deleted grocery list and items for ID: {grocery_list_id}")
                    return True
                else:
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error deleting grocery list: {e}")
            raise
    
    def get_grocery_list_statistics(self, grocery_list_id: int) -> Dict[str, Any]:
        """
        Get statistics for a grocery list.
        
        Args:
            grocery_list_id: ID of the grocery list
            
        Returns:
            Dictionary with statistics
        """
        try:
            grocery_list = self.get_grocery_list_with_items(grocery_list_id)
            if not grocery_list:
                return {}
            
            # Calculate statistics
            stats = {
                'total_items': len(grocery_list.items),
                'completion_percentage': grocery_list.get_completion_percentage(),
                'estimated_total': grocery_list.calculate_estimated_total(),
                'actual_total': grocery_list.calculate_actual_total(),
                'is_over_budget': grocery_list.is_over_budget(),
                'items_by_status': {},
                'items_by_category': {}
            }
            
            # Count items by status
            for status in GroceryItemStatus:
                items = grocery_list.get_items_by_status(status)
                stats['items_by_status'][status.value] = len(items)
            
            # Count items by category
            items_by_category = grocery_list.get_items_by_category()
            for category, items in items_by_category.items():
                stats['items_by_category'][category.value] = len(items)
            
            # Shopping route
            stats['shopping_route'] = [cat.value for cat in grocery_list.get_shopping_route()]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating grocery list statistics: {e}")
            raise
    
    def update_item(self, item_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update a grocery item.
        
        Args:
            item_id: ID of the grocery item
            update_data: Dictionary of fields to update (e.g., {"purchased": True})
            
        Returns:
            True if item was updated, False if not found
        """
        try:
            if not update_data:
                return False
            
            # Map 'checked' to 'purchased' if present (frontend compatibility)
            if 'checked' in update_data:
                update_data['purchased'] = update_data.pop('checked')
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                # Build update query
                set_clauses = [f"{column} = ?" for column in update_data.keys()]
                values = list(update_data.values()) + [item_id]
                
                query = f"""
                    UPDATE grocery_items
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Updated grocery item {item_id}")
                    return True
                else:
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error updating grocery item: {e}")
            raise
    
    def delete_checked_items(self, grocery_list_id: int) -> int:
        """
        Delete all checked/purchased items from a grocery list.
        
        Args:
            grocery_list_id: ID of the grocery list
            
        Returns:
            Number of items deleted
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM grocery_items WHERE grocery_list_id = ? AND purchased = 1",
                    (grocery_list_id,)
                )
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    self.logger.info(f"Deleted {deleted_count} checked items from grocery list {grocery_list_id}")
                
                return deleted_count
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error deleting checked items: {e}")
            raise
    
    def delete_all_items(self, grocery_list_id: int) -> int:
        """
        Delete all items from a grocery list.
        
        Args:
            grocery_list_id: ID of the grocery list
            
        Returns:
            Number of items deleted
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM grocery_items WHERE grocery_list_id = ?",
                    (grocery_list_id,)
                )
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    self.logger.info(f"Deleted all {deleted_count} items from grocery list {grocery_list_id}")
                
                return deleted_count
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error deleting all items: {e}")
            raise
    
    def get_or_create_default_list(self) -> GroceryList:
        """
        Get the default grocery list, or create one if it doesn't exist.
        
        Since we only support a single grocery list, this returns the first
        list found or creates a new one.
        
        Returns:
            GroceryList instance
        """
        try:
            # Try to get existing list
            lists = self.get_all(limit=1)
            if lists:
                return self.get_grocery_list_with_items(lists[0].id)
            
            # Create new default list
            grocery_list_create = GroceryListCreate(
                name="My Grocery List",
                meal_plan_id=None,
                budget_limit=None
            )
            
            return self.create_grocery_list(grocery_list_create)
            
        except Exception as e:
            self.logger.error(f"Error getting or creating default grocery list: {e}")
            raise
    
    def add_or_merge_item(
        self,
        grocery_list_id: int,
        ingredient_id: int,
        quantity: float,
        unit: str
    ) -> bool:
        """
        Add an item to a grocery list, merging quantity if the ingredient already exists.
        
        Args:
            grocery_list_id: ID of the grocery list
            ingredient_id: ID of the ingredient
            quantity: Quantity to add
            unit: Unit of measurement
            
        Returns:
            True if item was added/updated successfully
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                # Check if item already exists with same ingredient and unit
                cursor.execute("""
                    SELECT id, quantity FROM grocery_items
                    WHERE grocery_list_id = ? AND ingredient_id = ? AND unit = ?
                """, (grocery_list_id, ingredient_id, unit))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Merge: add to existing quantity
                    new_quantity = existing['quantity'] + quantity
                    cursor.execute("""
                        UPDATE grocery_items
                        SET quantity = ?, purchased = 0
                        WHERE id = ?
                    """, (new_quantity, existing['id']))
                    self.logger.info(f"Merged item {ingredient_id} in list {grocery_list_id}: quantity now {new_quantity}")
                else:
                    # Insert new item
                    cursor.execute("""
                        INSERT INTO grocery_items 
                        (grocery_list_id, ingredient_id, quantity, unit, purchased)
                        VALUES (?, ?, ?, ?, 0)
                    """, (grocery_list_id, ingredient_id, quantity, unit))
                    self.logger.info(f"Added new item {ingredient_id} to list {grocery_list_id}")
                
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error adding/merging item: {e}")
            raise