"""
Meal Plan API endpoints.
"""

import json
from typing import Optional, List, AsyncGenerator
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.models import MealPlanCreate
from src.services import MealPlanService

router = APIRouter()


async def generate_meal_plan_sse_stream(
    days: int,
    people: int,
    prompt: Optional[str],
    budget: Optional[float],
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events stream for meal plan creation.
    
    Streams agent activity events as the AI creates the meal plan.
    Properly handles client disconnection to prevent orphaned threads.
    """
    service = MealPlanService()
    stream = None
    
    try:
        stream = service.create_meal_plan_stream(
            days=days,
            people=people,
            prompt=prompt,
            budget=budget,
        )
        
        async for event in stream:
            yield f"data: {json.dumps(event)}\n\n"
        
        # Send done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except GeneratorExit:
        # Client disconnected - ensure the service stream is properly closed
        if stream is not None:
            await stream.aclose()
        raise
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/stream", response_class=StreamingResponse)
async def create_meal_plan_stream(
    days: int = Query(7, ge=1, le=30, description="Number of days for the meal plan"),
    people: int = Query(2, ge=1, le=20, description="Number of people to plan for"),
    prompt: Optional[str] = Query(None, description="Free-form preferences and instructions for the meal plan"),
    budget: Optional[float] = Query(None, ge=0, description="Budget constraint"),
):
    """
    Create a meal plan with real-time SSE streaming of agent activity.
    
    Streams events as the AI agent works:
    - agent_thinking: Agent is reasoning
    - tool_start: Tool is being invoked
    - tool_result: Tool returned a result
    - task_complete: A task finished
    - preview_update: Partial meal plan preview
    - complete: Final meal plan ready
    - error: An error occurred
    - done: Stream complete
    """
    return StreamingResponse(
        generate_meal_plan_sse_stream(days, people, prompt, budget),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


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
    prompt: Optional[str] = Query(None, description="Free-form preferences and instructions for the meal plan"),
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
        prompt=prompt,
        budget=budget,
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to create meal plan"))
    
    return result


@router.post("/{meal_plan_id}/activate", response_model=dict)
async def activate_meal_plan(meal_plan_id: int):
    """
    Set a meal plan as the active plan.

    Automatically deactivates all other meal plans.
    Only one meal plan can be active at a time.
    """
    service = MealPlanService()
    result = service.set_active_meal_plan(meal_plan_id)

    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Meal plan not found"))

    return result


@router.get("/active", response_model=dict)
async def get_active_meal_plan():
    """
    Get the currently active meal plan.

    Returns the active meal plan with all meals and recipes, or None if no plan is active.
    """
    service = MealPlanService()
    result = service.get_active_meal_plan()
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

