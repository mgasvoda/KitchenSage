"""
Complete end-to-end test of meal plan creation flow.
Tests the full stack from API to database.
"""

import sys
import asyncio
sys.path.insert(0, 'src')

from src.services.meal_plan_service import MealPlanService
from src.database import MealPlanRepository

async def test_complete_flow():
    """Test the complete meal plan creation flow."""
    print("Testing complete meal plan creation flow...")
    print("=" * 60)

    service = MealPlanService()
    repo = MealPlanRepository()

    # Get initial count
    initial_plans = repo.get_all()
    initial_count = len(initial_plans)
    print(f"Initial meal plan count: {initial_count}")

    # Test parameters
    params = {
        'days': 3,
        'people': 2,
        'dietary_restrictions': ['vegetarian'],
        'budget': 100.0,
    }

    print(f"\nCreating meal plan with params: {params}")
    print("-" * 60)

    events_received = []
    complete_event = None
    error_event = None

    # Stream events
    async for event in service.create_meal_plan_stream(**params):
        event_type = event.get('type')
        events_received.append(event_type)

        if event_type == 'agent_thinking':
            content = event.get('content', '')[:80]
            print(f"  [THINKING] {content}...")
        elif event_type == 'tool_start':
            tool = event.get('tool', 'Unknown')
            print(f"  [TOOL] Using {tool}...")
        elif event_type == 'tool_result':
            summary = event.get('summary', '')[:80]
            print(f"  [RESULT] {summary}")
        elif event_type == 'task_complete':
            task = event.get('task', 'Task')
            print(f"  [COMPLETE] {task}")
        elif event_type == 'complete':
            complete_event = event
            meal_plan_text = event.get('meal_plan', '')[:100]
            print(f"\n  ✓ COMPLETE: {meal_plan_text}...")
        elif event_type == 'error':
            error_event = event
            print(f"\n  ✗ ERROR: {event.get('content')}")
        elif event_type == 'done':
            print(f"  [DONE] Stream finished")

    print("-" * 60)
    print(f"\nTotal events received: {len(events_received)}")
    print(f"Event types: {set(events_received)}")

    # Check final state
    final_plans = repo.get_all()
    final_count = len(final_plans)
    print(f"\nFinal meal plan count: {final_count}")
    print(f"New meal plans created: {final_count - initial_count}")

    if complete_event:
        print("\n✓ Complete event was received")
    else:
        print("\n✗ Complete event was NOT received")

    if error_event:
        print(f"✗ Error occurred: {error_event.get('content')}")
        return False

    if final_count > initial_count:
        print("\n✓ Meal plan was successfully created in database")
        # Get the newest meal plan
        newest_plan = final_plans[-1]
        print(f"\n  Meal Plan Details:")
        print(f"  - ID: {newest_plan.id}")
        print(f"  - Name: {newest_plan.name}")
        print(f"  - Dates: {newest_plan.start_date} to {newest_plan.end_date}")
        print(f"  - People: {newest_plan.people_count}")
        print(f"  - Dietary restrictions: {[tag.value for tag in newest_plan.dietary_restrictions]}")
        print(f"  - Meals: {len(newest_plan.meals)}")

        # Clean up
        repo.delete(newest_plan.id)
        print(f"\n✓ Test data cleaned up")
        return True
    else:
        print("\n✗ No new meal plan was created")
        return False

if __name__ == '__main__':
    try:
        success = asyncio.run(test_complete_flow())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
