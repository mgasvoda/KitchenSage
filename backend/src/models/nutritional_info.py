"""
Nutritional information data model.
"""

from pydantic import BaseModel, Field
from typing import Optional


class NutritionalInfo(BaseModel):
    """
    Nutritional information for recipes and meals.
    
    Tracks calories, macronutrients, and key micronutrients.
    """
    
    calories: Optional[float] = Field(None, ge=0, description="Total calories per serving")
    protein_g: Optional[float] = Field(None, ge=0, description="Protein in grams")
    carbs_g: Optional[float] = Field(None, ge=0, description="Carbohydrates in grams")
    fat_g: Optional[float] = Field(None, ge=0, description="Fat in grams")
    fiber_g: Optional[float] = Field(None, ge=0, description="Fiber in grams")
    sugar_g: Optional[float] = Field(None, ge=0, description="Sugar in grams")
    sodium_mg: Optional[float] = Field(None, ge=0, description="Sodium in milligrams")
    
    # Vitamins and minerals (optional)
    vitamin_c_mg: Optional[float] = Field(None, ge=0, description="Vitamin C in milligrams")
    iron_mg: Optional[float] = Field(None, ge=0, description="Iron in milligrams")
    calcium_mg: Optional[float] = Field(None, ge=0, description="Calcium in milligrams")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "calories": 350.0,
                "protein_g": 25.0,
                "carbs_g": 30.0,
                "fat_g": 15.0,
                "fiber_g": 8.0,
                "sugar_g": 5.0,
                "sodium_mg": 650.0
            }
        }
    
    def calculate_macros_percentage(self) -> dict:
        """Calculate macronutrient percentages."""
        if not all([self.protein_g, self.carbs_g, self.fat_g]):
            return {}
        
        # Calculate calories from macros (protein=4cal/g, carbs=4cal/g, fat=9cal/g)
        protein_calories = self.protein_g * 4
        carb_calories = self.carbs_g * 4
        fat_calories = self.fat_g * 9
        total_macro_calories = protein_calories + carb_calories + fat_calories
        
        if total_macro_calories == 0:
            return {}
        
        return {
            "protein_percent": round((protein_calories / total_macro_calories) * 100, 1),
            "carbs_percent": round((carb_calories / total_macro_calories) * 100, 1),
            "fat_percent": round((fat_calories / total_macro_calories) * 100, 1)
        } 