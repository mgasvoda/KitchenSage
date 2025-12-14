"""
Recipe data models for the cooking assistant.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from .ingredient import RecipeIngredient
from .nutritional_info import NutritionalInfo


class DifficultyLevel(str, Enum):
    """Recipe difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CuisineType(str, Enum):
    """Common cuisine types."""
    AMERICAN = "american"
    ITALIAN = "italian"
    MEXICAN = "mexican"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    INDIAN = "indian"
    FRENCH = "french"
    THAI = "thai"
    GREEK = "greek"
    MEDITERRANEAN = "mediterranean"
    SPANISH = "spanish"
    GERMAN = "german"
    KOREAN = "korean"
    VIETNAMESE = "vietnamese"
    MIDDLE_EASTERN = "middle_eastern"
    AFRICAN = "african"
    FUSION = "fusion"
    OTHER = "other"


class DietaryTag(str, Enum):
    """Dietary restriction and preference tags."""
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    SOY_FREE = "soy_free"
    EGG_FREE = "egg_free"
    LOW_CARB = "low_carb"
    KETO = "keto"
    PALEO = "paleo"
    WHOLE30 = "whole30"
    LOW_SODIUM = "low_sodium"
    LOW_FAT = "low_fat"
    HIGH_PROTEIN = "high_protein"
    DIABETIC_FRIENDLY = "diabetic_friendly"
    HEART_HEALTHY = "heart_healthy"


class Recipe(BaseModel):
    """
    Complete recipe model with all details.
    """
    
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200, description="Recipe name")
    description: Optional[str] = Field(None, max_length=1000, description="Recipe description")
    
    # Timing
    prep_time: int = Field(..., ge=0, description="Preparation time in minutes")
    cook_time: int = Field(..., ge=0, description="Cooking time in minutes")
    total_time: Optional[int] = Field(None, description="Total time (calculated)")
    
    # Serving info
    servings: int = Field(..., ge=1, le=50, description="Number of servings")
    
    # Classification
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM, description="Recipe difficulty")
    cuisine: CuisineType = Field(default=CuisineType.OTHER, description="Cuisine type")
    dietary_tags: List[DietaryTag] = Field(default_factory=list, description="Dietary restrictions and tags")
    
    # Recipe content
    ingredients: List[RecipeIngredient] = Field(default_factory=list, description="Recipe ingredients")
    instructions: List[str] = Field(..., min_items=1, description="Cooking instructions")
    
    # Optional details
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes or tips")
    source: Optional[str] = Field(None, max_length=200, description="Recipe source")
    image_url: Optional[str] = Field(None, description="URL to recipe image")
    
    # Nutritional information
    nutritional_info: Optional[NutritionalInfo] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('total_time', always=True)
    def calculate_total_time(cls, v, values):
        """Calculate total time from prep and cook times."""
        if 'prep_time' in values and 'cook_time' in values:
            return values['prep_time'] + values['cook_time']
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Normalize recipe name."""
        return v.strip().title()
    
    @validator('instructions')
    def validate_instructions(cls, v):
        """Ensure instructions are not empty and strip whitespace."""
        if not v:
            raise ValueError("Recipe must have at least one instruction")
        return [instruction.strip() for instruction in v if instruction.strip()]
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Chicken Stir Fry",
                "description": "A quick and healthy chicken stir fry with vegetables",
                "prep_time": 15,
                "cook_time": 10,
                "servings": 4,
                "difficulty": "easy",
                "cuisine": "chinese",
                "dietary_tags": ["gluten_free", "high_protein"],
                "instructions": [
                    "Cut chicken into bite-sized pieces",
                    "Heat oil in wok over high heat",
                    "Add chicken and cook for 3-4 minutes",
                    "Add vegetables and stir fry for 5 minutes",
                    "Add sauce and toss to coat"
                ],
                "notes": "Can substitute chicken with tofu for vegetarian version"
            }
        }
    
    def get_estimated_calories_per_serving(self) -> Optional[float]:
        """Get estimated calories per serving."""
        if self.nutritional_info and self.nutritional_info.calories:
            return self.nutritional_info.calories
        return None
    
    def get_dietary_tags_display(self) -> str:
        """Get dietary tags as a comma-separated string."""
        return ", ".join([tag.value.replace("_", " ").title() for tag in self.dietary_tags])
    
    def is_suitable_for_diet(self, dietary_requirements: List[str]) -> bool:
        """Check if recipe meets dietary requirements."""
        recipe_tags = [tag.value for tag in self.dietary_tags]
        return all(req in recipe_tags for req in dietary_requirements)


class RecipeCreate(BaseModel):
    """Model for creating a new recipe."""
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    prep_time: int = Field(..., ge=0)
    cook_time: int = Field(..., ge=0)
    servings: int = Field(..., ge=1, le=50)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    cuisine: CuisineType = CuisineType.OTHER
    dietary_tags: List[DietaryTag] = Field(default_factory=list)
    instructions: List[str] = Field(..., min_items=1)
    notes: Optional[str] = Field(None, max_length=500)
    source: Optional[str] = Field(None, max_length=200)
    image_url: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        return v.strip().title()
    
    @validator('instructions')
    def validate_instructions(cls, v):
        if not v:
            raise ValueError("Recipe must have at least one instruction")
        return [instruction.strip() for instruction in v if instruction.strip()]


class RecipeUpdate(BaseModel):
    """Model for updating an existing recipe."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    prep_time: Optional[int] = Field(None, ge=0)
    cook_time: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1, le=50)
    difficulty: Optional[DifficultyLevel] = None
    cuisine: Optional[CuisineType] = None
    dietary_tags: Optional[List[DietaryTag]] = None
    instructions: Optional[List[str]] = Field(None, min_items=1)
    notes: Optional[str] = Field(None, max_length=500)
    source: Optional[str] = Field(None, max_length=200)
    image_url: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            return v.strip().title()
        return v
    
    @validator('instructions')
    def validate_instructions(cls, v):
        if v is not None:
            if not v:
                raise ValueError("Recipe must have at least one instruction")
            return [instruction.strip() for instruction in v if instruction.strip()]
        return v 