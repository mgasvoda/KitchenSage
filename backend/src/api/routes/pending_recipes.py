"""
Pending recipes API endpoints for URL parsing and AI discovery.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl

from src.services import PendingRecipeService

router = APIRouter()


class ParseUrlRequest(BaseModel):
    """Request model for URL parsing."""
    url: str = Field(..., description="URL of the recipe to parse")


class DiscoverRecipesRequest(BaseModel):
    """Request model for AI recipe discovery."""
    query: str = Field(..., min_length=2, description="Natural language search query")
    cuisine: Optional[str] = Field(None, description="Cuisine type filter")
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of recipes to discover")


class UpdatePendingRequest(BaseModel):
    """Request model for updating a pending recipe."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    prep_time: Optional[int] = Field(None, ge=0)
    cook_time: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1, le=50)
    difficulty: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_tags: Optional[List[str]] = None
    ingredients: Optional[List[dict]] = None
    instructions: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None


@router.post("/parse", response_model=dict)
async def parse_recipe_url(request: ParseUrlRequest):
    """
    Parse a recipe from a URL and save it for review.
    
    Extracts recipe data (ingredients, instructions, etc.) from a given URL
    and saves it as a pending recipe for user approval.
    """
    service = PendingRecipeService()
    result = service.parse_url(request.url)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to parse URL"))
    
    return result


@router.post("/discover", response_model=dict)
async def discover_recipes(request: DiscoverRecipesRequest):
    """
    Discover new recipes using AI-powered search.
    
    Searches for recipes matching the given criteria and saves them
    as pending recipes for user approval.
    """
    service = PendingRecipeService()
    result = service.discover_recipes(
        query=request.query,
        cuisine=request.cuisine,
        dietary_restrictions=request.dietary_restrictions,
        max_results=request.max_results
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Discovery failed"))
    
    return result


@router.get("", response_model=dict)
async def list_pending_recipes(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """
    List all pending recipes awaiting review.
    
    Returns recipes that have been parsed or discovered but not yet
    approved or rejected by the user.
    """
    service = PendingRecipeService()
    result = service.list_pending(limit=limit)
    
    return result


@router.get("/{pending_id}", response_model=dict)
async def get_pending_recipe(pending_id: int):
    """
    Get a specific pending recipe by ID.
    
    Returns the full details of a pending recipe for review.
    """
    service = PendingRecipeService()
    result = service.get_pending(pending_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Pending recipe not found"))
    
    return result


@router.put("/{pending_id}", response_model=dict)
async def update_pending_recipe(pending_id: int, request: UpdatePendingRequest):
    """
    Update a pending recipe before approval.
    
    Allows editing recipe details (name, ingredients, instructions, etc.)
    before approving it into the main collection.
    """
    service = PendingRecipeService()
    
    # Convert request to dict, excluding None values
    update_data = request.model_dump(exclude_none=True)
    
    result = service.update_pending(pending_id, update_data)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Failed to update"))
    
    return result


@router.post("/{pending_id}/approve", response_model=dict)
async def approve_pending_recipe(pending_id: int):
    """
    Approve a pending recipe and add it to the main collection.
    
    Validates the pending recipe data and creates a new recipe in the
    main recipes table. The pending recipe is then deleted.
    """
    service = PendingRecipeService()
    result = service.approve(pending_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to approve"))
    
    return result


@router.delete("/{pending_id}", response_model=dict)
async def reject_pending_recipe(pending_id: int):
    """
    Reject and delete a pending recipe.
    
    Removes the pending recipe from the staging area without
    adding it to the main collection.
    """
    service = PendingRecipeService()
    result = service.reject(pending_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Failed to reject"))
    
    return result

