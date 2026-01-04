"""
Recipe API endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from src.models import Recipe, RecipeCreate, RecipeUpdate, CuisineType, DietaryTag, DifficultyLevel, MealType
from src.services import RecipeService, RecipeSearchService, EmbeddingService

router = APIRouter()


class RecipeSearchRequest(BaseModel):
    """Request body for POST /recipes/search endpoint."""
    
    # Structured filters
    name: Optional[str] = Field(None, description="Search in recipe name")
    ingredients: Optional[List[str]] = Field(None, description="Filter by ingredient names")
    meal_types: Optional[List[MealType]] = Field(None, description="Filter by meal types")
    cuisine: Optional[CuisineType] = Field(None, description="Filter by cuisine type")
    dietary_tags: Optional[List[DietaryTag]] = Field(None, description="Filter by dietary tags")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Filter by difficulty")
    max_prep_time: Optional[int] = Field(None, ge=1, description="Maximum prep time in minutes")
    max_cook_time: Optional[int] = Field(None, ge=1, description="Maximum cook time in minutes")
    max_total_time: Optional[int] = Field(None, ge=1, description="Maximum total time in minutes")
    
    # Semantic search
    query: Optional[str] = Field(None, description="Natural language search query")
    use_semantic: bool = Field(True, description="Whether to use semantic search")
    
    # Pagination
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


@router.get("", response_model=dict)
async def list_recipes(
    search: Optional[str] = Query(None, description="Search term for recipe name or semantic query"),
    cuisine: Optional[CuisineType] = Query(None, description="Filter by cuisine type"),
    dietary_tags: Optional[List[DietaryTag]] = Query(None, description="Filter by dietary tags"),
    meal_types: Optional[List[MealType]] = Query(None, description="Filter by meal types"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    max_prep_time: Optional[int] = Query(None, ge=1, description="Maximum prep time in minutes"),
    max_cook_time: Optional[int] = Query(None, ge=1, description="Maximum cook time in minutes"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List recipes with optional filters.
    
    Returns a paginated list of recipes matching the specified criteria.
    Supports both structured filters and semantic search via the 'search' parameter.
    """
    search_service = RecipeSearchService()
    
    # Build filters dict
    filters = {}
    if cuisine:
        filters['cuisine'] = cuisine.value
    if dietary_tags:
        filters['dietary_tags'] = [tag.value for tag in dietary_tags]
    if meal_types:
        filters['meal_types'] = [mt.value for mt in meal_types]
    if difficulty:
        filters['difficulty'] = difficulty.value
    if max_prep_time:
        filters['max_prep_time'] = max_prep_time
    if max_cook_time:
        filters['max_cook_time'] = max_cook_time
    
    result = search_service.search_dict(
        filters=filters if filters else None,
        query=search,
        limit=limit,
        offset=offset,
        use_semantic=True
    )
    
    # Transform to match expected response format
    return {
        "status": result.get("status", "success"),
        "recipes": [r["recipe"] for r in result.get("recipes", [])],
        "total": result.get("total", 0),
        "limit": limit,
        "offset": offset,
    }


@router.post("/search", response_model=dict)
async def search_recipes(request: RecipeSearchRequest):
    """
    Advanced recipe search with structured filters and semantic search.
    
    This endpoint supports complex search queries combining:
    - Structured field filters (name, cuisine, ingredients, meal types, etc.)
    - Natural language semantic search
    - Hybrid search combining both
    
    The search functionality is identical to what AI agents use,
    ensuring consistent results between the UI and automated tools.
    """
    search_service = RecipeSearchService()
    
    # Build filters dict from request
    filters = {}
    if request.name:
        filters['name'] = request.name
    if request.ingredients:
        filters['ingredients'] = request.ingredients
    if request.meal_types:
        filters['meal_types'] = [mt.value for mt in request.meal_types]
    if request.cuisine:
        filters['cuisine'] = request.cuisine.value
    if request.dietary_tags:
        filters['dietary_tags'] = [tag.value for tag in request.dietary_tags]
    if request.difficulty:
        filters['difficulty'] = request.difficulty.value
    if request.max_prep_time:
        filters['max_prep_time'] = request.max_prep_time
    if request.max_cook_time:
        filters['max_cook_time'] = request.max_cook_time
    if request.max_total_time:
        filters['max_total_time'] = request.max_total_time
    
    result = search_service.search_dict(
        filters=filters if filters else None,
        query=request.query,
        limit=request.limit,
        offset=request.offset,
        use_semantic=request.use_semantic
    )
    
    return result


@router.post("/{recipe_id}/embed", response_model=dict)
async def embed_recipe(recipe_id: int):
    """
    Generate or update the embedding for a specific recipe.
    
    Creates a vector embedding for semantic search functionality.
    """
    recipe_service = RecipeService()
    embedding_service = EmbeddingService()
    
    # Get the recipe
    recipe_result = recipe_service.get_recipe(recipe_id)
    if recipe_result.get("status") == "error":
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    recipe = recipe_result.get("recipe")
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    try:
        embedding_service.embed_recipe(recipe)
        return {
            "status": "success",
            "message": f"Embedding generated for recipe {recipe_id}",
            "recipe_id": recipe_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")


@router.post("/embed-all", response_model=dict)
async def embed_all_recipes():
    """
    Generate embeddings for all recipes that don't have them.
    
    This is an admin operation that can take a while for large databases.
    """
    from src.database import RecipeRepository
    
    recipe_repo = RecipeRepository()
    embedding_service = EmbeddingService()
    
    try:
        # Get all recipes
        recipes = recipe_repo.search_recipes(limit=10000)  # High limit to get all
        
        # Convert to dicts and embed
        recipe_dicts = []
        for recipe in recipes:
            recipe_dict = recipe.model_dump() if hasattr(recipe, 'model_dump') else dict(recipe)
            # Get full recipe with ingredients for better embeddings
            full_recipe = recipe_repo.get_recipe_with_ingredients(recipe.id)
            if full_recipe:
                recipe_dict = full_recipe.model_dump() if hasattr(full_recipe, 'model_dump') else dict(full_recipe)
            recipe_dicts.append(recipe_dict)
        
        embedded_count = embedding_service.embed_recipes_batch(recipe_dicts)
        
        return {
            "status": "success",
            "message": f"Embedded {embedded_count} recipes",
            "total_recipes": len(recipes),
            "embedded_count": embedded_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")


@router.get("/{recipe_id}", response_model=dict)
async def get_recipe(recipe_id: int):
    """
    Get a specific recipe by ID.
    
    Returns the full recipe details including ingredients.
    """
    service = RecipeService()
    result = service.get_recipe(recipe_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Recipe not found"))
    
    return result


@router.post("", response_model=dict, status_code=201)
async def create_recipe(recipe: RecipeCreate):
    """
    Create a new recipe.
    
    Validates the recipe data and stores it in the database.
    """
    service = RecipeService()
    result = service.create_recipe(recipe)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to create recipe"))
    
    return result


@router.put("/{recipe_id}", response_model=dict)
async def update_recipe(recipe_id: int, recipe: RecipeUpdate):
    """
    Update an existing recipe.
    
    Only the fields provided will be updated.
    """
    service = RecipeService()
    result = service.update_recipe(recipe_id, recipe)
    
    if result.get("status") == "error":
        if "not found" in result.get("message", "").lower():
            raise HTTPException(status_code=404, detail=result.get("message"))
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to update recipe"))
    
    return result


@router.delete("/{recipe_id}", response_model=dict)
async def delete_recipe(recipe_id: int):
    """
    Delete a recipe by ID.
    """
    service = RecipeService()
    result = service.delete_recipe(recipe_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Recipe not found"))
    
    return result


@router.post("/discover", response_model=dict)
async def discover_recipes(
    cuisine: Optional[str] = Query(None, description="Cuisine type to search for"),
    dietary_restrictions: Optional[List[str]] = Query(None, description="Dietary restrictions"),
    ingredients: Optional[List[str]] = Query(None, description="Available ingredients"),
    max_prep_time: Optional[int] = Query(None, ge=1, description="Maximum prep time in minutes"),
    query: Optional[str] = Query(None, description="Natural language search query"),
):
    """
    Discover new recipes using AI agents.
    
    Uses the Recipe Scout agent to find recipes from external sources
    based on the provided criteria.
    """
    service = RecipeService()
    result = service.discover_recipes(
        cuisine=cuisine,
        dietary_restrictions=dietary_restrictions,
        ingredients=ingredients,
        max_prep_time=max_prep_time,
        original_query=query,
    )
    return result

