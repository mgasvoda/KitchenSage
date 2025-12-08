"""
Meal planning tools for nutritional analysis and meal optimization.
"""

from crewai.tools import BaseTool
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import logging

from src.database import RecipeRepository, MealPlanRepository, DatabaseError
from src.models import (
    Recipe, MealPlan, MealPlanCreate, Meal, MealType,
    DietaryTag, DifficultyLevel, NutritionalInfo
)

logger = logging.getLogger(__name__)


class MealPlanningTool(BaseTool):
    """Tool for creating and optimizing meal plans."""
    
    name: str = "Meal Planning Tool"
    description: str = "Creates optimized meal plans based on dietary requirements, preferences, and constraints."
    
    def _get_repositories(self):
        """Get repository instances (lazy initialization)."""
        if not hasattr(self, '_repos'):
            self._repos = {
                'recipes': RecipeRepository(),
                'meal_plans': MealPlanRepository()
            }
        return self._repos
    
    def _run(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a meal plan based on requirements.
        
        Args:
            requirements: Dictionary containing meal plan requirements like:
                - start_date: Start date for meal plan
                - days: Number of days (default: 7)
                - people: Number of people (default: 2)
                - dietary_restrictions: List of dietary tags
                - max_prep_time: Maximum prep time per meal
                - difficulty: Preferred difficulty level
                - cuisine_preferences: List of preferred cuisines
                - exclude_ingredients: List of ingredients to avoid
                
        Returns:
            Generated meal plan with assigned recipes
        """
        try:
            # Parse requirements
            days = requirements.get('days', 7)
            people = requirements.get('people', 2)
            start_date_str = requirements.get('start_date', datetime.now().strftime('%Y-%m-%d'))
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
            dietary_restrictions = requirements.get('dietary_restrictions', [])
            max_prep_time = requirements.get('max_prep_time', 60)
            difficulty = requirements.get('difficulty')
            cuisine_preferences = requirements.get('cuisine_preferences', [])
            exclude_ingredients = requirements.get('exclude_ingredients', [])
            
            # Get suitable recipes
            recipe_filters = self._build_recipe_filters(
                dietary_restrictions, max_prep_time, difficulty, 
                cuisine_preferences, exclude_ingredients
            )
            
            # Use search_recipes method from RecipeRepository
            available_recipes = self._get_repositories()['recipes'].search_recipes(
                max_prep_time=max_prep_time,
                difficulty=difficulty,
                limit=100  # Get more recipes for better variety
            )
            
            # Convert to dictionaries for processing
            recipe_dicts = []
            for recipe in available_recipes:
                if hasattr(recipe, 'model_dump'):
                    recipe_dict = recipe.model_dump()
                elif hasattr(recipe, 'dict'):
                    recipe_dict = recipe.dict()
                else:
                    recipe_dict = recipe.__dict__
                recipe_dicts.append(recipe_dict)
            
            if len(recipe_dicts) < days * 3:  # Need enough for 3 meals per day
                return {
                    "status": "warning",
                    "message": f"Limited recipes available ({len(recipe_dicts)}). Meal plan may have repetitions.",
                    "meal_plan": self._create_basic_meal_plan(recipe_dicts, days, people, start_date)
                }
            
            # Create optimized meal plan
            meal_plan = self._create_optimized_meal_plan(
                recipe_dicts, days, people, start_date, requirements
            )
            
            # Save to database
            meal_plan_data = {
                'name': f"Meal Plan {start_date.strftime('%Y-%m-%d')}",
                'start_date': start_date,
                'end_date': start_date + timedelta(days=days-1),
                'people_count': people,
                'dietary_restrictions': dietary_restrictions,
                'meals': meal_plan['meals']
            }
            
            meal_plan_id = self._get_repositories()['meal_plans'].create(meal_plan_data)
            meal_plan['meal_plan_id'] = meal_plan_id
            
            return {
                "status": "success",
                "meal_plan": meal_plan,
                "message": f"Meal plan created successfully for {days} days"
            }
            
        except Exception as e:
            logger.error(f"Meal planning failed: {e}")
            return {
                "status": "error",
                "message": f"Failed to create meal plan: {str(e)}"
            }
    
    def _build_recipe_filters(self, dietary_restrictions: List[str], max_prep_time: int,
                             difficulty: Optional[str], cuisine_preferences: List[str],
                             exclude_ingredients: List[str]) -> Dict[str, Any]:
        """Build recipe search filters based on requirements."""
        filters = {}
        
        if max_prep_time:
            filters['max_prep_time'] = max_prep_time
        
        if difficulty:
            filters['difficulty'] = difficulty
        
        # Note: dietary_restrictions and cuisine_preferences will be filtered post-query
        # since they might require more complex logic
        
        return filters
    
    def _filter_recipes_by_requirements(self, recipes: List[Dict[str, Any]], 
                                       dietary_restrictions: List[str],
                                       cuisine_preferences: List[str],
                                       exclude_ingredients: List[str]) -> List[Dict[str, Any]]:
        """Filter recipes based on dietary and preference requirements."""
        filtered_recipes = []
        
        for recipe in recipes:
            # Check dietary restrictions
            recipe_tags = set(recipe.get('dietary_tags', []))
            required_tags = set(dietary_restrictions)
            
            if required_tags and not required_tags.issubset(recipe_tags):
                continue
            
            # Check cuisine preferences (if specified)
            if cuisine_preferences:
                recipe_cuisine = recipe.get('cuisine', '').lower()
                if recipe_cuisine not in [c.lower() for c in cuisine_preferences]:
                    continue
            
            # Check excluded ingredients
            if exclude_ingredients:
                recipe_ingredients = [
                    ing.get('name', '').lower() 
                    for ing in recipe.get('ingredients', [])
                ]
                
                has_excluded = any(
                    excluded.lower() in ingredient 
                    for excluded in exclude_ingredients 
                    for ingredient in recipe_ingredients
                )
                
                if has_excluded:
                    continue
            
            filtered_recipes.append(recipe)
        
        return filtered_recipes
    
    def _create_basic_meal_plan(self, recipes: List[Dict[str, Any]], days: int, 
                               people: int, start_date: date) -> Dict[str, Any]:
        """Create a basic meal plan with simple recipe assignment."""
        meals = []
        recipe_index = 0
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Assign breakfast, lunch, dinner
            for meal_type in [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]:
                if recipe_index < len(recipes):
                    recipe = recipes[recipe_index]
                    recipe_index += 1
                else:
                    # Cycle back to beginning if we run out of recipes
                    recipe_index = 0
                    recipe = recipes[recipe_index] if recipes else None
                
                if recipe:
                    meal = {
                        'date': current_date,
                        'meal_type': meal_type.value,
                        'recipe_id': recipe['id'],
                        'recipe_name': recipe['name'],
                        'servings': recipe.get('servings', people),
                        'prep_time': recipe.get('prep_time', 0),
                        'cook_time': recipe.get('cook_time', 0)
                    }
                    meals.append(meal)
        
        return {
            'days': days,
            'people': people,
            'start_date': start_date,
            'end_date': start_date + timedelta(days=days-1),
            'meals': meals,
            'total_recipes': len(set(meal['recipe_id'] for meal in meals))
        }
    
    def _create_optimized_meal_plan(self, recipes: List[Dict[str, Any]], days: int,
                                   people: int, start_date: date, 
                                   requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create an optimized meal plan with balanced nutrition and variety."""
        
        # Filter recipes by requirements
        dietary_restrictions = requirements.get('dietary_restrictions', [])
        cuisine_preferences = requirements.get('cuisine_preferences', [])
        exclude_ingredients = requirements.get('exclude_ingredients', [])
        
        filtered_recipes = self._filter_recipes_by_requirements(
            recipes, dietary_restrictions, cuisine_preferences, exclude_ingredients
        )
        
        # Categorize recipes by meal type suitability
        breakfast_recipes = self._categorize_recipes_for_meal_type(filtered_recipes, MealType.BREAKFAST)
        lunch_recipes = self._categorize_recipes_for_meal_type(filtered_recipes, MealType.LUNCH)
        dinner_recipes = self._categorize_recipes_for_meal_type(filtered_recipes, MealType.DINNER)
        
        meals = []
        used_recipes = set()
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Assign breakfast
            breakfast = self._select_optimal_recipe(
                breakfast_recipes, used_recipes, MealType.BREAKFAST, people
            )
            if breakfast:
                meals.append({
                    'date': current_date,
                    'meal_type': MealType.BREAKFAST.value,
                    **breakfast
                })
                used_recipes.add(breakfast['recipe_id'])
            
            # Assign lunch
            lunch = self._select_optimal_recipe(
                lunch_recipes, used_recipes, MealType.LUNCH, people
            )
            if lunch:
                meals.append({
                    'date': current_date,
                    'meal_type': MealType.LUNCH.value,
                    **lunch
                })
                used_recipes.add(lunch['recipe_id'])
            
            # Assign dinner
            dinner = self._select_optimal_recipe(
                dinner_recipes, used_recipes, MealType.DINNER, people
            )
            if dinner:
                meals.append({
                    'date': current_date,
                    'meal_type': MealType.DINNER.value,
                    **dinner
                })
                used_recipes.add(dinner['recipe_id'])
        
        return {
            'days': days,
            'people': people,
            'start_date': start_date,
            'end_date': start_date + timedelta(days=days-1),
            'meals': meals,
            'total_recipes': len(used_recipes),
            'variety_score': len(used_recipes) / len(meals) if meals else 0
        }
    
    def _categorize_recipes_for_meal_type(self, recipes: List[Dict[str, Any]], 
                                         meal_type: MealType) -> List[Dict[str, Any]]:
        """Categorize recipes based on their suitability for different meal types."""
        suitable_recipes = []
        
        for recipe in recipes:
            name = recipe.get('name', '').lower()
            prep_time = recipe.get('prep_time', 0)
            cook_time = recipe.get('cook_time', 0)
            total_time = prep_time + cook_time
            
            is_suitable = False
            
            if meal_type == MealType.BREAKFAST:
                # Quick meals, breakfast foods
                breakfast_keywords = ['breakfast', 'cereal', 'eggs', 'toast', 'pancake', 'oatmeal', 'smoothie']
                is_suitable = (
                    any(keyword in name for keyword in breakfast_keywords) or
                    total_time <= 20
                )
            
            elif meal_type == MealType.LUNCH:
                # Medium prep time, lighter meals
                lunch_keywords = ['salad', 'sandwich', 'soup', 'bowl', 'wrap', 'pasta']
                is_suitable = (
                    any(keyword in name for keyword in lunch_keywords) or
                    (10 <= total_time <= 45)
                )
            
            elif meal_type == MealType.DINNER:
                # Can be more complex, heartier meals
                dinner_keywords = ['dinner', 'roast', 'stew', 'curry', 'casserole', 'grilled']
                is_suitable = (
                    any(keyword in name for keyword in dinner_keywords) or
                    total_time >= 20
                )
            
            if is_suitable:
                suitable_recipes.append(recipe)
        
        # If no specific matches, use all recipes as fallback
        return suitable_recipes if suitable_recipes else recipes
    
    def _select_optimal_recipe(self, recipes: List[Dict[str, Any]], used_recipes: set,
                              meal_type: MealType, people: int) -> Optional[Dict[str, Any]]:
        """Select the optimal recipe for a meal considering variety and preferences."""
        available_recipes = [r for r in recipes if r['id'] not in used_recipes]
        
        if not available_recipes:
            # If all recipes used, allow repetition but prefer least recently used
            available_recipes = recipes
        
        if not available_recipes:
            return None
        
        # Score recipes based on various factors
        scored_recipes = []
        for recipe in available_recipes:
            score = 0
            
            # Preference for unused recipes
            if recipe['id'] not in used_recipes:
                score += 10
            
            # Preference for appropriate prep time for meal type
            prep_time = recipe.get('prep_time', 0)
            if meal_type == MealType.BREAKFAST and prep_time <= 15:
                score += 5
            elif meal_type == MealType.LUNCH and 15 <= prep_time <= 30:
                score += 5
            elif meal_type == MealType.DINNER and prep_time >= 20:
                score += 5
            
            # Preference for appropriate servings
            servings = recipe.get('servings', 2)
            if servings >= people:
                score += 3
            
            scored_recipes.append((score, recipe))
        
        # Select highest scored recipe
        scored_recipes.sort(key=lambda x: x[0], reverse=True)
        selected_recipe = scored_recipes[0][1]
        
        return {
            'recipe_id': selected_recipe['id'],
            'recipe_name': selected_recipe['name'],
            'servings': selected_recipe.get('servings', people),
            'prep_time': selected_recipe.get('prep_time', 0),
            'cook_time': selected_recipe.get('cook_time', 0)
        }


class NutritionAnalysisTool(BaseTool):
    """Tool for analyzing nutritional content of recipes and meal plans."""
    
    name: str = "Nutrition Analysis Tool"
    description: str = "Analyzes nutritional content including calories, macronutrients, and micronutrients."
    
    def _get_recipe_repo(self):
        """Get recipe repository instance (lazy initialization)."""
        if not hasattr(self, '_recipe_repo'):
            self._recipe_repo = RecipeRepository()
        return self._recipe_repo
    
    def _run(self, recipes: List[Dict[str, Any]], servings_multiplier: float = 1.0) -> Dict[str, Any]:
        """
        Analyze nutritional content of recipes.
        
        Args:
            recipes: List of recipes to analyze (can include recipe IDs or full recipe data)
            servings_multiplier: Multiplier for serving sizes
            
        Returns:
            Nutritional analysis results
        """
        try:
            total_nutrition = {
                'calories': 0,
                'protein': 0,
                'carbohydrates': 0,
                'fat': 0,
                'fiber': 0,
                'sugar': 0,
                'sodium': 0
            }
            
            analyzed_recipes = []
            
            for recipe_input in recipes:
                # Get full recipe data if only ID provided
                if isinstance(recipe_input, int) or 'id' in recipe_input and len(recipe_input) == 1:
                    recipe_id = recipe_input if isinstance(recipe_input, int) else recipe_input['id']
                    recipe = self._get_recipe_repo().get_by_id(recipe_id)
                else:
                    recipe = recipe_input
                
                if not recipe:
                    continue
                
                # Get nutritional info
                nutrition_info = recipe.get('nutritional_info', {})
                recipe_servings = recipe.get('servings', 1)
                
                # Calculate per-serving nutrition and apply multiplier
                per_serving_nutrition = {}
                for nutrient, value in nutrition_info.items():
                    if isinstance(value, (int, float)):
                        per_serving_value = value / recipe_servings
                        adjusted_value = per_serving_value * servings_multiplier
                        per_serving_nutrition[nutrient] = adjusted_value
                        
                        if nutrient in total_nutrition:
                            total_nutrition[nutrient] += adjusted_value
                
                analyzed_recipes.append({
                    'recipe_id': recipe.get('id'),
                    'recipe_name': recipe.get('name'),
                    'servings': recipe_servings,
                    'servings_multiplier': servings_multiplier,
                    'nutrition': per_serving_nutrition
                })
            
            # Calculate percentages and daily values
            daily_values = self._calculate_daily_value_percentages(total_nutrition)
            macros_breakdown = self._calculate_macros_breakdown(total_nutrition)
            
            return {
                "status": "success",
                "total_nutrition": total_nutrition,
                "daily_value_percentages": daily_values,
                "macros_breakdown": macros_breakdown,
                "analyzed_recipes": analyzed_recipes,
                "analysis_summary": self._generate_nutrition_summary(total_nutrition, daily_values),
                "message": f"Analyzed nutrition for {len(analyzed_recipes)} recipes"
            }
            
        except Exception as e:
            logger.error(f"Nutrition analysis failed: {e}")
            return {
                "status": "error",
                "message": f"Nutrition analysis failed: {str(e)}"
            }
    
    def _calculate_daily_value_percentages(self, nutrition: Dict[str, float]) -> Dict[str, float]:
        """Calculate percentage of daily values for nutrients."""
        # Standard daily values (based on 2000 calorie diet)
        daily_values = {
            'calories': 2000,
            'protein': 50,      # grams
            'carbohydrates': 300,  # grams
            'fat': 65,          # grams
            'fiber': 25,        # grams
            'sodium': 2300      # mg
        }
        
        percentages = {}
        for nutrient, total_amount in nutrition.items():
            if nutrient in daily_values and daily_values[nutrient] > 0:
                percentage = (total_amount / daily_values[nutrient]) * 100
                percentages[nutrient] = round(percentage, 1)
        
        return percentages
    
    def _calculate_macros_breakdown(self, nutrition: Dict[str, float]) -> Dict[str, Any]:
        """Calculate macronutrient breakdown by calories."""
        protein_cals = nutrition.get('protein', 0) * 4  # 4 cal/g
        carb_cals = nutrition.get('carbohydrates', 0) * 4  # 4 cal/g
        fat_cals = nutrition.get('fat', 0) * 9  # 9 cal/g
        
        total_macro_cals = protein_cals + carb_cals + fat_cals
        
        if total_macro_cals == 0:
            return {
                "protein_percentage": 0,
                "carbohydrates_percentage": 0,
                "fat_percentage": 0,
                "total_macro_calories": 0
            }
        
        return {
            "protein_percentage": round((protein_cals / total_macro_cals) * 100, 1),
            "carbohydrates_percentage": round((carb_cals / total_macro_cals) * 100, 1),
            "fat_percentage": round((fat_cals / total_macro_cals) * 100, 1),
            "total_macro_calories": round(total_macro_cals, 1),
            "protein_calories": round(protein_cals, 1),
            "carbohydrates_calories": round(carb_cals, 1),
            "fat_calories": round(fat_cals, 1)
        }
    
    def _generate_nutrition_summary(self, nutrition: Dict[str, float], 
                                   daily_values: Dict[str, float]) -> Dict[str, str]:
        """Generate a human-readable nutrition summary."""
        summary = {}
        
        # Calorie assessment
        calories = nutrition.get('calories', 0)
        if calories < 1200:
            summary['calories'] = "Low calorie intake - may not meet daily needs"
        elif calories > 2500:
            summary['calories'] = "High calorie intake - consider portion control"
        else:
            summary['calories'] = "Moderate calorie intake"
        
        # Protein assessment
        protein_pct = daily_values.get('protein', 0)
        if protein_pct < 80:
            summary['protein'] = "Low protein - consider adding protein sources"
        elif protein_pct > 150:
            summary['protein'] = "High protein intake"
        else:
            summary['protein'] = "Adequate protein intake"
        
        # Fiber assessment
        fiber_pct = daily_values.get('fiber', 0)
        if fiber_pct < 50:
            summary['fiber'] = "Low fiber - add more fruits, vegetables, and whole grains"
        else:
            summary['fiber'] = "Good fiber intake"
        
        # Sodium assessment
        sodium_pct = daily_values.get('sodium', 0)
        if sodium_pct > 100:
            summary['sodium'] = "High sodium - consider reducing salt and processed foods"
        else:
            summary['sodium'] = "Moderate sodium intake"
        
        return summary


class CalendarTool(BaseTool):
    """Tool for scheduling meals and managing meal plan calendar."""
    
    name: str = "Calendar Tool"
    description: str = "Manages meal scheduling and calendar integration for meal plans."
    
    def _get_meal_plan_repo(self):
        """Get meal plan repository instance (lazy initialization)."""
        if not hasattr(self, '_meal_plan_repo'):
            self._meal_plan_repo = MealPlanRepository()
        return self._meal_plan_repo
    
    def _run(self, meal_plan: Dict[str, Any], start_date: str, 
             calendar_format: str = "weekly") -> Dict[str, Any]:
        """
        Schedule meals on a calendar.
        
        Args:
            meal_plan: Meal plan to schedule
            start_date: Start date for the meal plan
            calendar_format: Format for calendar display (daily, weekly, monthly)
            
        Returns:
            Calendar with scheduled meals
        """
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            meals = meal_plan.get('meals', [])
            
            if calendar_format == "weekly":
                calendar_data = self._create_weekly_calendar(meals, start_date_obj)
            elif calendar_format == "daily":
                calendar_data = self._create_daily_calendar(meals, start_date_obj)
            elif calendar_format == "monthly":
                calendar_data = self._create_monthly_calendar(meals, start_date_obj)
            else:
                raise ValueError(f"Unsupported calendar format: {calendar_format}")
            
            # Calculate summary statistics
            summary = self._calculate_calendar_summary(meals)
            
            end_date = start_date_obj + timedelta(days=meal_plan.get('days', 7) - 1)
            
            return {
                "status": "success",
                "calendar": calendar_data,
                "format": calendar_format,
                "start_date": start_date,
                "end_date": end_date.strftime('%Y-%m-%d'),
                "summary": summary,
                "message": "Meal plan scheduled successfully"
            }
            
        except Exception as e:
            logger.error(f"Calendar scheduling failed: {e}")
            return {
                "status": "error",
                "message": f"Calendar scheduling failed: {str(e)}"
            }
    
    def _create_weekly_calendar(self, meals: List[Dict[str, Any]], 
                               start_date: date) -> Dict[str, Any]:
        """Create a weekly calendar view."""
        calendar_data = {}
        
        # Group meals by date
        meals_by_date = {}
        for meal in meals:
            meal_date = meal.get('date')
            if isinstance(meal_date, str):
                meal_date = datetime.strptime(meal_date, '%Y-%m-%d').date()
            
            date_str = meal_date.strftime('%Y-%m-%d')
            if date_str not in meals_by_date:
                meals_by_date[date_str] = []
            
            meals_by_date[date_str].append(meal)
        
        # Create weekly structure
        current_date = start_date
        week_num = 1
        
        while current_date.strftime('%Y-%m-%d') in meals_by_date:
            week_start = current_date
            week_end = current_date + timedelta(days=6)
            
            week_data = {
                'week_start': week_start.strftime('%Y-%m-%d'),
                'week_end': week_end.strftime('%Y-%m-%d'),
                'days': {}
            }
            
            for day_offset in range(7):
                day_date = week_start + timedelta(days=day_offset)
                day_str = day_date.strftime('%Y-%m-%d')
                day_name = day_date.strftime('%A')
                
                week_data['days'][day_name] = {
                    'date': day_str,
                    'meals': meals_by_date.get(day_str, [])
                }
                
                if day_str not in meals_by_date:
                    break
            
            calendar_data[f'week_{week_num}'] = week_data
            week_num += 1
            current_date = week_end + timedelta(days=1)
        
        return calendar_data
    
    def _create_daily_calendar(self, meals: List[Dict[str, Any]], 
                              start_date: date) -> Dict[str, Any]:
        """Create a daily calendar view."""
        calendar_data = {}
        
        for meal in meals:
            meal_date = meal.get('date')
            if isinstance(meal_date, str):
                meal_date = datetime.strptime(meal_date, '%Y-%m-%d').date()
            
            date_str = meal_date.strftime('%Y-%m-%d')
            
            if date_str not in calendar_data:
                calendar_data[date_str] = {
                    'date': date_str,
                    'day_name': meal_date.strftime('%A'),
                    'meals': []
                }
            
            calendar_data[date_str]['meals'].append(meal)
        
        return calendar_data
    
    def _create_monthly_calendar(self, meals: List[Dict[str, Any]], 
                                start_date: date) -> Dict[str, Any]:
        """Create a monthly calendar view."""
        calendar_data = {}
        
        # Group meals by month
        for meal in meals:
            meal_date = meal.get('date')
            if isinstance(meal_date, str):
                meal_date = datetime.strptime(meal_date, '%Y-%m-%d').date()
            
            month_key = meal_date.strftime('%Y-%m')
            date_str = meal_date.strftime('%Y-%m-%d')
            
            if month_key not in calendar_data:
                calendar_data[month_key] = {
                    'month_year': meal_date.strftime('%B %Y'),
                    'days': {}
                }
            
            if date_str not in calendar_data[month_key]['days']:
                calendar_data[month_key]['days'][date_str] = {
                    'date': date_str,
                    'day_name': meal_date.strftime('%A'),
                    'meals': []
                }
            
            calendar_data[month_key]['days'][date_str]['meals'].append(meal)
        
        return calendar_data
    
    def _calculate_calendar_summary(self, meals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for the calendar."""
        total_meals = len(meals)
        unique_recipes = len(set(meal.get('recipe_id') for meal in meals if meal.get('recipe_id')))
        
        total_prep_time = sum(meal.get('prep_time', 0) for meal in meals)
        total_cook_time = sum(meal.get('cook_time', 0) for meal in meals)
        
        meal_types = {}
        for meal in meals:
            meal_type = meal.get('meal_type', 'unknown')
            meal_types[meal_type] = meal_types.get(meal_type, 0) + 1
        
        return {
            'total_meals': total_meals,
            'unique_recipes': unique_recipes,
            'variety_score': unique_recipes / total_meals if total_meals > 0 else 0,
            'total_prep_time': total_prep_time,
            'total_cook_time': total_cook_time,
            'average_prep_time': total_prep_time / total_meals if total_meals > 0 else 0,
            'average_cook_time': total_cook_time / total_meals if total_meals > 0 else 0,
            'meals_by_type': meal_types
        } 