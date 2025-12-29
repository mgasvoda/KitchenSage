"""
Centralized settings management for KitchenSage.

All tunable parameters for LLM models, agent behavior, meal planning,
and other configurable options.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class LLMSettings(BaseSettings):
    """LLM and AI model configuration."""

    # Default models for different purposes
    default_model: str = Field(
        default="gpt-4o-mini",
        description="Default LLM model for general agent tasks"
    )

    consolidation_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model for grocery list consolidation"
    )

    # Agent-specific models
    orchestrator_model: str = Field(
        default="gpt-4.1-mini",
        description="Model for orchestrator agent"
    )

    meal_planner_model: str = Field(
        default="gpt-4.1-mini",
        description="Model for meal planning agent"
    )

    recipe_scout_model: str = Field(
        default="gpt-4.1-mini",
        description="Model for recipe discovery agent"
    )

    recipe_manager_model: str = Field(
        default="gpt-4.1-mini",
        description="Model for recipe management agent"
    )

    grocery_list_model: str = Field(
        default="gpt-4.1-mini",
        description="Model for grocery list agent"
    )

    # Temperature settings (controls randomness)
    orchestrator_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for orchestrator agent (lower = more deterministic)"
    )

    meal_planner_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Temperature for meal planner agent"
    )

    recipe_scout_temperature: float = Field(
        default=0.4,
        ge=0.0,
        le=2.0,
        description="Temperature for recipe scout agent"
    )

    recipe_manager_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for recipe manager agent"
    )

    grocery_list_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Temperature for grocery list agent"
    )

    consolidation_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for grocery consolidation"
    )

    # Token limits
    consolidation_max_tokens: int = Field(
        default=4000,
        ge=100,
        le=16000,
        description="Max tokens for grocery consolidation responses"
    )

    # Agent behavior
    agent_verbose: bool = Field(
        default=True,
        description="Enable verbose output from agents"
    )

    class Config:
        env_prefix = "LLM_"
        case_sensitive = False


class MealPlanningSettings(BaseSettings):
    """Meal planning defaults and configuration."""

    default_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Default number of days for meal plans"
    )

    default_people: int = Field(
        default=2,
        ge=1,
        le=20,
        description="Default number of people to plan for"
    )

    default_servings: int = Field(
        default=4,
        ge=1,
        le=50,
        description="Default servings when recipe doesn't specify"
    )

    meals_per_day: int = Field(
        default=3,
        ge=1,
        le=6,
        description="Number of meals per day (breakfast, lunch, dinner)"
    )

    class Config:
        env_prefix = "MEAL_"
        case_sensitive = False


class RecipeDiscoverySettings(BaseSettings):
    """Recipe discovery and search configuration."""

    default_max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Default maximum number of recipes to discover"
    )

    default_servings_fallback: int = Field(
        default=4,
        ge=1,
        le=50,
        description="Fallback servings when scraping doesn't find value"
    )

    class Config:
        env_prefix = "RECIPE_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main settings class that aggregates all configuration."""

    # Sub-settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    meal_planning: MealPlanningSettings = Field(default_factory=MealPlanningSettings)
    recipe_discovery: RecipeDiscoverySettings = Field(default_factory=RecipeDiscoverySettings)

    class Config:
        case_sensitive = False


# Global settings instance
settings = Settings()
