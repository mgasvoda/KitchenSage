"""
Recipe API endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from src.models import Recipe, RecipeCreate, RecipeUpdate, CuisineType, DietaryTag, DifficultyLevel
from src.services import RecipeService

router = APIRouter()


@router.get("", response_model=dict)
async def list_recipes(
    search: Optional[str] = Query(None, description="Search term for recipe name"),
    cuisine: Optional[CuisineType] = Query(None, description="Filter by cuisine type"),
    dietary_tags: Optional[List[DietaryTag]] = Query(None, description="Filter by dietary tags"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    max_prep_time: Optional[int] = Query(None, ge=1, description="Maximum prep time in minutes"),
    max_cook_time: Optional[int] = Query(None, ge=1, description="Maximum cook time in minutes"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List recipes with optional filters.
    
    Returns a paginated list of recipes matching the specified criteria.
    """
    service = RecipeService()
    result = service.search_recipes(
        search_term=search,
        cuisine=cuisine,
        dietary_tags=dietary_tags,
        difficulty=difficulty,
        max_prep_time=max_prep_time,
        max_cook_time=max_cook_time,
        limit=limit,
        offset=offset,
    )
    return result


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

