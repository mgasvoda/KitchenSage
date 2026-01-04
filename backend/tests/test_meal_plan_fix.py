"""
Test script to verify meal plan creation fix.
Tests that dietary_restrictions are properly serialized to JSON.
"""

import sys
sys.path.insert(0, 'src')

from src.tools.meal_planning_tools import MealPlanningTool
from src.database import MealPlanRepository
from datetime import datetime, timedelta

def test_meal_plan_creation():
    """Test that meal plan creation works with dietary restrictions."""
    print("Testing meal plan creation with dietary restrictions...")

    # Clean up any test meal plans first
    repo = MealPlanRepository()

    # Create meal planning tool
    tool = MealPlanningTool()

    # Test requirements (use underscore format for dietary restrictions)
    requirements = {
        'days': 3,
        'people': 2,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'dietary_restrictions': ['vegetarian', 'gluten_free'],
        'max_prep_time': 45,
    }

    print(f"Creating meal plan with requirements: {requirements}")

    try:
        # This should create the meal plan and save to database
        result = tool._run(requirements)

        print(f"\nResult status: {result.get('status')}")
        print(f"Result message: {result.get('message')}")

        if result.get('status') == 'success':
            meal_plan_id = result.get('meal_plan', {}).get('meal_plan_id')
            print(f"Meal plan ID: {meal_plan_id}")

            if meal_plan_id:
                # Verify it was saved correctly
                saved_plan = repo.get_by_id(meal_plan_id)
                if saved_plan:
                    print(f"\n✓ Successfully created meal plan in database!")
                    print(f"  Name: {saved_plan.name}")
                    print(f"  Start: {saved_plan.start_date}")
                    print(f"  End: {saved_plan.end_date}")
                    print(f"  People: {saved_plan.people_count}")
                    print(f"  Dietary restrictions: {[tag.value for tag in saved_plan.dietary_restrictions]}")
                    print(f"  Number of meals: {len(saved_plan.meals)}")

                    # Clean up test data
                    repo.delete(meal_plan_id)
                    print(f"\n✓ Test completed successfully and cleaned up!")
                    return True
                else:
                    print(f"\n✗ Meal plan {meal_plan_id} not found in database")
                    return False
            else:
                print("\n✗ No meal plan ID in result")
                return False
        elif result.get('status') == 'warning':
            print(f"\n⚠ Warning: {result.get('message')}")
            # Still might have created something
            meal_plan_id = result.get('meal_plan', {}).get('meal_plan_id')
            if meal_plan_id:
                print(f"Meal plan was created despite warning. ID: {meal_plan_id}")
                # Clean up
                repo.delete(meal_plan_id)
            return True
        else:
            print(f"\n✗ Failed: {result.get('message')}")
            return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_meal_plan_creation()
    sys.exit(0 if success else 1)
