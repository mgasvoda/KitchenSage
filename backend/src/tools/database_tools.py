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
    DifficultyLevel, CuisineType, DietaryTag, MealType, IngredientCategory, MeasurementUnit
)

logger = logging.getLogger(__name__)


def _get_recipe_search_service():
    """Lazy import to avoid circular dependency."""
    from src.services.recipe_search_service import RecipeSearchService
    return RecipeSearchService()


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
    """
    Tool for searching recipes in the database.
    
    Supports both structured field searches and semantic/natural language queries.
    This tool provides the same search functionality as the human-facing UI.
    """
    
    name: str = "Recipe Search Tool"
    description: str = """Searches for recipes in the database using structured filters and/or natural language queries.

STRUCTURED FILTERS (use 'filters' parameter):
- name: Recipe name (partial match)
- ingredients: List of ingredient names to search for
- meal_types: Filter by meal type - 'breakfast', 'lunch', 'dinner', 'snack', 'dessert'
- cuisine: Cuisine type - 'american', 'italian', 'mexican', 'chinese', 'japanese', 'indian', 'french', 'thai', 'greek', 'mediterranean', 'spanish', 'korean', 'vietnamese', 'middle_eastern', 'african', 'fusion', 'other'
- dietary_tags: List of dietary restrictions - 'vegetarian', 'vegan', 'gluten_free', 'dairy_free', 'nut_free', 'low_carb', 'keto', 'paleo', etc.
- difficulty: 'easy', 'medium', or 'hard'
- max_prep_time: Maximum prep time in minutes
- max_cook_time: Maximum cook time in minutes
- max_total_time: Maximum total time in minutes

SEMANTIC SEARCH (use 'query' parameter):
- Natural language query like "quick weeknight chicken dinners" or "healthy vegetarian lunches"
- Finds recipes by meaning, not just keyword matching

OPTIONS:
- limit: Maximum number of results (default 20, max 100)
- use_semantic: Whether to use AI-powered semantic search (default true)

EXAMPLES:
- Find breakfast recipes: {"filters": {"meal_types": ["breakfast"]}}
- Find quick Italian dinners: {"filters": {"cuisine": "italian", "max_total_time": 30}, "query": "easy weeknight dinner"}
- Semantic search: {"query": "kabob dinners for a summer party"}
"""
    
    def _get_search_service(self):
        """Get search service instance (lazy initialization)."""
        if not hasattr(self, '_search_service'):
            self._search_service = _get_recipe_search_service()
        return self._search_service
    
    def _run(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for recipes based on criteria.
        
        Args:
            search_criteria: Dictionary containing search parameters:
                - filters: Dictionary of structured filters (name, ingredients, meal_types, cuisine, etc.)
                - query: Natural language search query for semantic search
                - limit: Maximum number of results (default 20)
                - use_semantic: Whether to use semantic search (default True)
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            search_service = self._get_search_service()
            
            # Extract parameters
            filters = search_criteria.get('filters', {})
            query = search_criteria.get('query')
            limit = search_criteria.get('limit', 20)
            use_semantic = search_criteria.get('use_semantic', True)
            
            # Handle legacy format where filters are at the top level
            if not filters and not query:
                # Check for legacy parameters at top level
                legacy_keys = ['name', 'cuisine', 'dietary_tags', 'ingredients', 
                              'max_prep_time', 'max_cook_time', 'difficulty', 'meal_types']
                filters = {k: v for k, v in search_criteria.items() if k in legacy_keys and v is not None}
            
            # Use the unified search service
            result = search_service.search_dict(
                filters=filters if filters else None,
                query=query,
                limit=limit,
                use_semantic=use_semantic
            )
            
            # Format response for agent consumption
            return {
                "status": result.get("status", "success"),
                "recipes": [r["recipe"] for r in result.get("recipes", [])],
                "count": result.get("total", 0),
                "search_criteria": search_criteria,
                "message": f"Found {result.get('total', 0)} matching recipes",
                "relevance_scores": {
                    r["recipe"].get("id", i): r["relevance_score"] 
                    for i, r in enumerate(result.get("recipes", []))
                }
            }
            
        except Exception as e:
            logger.error(f"Recipe search failed: {e}")
            return {
                "status": "error",
                "recipes": [],
                "count": 0,
                "message": f"Search failed: {str(e)}"
            } 