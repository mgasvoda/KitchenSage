"""
Ingredient data models for recipes and shopping.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class IngredientCategory(str, Enum):
    """Categories for organizing ingredients."""
    PRODUCE = "produce"
    MEAT = "meat"
    SEAFOOD = "seafood"
    DAIRY = "dairy"
    PANTRY = "pantry"
    SPICES = "spices"
    GRAINS = "grains"
    LEGUMES = "legumes"
    NUTS_SEEDS = "nuts_seeds"
    BEVERAGES = "beverages"
    FROZEN = "frozen"
    CANNED = "canned"
    BAKING = "baking"
    CONDIMENTS = "condiments"
    OTHER = "other"


class MeasurementUnit(str, Enum):
    """Standard measurement units for ingredients."""
    # Volume
    CUP = "cup"
    TABLESPOON = "tbsp"
    TEASPOON = "tsp"
    FLUID_OUNCE = "fl oz"
    PINT = "pint"
    QUART = "quart"
    GALLON = "gallon"
    MILLILITER = "ml"
    LITER = "liter"
    
    # Weight
    OUNCE = "oz"
    POUND = "lb"
    GRAM = "g"
    KILOGRAM = "kg"
    
    # Count
    PIECE = "piece"
    ITEM = "item"
    CLOVE = "clove"
    SLICE = "slice"
    
    # Other
    PINCH = "pinch"
    DASH = "dash"
    TO_TASTE = "to taste"


class Ingredient(BaseModel):
    """
    Base ingredient model representing a single ingredient.
    """
    
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100, description="Ingredient name")
    category: IngredientCategory = Field(default=IngredientCategory.OTHER, description="Ingredient category")
    common_unit: Optional[MeasurementUnit] = Field(None, description="Most common unit for this ingredient")
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('name')
    def normalize_name(cls, v):
        """Normalize ingredient names to lowercase and strip whitespace."""
        return v.strip().lower()
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "chicken breast",
                "category": "meat",
                "common_unit": "lb"
            }
        }


class IngredientCreate(BaseModel):
    """Model for creating a new ingredient."""
    
    name: str = Field(..., min_length=1, max_length=100)
    category: IngredientCategory = IngredientCategory.OTHER
    common_unit: Optional[MeasurementUnit] = None
    
    @validator('name')
    def normalize_name(cls, v):
        return v.strip().lower()


class IngredientUpdate(BaseModel):
    """Model for updating an existing ingredient."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[IngredientCategory] = None
    common_unit: Optional[MeasurementUnit] = None
    
    @validator('name')
    def normalize_name(cls, v):
        if v is not None:
            return v.strip().lower()
        return v


class RecipeIngredient(BaseModel):
    """
    Model representing an ingredient as used in a specific recipe.
    
    This includes quantity, unit, and any recipe-specific notes.
    """
    
    id: Optional[int] = None
    recipe_id: Optional[int] = None
    ingredient_id: Optional[int] = None
    
    # Ingredient reference (for denormalized access)
    ingredient: Optional[Ingredient] = None
    
    quantity: float = Field(..., gt=0, description="Amount of ingredient needed")
    unit: MeasurementUnit = Field(..., description="Unit of measurement")
    notes: Optional[str] = Field(None, max_length=200, description="Additional notes (e.g., 'diced', 'optional')")
    
    # For grocery shopping
    optional: bool = Field(default=False, description="Whether this ingredient is optional")
    substitutes: List[str] = Field(default_factory=list, description="Possible substitutes")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "quantity": 1.5,
                "unit": "lb",
                "notes": "boneless, skinless, diced",
                "optional": False,
                "substitutes": ["turkey breast", "tofu"]
            }
        }
    
    def display_quantity(self) -> str:
        """Format quantity for display."""
        if self.quantity == int(self.quantity):
            return f"{int(self.quantity)} {self.unit}"
        else:
            # Handle fractions nicely
            if self.quantity < 1:
                # Convert to fraction for common values
                fraction_map = {
                    0.25: "1/4",
                    0.33: "1/3", 
                    0.5: "1/2",
                    0.67: "2/3",
                    0.75: "3/4"
                }
                for decimal, fraction in fraction_map.items():
                    if abs(self.quantity - decimal) < 0.01:
                        return f"{fraction} {self.unit}"
            
            return f"{self.quantity:.2f} {self.unit}".rstrip('0').rstrip('.')
    
    def get_base_name(self) -> str:
        """Get the base ingredient name without notes."""
        if self.ingredient:
            return self.ingredient.name
        return "Unknown ingredient" 