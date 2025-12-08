"""
Meal plan repository for database operations.

Handles meal plans and their associated meals with full CRUD operations.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from src.models import MealPlan, MealPlanCreate, MealPlanUpdate, Meal, MealType, DietaryTag
from .base_repository import BaseRepository
from .connection import get_db_session, RecordNotFoundError, ValidationError
from .recipe_repository import RecipeRepository


class MealPlanRepository(BaseRepository[MealPlan]):
    """Repository for meal plan operations with meal relationships."""
    
    def __init__(self):
        super().__init__("meal_plans", MealPlan)
        self.recipe_repo = RecipeRepository()
    
    def _row_to_model(self, row: sqlite3.Row) -> MealPlan:
        """Convert database row to MealPlan model."""
        meal_plan = MealPlan(
            id=row['id'],
            name=row['name'],
            start_date=date.fromisoformat(row['start_date']),
            end_date=date.fromisoformat(row['end_date']),
            people_count=row['people_count'],
            dietary_restrictions=json.loads(row['dietary_restrictions']) if row['dietary_restrictions'] else [],
            description=row['description'],
            budget_target=row['budget_target'],
            calories_per_day_target=row['calories_per_day_target'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
        
        # Convert dietary tags to enum
        meal_plan.dietary_restrictions = [
            DietaryTag(tag) for tag in meal_plan.dietary_restrictions 
            if tag in DietaryTag._value2member_map_
        ]
        
        return meal_plan
    
    def _model_to_dict(self, model: MealPlan, include_id: bool = True) -> Dict[str, Any]:
        """Convert MealPlan model to dictionary."""
        data = {
            'name': model.name,
            'start_date': model.start_date.isoformat(),
            'end_date': model.end_date.isoformat(),
            'people_count': model.people_count,
            'dietary_restrictions': json.dumps([tag.value for tag in model.dietary_restrictions]),
            'description': model.description,
            'budget_target': model.budget_target,
            'calories_per_day_target': model.calories_per_day_target,
        }
        
        if include_id and model.id is not None:
            data['id'] = model.id
        
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
        if model.updated_at:
            data['updated_at'] = model.updated_at.isoformat()
            
        return data
    
    def create_meal_plan(self, meal_plan_create: MealPlanCreate) -> MealPlan:
        """
        Create a new meal plan.
        
        Args:
            meal_plan_create: Meal plan creation data
            
        Returns:
            Created MealPlan instance
        """
        try:
            meal_plan_data = {
                'name': meal_plan_create.name,
                'start_date': meal_plan_create.start_date.isoformat(),
                'end_date': meal_plan_create.end_date.isoformat(),
                'people_count': meal_plan_create.people_count,
                'dietary_restrictions': json.dumps([tag.value for tag in meal_plan_create.dietary_restrictions]),
                'description': meal_plan_create.description,
                'budget_target': meal_plan_create.budget_target,
                'calories_per_day_target': meal_plan_create.calories_per_day_target,
            }
            
            meal_plan_id = self.create(meal_plan_data)
            return self.get_meal_plan_with_meals(meal_plan_id)
            
        except Exception as e:
            self.logger.error(f"Error creating meal plan: {e}")
            raise
    
    def get_meal_plan_with_meals(self, meal_plan_id: int) -> Optional[MealPlan]:
        """
        Get a meal plan with all its meals and recipes loaded.
        
        Args:
            meal_plan_id: ID of the meal plan
            
        Returns:
            MealPlan instance with meals, or None if not found
        """
        # Get base meal plan
        meal_plan = self.get_by_id(meal_plan_id)
        if not meal_plan:
            return None
        
        # Load meals
        meal_plan.meals = self._get_meal_plan_meals(meal_plan_id)
        
        return meal_plan
    
    def _get_meal_plan_meals(self, meal_plan_id: int) -> List[Meal]:
        """Get all meals for a meal plan."""
        try:
            query = """
                SELECT m.*, r.name as recipe_name, r.servings as recipe_servings
                FROM meals m
                LEFT JOIN recipes r ON m.recipe_id = r.id
                WHERE m.meal_plan_id = ?
                ORDER BY m.meal_date, m.meal_type
            """
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (meal_plan_id,))
                rows = cursor.fetchall()
                
                meals = []
                for row in rows:
                    # Get full recipe if recipe_id exists
                    recipe = None
                    if row['recipe_id']:
                        recipe = self.recipe_repo.get_recipe_with_ingredients(row['recipe_id'])
                    
                    meal = Meal(
                        id=row['id'],
                        meal_plan_id=row['meal_plan_id'],
                        recipe_id=row['recipe_id'],
                        recipe=recipe,
                        meal_type=MealType(row['meal_type']),
                        meal_date=date.fromisoformat(row['meal_date']),
                        servings_override=row['servings_override'],
                        notes=row['notes']
                    )
                    
                    meals.append(meal)
                
                return meals
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting meal plan meals: {e}")
            raise
    
    def add_meal_to_plan(self, meal_plan_id: int, recipe_id: int, meal_type: MealType, 
                        meal_date: date, servings_override: Optional[int] = None, 
                        notes: Optional[str] = None) -> Meal:
        """
        Add a meal to a meal plan.
        
        Args:
            meal_plan_id: ID of the meal plan
            recipe_id: ID of the recipe for this meal
            meal_type: Type of meal (breakfast, lunch, dinner, etc.)
            meal_date: Date for this meal
            servings_override: Override the recipe's default serving size
            notes: Optional notes for this meal
            
        Returns:
            Created Meal instance
        """
        try:
            # Verify meal plan exists
            if not self.exists(meal_plan_id):
                raise RecordNotFoundError(f"Meal plan {meal_plan_id} not found")
            
            # Verify recipe exists
            if not self.recipe_repo.exists(recipe_id):
                raise RecordNotFoundError(f"Recipe {recipe_id} not found")
            
            meal_data = {
                'meal_plan_id': meal_plan_id,
                'recipe_id': recipe_id,
                'meal_type': meal_type.value,
                'meal_date': meal_date.isoformat(),
                'servings_override': servings_override,
                'notes': notes
            }
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO meals (meal_plan_id, recipe_id, meal_type, meal_date, servings_override, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    meal_data['meal_plan_id'],
                    meal_data['recipe_id'],
                    meal_data['meal_type'],
                    meal_data['meal_date'],
                    meal_data['servings_override'],
                    meal_data['notes']
                ))
                
                meal_id = cursor.lastrowid
                
                # Get full meal with recipe
                recipe = self.recipe_repo.get_recipe_with_ingredients(recipe_id)
                
                meal = Meal(
                    id=meal_id,
                    meal_plan_id=meal_plan_id,
                    recipe_id=recipe_id,
                    recipe=recipe,
                    meal_type=meal_type,
                    meal_date=meal_date,
                    servings_override=servings_override,
                    notes=notes
                )
                
                self.logger.info(f"Added meal to plan {meal_plan_id}: {meal_type.value} on {meal_date}")
                return meal
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error adding meal to plan: {e}")
            raise
    
    def remove_meal_from_plan(self, meal_id: int) -> bool:
        """
        Remove a meal from a meal plan.
        
        Args:
            meal_id: ID of the meal to remove
            
        Returns:
            True if meal was removed, False if not found
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Removed meal ID: {meal_id}")
                    return True
                else:
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error removing meal: {e}")
            raise
    
    def update_meal_plan(self, meal_plan_id: int, meal_plan_update: MealPlanUpdate) -> Optional[MealPlan]:
        """
        Update a meal plan.
        
        Args:
            meal_plan_id: ID of the meal plan to update
            meal_plan_update: Meal plan update data
            
        Returns:
            Updated MealPlan instance, or None if not found
        """
        try:
            # Build update data
            update_data = {}
            
            if meal_plan_update.name is not None:
                update_data['name'] = meal_plan_update.name
            if meal_plan_update.start_date is not None:
                update_data['start_date'] = meal_plan_update.start_date.isoformat()
            if meal_plan_update.end_date is not None:
                update_data['end_date'] = meal_plan_update.end_date.isoformat()
            if meal_plan_update.people_count is not None:
                update_data['people_count'] = meal_plan_update.people_count
            if meal_plan_update.dietary_restrictions is not None:
                update_data['dietary_restrictions'] = json.dumps([tag.value for tag in meal_plan_update.dietary_restrictions])
            if meal_plan_update.description is not None:
                update_data['description'] = meal_plan_update.description
            if meal_plan_update.budget_target is not None:
                update_data['budget_target'] = meal_plan_update.budget_target
            if meal_plan_update.calories_per_day_target is not None:
                update_data['calories_per_day_target'] = meal_plan_update.calories_per_day_target
            
            # Update meal plan
            if update_data:
                updated = self.update(meal_plan_id, update_data)
                if not updated:
                    return None
            
            # Return updated meal plan with meals
            return self.get_meal_plan_with_meals(meal_plan_id)
            
        except Exception as e:
            self.logger.error(f"Error updating meal plan: {e}")
            raise
    
    def get_meal_plans_by_date_range(self, start_date: date, end_date: date) -> List[MealPlan]:
        """
        Get meal plans that overlap with the given date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            List of overlapping meal plans
        """
        try:
            query = """
                SELECT * FROM meal_plans
                WHERE (start_date <= ? AND end_date >= ?)
                   OR (start_date >= ? AND start_date <= ?)
                ORDER BY start_date
            """
            
            params = [
                end_date.isoformat(),     # Plans that start before our end
                start_date.isoformat(),   # Plans that end after our start
                start_date.isoformat(),   # Plans that start within our range
                end_date.isoformat()      # Plans that start within our range
            ]
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_model(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting meal plans by date range: {e}")
            raise
    
    def get_meals_by_date(self, meal_date: date) -> List[Meal]:
        """
        Get all meals scheduled for a specific date across all meal plans.
        
        Args:
            meal_date: Date to search for meals
            
        Returns:
            List of meals on that date
        """
        try:
            query = """
                SELECT m.*, mp.name as meal_plan_name
                FROM meals m
                JOIN meal_plans mp ON m.meal_plan_id = mp.id
                WHERE m.meal_date = ?
                ORDER BY m.meal_type
            """
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (meal_date.isoformat(),))
                rows = cursor.fetchall()
                
                meals = []
                for row in rows:
                    # Get full recipe if recipe_id exists
                    recipe = None
                    if row['recipe_id']:
                        recipe = self.recipe_repo.get_recipe_with_ingredients(row['recipe_id'])
                    
                    meal = Meal(
                        id=row['id'],
                        meal_plan_id=row['meal_plan_id'],
                        recipe_id=row['recipe_id'],
                        recipe=recipe,
                        meal_type=MealType(row['meal_type']),
                        meal_date=date.fromisoformat(row['meal_date']),
                        servings_override=row['servings_override'],
                        notes=row['notes']
                    )
                    
                    meals.append(meal)
                
                return meals
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting meals by date: {e}")
            raise
    
    def search_meal_plans(self, 
                         search_term: Optional[str] = None,
                         dietary_restrictions: Optional[List[DietaryTag]] = None,
                         people_count: Optional[int] = None,
                         max_budget: Optional[float] = None,
                         limit: int = 20) -> List[MealPlan]:
        """
        Search meal plans with various filters.
        
        Args:
            search_term: Search in meal plan name and description
            dietary_restrictions: Filter by dietary restrictions
            people_count: Filter by people count
            max_budget: Maximum budget target
            limit: Maximum number of results
            
        Returns:
            List of matching meal plans
        """
        try:
            query_parts = ["SELECT * FROM meal_plans WHERE 1=1"]
            params = []
            
            # Search term
            if search_term:
                query_parts.append("AND (name LIKE ? OR description LIKE ?)")
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])
            
            # People count filter
            if people_count is not None:
                query_parts.append("AND people_count = ?")
                params.append(people_count)
            
            # Budget filter
            if max_budget is not None:
                query_parts.append("AND (budget_target IS NULL OR budget_target <= ?)")
                params.append(max_budget)
            
            # Dietary restrictions filter
            if dietary_restrictions:
                for tag in dietary_restrictions:
                    query_parts.append("AND dietary_restrictions LIKE ?")
                    params.append(f'%"{tag.value}"%')
            
            query_parts.append("ORDER BY name LIMIT ?")
            params.append(limit)
            
            query = " ".join(query_parts)
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_model(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error searching meal plans: {e}")
            raise
    
    def delete_meal_plan(self, meal_plan_id: int) -> bool:
        """
        Delete a meal plan and all its meals.
        
        Args:
            meal_plan_id: ID of the meal plan to delete
            
        Returns:
            True if meal plan was deleted, False if not found
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                # Delete meals first (foreign key constraint)
                cursor.execute("DELETE FROM meals WHERE meal_plan_id = ?", (meal_plan_id,))
                
                # Delete meal plan
                cursor.execute("DELETE FROM meal_plans WHERE id = ?", (meal_plan_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Deleted meal plan and meals for ID: {meal_plan_id}")
                    return True
                else:
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error deleting meal plan: {e}")
            raise
    
    def get_meal_plan_statistics(self, meal_plan_id: int) -> Dict[str, Any]:
        """
        Get statistics for a meal plan.
        
        Args:
            meal_plan_id: ID of the meal plan
            
        Returns:
            Dictionary with statistics
        """
        try:
            meal_plan = self.get_meal_plan_with_meals(meal_plan_id)
            if not meal_plan:
                return {}
            
            # Calculate statistics
            stats = {
                'total_meals': len(meal_plan.meals),
                'unique_recipes': len(meal_plan.get_unique_recipes()),
                'duration_days': meal_plan.get_duration_days(),
                'meals_by_type': {},
                'dietary_conflicts': meal_plan.has_dietary_conflicts()
            }
            
            # Count meals by type
            for meal_type in MealType:
                meals = meal_plan.get_meals_by_type(meal_type)
                stats['meals_by_type'][meal_type.value] = len(meals)
            
            # Calculate total servings needed per recipe
            stats['servings_needed'] = meal_plan.calculate_total_servings_needed()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating meal plan statistics: {e}")
            raise 