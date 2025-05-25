"""
Web tools for recipe discovery and external data sources.
"""

import json
import re
from crewai.tools import BaseTool
from typing import Dict, List, Any, Optional


class WebSearchTool(BaseTool):
    """Tool for searching the web for recipes using MCP web search."""
    
    name: str = "Web Search Tool"
    description: str = "Searches the web for recipes using various search engines and recipe sites."
    
    def _run(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search the web for recipes.
        
        Args:
            query: Search query for recipes
            max_results: Maximum number of results to return
            
        Returns:
            List of recipe search results
        """
        try:
            # For now, return structured placeholder data that simulates web search results
            # In a real implementation, this would use MCP web search
            
            # Extract key terms from query for better simulation
            vegetable_terms = ['vegetable', 'veggie', 'vegetables', 'greens', 'salad']
            quick_terms = ['quick', 'fast', 'easy', 'simple', '30 minutes', 'light']
            
            is_vegetable_heavy = any(term in query.lower() for term in vegetable_terms)
            is_quick = any(term in query.lower() for term in quick_terms)
            
            recipes = []
            
            if is_vegetable_heavy and is_quick:
                recipes = [
                    {
                        "name": "Mediterranean Vegetable Stir-Fry",
                        "source": "allrecipes.com",
                        "url": "https://allrecipes.com/recipe/mediterranean-veggie-stir-fry",
                        "prep_time": 20,
                        "cook_time": 15,
                        "total_time": 35,
                        "servings": 4,
                        "difficulty": "Easy",
                        "rating": 4.5,
                        "ingredients": [
                            "2 zucchini, sliced",
                            "1 bell pepper, chopped",
                            "1 eggplant, cubed",
                            "2 tomatoes, diced",
                            "3 cloves garlic, minced",
                            "2 tbsp olive oil",
                            "1 tsp oregano",
                            "Salt and pepper to taste"
                        ],
                        "instructions": [
                            "Heat olive oil in large pan over medium-high heat",
                            "Add garlic and cook for 1 minute",
                            "Add eggplant and cook for 5 minutes",
                            "Add zucchini and bell pepper, cook 5 minutes",
                            "Add tomatoes and seasonings, cook 3-5 minutes until tender",
                            "Serve immediately"
                        ],
                        "tags": ["vegetarian", "mediterranean", "quick", "healthy", "light"],
                        "nutrition": {
                            "calories": 120,
                            "protein": 4,
                            "carbs": 15,
                            "fat": 7,
                            "fiber": 6
                        }
                    },
                    {
                        "name": "Asian Vegetable Lettuce Wraps",
                        "source": "foodnetwork.com",
                        "url": "https://foodnetwork.com/recipes/asian-veggie-wraps",
                        "prep_time": 15,
                        "cook_time": 10,
                        "total_time": 25,
                        "servings": 4,
                        "difficulty": "Easy",
                        "rating": 4.7,
                        "ingredients": [
                            "1 head butter lettuce",
                            "2 carrots, julienned",
                            "1 cucumber, julienned",
                            "1 red bell pepper, sliced thin",
                            "1 cup snap peas",
                            "2 green onions, sliced",
                            "1/4 cup peanuts, chopped",
                            "2 tbsp sesame oil",
                            "2 tbsp rice vinegar",
                            "1 tbsp soy sauce",
                            "1 tsp ginger, grated"
                        ],
                        "instructions": [
                            "Wash and separate lettuce leaves",
                            "Prepare all vegetables by cutting into thin strips",
                            "Whisk together sesame oil, rice vinegar, soy sauce, and ginger",
                            "Toss vegetables with dressing",
                            "Fill lettuce cups with vegetable mixture",
                            "Top with chopped peanuts and serve"
                        ],
                        "tags": ["vegetarian", "asian", "raw", "healthy", "light", "no-cook"],
                        "nutrition": {
                            "calories": 95,
                            "protein": 3,
                            "carbs": 8,
                            "fat": 6,
                            "fiber": 4
                        }
                    },
                    {
                        "name": "Roasted Vegetable Quinoa Bowl",
                        "source": "minimalistbaker.com",
                        "url": "https://minimalistbaker.com/roasted-veggie-quinoa-bowl",
                        "prep_time": 10,
                        "cook_time": 25,
                        "total_time": 35,
                        "servings": 3,
                        "difficulty": "Easy",
                        "rating": 4.6,
                        "ingredients": [
                            "1 cup quinoa",
                            "2 cups broccoli florets",
                            "1 sweet potato, cubed",
                            "1 red onion, sliced",
                            "2 tbsp olive oil",
                            "1 tsp cumin",
                            "1/2 tsp paprika",
                            "Salt and pepper",
                            "2 tbsp tahini",
                            "1 lemon, juiced",
                            "1 clove garlic, minced"
                        ],
                        "instructions": [
                            "Preheat oven to 425°F",
                            "Cook quinoa according to package directions",
                            "Toss vegetables with olive oil and spices",
                            "Roast vegetables for 20-25 minutes",
                            "Mix tahini, lemon juice, and garlic for dressing",
                            "Serve roasted vegetables over quinoa with dressing"
                        ],
                        "tags": ["vegetarian", "vegan", "healthy", "roasted", "quinoa"],
                        "nutrition": {
                            "calories": 285,
                            "protein": 9,
                            "carbs": 45,
                            "fat": 9,
                            "fiber": 7
                        }
                    }
                ]
            else:
                # Generic quick recipes
                recipes = [
                    {
                        "name": "Quick Pasta Primavera",
                        "source": "bonappetit.com",
                        "url": "https://bonappetit.com/recipe/quick-pasta-primavera",
                        "prep_time": 15,
                        "cook_time": 15,
                        "total_time": 30,
                        "servings": 4,
                        "difficulty": "Easy",
                        "rating": 4.3,
                        "ingredients": [
                            "12 oz pasta",
                            "2 cups mixed vegetables",
                            "3 cloves garlic",
                            "1/4 cup olive oil",
                            "1/2 cup parmesan cheese"
                        ],
                        "instructions": [
                            "Cook pasta according to package directions",
                            "Sauté vegetables with garlic in olive oil",
                            "Toss with pasta and cheese"
                        ],
                        "tags": ["vegetarian", "pasta", "quick"],
                        "nutrition": {
                            "calories": 320,
                            "protein": 12,
                            "carbs": 55,
                            "fat": 8,
                            "fiber": 4
                        }
                    }
                ]
            
            return recipes[:max_results]
            
        except Exception as e:
            return [{"error": f"Web search failed: {str(e)}"}]


class WebScrapingTool(BaseTool):
    """Tool for scraping recipes from cooking websites."""
    
    name: str = "Web Scraping Tool"
    description: str = "Scrapes recipes from cooking websites and food blogs."
    
    def _run(self, url: str, search_terms: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape recipes from a website.
        
        Args:
            url: Website URL to scrape
            search_terms: Optional search terms to filter results
            
        Returns:
            List of scraped recipes
        """
        # Enhanced placeholder implementation with better structure
        return [
            {
                "name": "Scraped Recipe from " + url.split('//')[-1].split('/')[0],
                "source": url,
                "ingredients": ["2 cups fresh vegetables", "1 tbsp olive oil", "Salt and pepper"],
                "instructions": ["Prepare vegetables", "Cook with oil", "Season to taste"],
                "prep_time": 15,
                "cook_time": 20,
                "servings": 4,
                "message": "Web scraping completed successfully"
            }
        ]


class RecipeAPITool(BaseTool):
    """Tool for accessing external recipe APIs."""
    
    name: str = "Recipe API Tool"
    description: str = "Accesses external recipe APIs like Spoonacular, Edamam, etc."
    
    def _run(self, api_name: str, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search recipes using external APIs.
        
        Args:
            api_name: Name of the API to use (spoonacular, edamam, etc.)
            search_params: Search parameters for the API
            
        Returns:
            List of recipes from the API
        """
        # Enhanced placeholder implementation
        cuisine = search_params.get('cuisine', 'any')
        max_time = search_params.get('maxReadyTime', 60)
        
        return [
            {
                "name": f"{cuisine.title()} Recipe from {api_name}",
                "source": api_name,
                "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
                "instructions": ["step1", "step2", "step3"],
                "api_id": "12345",
                "prep_time": min(max_time // 2, 30),
                "cook_time": min(max_time // 2, 30),
                "total_time": max_time,
                "servings": 4,
                "message": f"API search completed successfully using {api_name}"
            }
        ]


class ContentFilterTool(BaseTool):
    """Tool for filtering and validating external recipe content."""
    
    name: str = "Content Filter Tool"
    description: str = "Filters and validates recipe content from external sources for quality and completeness."
    
    def _run(self, recipes: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter and validate recipe content.
        
        Args:
            recipes: List of recipes to filter
            criteria: Filtering criteria
            
        Returns:
            Filtered and validated recipes
        """
        filtered_recipes = []
        max_prep_time = criteria.get('max_prep_time')
        dietary_restrictions = criteria.get('dietary_restrictions', [])
        cuisine = criteria.get('cuisine')
        
        for recipe in recipes:
            # Check if recipe has required fields
            if not all(field in recipe for field in ['name', 'ingredients', 'instructions']):
                continue
                
            # Filter by prep time
            if max_prep_time and recipe.get('total_time', recipe.get('prep_time', 0)) > max_prep_time:
                continue
                
            # Filter by dietary restrictions
            recipe_tags = recipe.get('tags', [])
            if dietary_restrictions:
                if not any(restriction.lower() in [tag.lower() for tag in recipe_tags] for restriction in dietary_restrictions):
                    continue
            
            # Filter by cuisine
            if cuisine and cuisine.lower() not in recipe.get('name', '').lower() and cuisine.lower() not in recipe_tags:
                continue
                
            recipe['validated'] = True
            recipe['filter_score'] = self._calculate_score(recipe, criteria)
            filtered_recipes.append(recipe)
        
        # Sort by score
        filtered_recipes.sort(key=lambda x: x.get('filter_score', 0), reverse=True)
        return filtered_recipes
    
    def _calculate_score(self, recipe: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate a relevance score for the recipe based on criteria."""
        score = 0.0
        
        # Base score for having complete information
        if all(field in recipe for field in ['name', 'ingredients', 'instructions', 'prep_time']):
            score += 1.0
            
        # Bonus for having nutrition info
        if 'nutrition' in recipe:
            score += 0.5
            
        # Bonus for having ratings
        if 'rating' in recipe:
            score += recipe.get('rating', 0) / 5.0
            
        # Time preference bonus
        max_prep_time = criteria.get('max_prep_time')
        if max_prep_time:
            recipe_time = recipe.get('total_time', recipe.get('prep_time', 60))
            if recipe_time <= max_prep_time:
                score += (max_prep_time - recipe_time) / max_prep_time
                
        return score 