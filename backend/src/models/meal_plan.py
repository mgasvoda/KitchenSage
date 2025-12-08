"""
Meal plan data models for organizing recipes into scheduled meals.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime, date
from enum import Enum

from .recipe import Recipe, DietaryTag


class MealType(str, Enum):
    """Types of meals in a day."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"


class Meal(BaseModel):
    """
    Individual meal within a meal plan.
    
    Links a recipe to a specific day and meal type.
    """
    
    id: Optional[int] = None
    meal_plan_id: Optional[int] = None
    recipe_id: Optional[int] = None
    
    # Recipe reference (for denormalized access)
    recipe: Optional[Recipe] = None
    
    meal_type: MealType = Field(..., description="Type of meal")
    meal_date: date = Field(..., description="Date for this meal")
    
    # Optional customizations
    servings_override: Optional[int] = Field(None, ge=1, description="Override recipe serving size")
    notes: Optional[str] = Field(None, max_length=200, description="Meal-specific notes")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "meal_type": "dinner",
                "meal_date": "2024-01-15",
                "servings_override": 4,
                "notes": "Double the vegetables"
            }
        }
    
    def get_effective_servings(self) -> int:
        """Get the number of servings for this meal."""
        if self.servings_override:
            return self.servings_override
        elif self.recipe:
            return self.recipe.servings
        return 1
    
    def get_recipe_name(self) -> str:
        """Get the recipe name for this meal."""
        if self.recipe:
            return self.recipe.name
        return "Unknown Recipe"


class MealPlan(BaseModel):
    """
    Complete meal plan model containing multiple meals over a time period.
    """
    
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200, description="Meal plan name")
    
    # Date range
    start_date: date = Field(..., description="Start date of meal plan")
    end_date: date = Field(..., description="End date of meal plan")
    
    # Target audience
    people_count: int = Field(..., ge=1, le=20, description="Number of people this plan serves")
    
    # Dietary considerations
    dietary_restrictions: List[DietaryTag] = Field(
        default_factory=list, 
        description="Dietary restrictions for this meal plan"
    )
    
    # Meals in this plan
    meals: List[Meal] = Field(default_factory=list, description="All meals in this plan")
    
    # Optional metadata
    description: Optional[str] = Field(None, max_length=500, description="Meal plan description")
    budget_target: Optional[float] = Field(None, ge=0, description="Target budget for groceries")
    calories_per_day_target: Optional[int] = Field(None, ge=800, le=5000, description="Target calories per day")
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Ensure end date is after start date."""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Normalize meal plan name."""
        return v.strip().title()
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Weekly Family Meal Plan",
                "start_date": "2024-01-15",
                "end_date": "2024-01-21",
                "people_count": 4,
                "dietary_restrictions": ["vegetarian"],
                "description": "Healthy vegetarian meals for a family of 4",
                "budget_target": 150.00,
                "calories_per_day_target": 2000
            }
        }
    
    def get_duration_days(self) -> int:
        """Get the number of days in this meal plan."""
        return (self.end_date - self.start_date).days + 1
    
    def get_meals_by_date(self) -> Dict[date, List[Meal]]:
        """Group meals by date."""
        meals_by_date = {}
        for meal in self.meals:
            if meal.meal_date not in meals_by_date:
                meals_by_date[meal.meal_date] = []
            meals_by_date[meal.meal_date].append(meal)
        return meals_by_date
    
    def get_meals_by_type(self, meal_type: MealType) -> List[Meal]:
        """Get all meals of a specific type."""
        return [meal for meal in self.meals if meal.meal_type == meal_type]
    
    def get_unique_recipes(self) -> List[Recipe]:
        """Get list of unique recipes used in this meal plan."""
        unique_recipes = {}
        for meal in self.meals:
            if meal.recipe and meal.recipe.id:
                unique_recipes[meal.recipe.id] = meal.recipe
        return list(unique_recipes.values())
    
    def calculate_total_servings_needed(self) -> Dict[int, int]:
        """Calculate total servings needed per recipe."""
        servings_count = {}
        for meal in self.meals:
            if meal.recipe_id:
                effective_servings = meal.get_effective_servings()
                if meal.recipe_id in servings_count:
                    servings_count[meal.recipe_id] += effective_servings
                else:
                    servings_count[meal.recipe_id] = effective_servings
        return servings_count
    
    def has_dietary_conflicts(self) -> List[str]:
        """Check for dietary conflicts in assigned recipes."""
        conflicts = []
        plan_restrictions = [tag.value for tag in self.dietary_restrictions]
        
        for meal in self.meals:
            if meal.recipe:
                if not meal.recipe.is_suitable_for_diet(plan_restrictions):
                    conflicts.append(
                        f"{meal.recipe.name} on {meal.meal_date} ({meal.meal_type}) "
                        f"conflicts with dietary restrictions"
                    )
        
        return conflicts


class MealPlanCreate(BaseModel):
    """Model for creating a new meal plan."""
    
    name: str = Field(..., min_length=1, max_length=200)
    start_date: date
    end_date: date
    people_count: int = Field(..., ge=1, le=20)
    dietary_restrictions: List[DietaryTag] = Field(default_factory=list)
    description: Optional[str] = Field(None, max_length=500)
    budget_target: Optional[float] = Field(None, ge=0)
    calories_per_day_target: Optional[int] = Field(None, ge=800, le=5000)
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v
    
    @validator('name')
    def validate_name(cls, v):
        return v.strip().title()


class MealPlanUpdate(BaseModel):
    """Model for updating an existing meal plan."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    people_count: Optional[int] = Field(None, ge=1, le=20)
    dietary_restrictions: Optional[List[DietaryTag]] = None
    description: Optional[str] = Field(None, max_length=500)
    budget_target: Optional[float] = Field(None, ge=0)
    calories_per_day_target: Optional[int] = Field(None, ge=800, le=5000)
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            return v.strip().title()
        return v 