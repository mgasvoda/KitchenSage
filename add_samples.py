#!/usr/bin/env python3
"""
Temporary script to add sample recipes to the database.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.recipe_repository import RecipeRepository
from src.models import RecipeCreate, DietaryTag, DifficultyLevel, CuisineType

def add_sample_recipes():
    """Add sample recipes to the database."""
    
    sample_recipes = [
        RecipeCreate(
            name="Quick Pasta Carbonara",
            description="Classic Italian pasta with eggs and pancetta",
            cuisine=CuisineType.ITALIAN,
            difficulty=DifficultyLevel.MEDIUM,
            prep_time=10,
            cook_time=15,
            servings=4,
            dietary_tags=[],
            instructions=[
                "Boil pasta in salted water",
                "Cook pancetta until crispy", 
                "Beat eggs with cheese",
                "Combine pasta with pancetta and egg mixture"
            ]
        ),
        RecipeCreate(
            name="Simple Green Salad",
            description="Fresh mixed greens with vinaigrette",
            cuisine=CuisineType.AMERICAN,
            difficulty=DifficultyLevel.EASY,
            prep_time=10,
            cook_time=0,
            servings=4,
            dietary_tags=[DietaryTag.VEGETARIAN, DietaryTag.VEGAN, DietaryTag.LOW_FAT],
            instructions=[
                "Wash and dry greens",
                "Whisk oil and vinegar",
                "Toss salad with dressing"
            ]
        ),
        RecipeCreate(
            name="Grilled Chicken Breast",
            description="Simple grilled chicken with herbs",
            cuisine=CuisineType.AMERICAN,
            difficulty=DifficultyLevel.EASY,
            prep_time=5,
            cook_time=20,
            servings=4,
            dietary_tags=[DietaryTag.GLUTEN_FREE, DietaryTag.LOW_CARB, DietaryTag.HIGH_PROTEIN],
            instructions=[
                "Preheat grill to medium-high heat",
                "Season chicken with salt, pepper, and garlic powder",
                "Brush with olive oil",
                "Grill 6-8 minutes per side until cooked through"
            ]
        )
    ]
    
    # Sample ingredients for each recipe
    recipe_ingredients = [
        [  # Carbonara ingredients
            {"name": "spaghetti", "quantity": 400, "unit": "gram"},
            {"name": "pancetta", "quantity": 150, "unit": "gram"},
            {"name": "eggs", "quantity": 3, "unit": "piece"},
            {"name": "parmesan cheese", "quantity": 100, "unit": "gram"}
        ],
        [  # Salad ingredients
            {"name": "mixed greens", "quantity": 200, "unit": "gram"},
            {"name": "olive oil", "quantity": 3, "unit": "tbsp"},
            {"name": "balsamic vinegar", "quantity": 1, "unit": "tbsp"},
            {"name": "salt", "quantity": 0.5, "unit": "tsp"}
        ],
        [  # Chicken ingredients
            {"name": "chicken breast", "quantity": 800, "unit": "gram"},
            {"name": "olive oil", "quantity": 2, "unit": "tbsp"},
            {"name": "salt", "quantity": 1, "unit": "tsp"},
            {"name": "black pepper", "quantity": 0.5, "unit": "tsp"},
            {"name": "garlic powder", "quantity": 1, "unit": "tsp"}
        ]
    ]
    
    repo = RecipeRepository()
    created_count = 0
    
    for i, recipe_data in enumerate(sample_recipes):
        try:
            recipe = repo.create_recipe(recipe_data, recipe_ingredients[i])
            created_count += 1
            print(f"✅ Created: {recipe.name} (ID: {recipe.id})")
                
        except Exception as e:
            print(f"❌ Error creating {recipe_data.name}: {e}")
    
    print(f"\n✅ Successfully created {created_count}/{len(sample_recipes)} sample recipes!")

if __name__ == "__main__":
    add_sample_recipes() 