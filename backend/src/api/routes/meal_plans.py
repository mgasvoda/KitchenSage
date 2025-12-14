"""
Meal Plan API endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from src.models import MealPlanCreate
from src.services import MealPlanService

router = APIRouter()


@router.get("", response_model=dict)
async def list_meal_plans(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List all meal plans.
    
    Returns a paginated list of meal plans.
    """
    service = MealPlanService()
    result = service.list_meal_plans(limit=limit, offset=offset)
    return result


@router.get("/{meal_plan_id}", response_model=dict)
async def get_meal_plan(meal_plan_id: int):
    """
    Get a specific meal plan by ID.
    
    Returns the full meal plan with all associated meals and recipes.
    """
    service = MealPlanService()
    result = service.get_meal_plan(meal_plan_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Meal plan not found"))
    
    return result


@router.post("", response_model=dict, status_code=201)
async def create_meal_plan(
    days: int = Query(7, ge=1, le=30, description="Number of days for the meal plan"),
    people: int = Query(2, ge=1, le=20, description="Number of people to plan for"),
    dietary_restrictions: Optional[List[str]] = Query(None, description="Dietary restrictions"),
    budget: Optional[float] = Query(None, ge=0, description="Budget constraint"),
):
    """
    Create a new meal plan using AI agents.
    
    Uses the Meal Planner agent to create an optimized meal plan
    based on the provided parameters.
    """
    service = MealPlanService()
    result = service.create_meal_plan(
        days=days,
        people=people,
        dietary_restrictions=dietary_restrictions,
        budget=budget,
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to create meal plan"))
    
    return result


@router.delete("/{meal_plan_id}", response_model=dict)
async def delete_meal_plan(meal_plan_id: int):
    """
    Delete a meal plan by ID.
    """
    service = MealPlanService()
    result = service.delete_meal_plan(meal_plan_id)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Meal plan not found"))
    
    return result

