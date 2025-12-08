"""
Pending recipe model for recipes awaiting user approval.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PendingRecipeStatus(str, Enum):
    """Status of a pending recipe."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PendingRecipeIngredient(BaseModel):
    """Simplified ingredient for pending recipes (not yet linked to ingredient table)."""
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    notes: Optional[str] = None


class PendingRecipe(BaseModel):
    """
    Recipe awaiting user approval before being added to the authoritative collection.
    """
    
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200, description="Recipe name")
    description: Optional[str] = Field(None, max_length=1000, description="Recipe description")
    
    # Timing
    prep_time: Optional[int] = Field(None, ge=0, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(None, ge=0, description="Cooking time in minutes")
    
    # Serving info
    servings: Optional[int] = Field(None, ge=1, le=50, description="Number of servings")
    
    # Classification
    difficulty: Optional[str] = Field(None, description="Recipe difficulty")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    dietary_tags: List[str] = Field(default_factory=list, description="Dietary tags")
    
    # Recipe content - stored as simple lists/dicts for flexibility
    ingredients: List[PendingRecipeIngredient] = Field(default_factory=list, description="Recipe ingredients")
    instructions: List[str] = Field(default_factory=list, description="Cooking instructions")
    
    # Optional details
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes or tips")
    image_url: Optional[str] = Field(None, description="URL to recipe image")
    
    # Nutritional information (raw dict for flexibility)
    nutritional_info: Optional[Dict[str, Any]] = None
    
    # Source tracking
    source_url: Optional[str] = Field(None, description="Original URL if parsed from web")
    discovery_query: Optional[str] = Field(None, description="AI search query if discovered")
    
    # Status
    status: PendingRecipeStatus = Field(default=PendingRecipeStatus.PENDING)
    
    # Metadata
    created_at: Optional[datetime] = None
    
    @validator('name')
    def validate_name(cls, v):
        """Normalize recipe name."""
        return v.strip().title() if v else v
    
    @validator('instructions', pre=True)
    def validate_instructions(cls, v):
        """Ensure instructions are a list of strings."""
        if isinstance(v, str):
            # Split by newlines or numbered steps
            return [step.strip() for step in v.split('\n') if step.strip()]
        return v if v else []
    
    @validator('ingredients', pre=True)
    def validate_ingredients(cls, v):
        """Convert various ingredient formats to PendingRecipeIngredient list."""
        if not v:
            return []
        
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(PendingRecipeIngredient(name=item))
            elif isinstance(item, dict):
                result.append(PendingRecipeIngredient(**item))
            elif isinstance(item, PendingRecipeIngredient):
                result.append(item)
        return result
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PendingRecipeCreate(BaseModel):
    """Model for creating a pending recipe from URL parsing or AI discovery."""
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    prep_time: Optional[int] = Field(None, ge=0)
    cook_time: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1, le=50)
    difficulty: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_tags: List[str] = Field(default_factory=list)
    ingredients: List[PendingRecipeIngredient] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    nutritional_info: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    discovery_query: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        return v.strip().title() if v else v
    
    @validator('instructions', pre=True)
    def validate_instructions(cls, v):
        if isinstance(v, str):
            return [step.strip() for step in v.split('\n') if step.strip()]
        return v if v else []
    
    @validator('ingredients', pre=True)
    def validate_ingredients(cls, v):
        if not v:
            return []
        
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(PendingRecipeIngredient(name=item))
            elif isinstance(item, dict):
                result.append(PendingRecipeIngredient(**item))
            elif isinstance(item, PendingRecipeIngredient):
                result.append(item)
        return result


class PendingRecipeUpdate(BaseModel):
    """Model for updating a pending recipe before approval."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    prep_time: Optional[int] = Field(None, ge=0)
    cook_time: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1, le=50)
    difficulty: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_tags: Optional[List[str]] = None
    ingredients: Optional[List[PendingRecipeIngredient]] = None
    instructions: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = None
    nutritional_info: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            return v.strip().title()
        return v
    
    @validator('instructions', pre=True)
    def validate_instructions(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return [step.strip() for step in v.split('\n') if step.strip()]
        return v
    
    @validator('ingredients', pre=True)
    def validate_ingredients(cls, v):
        if v is None:
            return None
        
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(PendingRecipeIngredient(name=item))
            elif isinstance(item, dict):
                result.append(PendingRecipeIngredient(**item))
            elif isinstance(item, PendingRecipeIngredient):
                result.append(item)
        return result

