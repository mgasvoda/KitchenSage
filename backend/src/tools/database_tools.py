"""
Database tools for recipe management operations.
"""

from crewai.tools import BaseTool
from typing import Dict, List, Any, Optional
import logging

from src.database import (
    RecipeRepository, IngredientRepository, MealPlanRepository, GroceryRepository,
    DatabaseError, RecordNotFoundError, ValidationError
)
from src.models import (
    Recipe, RecipeCreate, RecipeUpdate, Ingredient, IngredientCreate,
    MealPlan, MealPlanCreate, GroceryList, GroceryListCreate,
    DifficultyLevel, CuisineType, DietaryTag, IngredientCategory, MeasurementUnit
)

logger = logging.getLogger(__name__)


class DatabaseTool(BaseTool):
    """Tool for database CRUD operations."""
    
    name: str = "Database Tool"
    description: str = "Performs CRUD operations on the recipe database including storing, retrieving, updating, and deleting recipes and related data."
    
    def _get_repositories(self):
        """Get repository instances (lazy initialization)."""
        if not hasattr(self, '_repos'):
            self._repos = {
                'recipes': RecipeRepository(),
                'ingredients': IngredientRepository(),
                'meal_plans': MealPlanRepository(),
                'grocery_lists': GroceryRepository()
            }
        return self._repos
    
    def _run(self, operation: str, table: str, data: Optional[Dict[str, Any]] = None, 
             filters: Optional[Dict[str, Any]] = None, record_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute database operations.
        
        Args:
            operation: Type of operation (create, read, update, delete, list)
            table: Database table name (recipes, ingredients, meal_plans, grocery_lists)
            data: Data for create/update operations
            filters: Filters for read/list operations
            record_id: ID for read/update/delete operations
            
        Returns:
            Result of the database operation
        """
        try:
            repo = self._get_repository(table)
            
            if operation == "create":
                return self._create_record(repo, table, data)
            elif operation == "read":
                return self._read_record(repo, record_id)
            elif operation == "list":
                return self._list_records(repo, filters or {})
            elif operation == "update":
                return self._update_record(repo, record_id, data)
            elif operation == "delete":
                return self._delete_record(repo, record_id)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown operation: {operation}"
                }
                
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _get_repository(self, table: str):
        """Get the appropriate repository for the table."""
        repos = self._get_repositories()
        
        if table not in repos:
            raise ValueError(f"Unknown table: {table}")
        
        return repos[table]
    
    def _create_record(self, repo, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        try:
            if table == "recipes":
                # Use specialized recipe creation method
                recipe_data = RecipeCreate(**data)
                ingredients = data.get('ingredients', [])
                recipe = repo.create_recipe(recipe_data, ingredients)
                record_id = recipe.id
            elif table == "ingredients":
                ingredient_data = IngredientCreate(**data)
                record_id = repo.create(ingredient_data.model_dump())
            elif table == "meal_plans":
                meal_plan_data = MealPlanCreate(**data)
                record_id = repo.create(meal_plan_data.model_dump())
            elif table == "grocery_lists":
                grocery_data = GroceryListCreate(**data)
                record_id = repo.create(grocery_data.model_dump())
            else:
                raise ValueError(f"Cannot create record for table: {table}")
            
            return {
                "status": "success",
                "operation": "create",
                "table": table,
                "record_id": record_id,
                "message": f"Record created successfully in {table}"
            }
        except ValidationError as e:
            return {
                "status": "error",
                "message": f"Validation error: {str(e)}"
            }
    
    def _read_record(self, repo, record_id: int) -> Dict[str, Any]:
        """Read a single record by ID."""
        try:
            record = repo.get_by_id(record_id)
            if record:
                # Convert model instance to dictionary for JSON serialization
                if hasattr(record, 'model_dump'):
                    record_dict = record.model_dump()
                elif hasattr(record, 'dict'):
                    record_dict = record.dict()
                else:
                    # Fallback for basic objects
                    record_dict = record.__dict__
                
                return {
                    "status": "success",
                    "operation": "read",
                    "record": record_dict,
                    "message": "Record retrieved successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Record with ID {record_id} not found"
                }
        except RecordNotFoundError as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _list_records(self, repo, filters: Dict[str, Any]) -> Dict[str, Any]:
        """List records with optional filters."""
        try:
            if filters:
                records = repo.find_by_criteria(filters)
            else:
                records = repo.get_all()
            
            # Convert model instances to dictionaries for JSON serialization
            record_dicts = []
            for record in records:
                if hasattr(record, 'model_dump'):
                    record_dicts.append(record.model_dump())
                elif hasattr(record, 'dict'):
                    record_dicts.append(record.dict())
                else:
                    # Fallback for basic objects
                    record_dicts.append(record.__dict__)
            
            return {
                "status": "success",
                "operation": "list",
                "records": record_dicts,
                "count": len(record_dicts),
                "message": f"Retrieved {len(record_dicts)} records"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to list records: {str(e)}"
            }
    
    def _update_record(self, repo, record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record by ID."""
        try:
            success = repo.update(record_id, data)
            if success:
                return {
                    "status": "success",
                    "operation": "update",
                    "record_id": record_id,
                    "message": "Record updated successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to update record with ID {record_id}"
                }
        except RecordNotFoundError as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _delete_record(self, repo, record_id: int) -> Dict[str, Any]:
        """Delete a record by ID."""
        try:
            success = repo.delete(record_id)
            if success:
                return {
                    "status": "success",
                    "operation": "delete",
                    "record_id": record_id,
                    "message": "Record deleted successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to delete record with ID {record_id}"
                }
        except RecordNotFoundError as e:
            return {
                "status": "error",
                "message": str(e)
            }


class RecipeValidatorTool(BaseTool):
    """Tool for validating recipe data."""
    
    name: str = "Recipe Validator Tool"
    description: str = "Validates recipe data for completeness, format, and consistency before storage."
    
    def _run(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate recipe data.
        
        Args:
            recipe_data: Recipe data to validate
            
        Returns:
            Validation result with any errors or warnings
        """
        errors = []
        warnings = []
        
        try:
            # Validate using Pydantic model
            if 'id' in recipe_data:
                Recipe(**recipe_data)
            else:
                RecipeCreate(**recipe_data)
            
            # Additional business logic validation
            errors.extend(self._validate_business_rules(recipe_data))
            warnings.extend(self._generate_warnings(recipe_data))
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "message": "Recipe validation completed" + (" with errors" if errors else " successfully")
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": warnings,
                "message": "Recipe validation failed"
            }
    
    def _validate_business_rules(self, recipe_data: Dict[str, Any]) -> List[str]:
        """Validate business-specific rules."""
        errors = []
        
        # Check for minimum ingredients
        ingredients = recipe_data.get('ingredients', [])
        if len(ingredients) < 2:
            errors.append("Recipe must have at least 2 ingredients")
        
        # Check for reasonable prep/cook times
        prep_time = recipe_data.get('prep_time', 0)
        cook_time = recipe_data.get('cook_time', 0)
        
        if prep_time <= 0 and cook_time <= 0:
            errors.append("Recipe must have either prep time or cook time greater than 0")
        
        if prep_time > 720:  # 12 hours
            errors.append("Prep time seems unreasonably long (>12 hours)")
        
        if cook_time > 1440:  # 24 hours
            errors.append("Cook time seems unreasonably long (>24 hours)")
        
        # Check for minimum instructions
        instructions = recipe_data.get('instructions', [])
        if len(instructions) < 2:
            errors.append("Recipe must have at least 2 instruction steps")
        
        # Validate servings
        servings = recipe_data.get('servings', 0)
        if servings <= 0 or servings > 50:
            errors.append("Servings must be between 1 and 50")
        
        return errors
    
    def _generate_warnings(self, recipe_data: Dict[str, Any]) -> List[str]:
        """Generate warnings for potential issues."""
        warnings = []
        
        # Check for missing optional fields
        if not recipe_data.get('description'):
            warnings.append("Recipe description is missing")
        
        if not recipe_data.get('nutritional_info'):
            warnings.append("Nutritional information is missing")
        
        # Check for unusual values
        prep_time = recipe_data.get('prep_time', 0)
        if prep_time > 120:  # 2 hours
            warnings.append("Prep time is quite long (>2 hours)")
        
        difficulty = recipe_data.get('difficulty')
        if difficulty == DifficultyLevel.HARD and prep_time < 30:
            warnings.append("Hard difficulty with short prep time may be inconsistent")
        
        return warnings


class RecipeSearchTool(BaseTool):
    """Tool for searching recipes in the database."""
    
    name: str = "Recipe Search Tool"
    description: str = "Searches for recipes in the database using various criteria like ingredients, cuisine, dietary restrictions, etc."
    
    def _get_recipe_repo(self):
        """Get recipe repository instance (lazy initialization)."""
        if not hasattr(self, '_recipe_repo'):
            self._recipe_repo = RecipeRepository()
        return self._recipe_repo
    
    def _run(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for recipes based on criteria.
        
        Args:
            search_criteria: Dictionary containing search parameters like:
                - name: Recipe name (partial match)
                - cuisine: Cuisine type
                - dietary_tags: List of dietary tags
                - ingredients: List of ingredients to include
                - max_prep_time: Maximum prep time in minutes
                - max_cook_time: Maximum cook time in minutes
                - difficulty: Difficulty level
                - servings: Number of servings
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            repo = self._get_recipe_repo()
            
            # Use the repository's search_recipes method
            recipes = repo.search_recipes(
                search_term=search_criteria.get('name'),
                cuisine=search_criteria.get('cuisine'),
                dietary_tags=search_criteria.get('dietary_tags'),
                max_prep_time=search_criteria.get('max_prep_time'),
                max_cook_time=search_criteria.get('max_cook_time'),
                difficulty=search_criteria.get('difficulty'),
                limit=search_criteria.get('limit', 20)
            )
            
            # Convert to dictionaries for JSON serialization
            recipe_dicts = []
            for recipe in recipes:
                if hasattr(recipe, 'model_dump'):
                    recipe_dict = recipe.model_dump()
                elif hasattr(recipe, 'dict'):
                    recipe_dict = recipe.dict()
                else:
                    recipe_dict = recipe.__dict__
                recipe_dicts.append(recipe_dict)
            
            # Filter by ingredients if specified (post-processing)
            if 'ingredients' in search_criteria:
                required_ingredients = set(ing.lower() for ing in search_criteria['ingredients'])
                filtered_recipes = []
                
                for recipe_dict in recipe_dicts:
                    # Get recipe with ingredients
                    full_recipe = repo.get_recipe_with_ingredients(recipe_dict['id'])
                    if full_recipe and hasattr(full_recipe, 'ingredients'):
                        recipe_ingredients = set(
                            ing.ingredient.name.lower() if hasattr(ing, 'ingredient') else str(ing).lower()
                            for ing in full_recipe.ingredients
                        )
                        if required_ingredients.issubset(recipe_ingredients):
                            filtered_recipes.append(recipe_dict)
                
                recipe_dicts = filtered_recipes
            
            # Sort results by relevance (simple scoring)
            recipe_dicts = self._score_and_sort_results(recipe_dicts, search_criteria)
            
            return {
                "status": "success",
                "recipes": recipe_dicts,
                "count": len(recipe_dicts),
                "search_criteria": search_criteria,
                "message": f"Found {len(recipe_dicts)} matching recipes"
            }
            
        except Exception as e:
            logger.error(f"Recipe search failed: {e}")
            return {
                "status": "error",
                "recipes": [],
                "count": 0,
                "message": f"Search failed: {str(e)}"
            }
    
    def _score_and_sort_results(self, recipes: List[Dict[str, Any]], 
                               criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Score and sort search results by relevance."""
        for recipe in recipes:
            score = 0
            
            # Boost score for exact name matches
            if 'name' in criteria:
                if criteria['name'].lower() in recipe.get('name', '').lower():
                    score += 10
            
            # Boost score for matching difficulty preference
            if 'difficulty' in criteria:
                if recipe.get('difficulty') == criteria['difficulty']:
                    score += 5
            
            # Boost score for appropriate prep time
            max_prep = criteria.get('max_prep_time')
            if max_prep and recipe.get('prep_time', 0) <= max_prep:
                score += 3
            
            recipe['_search_score'] = score
        
        # Sort by score (descending) then by name
        return sorted(
            recipes,
            key=lambda r: (-r.get('_search_score', 0), r.get('name', ''))
        ) 