"""
Grocery list data models for shopping list generation and management.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from .ingredient import Ingredient, IngredientCategory, MeasurementUnit


class GroceryItemStatus(str, Enum):
    """Status of grocery items."""
    NEEDED = "needed"
    IN_CART = "in_cart"
    PURCHASED = "purchased"
    UNAVAILABLE = "unavailable"


class GroceryItem(BaseModel):
    """
    Individual item in a grocery list.
    
    Represents a consolidated ingredient with quantity and shopping metadata.
    """
    
    id: Optional[int] = None
    grocery_list_id: Optional[int] = None
    ingredient_id: Optional[int] = None
    
    # Ingredient reference (for denormalized access)
    ingredient: Optional[Ingredient] = None
    
    # Quantity information
    quantity: float = Field(..., gt=0, description="Total quantity needed")
    unit: MeasurementUnit = Field(..., description="Unit of measurement")
    
    # Shopping metadata
    estimated_price: Optional[float] = Field(None, ge=0, description="Estimated price for this item")
    actual_price: Optional[float] = Field(None, ge=0, description="Actual price paid")
    status: GroceryItemStatus = Field(default=GroceryItemStatus.NEEDED, description="Shopping status")
    
    # Store information
    store_section: Optional[str] = Field(None, description="Store section/aisle")
    preferred_brand: Optional[str] = Field(None, max_length=100, description="Preferred brand")
    
    # Alternative options
    substitutes: List[str] = Field(default_factory=list, description="Acceptable substitutes")
    notes: Optional[str] = Field(None, max_length=200, description="Shopping notes")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "quantity": 2.5,
                "unit": "lb",
                "estimated_price": 12.99,
                "status": "needed",
                "store_section": "Meat",
                "preferred_brand": "Organic Valley",
                "notes": "Look for sale price"
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
    
    def get_ingredient_name(self) -> str:
        """Get the ingredient name."""
        if self.ingredient:
            return self.ingredient.name
        return "Unknown ingredient"
    
    def get_category(self) -> IngredientCategory:
        """Get the ingredient category."""
        if self.ingredient:
            return self.ingredient.category
        return IngredientCategory.OTHER


class GroceryList(BaseModel):
    """
    Complete grocery list model for a meal plan.
    
    Contains all items needed for shopping with organization and cost tracking.
    """
    
    id: Optional[int] = None
    meal_plan_id: Optional[int] = None
    
    # List metadata
    name: Optional[str] = Field(None, max_length=200, description="Custom list name")
    
    # Items in the list
    items: List[GroceryItem] = Field(default_factory=list, description="All grocery items")
    
    # Cost tracking
    estimated_total: Optional[float] = Field(None, ge=0, description="Estimated total cost")
    actual_total: Optional[float] = Field(None, ge=0, description="Actual total cost")
    budget_limit: Optional[float] = Field(None, ge=0, description="Budget limit for this list")
    
    # Shopping metadata
    store_preferences: List[str] = Field(default_factory=list, description="Preferred stores")
    completed: bool = Field(default=False, description="Whether shopping is completed")
    
    # Timestamps
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Weekly Grocery Run",
                "estimated_total": 85.50,
                "budget_limit": 100.00,
                "store_preferences": ["Whole Foods", "Trader Joe's"],
                "completed": False
            }
        }
    
    def get_items_by_category(self) -> Dict[IngredientCategory, List[GroceryItem]]:
        """Group items by ingredient category for organized shopping."""
        items_by_category = {}
        
        for item in self.items:
            category = item.get_category()
            if category not in items_by_category:
                items_by_category[category] = []
            items_by_category[category].append(item)
        
        return items_by_category
    
    def get_items_by_status(self, status: GroceryItemStatus) -> List[GroceryItem]:
        """Get items with specific status."""
        return [item for item in self.items if item.status == status]
    
    def calculate_estimated_total(self) -> float:
        """Calculate estimated total from item prices."""
        total = 0.0
        for item in self.items:
            if item.estimated_price:
                total += item.estimated_price
        return round(total, 2)
    
    def calculate_actual_total(self) -> float:
        """Calculate actual total from purchased items."""
        total = 0.0
        for item in self.items:
            if item.status == GroceryItemStatus.PURCHASED and item.actual_price:
                total += item.actual_price
        return round(total, 2)
    
    def get_completion_percentage(self) -> float:
        """Get percentage of items purchased."""
        if not self.items:
            return 0.0
        
        purchased_count = len(self.get_items_by_status(GroceryItemStatus.PURCHASED))
        return round((purchased_count / len(self.items)) * 100, 1)
    
    def is_over_budget(self) -> bool:
        """Check if list is over budget."""
        if not self.budget_limit:
            return False
        
        if self.completed:
            actual_total = self.calculate_actual_total()
            return actual_total > self.budget_limit
        else:
            estimated_total = self.calculate_estimated_total()
            return estimated_total > self.budget_limit
    
    def get_shopping_route(self) -> List[IngredientCategory]:
        """Get recommended shopping route by category."""
        # Typical store layout order
        category_order = [
            IngredientCategory.PRODUCE,
            IngredientCategory.DAIRY,
            IngredientCategory.MEAT,
            IngredientCategory.SEAFOOD,
            IngredientCategory.FROZEN,
            IngredientCategory.PANTRY,
            IngredientCategory.CANNED,
            IngredientCategory.GRAINS,
            IngredientCategory.LEGUMES,
            IngredientCategory.NUTS_SEEDS,
            IngredientCategory.BAKING,
            IngredientCategory.SPICES,
            IngredientCategory.CONDIMENTS,
            IngredientCategory.BEVERAGES,
            IngredientCategory.OTHER
        ]
        
        items_by_category = self.get_items_by_category()
        route = []
        
        for category in category_order:
            if category in items_by_category and items_by_category[category]:
                route.append(category)
        
        return route


class GroceryListCreate(BaseModel):
    """Model for creating a new grocery list."""
    
    meal_plan_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    budget_limit: Optional[float] = Field(None, ge=0)
    store_preferences: List[str] = Field(default_factory=list)


class GroceryItemCreate(BaseModel):
    """Model for creating a grocery item."""
    
    ingredient_id: Optional[int] = None
    quantity: float = Field(..., gt=0)
    unit: MeasurementUnit
    estimated_price: Optional[float] = Field(None, ge=0)
    store_section: Optional[str] = None
    preferred_brand: Optional[str] = Field(None, max_length=100)
    substitutes: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=200) 