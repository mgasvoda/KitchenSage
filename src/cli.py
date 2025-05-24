#!/usr/bin/env python3
"""
KitchenCrew CLI Interface

Command-line interface for managing recipes, meal plans, and grocery lists.
"""

import click
import json
import sys
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents import RecipeManagerAgent, MealPlannerAgent, GroceryListAgent, RecipeScoutAgent
from src.models import DifficultyLevel, CuisineType, DietaryTag, MealType
from src.database import get_db_connection
from src.utils.logging_config import setup_logging

# Setup logging
try:
    logger = setup_logging()
    if logger is None:
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class KitchenCrewCLI:
    """Main CLI class for KitchenCrew operations."""
    
    def __init__(self):
        """Initialize CLI with agents."""
        self._agents_initialized = False
        self._recipe_manager = None
        self._meal_planner = None
        self._grocery_agent = None
        self._recipe_scout = None
    
    def _ensure_agents_initialized(self):
        """Lazy initialization of agents."""
        if not self._agents_initialized:
            try:
                self._recipe_manager = RecipeManagerAgent()
                self._meal_planner = MealPlannerAgent()
                self._grocery_agent = GroceryListAgent()
                self._recipe_scout = RecipeScoutAgent()
                self._agents_initialized = True
                logger.info("KitchenCrew CLI initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CLI: {e}")
                click.echo(f"Error initializing KitchenCrew: {e}", err=True)
                sys.exit(1)
    
    @property
    def recipe_manager(self):
        self._ensure_agents_initialized()
        return self._recipe_manager
    
    @property
    def meal_planner(self):
        self._ensure_agents_initialized()
        return self._meal_planner
    
    @property
    def grocery_agent(self):
        self._ensure_agents_initialized()
        return self._grocery_agent
    
    @property
    def recipe_scout(self):
        self._ensure_agents_initialized()
        return self._recipe_scout


# Create global CLI instance (with lazy initialization)
cli_instance = KitchenCrewCLI()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """🍳 KitchenCrew - AI-Powered Cooking Assistant
    
    Manage recipes, create meal plans, and generate grocery lists with AI assistance.
    """
    pass


# ============================================================================
# RECIPE MANAGEMENT COMMANDS
# ============================================================================

@cli.group()
def recipe():
    """🍽️ Recipe management commands."""
    pass


@recipe.command('add')
@click.option('--name', required=True, help='Recipe name')
@click.option('--description', help='Recipe description')
@click.option('--cuisine', type=click.Choice([c.value for c in CuisineType]), help='Cuisine type')
@click.option('--difficulty', type=click.Choice([d.value for d in DifficultyLevel]), default='medium', help='Difficulty level')
@click.option('--prep-time', type=int, help='Preparation time in minutes')
@click.option('--cook-time', type=int, help='Cooking time in minutes')
@click.option('--servings', type=int, default=4, help='Number of servings')
@click.option('--ingredients', help='Ingredients (JSON format or comma-separated)')
@click.option('--instructions', help='Instructions (JSON format or semicolon-separated)')
@click.option('--dietary-tags', help='Dietary tags (comma-separated)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode for adding recipe')
def add_recipe(name, description, cuisine, difficulty, prep_time, cook_time, servings, 
               ingredients, instructions, dietary_tags, interactive):
    """Add a new recipe to the database."""
    try:
        if interactive:
            recipe_data = _interactive_recipe_input(name)
        else:
            recipe_data = _parse_recipe_args(
                name, description, cuisine, difficulty, prep_time, cook_time,
                servings, ingredients, instructions, dietary_tags
            )
        
        # Validate recipe using the agent's tools
        click.echo("🔍 Validating recipe...")
        validator_tool = None
        for tool in cli_instance.recipe_manager.tools:
            if hasattr(tool, 'name') and 'validator' in tool.name.lower():
                validator_tool = tool
                break
        
        if validator_tool:
            validation_result = validator_tool._run(recipe_data)
            if not validation_result.get('valid', False):
                click.echo("❌ Recipe validation failed:", err=True)
                for error in validation_result.get('errors', []):
                    click.echo(f"  • {error}", err=True)
                return
            
            # Show warnings if any
            warnings = validation_result.get('warnings', [])
            if warnings:
                click.echo("⚠️  Warnings:")
                for warning in warnings:
                    click.echo(f"  • {warning}")
        
        # Store recipe using database tool
        click.echo("💾 Storing recipe...")
        db_tool = None
        for tool in cli_instance.recipe_manager.tools:
            if hasattr(tool, 'name') and 'database' in tool.name.lower():
                db_tool = tool
                break
        
        if db_tool:
            result = db_tool._run(
                operation="create",
                table="recipes",
                data=recipe_data
            )
            
            if result.get('status') == 'success':
                recipe_id = result.get('record_id')
                click.echo(f"✅ Recipe '{name}' added successfully! (ID: {recipe_id})")
            else:
                click.echo(f"❌ Failed to store recipe: {result.get('message')}", err=True)
        else:
            click.echo("❌ Database tool not available", err=True)
            
    except Exception as e:
        logger.error(f"Error adding recipe: {e}")
        click.echo(f"❌ Error adding recipe: {e}", err=True)


@recipe.command('list')
@click.option('--limit', type=int, default=20, help='Maximum number of recipes to show')
@click.option('--cuisine', type=click.Choice([c.value for c in CuisineType]), help='Filter by cuisine')
@click.option('--difficulty', type=click.Choice([d.value for d in DifficultyLevel]), help='Filter by difficulty')
@click.option('--dietary-tags', help='Filter by dietary tags (comma-separated)')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'detailed']), 
              default='table', help='Output format')
def list_recipes(limit, cuisine, difficulty, dietary_tags, output_format):
    """List recipes from the database."""
    try:
        # Build filters
        filters = {}
        if cuisine:
            filters['cuisine'] = cuisine
        if difficulty:
            filters['difficulty'] = difficulty
        if dietary_tags:
            filters['dietary_tags'] = [tag.strip() for tag in dietary_tags.split(',')]
        
        # Get recipes using database tool
        db_tool = None
        for tool in cli_instance.recipe_manager.tools:
            if hasattr(tool, 'name') and 'database' in tool.name.lower():
                db_tool = tool
                break
        
        if not db_tool:
            click.echo("❌ Database tool not available", err=True)
            return
        
        result = db_tool._run(
            operation="list",
            table="recipes",
            filters=filters
        )
        
        if result.get('status') != 'success':
            click.echo(f"❌ Failed to retrieve recipes: {result.get('message')}", err=True)
            return
        
        recipes = result.get('records', [])
        
        if not recipes:
            click.echo("📭 No recipes found matching your criteria.")
            return
        
        # Limit results
        recipes = recipes[:limit]
        
        _display_recipes(recipes, output_format)
        
    except Exception as e:
        logger.error(f"Error listing recipes: {e}")
        click.echo(f"❌ Error listing recipes: {e}", err=True)


@recipe.command('search')
@click.option('--name', help='Search by recipe name')
@click.option('--ingredients', help='Search by ingredients (comma-separated)')
@click.option('--cuisine', type=click.Choice([c.value for c in CuisineType]), help='Filter by cuisine')
@click.option('--max-prep-time', type=int, help='Maximum prep time in minutes')
@click.option('--max-cook-time', type=int, help='Maximum cook time in minutes')
@click.option('--dietary-tags', help='Required dietary tags (comma-separated)')
@click.option('--limit', type=int, default=10, help='Maximum number of results')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'detailed']), 
              default='table', help='Output format')
def search_recipes(name, ingredients, cuisine, max_prep_time, max_cook_time, dietary_tags, limit, output_format):
    """Search recipes using advanced criteria."""
    try:
        # Build search criteria
        search_criteria = {}
        if name:
            search_criteria['name'] = name
        if ingredients:
            search_criteria['ingredients'] = [ing.strip() for ing in ingredients.split(',')]
        if cuisine:
            search_criteria['cuisine'] = cuisine
        if max_prep_time:
            search_criteria['max_prep_time'] = max_prep_time
        if max_cook_time:
            search_criteria['max_cook_time'] = max_cook_time
        if dietary_tags:
            search_criteria['dietary_tags'] = [tag.strip() for tag in dietary_tags.split(',')]
        if limit:
            search_criteria['limit'] = limit
        
        # Use recipe search tool
        search_tool = None
        for tool in cli_instance.recipe_manager.tools:
            if hasattr(tool, 'name') and 'search' in tool.name.lower():
                search_tool = tool
                break
        
        if not search_tool:
            click.echo("❌ Recipe search tool not available", err=True)
            return
        
        click.echo("🔍 Searching recipes...")
        result = search_tool._run(search_criteria)
        
        if result.get('status') != 'success':
            click.echo(f"❌ Search failed: {result.get('message')}", err=True)
            return
        
        recipes = result.get('recipes', [])
        
        if not recipes:
            click.echo("📭 No recipes found matching your search criteria.")
            return
        
        click.echo(f"🎯 Found {len(recipes)} matching recipe(s)")
        _display_recipes(recipes, output_format)
        
    except Exception as e:
        logger.error(f"Error searching recipes: {e}")
        click.echo(f"❌ Error searching recipes: {e}", err=True)


@recipe.command('show')
@click.argument('recipe_id', type=int)
@click.option('--format', 'output_format', type=click.Choice(['detailed', 'json']), 
              default='detailed', help='Output format')
def show_recipe(recipe_id, output_format):
    """Show detailed information for a specific recipe."""
    try:
        # Get recipe using database tool
        db_tool = None
        for tool in cli_instance.recipe_manager.tools:
            if hasattr(tool, 'name') and 'database' in tool.name.lower():
                db_tool = tool
                break
        
        if not db_tool:
            click.echo("❌ Database tool not available", err=True)
            return
        
        result = db_tool._run(
            operation="read",
            table="recipes",
            record_id=recipe_id
        )
        
        if result.get('status') != 'success':
            click.echo(f"❌ Recipe not found: {result.get('message')}", err=True)
            return
        
        recipe = result.get('record')
        
        if output_format == 'json':
            click.echo(json.dumps(recipe, indent=2, default=str))
        else:
            _display_recipe_detailed(recipe)
            
    except Exception as e:
        logger.error(f"Error showing recipe: {e}")
        click.echo(f"❌ Error showing recipe: {e}", err=True)


# ============================================================================
# MEAL PLANNING COMMANDS
# ============================================================================

@cli.group()
def meal():
    """🗓️ Meal planning commands."""
    pass


@meal.command('plan')
@click.option('--days', type=int, default=7, help='Number of days for meal plan')
@click.option('--people', type=int, default=2, help='Number of people')
@click.option('--start-date', help='Start date (YYYY-MM-DD, default: today)')
@click.option('--dietary-restrictions', help='Dietary restrictions (comma-separated)')
@click.option('--cuisine-preferences', help='Cuisine preferences (comma-separated)')
@click.option('--max-prep-time', type=int, help='Maximum prep time per meal (minutes)')
@click.option('--exclude-ingredients', help='Ingredients to exclude (comma-separated)')
@click.option('--save', is_flag=True, help='Save meal plan to database')
def create_meal_plan(days, people, start_date, dietary_restrictions, cuisine_preferences,
                    max_prep_time, exclude_ingredients, save):
    """Create a new meal plan."""
    try:
        # Parse start date
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date_obj = date.today()
        
        # Build requirements
        requirements = {
            'days': days,
            'people': people,
            'start_date': start_date_obj.strftime('%Y-%m-%d')
        }
        
        if dietary_restrictions:
            requirements['dietary_restrictions'] = [tag.strip() for tag in dietary_restrictions.split(',')]
        if cuisine_preferences:
            requirements['cuisine_preferences'] = [c.strip() for c in cuisine_preferences.split(',')]
        if max_prep_time:
            requirements['max_prep_time'] = max_prep_time
        if exclude_ingredients:
            requirements['exclude_ingredients'] = [ing.strip() for ing in exclude_ingredients.split(',')]
        
        # Create meal plan using meal planning tool
        meal_planning_tool = None
        for tool in cli_instance.meal_planner.tools:
            if hasattr(tool, 'name') and 'meal planning' in tool.name.lower():
                meal_planning_tool = tool
                break
        
        if not meal_planning_tool:
            click.echo("❌ Meal planning tool not available", err=True)
            return
        
        click.echo("🍽️ Creating meal plan...")
        result = meal_planning_tool._run(requirements)
        
        if result.get('status') not in ['success', 'warning']:
            click.echo(f"❌ Failed to create meal plan: {result.get('message')}", err=True)
            return
        
        meal_plan = result.get('meal_plan')
        
        if result.get('status') == 'warning':
            click.echo(f"⚠️  {result.get('message')}")
        
        click.echo("✅ Meal plan created successfully!")
        _display_meal_plan(meal_plan)
        
        if save and meal_plan.get('meal_plan_id'):
            click.echo(f"💾 Meal plan saved with ID: {meal_plan['meal_plan_id']}")
        
    except Exception as e:
        logger.error(f"Error creating meal plan: {e}")
        click.echo(f"❌ Error creating meal plan: {e}", err=True)


# ============================================================================
# GROCERY LIST COMMANDS
# ============================================================================

@cli.group()
def grocery():
    """🛒 Grocery list commands."""
    pass


@grocery.command('generate')
@click.option('--meal-plan-id', type=int, help='Meal plan ID to generate grocery list from')
@click.option('--check-inventory', is_flag=True, help='Check inventory to reduce list')
@click.option('--budget', type=float, help='Budget limit for groceries')
@click.option('--store-preference', help='Preferred store for shopping')
@click.option('--save', is_flag=True, help='Save grocery list to database')
def generate_grocery_list(meal_plan_id, check_inventory, budget, store_preference, save):
    """Generate an optimized grocery list from a meal plan."""
    try:
        if not meal_plan_id:
            click.echo("❌ Meal plan ID is required", err=True)
            return
        
        # Build preferences
        preferences = {}
        if check_inventory:
            preferences['check_inventory'] = True
        if budget:
            preferences['budget'] = budget
        if store_preference:
            preferences['preferred_store'] = store_preference
        
        # Generate grocery list using list optimization tool
        list_tool = None
        for tool in cli_instance.grocery_agent.tools:
            if hasattr(tool, 'name') and 'optimization' in tool.name.lower():
                list_tool = tool
                break
        
        if not list_tool:
            click.echo("❌ List optimization tool not available", err=True)
            return
        
        click.echo("🛒 Generating grocery list...")
        result = list_tool._run(
            meal_plan_id=meal_plan_id,
            preferences=preferences
        )
        
        if result.get('status') != 'success':
            click.echo(f"❌ Failed to generate grocery list: {result.get('message')}", err=True)
            return
        
        click.echo("✅ Grocery list generated successfully!")
        _display_grocery_list(result)
        
        if save and result.get('grocery_list_id'):
            click.echo(f"💾 Grocery list saved with ID: {result['grocery_list_id']}")
        
    except Exception as e:
        logger.error(f"Error generating grocery list: {e}")
        click.echo(f"❌ Error generating grocery list: {e}", err=True)


# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@cli.group()
def data():
    """📊 Data management commands."""
    pass


@data.command('import-samples')
@click.option('--file', help='JSON file with sample recipes')
@click.option('--count', type=int, default=10, help='Number of sample recipes to create')
def import_sample_recipes(file, count):
    """Import sample recipes for testing."""
    try:
        if file:
            click.echo(f"📥 Importing recipes from {file}...")
            _import_recipes_from_file(file)
        else:
            click.echo(f"🏗️ Creating {count} sample recipes...")
            _create_sample_recipes(count)
        
    except Exception as e:
        logger.error(f"Error importing sample recipes: {e}")
        click.echo(f"❌ Error importing sample recipes: {e}", err=True)


@data.command('status')
def show_status():
    """Show database status and statistics."""
    try:
        click.echo("📊 KitchenCrew Database Status")
        click.echo("=" * 40)
        
        # Get statistics using database tool
        db_tool = None
        for tool in cli_instance.recipe_manager.tools:
            if hasattr(tool, 'name') and 'database' in tool.name.lower():
                db_tool = tool
                break
        
        if not db_tool:
            click.echo("❌ Database tool not available", err=True)
            return
        
        # Get counts for each table
        tables = ['recipes', 'meal_plans', 'grocery_lists']
        stats = {}
        
        for table in tables:
            result = db_tool._run(operation="list", table=table)
            if result.get('status') == 'success':
                stats[table] = result.get('count', 0)
            else:
                stats[table] = 0
        
        click.echo(f"Recipes:      {stats.get('recipes', 0)}")
        click.echo(f"Meal Plans:   {stats.get('meal_plans', 0)}")
        click.echo(f"Grocery Lists: {stats.get('grocery_lists', 0)}")
        
        # Check database file
        db_path = "kitchen_crew.db"
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            click.echo(f"Database Size: {size:,} bytes")
        
    except Exception as e:
        logger.error(f"Error showing status: {e}")
        click.echo(f"❌ Error showing status: {e}", err=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _interactive_recipe_input(name: str) -> Dict[str, Any]:
    """Interactive mode for recipe input."""
    click.echo("🍳 Interactive Recipe Creation")
    click.echo("=" * 30)
    
    # Basic info
    if not name:
        name = click.prompt("Recipe name")
    
    description = click.prompt("Description", default="")
    
    # Cuisine
    cuisines = [c.value for c in CuisineType]
    click.echo(f"Available cuisines: {', '.join(cuisines)}")
    cuisine = click.prompt("Cuisine type", default="american")
    
    # Difficulty
    difficulties = [d.value for d in DifficultyLevel]
    click.echo(f"Difficulty levels: {', '.join(difficulties)}")
    difficulty = click.prompt("Difficulty", default="medium")
    
    # Times and servings
    prep_time = click.prompt("Prep time (minutes)", type=int, default=30)
    cook_time = click.prompt("Cook time (minutes)", type=int, default=30)
    servings = click.prompt("Servings", type=int, default=4)
    
    # Ingredients
    click.echo("\nEnter ingredients (one per line, empty line to finish):")
    ingredients = []
    while True:
        ingredient = click.prompt("Ingredient", default="", show_default=False)
        if not ingredient:
            break
        
        # Parse ingredient
        parts = ingredient.split()
        if len(parts) >= 3:
            try:
                quantity = float(parts[0])
                unit = parts[1]
                name = " ".join(parts[2:])
                ingredients.append({
                    "name": name,
                    "quantity": quantity,
                    "unit": unit
                })
            except ValueError:
                ingredients.append({
                    "name": ingredient,
                    "quantity": 1,
                    "unit": "piece"
                })
        else:
            ingredients.append({
                "name": ingredient,
                "quantity": 1,
                "unit": "piece"
            })
    
    # Instructions
    click.echo("\nEnter instructions (one per line, empty line to finish):")
    instructions = []
    step = 1
    while True:
        instruction = click.prompt(f"Step {step}", default="", show_default=False)
        if not instruction:
            break
        instructions.append(instruction)
        step += 1
    
    return {
        "name": name,
        "description": description,
        "cuisine": cuisine,
        "difficulty": difficulty,
        "prep_time": prep_time,
        "cook_time": cook_time,
        "servings": servings,
        "ingredients": ingredients,
        "instructions": instructions
    }


def _parse_recipe_args(name, description, cuisine, difficulty, prep_time, cook_time,
                      servings, ingredients, instructions, dietary_tags) -> Dict[str, Any]:
    """Parse recipe arguments into recipe data structure."""
    recipe_data = {
        "name": name,
        "description": description or "",
        "cuisine": cuisine or "american",
        "difficulty": difficulty,
        "prep_time": prep_time or 30,
        "cook_time": cook_time or 30,
        "servings": servings,
        "ingredients": [],
        "instructions": []
    }
    
    # Parse ingredients
    if ingredients:
        try:
            # Try JSON format first
            recipe_data["ingredients"] = json.loads(ingredients)
        except json.JSONDecodeError:
            # Fall back to comma-separated
            ing_list = [ing.strip() for ing in ingredients.split(',')]
            recipe_data["ingredients"] = [
                {"name": ing, "quantity": 1, "unit": "piece"} for ing in ing_list
            ]
    
    # Parse instructions
    if instructions:
        try:
            # Try JSON format first
            recipe_data["instructions"] = json.loads(instructions)
        except json.JSONDecodeError:
            # Fall back to semicolon-separated
            recipe_data["instructions"] = [inst.strip() for inst in instructions.split(';')]
    
    # Parse dietary tags
    if dietary_tags:
        recipe_data["dietary_tags"] = [tag.strip() for tag in dietary_tags.split(',')]
    
    return recipe_data


def _display_recipes(recipes: List[Dict[str, Any]], output_format: str):
    """Display recipes in the specified format."""
    if output_format == 'json':
        click.echo(json.dumps(recipes, indent=2, default=str))
        return
    
    if output_format == 'table':
        # Table format
        click.echo("\n📋 Recipe List")
        click.echo("-" * 80)
        click.echo(f"{'ID':<4} {'Name':<30} {'Cuisine':<12} {'Difficulty':<10} {'Time':<8}")
        click.echo("-" * 80)
        
        for recipe in recipes:
            recipe_id = recipe.get('id', 'N/A')
            name = recipe.get('name', 'Unknown')[:29]
            cuisine = recipe.get('cuisine', 'N/A')[:11]
            difficulty = recipe.get('difficulty', 'N/A')[:9]
            total_time = (recipe.get('prep_time', 0) + recipe.get('cook_time', 0))
            time_str = f"{total_time}min"
            
            click.echo(f"{recipe_id:<4} {name:<30} {cuisine:<12} {difficulty:<10} {time_str:<8}")
    
    elif output_format == 'detailed':
        # Detailed format
        for i, recipe in enumerate(recipes):
            if i > 0:
                click.echo("\n" + "-" * 60)
            _display_recipe_detailed(recipe)


def _display_recipe_detailed(recipe: Dict[str, Any]):
    """Display detailed recipe information."""
    click.echo(f"\n🍽️ {recipe.get('name', 'Unknown Recipe')}")
    click.echo("=" * 50)
    
    if recipe.get('description'):
        click.echo(f"Description: {recipe['description']}")
    
    click.echo(f"ID: {recipe.get('id', 'N/A')}")
    click.echo(f"Cuisine: {recipe.get('cuisine', 'N/A')}")
    click.echo(f"Difficulty: {recipe.get('difficulty', 'N/A')}")
    click.echo(f"Prep Time: {recipe.get('prep_time', 0)} minutes")
    click.echo(f"Cook Time: {recipe.get('cook_time', 0)} minutes")
    click.echo(f"Servings: {recipe.get('servings', 'N/A')}")
    
    # Dietary tags
    dietary_tags = recipe.get('dietary_tags', [])
    if dietary_tags:
        click.echo(f"Dietary Tags: {', '.join(dietary_tags)}")
    
    # Ingredients
    ingredients = recipe.get('ingredients', [])
    if ingredients:
        click.echo("\n📦 Ingredients:")
        for ing in ingredients:
            if isinstance(ing, dict):
                name = ing.get('name', 'Unknown')
                quantity = ing.get('quantity', '')
                unit = ing.get('unit', '')
                click.echo(f"  • {quantity} {unit} {name}")
            else:
                click.echo(f"  • {ing}")
    
    # Instructions
    instructions = recipe.get('instructions', [])
    if instructions:
        click.echo("\n👨‍🍳 Instructions:")
        for i, instruction in enumerate(instructions, 1):
            click.echo(f"  {i}. {instruction}")


def _display_meal_plan(meal_plan: Dict[str, Any]):
    """Display meal plan information."""
    click.echo(f"\n🗓️ Meal Plan ({meal_plan.get('days', 0)} days)")
    click.echo("=" * 50)
    
    click.echo(f"Start Date: {meal_plan.get('start_date', 'N/A')}")
    click.echo(f"End Date: {meal_plan.get('end_date', 'N/A')}")
    click.echo(f"People: {meal_plan.get('people', 'N/A')}")
    click.echo(f"Total Recipes: {meal_plan.get('total_recipes', 'N/A')}")
    
    variety_score = meal_plan.get('variety_score', 0)
    if variety_score:
        click.echo(f"Variety Score: {variety_score:.2f}")
    
    meals = meal_plan.get('meals', [])
    if meals:
        # Group meals by date
        meals_by_date = {}
        for meal in meals:
            meal_date = str(meal.get('date', 'Unknown'))
            if meal_date not in meals_by_date:
                meals_by_date[meal_date] = []
            meals_by_date[meal_date].append(meal)
        
        click.echo("\n📅 Meal Schedule:")
        for date_str, day_meals in sorted(meals_by_date.items()):
            click.echo(f"\n  📆 {date_str}")
            for meal in day_meals:
                meal_type = meal.get('meal_type', 'Unknown')
                recipe_name = meal.get('recipe_name', 'Unknown Recipe')
                prep_time = meal.get('prep_time', 0)
                click.echo(f"    {meal_type}: {recipe_name} ({prep_time} min prep)")


def _display_grocery_list(result: Dict[str, Any]):
    """Display grocery list information."""
    click.echo(f"\n🛒 Grocery List")
    click.echo("=" * 50)
    
    optimization_summary = result.get('optimization_summary', {})
    click.echo(f"Total Items: {optimization_summary.get('total_items', 'N/A')}")
    click.echo(f"Categories: {optimization_summary.get('categories', 'N/A')}")
    click.echo(f"Estimated Cost: ${result.get('estimated_total_cost', 0):.2f}")
    click.echo(f"Estimated Time: {result.get('estimated_shopping_time', 'N/A')}")
    
    # Shopping route
    shopping_route = result.get('shopping_route', [])
    if shopping_route:
        click.echo(f"\n🗺️ Shopping Route: {' → '.join(shopping_route)}")
    
    # Organized list
    organized_list = result.get('optimized_list', {})
    if organized_list:
        click.echo("\n📝 Shopping List by Category:")
        for category, items in organized_list.items():
            click.echo(f"\n  📦 {category}:")
            for item in items:
                name = item.get('name', 'Unknown')
                quantity = item.get('quantity', '')
                unit = item.get('unit', '')
                price = item.get('estimated_price', 0)
                click.echo(f"    • {quantity} {unit} {name} (${price:.2f})")
    
    # Bulk opportunities
    bulk_opportunities = result.get('bulk_opportunities', [])
    if bulk_opportunities:
        click.echo("\n💡 Bulk Purchase Opportunities:")
        for bulk in bulk_opportunities:
            savings = bulk.get('estimated_savings', 0)
            recommendation = bulk.get('recommendation', '')
            click.echo(f"  • {recommendation} (Save ${savings:.2f})")
    
    # Shopping tips
    shopping_tips = result.get('shopping_tips', [])
    if shopping_tips:
        click.echo("\n💡 Shopping Tips:")
        for tip in shopping_tips[:3]:  # Show first 3 tips
            click.echo(f"  • {tip}")


def _create_sample_recipes(count: int):
    """Create sample recipes for testing."""
    sample_recipes = _get_sample_recipe_data()
    
    # Limit to requested count
    recipes_to_create = sample_recipes[:count]
    
    click.echo(f"Creating {len(recipes_to_create)} sample recipes...")
    
    # Get database tool
    db_tool = None
    for tool in cli_instance.recipe_manager.tools:
        if hasattr(tool, 'name') and 'database' in tool.name.lower():
            db_tool = tool
            break
    
    if not db_tool:
        click.echo("❌ Database tool not available", err=True)
        return
    
    created_count = 0
    for recipe_data in recipes_to_create:
        try:
            result = db_tool._run(
                operation="create",
                table="recipes",
                data=recipe_data
            )
            
            if result.get('status') == 'success':
                created_count += 1
                click.echo(f"  ✅ Created: {recipe_data['name']}")
            else:
                click.echo(f"  ❌ Failed: {recipe_data['name']} - {result.get('message')}")
                
        except Exception as e:
            click.echo(f"  ❌ Error creating {recipe_data['name']}: {e}")
    
    click.echo(f"\n✅ Successfully created {created_count}/{len(recipes_to_create)} sample recipes!")


def _import_recipes_from_file(file_path: str):
    """Import recipes from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            recipes = json.load(f)
        
        if not isinstance(recipes, list):
            click.echo("❌ File must contain a JSON array of recipes", err=True)
            return
        
        click.echo(f"Importing {len(recipes)} recipes from {file_path}...")
        
        # Get database tool
        db_tool = None
        for tool in cli_instance.recipe_manager.tools:
            if hasattr(tool, 'name') and 'database' in tool.name.lower():
                db_tool = tool
                break
        
        if not db_tool:
            click.echo("❌ Database tool not available", err=True)
            return
        
        created_count = 0
        for recipe_data in recipes:
            try:
                result = db_tool._run(
                    operation="create",
                    table="recipes",
                    data=recipe_data
                )
                
                if result.get('status') == 'success':
                    created_count += 1
                    click.echo(f"  ✅ Imported: {recipe_data.get('name', 'Unknown')}")
                else:
                    click.echo(f"  ❌ Failed: {recipe_data.get('name', 'Unknown')} - {result.get('message')}")
                    
            except Exception as e:
                click.echo(f"  ❌ Error importing {recipe_data.get('name', 'Unknown')}: {e}")
        
        click.echo(f"\n✅ Successfully imported {created_count}/{len(recipes)} recipes!")
        
    except FileNotFoundError:
        click.echo(f"❌ File not found: {file_path}", err=True)
    except json.JSONDecodeError:
        click.echo(f"❌ Invalid JSON format in file: {file_path}", err=True)


def _get_sample_recipe_data() -> List[Dict[str, Any]]:
    """Get sample recipe data for testing."""
    return [
        {
            "name": "Classic Spaghetti Carbonara",
            "description": "Traditional Italian pasta dish with eggs, cheese, and pancetta",
            "cuisine": "italian",
            "difficulty": "medium",
            "prep_time": 15,
            "cook_time": 20,
            "servings": 4,
            "dietary_tags": [],
            "ingredients": [
                {"name": "spaghetti", "quantity": 400, "unit": "gram"},
                {"name": "pancetta", "quantity": 150, "unit": "gram"},
                {"name": "eggs", "quantity": 3, "unit": "piece"},
                {"name": "parmesan cheese", "quantity": 100, "unit": "gram"},
                {"name": "black pepper", "quantity": 1, "unit": "tsp"},
                {"name": "salt", "quantity": 1, "unit": "tsp"}
            ],
            "instructions": [
                "Cook spaghetti in salted boiling water until al dente",
                "Dice pancetta and cook in a large pan until crispy",
                "Beat eggs with grated parmesan and black pepper",
                "Drain pasta and add to pancetta pan",
                "Remove from heat and quickly mix in egg mixture",
                "Toss quickly to create creamy sauce without scrambling eggs",
                "Serve immediately with extra parmesan and black pepper"
            ]
        },
        {
            "name": "Chicken Tikka Masala",
            "description": "Creamy tomato-based curry with marinated chicken",
            "cuisine": "indian",
            "difficulty": "medium",
            "prep_time": 30,
            "cook_time": 45,
            "servings": 6,
            "dietary_tags": ["gluten_free"],
            "ingredients": [
                {"name": "chicken breast", "quantity": 800, "unit": "gram"},
                {"name": "yogurt", "quantity": 200, "unit": "ml"},
                {"name": "tomato sauce", "quantity": 400, "unit": "ml"},
                {"name": "heavy cream", "quantity": 200, "unit": "ml"},
                {"name": "onion", "quantity": 2, "unit": "piece"},
                {"name": "garlic", "quantity": 4, "unit": "clove"},
                {"name": "ginger", "quantity": 2, "unit": "tbsp"},
                {"name": "garam masala", "quantity": 2, "unit": "tsp"},
                {"name": "cumin", "quantity": 1, "unit": "tsp"},
                {"name": "paprika", "quantity": 1, "unit": "tsp"}
            ],
            "instructions": [
                "Cut chicken into bite-sized pieces",
                "Marinate chicken in yogurt and spices for 30 minutes",
                "Sauté onions until golden, add garlic and ginger",
                "Add spices and cook until fragrant",
                "Add tomato sauce and simmer for 10 minutes",
                "Add marinated chicken and cook until done",
                "Stir in cream and simmer until thick",
                "Serve with rice or naan bread"
            ]
        },
        {
            "name": "Avocado Toast with Poached Egg",
            "description": "Healthy breakfast with creamy avocado and perfectly poached egg",
            "cuisine": "american",
            "difficulty": "easy",
            "prep_time": 10,
            "cook_time": 10,
            "servings": 2,
            "dietary_tags": ["vegetarian", "healthy"],
            "ingredients": [
                {"name": "bread", "quantity": 2, "unit": "slice"},
                {"name": "avocado", "quantity": 1, "unit": "piece"},
                {"name": "eggs", "quantity": 2, "unit": "piece"},
                {"name": "lemon juice", "quantity": 1, "unit": "tbsp"},
                {"name": "salt", "quantity": 0.5, "unit": "tsp"},
                {"name": "black pepper", "quantity": 0.25, "unit": "tsp"},
                {"name": "red pepper flakes", "quantity": 0.25, "unit": "tsp"}
            ],
            "instructions": [
                "Toast bread slices until golden brown",
                "Mash avocado with lemon juice, salt, and pepper",
                "Bring water to simmer in a saucepan",
                "Create whirlpool and drop eggs one at a time",
                "Poach eggs for 3-4 minutes until whites are set",
                "Spread avocado mixture on toast",
                "Top with poached eggs and red pepper flakes",
                "Serve immediately"
            ]
        },
        {
            "name": "Beef Stir Fry with Vegetables",
            "description": "Quick and healthy stir fry with tender beef and crisp vegetables",
            "cuisine": "asian",
            "difficulty": "easy",
            "prep_time": 20,
            "cook_time": 15,
            "servings": 4,
            "dietary_tags": ["gluten_free"],
            "ingredients": [
                {"name": "beef sirloin", "quantity": 500, "unit": "gram"},
                {"name": "bell peppers", "quantity": 2, "unit": "piece"},
                {"name": "broccoli", "quantity": 300, "unit": "gram"},
                {"name": "carrots", "quantity": 2, "unit": "piece"},
                {"name": "soy sauce", "quantity": 3, "unit": "tbsp"},
                {"name": "sesame oil", "quantity": 2, "unit": "tbsp"},
                {"name": "garlic", "quantity": 3, "unit": "clove"},
                {"name": "ginger", "quantity": 1, "unit": "tbsp"}
            ],
            "instructions": [
                "Slice beef against the grain into thin strips",
                "Cut vegetables into bite-sized pieces",
                "Heat oil in wok or large skillet over high heat",
                "Stir-fry beef until just cooked through, remove",
                "Add vegetables and stir-fry until crisp-tender",
                "Return beef to pan with sauce ingredients",
                "Toss everything together until heated through",
                "Serve over rice"
            ]
        },
        {
            "name": "Greek Salad",
            "description": "Fresh Mediterranean salad with feta cheese and olives",
            "cuisine": "greek",
            "difficulty": "easy",
            "prep_time": 15,
            "cook_time": 0,
            "servings": 4,
            "dietary_tags": ["vegetarian", "healthy", "gluten_free"],
            "ingredients": [
                {"name": "cucumbers", "quantity": 2, "unit": "piece"},
                {"name": "tomatoes", "quantity": 4, "unit": "piece"},
                {"name": "red onion", "quantity": 0.5, "unit": "piece"},
                {"name": "feta cheese", "quantity": 200, "unit": "gram"},
                {"name": "kalamata olives", "quantity": 100, "unit": "gram"},
                {"name": "olive oil", "quantity": 4, "unit": "tbsp"},
                {"name": "lemon juice", "quantity": 2, "unit": "tbsp"},
                {"name": "oregano", "quantity": 1, "unit": "tsp"}
            ],
            "instructions": [
                "Chop cucumbers and tomatoes into chunks",
                "Slice red onion thinly",
                "Combine vegetables in large bowl",
                "Add olives and chunks of feta cheese",
                "Whisk together olive oil, lemon juice, and oregano",
                "Pour dressing over salad and toss gently",
                "Let stand 10 minutes before serving",
                "Serve at room temperature"
            ]
        },
        {
            "name": "Chocolate Chip Cookies",
            "description": "Classic homemade cookies with chocolate chips",
            "cuisine": "american",
            "difficulty": "easy",
            "prep_time": 15,
            "cook_time": 25,
            "servings": 24,
            "dietary_tags": ["vegetarian"],
            "ingredients": [
                {"name": "flour", "quantity": 300, "unit": "gram"},
                {"name": "butter", "quantity": 200, "unit": "gram"},
                {"name": "brown sugar", "quantity": 150, "unit": "gram"},
                {"name": "white sugar", "quantity": 100, "unit": "gram"},
                {"name": "eggs", "quantity": 2, "unit": "piece"},
                {"name": "vanilla extract", "quantity": 2, "unit": "tsp"},
                {"name": "baking soda", "quantity": 1, "unit": "tsp"},
                {"name": "salt", "quantity": 0.5, "unit": "tsp"},
                {"name": "chocolate chips", "quantity": 200, "unit": "gram"}
            ],
            "instructions": [
                "Preheat oven to 375°F (190°C)",
                "Cream butter and both sugars until fluffy",
                "Beat in eggs and vanilla extract",
                "Mix flour, baking soda, and salt in separate bowl",
                "Gradually add dry ingredients to wet ingredients",
                "Fold in chocolate chips",
                "Drop spoonfuls onto ungreased baking sheets",
                "Bake 9-11 minutes until golden brown",
                "Cool on baking sheet 5 minutes before transferring"
            ]
        },
        {
            "name": "Quinoa Buddha Bowl",
            "description": "Nutritious bowl with quinoa, roasted vegetables, and tahini dressing",
            "cuisine": "american",
            "difficulty": "medium",
            "prep_time": 20,
            "cook_time": 30,
            "servings": 4,
            "dietary_tags": ["vegan", "healthy", "gluten_free"],
            "ingredients": [
                {"name": "quinoa", "quantity": 200, "unit": "gram"},
                {"name": "sweet potato", "quantity": 2, "unit": "piece"},
                {"name": "chickpeas", "quantity": 400, "unit": "gram"},
                {"name": "kale", "quantity": 200, "unit": "gram"},
                {"name": "tahini", "quantity": 3, "unit": "tbsp"},
                {"name": "lemon juice", "quantity": 2, "unit": "tbsp"},
                {"name": "olive oil", "quantity": 3, "unit": "tbsp"},
                {"name": "garlic", "quantity": 2, "unit": "clove"}
            ],
            "instructions": [
                "Preheat oven to 400°F (200°C)",
                "Cook quinoa according to package directions",
                "Cube sweet potatoes and toss with oil",
                "Roast sweet potatoes and chickpeas for 25 minutes",
                "Massage kale with olive oil until softened",
                "Make dressing with tahini, lemon juice, and garlic",
                "Assemble bowls with quinoa base",
                "Top with roasted vegetables, kale, and dressing"
            ]
        },
        {
            "name": "Fish Tacos with Cilantro Lime Slaw",
            "description": "Fresh fish tacos with crispy slaw and lime crema",
            "cuisine": "mexican",
            "difficulty": "medium",
            "prep_time": 25,
            "cook_time": 15,
            "servings": 4,
            "dietary_tags": ["healthy"],
            "ingredients": [
                {"name": "white fish fillets", "quantity": 500, "unit": "gram"},
                {"name": "corn tortillas", "quantity": 8, "unit": "piece"},
                {"name": "cabbage", "quantity": 300, "unit": "gram"},
                {"name": "cilantro", "quantity": 50, "unit": "gram"},
                {"name": "lime", "quantity": 3, "unit": "piece"},
                {"name": "sour cream", "quantity": 200, "unit": "ml"},
                {"name": "cumin", "quantity": 1, "unit": "tsp"},
                {"name": "chili powder", "quantity": 1, "unit": "tsp"}
            ],
            "instructions": [
                "Season fish with cumin, chili powder, and lime juice",
                "Shred cabbage and mix with cilantro",
                "Make lime crema with sour cream and lime juice",
                "Grill or pan-fry fish until flaky",
                "Warm tortillas in dry skillet",
                "Assemble tacos with fish, slaw, and crema",
                "Garnish with lime wedges and extra cilantro",
                "Serve immediately"
            ]
        },
        {
            "name": "Mushroom Risotto",
            "description": "Creamy Italian rice dish with mixed mushrooms",
            "cuisine": "italian",
            "difficulty": "hard",
            "prep_time": 15,
            "cook_time": 45,
            "servings": 4,
            "dietary_tags": ["vegetarian", "gluten_free"],
            "ingredients": [
                {"name": "arborio rice", "quantity": 300, "unit": "gram"},
                {"name": "mixed mushrooms", "quantity": 400, "unit": "gram"},
                {"name": "vegetable broth", "quantity": 1000, "unit": "ml"},
                {"name": "white wine", "quantity": 200, "unit": "ml"},
                {"name": "onion", "quantity": 1, "unit": "piece"},
                {"name": "parmesan cheese", "quantity": 100, "unit": "gram"},
                {"name": "butter", "quantity": 50, "unit": "gram"},
                {"name": "olive oil", "quantity": 2, "unit": "tbsp"}
            ],
            "instructions": [
                "Heat broth in separate pot and keep warm",
                "Sauté mushrooms until golden, set aside",
                "Cook onion in oil until translucent",
                "Add rice and stir until coated",
                "Add wine and stir until absorbed",
                "Add warm broth one ladle at a time, stirring constantly",
                "Continue until rice is creamy but still firm",
                "Stir in mushrooms, butter, and parmesan",
                "Serve immediately with extra parmesan"
            ]
        },
        {
            "name": "Berry Smoothie Bowl",
            "description": "Thick smoothie bowl topped with fresh fruits and granola",
            "cuisine": "american",
            "difficulty": "easy",
            "prep_time": 10,
            "cook_time": 0,
            "servings": 2,
            "dietary_tags": ["vegetarian", "healthy", "gluten_free"],
            "ingredients": [
                {"name": "frozen mixed berries", "quantity": 300, "unit": "gram"},
                {"name": "banana", "quantity": 1, "unit": "piece"},
                {"name": "yogurt", "quantity": 200, "unit": "ml"},
                {"name": "honey", "quantity": 2, "unit": "tbsp"},
                {"name": "granola", "quantity": 100, "unit": "gram"},
                {"name": "fresh berries", "quantity": 150, "unit": "gram"},
                {"name": "coconut flakes", "quantity": 2, "unit": "tbsp"}
            ],
            "instructions": [
                "Blend frozen berries, banana, yogurt, and honey until thick",
                "Pour into bowls",
                "Top with fresh berries, granola, and coconut flakes",
                "Serve immediately with spoons"
            ]
        }
    ]


if __name__ == '__main__':
    cli() 