"""
Grocery List API endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from src.services import GroceryService

router = APIRouter()


@router.get("", response_model=dict)
async def list_grocery_lists(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List all grocery lists.
    
    Returns a paginated list of grocery lists.
    """
    service = GroceryService()
    result = service.list_grocery_lists(limit=limit, offset=offset)
    return result


@router.get("/default", response_model=dict)
async def get_default_grocery_list():
    """
    Get the default grocery list, creating one if it doesn't exist.
    
    Since the app uses a single grocery list, this endpoint returns
    that list or creates it if needed.
    """
    service = GroceryService()
    result = service.get_or_create_default_list()
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to get grocery list"))
    
    return result


@router.get("/{grocery_list_id}", response_model=dict)
async def get_grocery_list(grocery_list_id: int):
    """
    Get a specific grocery list by ID.
    
    Returns the full grocery list with all items.
    """
    service = GroceryService()
    result = service.get_grocery_list(grocery_list_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Grocery list not found"))
    
    return result


@router.post("", response_model=dict, status_code=201)
async def generate_grocery_list(
    meal_plan_id: int = Query(..., description="Meal plan ID to generate grocery list from"),
):
    """
    Generate a grocery list from a meal plan using AI agents.
    
    Uses the Grocery List agent to create an optimized shopping list
    from the specified meal plan.
    """
    service = GroceryService()
    result = service.generate_grocery_list(meal_plan_id=meal_plan_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to generate grocery list"))
    
    return result


@router.put("/{grocery_list_id}/items/{item_id}", response_model=dict)
async def update_grocery_item(
    grocery_list_id: int,
    item_id: int,
    checked: bool = Query(..., description="Whether the item is checked off"),
):
    """
    Update a grocery list item (e.g., mark as checked).
    """
    service = GroceryService()
    result = service.update_item(grocery_list_id, item_id, checked=checked)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Item not found"))
    
    return result


@router.delete("/{grocery_list_id}", response_model=dict)
async def delete_grocery_list(grocery_list_id: int):
    """
    Delete a grocery list by ID.
    """
    service = GroceryService()
    result = service.delete_grocery_list(grocery_list_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Grocery list not found"))
    
    return result


@router.post("/add-from-recipe", response_model=dict)
async def add_from_recipe(
    recipe_id: int = Query(..., description="Recipe ID to add ingredients from"),
    servings: Optional[int] = Query(None, description="Number of servings (uses recipe default if not provided)"),
):
    """
    Add ingredients from a recipe to the grocery list.
    
    Gets or creates the default grocery list, then merges recipe
    ingredients into it. If ingredients already exist, quantities
    are combined.
    """
    service = GroceryService()
    result = service.add_recipe_ingredients(recipe_id=recipe_id, servings=servings)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to add recipe ingredients"))
    
    return result


@router.post("/add-from-meal-plan", response_model=dict)
async def add_from_meal_plan(
    meal_plan_id: int = Query(..., description="Meal plan ID to add ingredients from"),
):
    """
    Add all ingredients from a meal plan to the grocery list.
    
    Gets or creates the default grocery list, then merges all
    recipe ingredients from the meal plan into it. Quantities
    are adjusted for servings and combined for duplicate ingredients.
    """
    service = GroceryService()
    result = service.add_meal_plan_ingredients(meal_plan_id=meal_plan_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to add meal plan ingredients"))
    
    return result


@router.delete("/{grocery_list_id}/checked", response_model=dict)
async def clear_checked_items(grocery_list_id: int):
    """
    Remove all checked/purchased items from a grocery list.
    """
    service = GroceryService()
    result = service.clear_checked_items(grocery_list_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Grocery list not found"))
    
    return result


@router.delete("/{grocery_list_id}/items", response_model=dict)
async def clear_all_items(grocery_list_id: int):
    """
    Remove all items from a grocery list.
    """
    service = GroceryService()
    result = service.clear_all_items(grocery_list_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Grocery list not found"))
    
    return result

