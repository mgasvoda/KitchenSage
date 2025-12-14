"""
Recipe repository for database operations.

Handles recipes and their ingredients with full CRUD operations.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.models import Recipe, RecipeCreate, RecipeUpdate, RecipeIngredient, Ingredient
from src.models import DifficultyLevel, CuisineType, DietaryTag, MeasurementUnit, IngredientCategory
from .base_repository import BaseRepository
from .connection import get_db_session, RecordNotFoundError, ValidationError


class IngredientRepository(BaseRepository[Ingredient]):
    """Repository for ingredient operations."""
    
    def __init__(self):
        super().__init__("ingredients", Ingredient)
    
    def _row_to_model(self, row: sqlite3.Row) -> Ingredient:
        """Convert database row to Ingredient model."""
        return Ingredient(
            id=row['id'],
            name=row['name'],
            category=IngredientCategory(row['category']) if row['category'] else IngredientCategory.OTHER,
            common_unit=MeasurementUnit(row['common_unit']) if row['common_unit'] else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    def _model_to_dict(self, model: Ingredient, include_id: bool = True) -> Dict[str, Any]:
        """Convert Ingredient model to dictionary."""
        data = {
            'name': model.name,
            'category': model.category.value if model.category else None,
            'common_unit': model.common_unit.value if model.common_unit else None,
        }
        
        if include_id and model.id is not None:
            data['id'] = model.id
        
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
        if model.updated_at:
            data['updated_at'] = model.updated_at.isoformat()
            
        return data
    
    def get_or_create_ingredient(self, name: str, category: IngredientCategory = IngredientCategory.OTHER) -> Ingredient:
        """
        Get an ingredient by name or create it if it doesn't exist.
        
        Args:
            name: Ingredient name (will be normalized)
            category: Ingredient category
            
        Returns:
            Ingredient instance
        """
        # Normalize name
        normalized_name = name.strip().lower()
        
        # Try to find existing ingredient
        existing = self.find_by_criteria({'name': normalized_name})
        if existing:
            return existing[0]
        
        # Create new ingredient
        ingredient_data = {
            'name': normalized_name,
            'category': category.value
        }
        
        ingredient_id = self.create(ingredient_data)
        return self.get_by_id(ingredient_id)
    
    def search_ingredients(self, search_term: str, limit: int = 20) -> List[Ingredient]:
        """
        Search ingredients by name.
        
        Args:
            search_term: Search term to match against ingredient names
            limit: Maximum number of results
            
        Returns:
            List of matching ingredients
        """
        try:
            query = """
                SELECT * FROM ingredients
                WHERE name LIKE ?
                ORDER BY name
                LIMIT ?
            """
            
            search_pattern = f"%{search_term.lower()}%"
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (search_pattern, limit))
                rows = cursor.fetchall()
                
                return [self._row_to_model(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error searching ingredients: {e}")
            raise


class RecipeRepository(BaseRepository[Recipe]):
    """Repository for recipe operations with ingredient relationships."""
    
    def __init__(self):
        super().__init__("recipes", Recipe)
        self.ingredient_repo = IngredientRepository()
    
    def _row_to_model(self, row: sqlite3.Row) -> Recipe:
        """Convert database row to Recipe model."""
        recipe = Recipe(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            prep_time=row['prep_time'],
            cook_time=row['cook_time'],
            servings=row['servings'],
            difficulty=DifficultyLevel(row['difficulty']) if row['difficulty'] else DifficultyLevel.MEDIUM,
            cuisine=CuisineType(row['cuisine']) if row['cuisine'] else CuisineType.OTHER,
            dietary_tags=json.loads(row['dietary_tags']) if row['dietary_tags'] else [],
            instructions=json.loads(row['instructions']) if row['instructions'] else [],
            notes=row['notes'],
            source=row['source'],
            image_url=row['image_url'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
        
        # Convert dietary tags to enum
        recipe.dietary_tags = [DietaryTag(tag) for tag in recipe.dietary_tags if tag in DietaryTag._value2member_map_]
        
        return recipe
    
    def _model_to_dict(self, model: Recipe, include_id: bool = True) -> Dict[str, Any]:
        """Convert Recipe model to dictionary."""
        data = {
            'name': model.name,
            'description': model.description,
            'prep_time': model.prep_time,
            'cook_time': model.cook_time,
            'servings': model.servings,
            'difficulty': model.difficulty.value if model.difficulty else None,
            'cuisine': model.cuisine.value if model.cuisine else None,
            'dietary_tags': json.dumps([tag.value for tag in model.dietary_tags]),
            'instructions': json.dumps(model.instructions),
            'notes': model.notes,
            'source': model.source,
            'image_url': model.image_url,
        }
        
        if include_id and model.id is not None:
            data['id'] = model.id
        
        if model.created_at:
            data['created_at'] = model.created_at.isoformat()
        if model.updated_at:
            data['updated_at'] = model.updated_at.isoformat()
            
        return data
    
    def create_recipe(self, recipe_create: RecipeCreate, ingredients: List[Dict[str, Any]] = None) -> Recipe:
        """
        Create a new recipe with ingredients.
        
        Args:
            recipe_create: Recipe creation data
            ingredients: List of ingredient dictionaries with keys:
                - name: ingredient name
                - quantity: amount needed
                - unit: measurement unit
                - notes: optional notes
                - category: optional ingredient category
                
        Returns:
            Created Recipe instance with ingredients loaded
        """
        try:
            # Convert model to dict
            recipe_data = {
                'name': recipe_create.name,
                'description': recipe_create.description,
                'prep_time': recipe_create.prep_time,
                'cook_time': recipe_create.cook_time,
                'servings': recipe_create.servings,
                'difficulty': recipe_create.difficulty.value,
                'cuisine': recipe_create.cuisine.value,
                'dietary_tags': json.dumps([tag.value for tag in recipe_create.dietary_tags]),
                'instructions': json.dumps(recipe_create.instructions),
                'notes': recipe_create.notes,
                'source': recipe_create.source,
                'image_url': recipe_create.image_url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Use a single database session for everything
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                # Insert recipe
                columns = list(recipe_data.keys())
                placeholders = ', '.join(['?' for _ in columns])
                values = list(recipe_data.values())
                
                recipe_query = f"""
                    INSERT INTO recipes ({', '.join(columns)})
                    VALUES ({placeholders})
                """
                
                cursor.execute(recipe_query, values)
                recipe_id = cursor.lastrowid
                
                # Add ingredients if provided
                if ingredients:
                    for ingredient_data in ingredients:
                        # Get or create ingredient within the same session
                        ingredient = self._get_or_create_ingredient_in_session(
                            cursor, 
                            ingredient_data['name'],
                            ingredient_data.get('category', IngredientCategory.OTHER)
                        )
                        
                        # Insert recipe ingredient relationship
                        cursor.execute("""
                            INSERT INTO recipe_ingredients 
                            (recipe_id, ingredient_id, quantity, unit, notes, optional, substitutes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            recipe_id,
                            ingredient.id,
                            ingredient_data['quantity'],
                            ingredient_data['unit'],
                            ingredient_data.get('notes'),
                            ingredient_data.get('optional', False),
                            json.dumps(ingredient_data.get('substitutes', []))
                        ))
                
                self.logger.info(f"Created recipe with ID: {recipe_id}")
            
            # Return full recipe with ingredients
            return self.get_recipe_with_ingredients(recipe_id)
            
        except Exception as e:
            self.logger.error(f"Error creating recipe: {e}")
            raise
    
    def _get_or_create_ingredient_in_session(self, cursor: sqlite3.Cursor, name: str, category: IngredientCategory = IngredientCategory.OTHER) -> Ingredient:
        """
        Get an ingredient by name or create it if it doesn't exist, within an existing database session.
        
        Args:
            cursor: Database cursor within an active session
            name: Ingredient name (will be normalized)
            category: Ingredient category
            
        Returns:
            Ingredient instance
        """
        # Normalize name
        normalized_name = name.strip().lower()
        
        # Try to find existing ingredient
        cursor.execute("SELECT * FROM ingredients WHERE name = ?", (normalized_name,))
        row = cursor.fetchone()
        
        if row:
            return self.ingredient_repo._row_to_model(row)
        
        # Create new ingredient
        cursor.execute("""
            INSERT INTO ingredients (name, category, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (
            normalized_name,
            category.value,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        ingredient_id = cursor.lastrowid
        
        return Ingredient(
            id=ingredient_id,
            name=normalized_name,
            category=category,
            created_at=datetime.now()
        )
    
    def get_recipe_with_ingredients(self, recipe_id: int) -> Optional[Recipe]:
        """
        Get a recipe with all its ingredients loaded.
        
        Args:
            recipe_id: ID of the recipe
            
        Returns:
            Recipe instance with ingredients, or None if not found
        """
        # Get base recipe
        recipe = self.get_by_id(recipe_id)
        if not recipe:
            return None
        
        # Load ingredients
        recipe.ingredients = self._get_recipe_ingredients(recipe_id)
        
        return recipe
    
    def _get_recipe_ingredients(self, recipe_id: int) -> List[RecipeIngredient]:
        """Get all ingredients for a recipe."""
        try:
            query = """
                SELECT ri.*, i.name, i.category, i.common_unit
                FROM recipe_ingredients ri
                JOIN ingredients i ON ri.ingredient_id = i.id
                WHERE ri.recipe_id = ?
                ORDER BY ri.id
            """
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (recipe_id,))
                rows = cursor.fetchall()
                
                ingredients = []
                for row in rows:
                    # Create ingredient instance
                    ingredient = Ingredient(
                        id=row['ingredient_id'],
                        name=row['name'],
                        category=IngredientCategory(row['category']) if row['category'] else IngredientCategory.OTHER,
                        common_unit=MeasurementUnit(row['common_unit']) if row['common_unit'] else None
                    )
                    
                    # Create recipe ingredient
                    recipe_ingredient = RecipeIngredient(
                        id=row['id'],
                        recipe_id=row['recipe_id'],
                        ingredient_id=row['ingredient_id'],
                        ingredient=ingredient,
                        quantity=row['quantity'],
                        unit=MeasurementUnit(row['unit']),
                        notes=row['notes'],
                        optional=bool(row['optional']),
                        substitutes=json.loads(row['substitutes']) if row['substitutes'] else []
                    )
                    
                    ingredients.append(recipe_ingredient)
                
                return ingredients
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting recipe ingredients: {e}")
            raise
    
    def _add_recipe_ingredients(self, recipe_id: int, ingredients: List[Dict[str, Any]]) -> None:
        """Add ingredients to a recipe."""
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                for ingredient_data in ingredients:
                    # Get or create ingredient
                    ingredient = self.ingredient_repo.get_or_create_ingredient(
                        ingredient_data['name'],
                        ingredient_data.get('category', IngredientCategory.OTHER)
                    )
                    
                    # Insert recipe ingredient relationship
                    cursor.execute("""
                        INSERT INTO recipe_ingredients 
                        (recipe_id, ingredient_id, quantity, unit, notes, optional, substitutes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        recipe_id,
                        ingredient.id,
                        ingredient_data['quantity'],
                        ingredient_data['unit'],
                        ingredient_data.get('notes'),
                        ingredient_data.get('optional', False),
                        json.dumps(ingredient_data.get('substitutes', []))
                    ))
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error adding recipe ingredients: {e}")
            raise
    
    def search_recipes(self, 
                      search_term: Optional[str] = None,
                      cuisine: Optional[CuisineType] = None,
                      dietary_tags: Optional[List[DietaryTag]] = None,
                      max_prep_time: Optional[int] = None,
                      max_cook_time: Optional[int] = None,
                      difficulty: Optional[DifficultyLevel] = None,
                      limit: int = 20) -> List[Recipe]:
        """
        Search recipes with various filters.
        
        Args:
            search_term: Search in recipe name and description
            cuisine: Filter by cuisine type
            dietary_tags: Filter by dietary restrictions (recipe must have ALL tags)
            max_prep_time: Maximum preparation time in minutes
            max_cook_time: Maximum cooking time in minutes
            difficulty: Filter by difficulty level
            limit: Maximum number of results
            
        Returns:
            List of matching recipes
        """
        try:
            query_parts = ["SELECT * FROM recipes WHERE 1=1"]
            params = []
            
            # Search term
            if search_term:
                query_parts.append("AND (name LIKE ? OR description LIKE ?)")
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])
            
            # Cuisine filter
            if cuisine:
                query_parts.append("AND cuisine = ?")
                params.append(cuisine.value)
            
            # Time filters
            if max_prep_time is not None:
                query_parts.append("AND prep_time <= ?")
                params.append(max_prep_time)
            
            if max_cook_time is not None:
                query_parts.append("AND cook_time <= ?")
                params.append(max_cook_time)
            
            # Difficulty filter
            if difficulty:
                query_parts.append("AND difficulty = ?")
                params.append(difficulty.value)
            
            # Dietary tags filter
            if dietary_tags:
                for tag in dietary_tags:
                    query_parts.append("AND dietary_tags LIKE ?")
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
            self.logger.error(f"Database error searching recipes: {e}")
            raise
    
    def get_recipes_by_ingredient(self, ingredient_name: str, limit: int = 20) -> List[Recipe]:
        """
        Find recipes that contain a specific ingredient.
        
        Args:
            ingredient_name: Name of the ingredient to search for
            limit: Maximum number of results
            
        Returns:
            List of recipes containing the ingredient
        """
        try:
            query = """
                SELECT DISTINCT r.*
                FROM recipes r
                JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                JOIN ingredients i ON ri.ingredient_id = i.id
                WHERE i.name LIKE ?
                ORDER BY r.name
                LIMIT ?
            """
            
            search_pattern = f"%{ingredient_name.lower()}%"
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (search_pattern, limit))
                rows = cursor.fetchall()
                
                return [self._row_to_model(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error finding recipes by ingredient: {e}")
            raise
    
    def update_recipe(self, recipe_id: int, recipe_update: RecipeUpdate, 
                     ingredients: Optional[List[Dict[str, Any]]] = None) -> Optional[Recipe]:
        """
        Update a recipe and optionally its ingredients.
        
        Args:
            recipe_id: ID of the recipe to update
            recipe_update: Recipe update data
            ingredients: Optional new ingredients list (replaces existing)
            
        Returns:
            Updated Recipe instance, or None if not found
        """
        try:
            # Build update data
            update_data = {}
            
            if recipe_update.name is not None:
                update_data['name'] = recipe_update.name
            if recipe_update.description is not None:
                update_data['description'] = recipe_update.description
            if recipe_update.prep_time is not None:
                update_data['prep_time'] = recipe_update.prep_time
            if recipe_update.cook_time is not None:
                update_data['cook_time'] = recipe_update.cook_time
            if recipe_update.servings is not None:
                update_data['servings'] = recipe_update.servings
            if recipe_update.difficulty is not None:
                update_data['difficulty'] = recipe_update.difficulty.value
            if recipe_update.cuisine is not None:
                update_data['cuisine'] = recipe_update.cuisine.value
            if recipe_update.dietary_tags is not None:
                update_data['dietary_tags'] = json.dumps([tag.value for tag in recipe_update.dietary_tags])
            if recipe_update.instructions is not None:
                update_data['instructions'] = json.dumps(recipe_update.instructions)
            if recipe_update.notes is not None:
                update_data['notes'] = recipe_update.notes
            if recipe_update.source is not None:
                update_data['source'] = recipe_update.source
            if recipe_update.image_url is not None:
                update_data['image_url'] = recipe_update.image_url
            
            # Update recipe
            if update_data:
                updated = self.update(recipe_id, update_data)
                if not updated:
                    return None
            
            # Update ingredients if provided
            if ingredients is not None:
                self._replace_recipe_ingredients(recipe_id, ingredients)
            
            # Return updated recipe
            return self.get_recipe_with_ingredients(recipe_id)
            
        except Exception as e:
            self.logger.error(f"Error updating recipe: {e}")
            raise
    
    def _replace_recipe_ingredients(self, recipe_id: int, ingredients: List[Dict[str, Any]]) -> None:
        """Replace all ingredients for a recipe."""
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                # Delete existing ingredients
                cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
                
                # Add new ingredients
                for ingredient_data in ingredients:
                    ingredient = self.ingredient_repo.get_or_create_ingredient(
                        ingredient_data['name'],
                        ingredient_data.get('category', IngredientCategory.OTHER)
                    )
                    
                    cursor.execute("""
                        INSERT INTO recipe_ingredients 
                        (recipe_id, ingredient_id, quantity, unit, notes, optional, substitutes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        recipe_id,
                        ingredient.id,
                        ingredient_data['quantity'],
                        ingredient_data['unit'],
                        ingredient_data.get('notes'),
                        ingredient_data.get('optional', False),
                        json.dumps(ingredient_data.get('substitutes', []))
                    ))
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error replacing recipe ingredients: {e}")
            raise
    
    def delete_recipe(self, recipe_id: int) -> bool:
        """
        Delete a recipe and all its ingredients.
        
        Args:
            recipe_id: ID of the recipe to delete
            
        Returns:
            True if recipe was deleted, False if not found
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                # Delete recipe ingredients first (foreign key constraint)
                cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
                
                # Delete recipe
                cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Deleted recipe and ingredients for ID: {recipe_id}")
                    return True
                else:
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error deleting recipe: {e}")
            raise 