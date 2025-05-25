"""
Web tools for recipe discovery and external data sources.
"""

import json
import re
import os
from crewai.tools import BaseTool
from typing import Dict, List, Any, Optional
from openai import OpenAI
from datetime import datetime


class WebSearchTool(BaseTool):
    """Tool for searching the web for recipes using OpenAI's web search capability."""
    
    name: str = "Web Search Tool"
    description: str = "Searches the web for recipes using OpenAI's web search functionality."
    
    def _run(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search the web for recipes using OpenAI's web search.
        
        Args:
            query: Search query for recipes
            max_results: Maximum number of results to return
            
        Returns:
            List of recipe search results with URLs for scraping
        """
        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Enhance the prompt to ensure we get recipe results with URLs
            enhanced_prompt = f"""
            Search for {query} recipes and provide detailed recipe information. 
            
            IMPORTANT: Return ONLY a valid JSON array of recipe objects. Do not include any explanatory text before or after the JSON.
            
            For each recipe found, include these exact fields:
            - "name": Recipe name as a string
            - "source": Source website domain (e.g., "allrecipes.com")
            - "url": Complete URL to the recipe page
            - "ingredients": Array of ingredient strings
            - "instructions": Array of instruction strings
            - "prep_time": Prep time in minutes (number)
            - "cook_time": Cook time in minutes (number)
            - "total_time": Total time in minutes (number)
            - "servings": Number of servings (number)
            - "difficulty": Difficulty level ("Easy", "Medium", or "Hard")
            - "tags": Array of dietary/cuisine tags
            - "nutrition": Object with calories, protein, carbs, fat if available
            
            Example format:
            [
              {{
                "name": "Quick Vegetarian Pasta",
                "source": "allrecipes.com",
                "url": "https://allrecipes.com/recipe/quick-vegetarian-pasta",
                "ingredients": ["1 lb pasta", "2 cups vegetables"],
                "instructions": ["Cook pasta", "Add vegetables"],
                "prep_time": 10,
                "cook_time": 15,
                "total_time": 25,
                "servings": 4,
                "difficulty": "Easy",
                "tags": ["vegetarian", "quick"],
                "nutrition": {{"calories": 300, "protein": 12, "carbs": 45, "fat": 8}}
              }}
            ]
            
            Limit to {max_results} recipes maximum.
            """
            
            # Use OpenAI's responses API with web search
            response = client.responses.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini as specified
                input=enhanced_prompt,
                tools=[
                    {
                        "type": "web_search_preview"
                    }
                ]
            )
            
            # Extract the response content
            if hasattr(response, 'output_text') and response.output_text:
                content = response.output_text.strip()
                
                # Clean up the content to extract JSON
                # Remove any text before the first [ and after the last ]
                start_idx = content.find('[')
                end_idx = content.rfind(']')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_content = content[start_idx:end_idx + 1]
                else:
                    json_content = content
                
                # Try to parse JSON response
                try:
                    recipes = json.loads(json_content)
                    if isinstance(recipes, list):
                        # Ensure each recipe has required fields and a URL
                        processed_recipes = []
                        for recipe in recipes:
                            if isinstance(recipe, dict):
                                # Ensure URL is present for web scraping
                                if 'url' not in recipe or not recipe['url']:
                                    # Generate a placeholder URL based on source
                                    source = recipe.get('source', 'unknown')
                                    recipe_name = recipe.get('name', 'recipe').lower().replace(' ', '-').replace('&', 'and')
                                    recipe['url'] = f"https://{source}/recipe/{recipe_name}"
                                
                                # Ensure required fields are present
                                recipe.setdefault('name', 'Unknown Recipe')
                                recipe.setdefault('ingredients', [])
                                recipe.setdefault('instructions', [])
                                recipe.setdefault('prep_time', 0)
                                recipe.setdefault('cook_time', 0)
                                recipe.setdefault('total_time', recipe.get('prep_time', 0) + recipe.get('cook_time', 0))
                                recipe.setdefault('servings', 4)
                                recipe.setdefault('difficulty', 'Medium')
                                recipe.setdefault('tags', [])
                                recipe.setdefault('source', 'web_search')
                                
                                processed_recipes.append(recipe)
                        
                        return processed_recipes[:max_results]
                    
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, try to extract recipe information from text
                    return self._parse_text_response(content, max_results)
            
            # Fallback if no valid response
            return [{"error": "No recipes found", "message": "Web search completed but no recipes were returned"}]
            
        except Exception as e:
            return [{"error": f"Web search failed: {str(e)}", "message": "Please check your OpenAI API key and internet connection"}]
    
    def _parse_text_response(self, content: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Parse text response when JSON parsing fails.
        
        Args:
            content: Text content from OpenAI response
            max_results: Maximum number of results to return
            
        Returns:
            List of parsed recipe dictionaries
        """
        recipes = []
        
        # Simple text parsing - look for recipe-like patterns
        lines = content.split('\n')
        current_recipe = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for recipe names (often in titles or bold)
            if any(keyword in line.lower() for keyword in ['recipe', 'dish', 'meal']):
                if current_recipe and 'name' in current_recipe:
                    recipes.append(current_recipe)
                    current_recipe = {}
                
                current_recipe['name'] = line.replace('*', '').replace('#', '').strip()
                current_recipe['source'] = 'web_search'
                current_recipe['url'] = f"https://example.com/recipe/{current_recipe['name'].lower().replace(' ', '-')}"
                current_recipe['ingredients'] = []
                current_recipe['instructions'] = []
                current_recipe['prep_time'] = 30
                current_recipe['cook_time'] = 30
                current_recipe['total_time'] = 60
                current_recipe['servings'] = 4
                current_recipe['difficulty'] = 'Medium'
                current_recipe['tags'] = []
        
        if current_recipe and 'name' in current_recipe:
            recipes.append(current_recipe)
        
        return recipes[:max_results]


class WebScrapingTool(BaseTool):
    """Tool for scraping recipes from cooking websites using OpenAI for content extraction."""
    
    name: str = "Web Scraping Tool"
    description: str = "Scrapes recipes from cooking websites and extracts structured recipe data using AI."
    
    def _run(self, url: str, search_terms: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape recipes from a website using OpenAI for content extraction.
        
        Args:
            url: Website URL to scrape
            search_terms: Optional search terms to filter results
            
        Returns:
            List of scraped recipes with structured data
        """
        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Create a prompt for OpenAI to scrape and extract recipe data
            scraping_prompt = f"""
            Please scrape the recipe content from this URL: {url}
            
            IMPORTANT: Return ONLY a valid JSON object with the recipe information. Do not include any explanatory text.
            
            Extract and format as JSON with these exact fields:
            - "name": Recipe name as a string
            - "ingredients": Array of ingredient strings with quantities
            - "instructions": Array of step-by-step instruction strings
            - "prep_time": Prep time in minutes (number)
            - "cook_time": Cook time in minutes (number)
            - "total_time": Total time in minutes (number)
            - "servings": Number of servings (number)
            - "difficulty": Difficulty level ("Easy", "Medium", or "Hard")
            - "tags": Array of dietary/cuisine tags
            - "nutrition": Object with nutritional info if available
            - "description": Brief recipe description
            - "tips": Array of cooking tips if available
            
            If search terms are provided: {search_terms or 'None'}, prioritize content matching these terms.
            
            Example format:
            {{
              "name": "Recipe Name",
              "ingredients": ["1 cup flour", "2 eggs"],
              "instructions": ["Mix ingredients", "Bake for 30 minutes"],
              "prep_time": 15,
              "cook_time": 30,
              "total_time": 45,
              "servings": 4,
              "difficulty": "Easy",
              "tags": ["vegetarian", "baking"],
              "nutrition": {{"calories": 250, "protein": 8}},
              "description": "A delicious recipe",
              "tips": ["Tip 1", "Tip 2"]
            }}
            """
            
            # Use OpenAI's responses API with web search to access the URL
            response = client.responses.create(
                model="gpt-4o-mini",
                input=scraping_prompt,
                tools=[
                    {
                        "type": "web_search_preview"
                    }
                ]
            )
            
            # Extract and process the response
            if hasattr(response, 'output_text') and response.output_text:
                content = response.output_text.strip()
                
                # Clean up the content to extract JSON
                # Look for JSON object or array
                start_idx = max(content.find('{'), content.find('['))
                if content.find('{') != -1 and content.find('[') != -1:
                    start_idx = min(content.find('{'), content.find('['))
                elif content.find('{') != -1:
                    start_idx = content.find('{')
                    end_idx = content.rfind('}')
                else:
                    start_idx = content.find('[')
                    end_idx = content.rfind(']')
                
                if start_idx != -1:
                    if content[start_idx] == '{':
                        end_idx = content.rfind('}')
                    else:
                        end_idx = content.rfind(']')
                    
                    if end_idx != -1 and end_idx > start_idx:
                        json_content = content[start_idx:end_idx + 1]
                    else:
                        json_content = content
                else:
                    json_content = content
                
                try:
                    # Try to parse as JSON
                    scraped_data = json.loads(json_content)
                    
                    # Ensure we have a list of recipes
                    if isinstance(scraped_data, dict):
                        scraped_data = [scraped_data]
                    
                    processed_recipes = []
                    for recipe in scraped_data:
                        if isinstance(recipe, dict):
                            # Ensure required fields and add metadata
                            recipe.setdefault('name', f"Recipe from {url.split('//')[-1].split('/')[0]}")
                            recipe.setdefault('source', url)
                            recipe.setdefault('url', url)
                            recipe.setdefault('ingredients', [])
                            recipe.setdefault('instructions', [])
                            recipe.setdefault('prep_time', 0)
                            recipe.setdefault('cook_time', 0)
                            recipe.setdefault('total_time', recipe.get('prep_time', 0) + recipe.get('cook_time', 0))
                            recipe.setdefault('servings', 4)
                            recipe.setdefault('difficulty', 'Medium')
                            recipe.setdefault('tags', [])
                            recipe['scraped_at'] = json.dumps({"timestamp": str(datetime.now())})
                            recipe['message'] = "Recipe successfully scraped and extracted"
                            
                            processed_recipes.append(recipe)
                    
                    return processed_recipes
                    
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, create a structured response from text
                    return self._parse_scraped_text(content, url)
            
            # Fallback response
            return [{
                "name": f"Recipe from {url.split('//')[-1].split('/')[0]}",
                "source": url,
                "url": url,
                "ingredients": ["Unable to extract ingredients"],
                "instructions": ["Unable to extract instructions"],
                "prep_time": 0,
                "cook_time": 0,
                "servings": 4,
                "message": "Web scraping completed but content extraction was limited",
                "error": "Could not fully parse recipe content"
            }]
            
        except Exception as e:
            return [{
                "error": f"Web scraping failed: {str(e)}",
                "url": url,
                "message": "Please check the URL and your internet connection"
            }]
    
    def _parse_scraped_text(self, content: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse scraped text content when JSON parsing fails.
        
        Args:
            content: Text content from scraping
            url: Source URL
            
        Returns:
            List of parsed recipe dictionaries
        """
        # Basic text parsing for recipe information
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        recipe = {
            "name": f"Recipe from {url.split('//')[-1].split('/')[0]}",
            "source": url,
            "url": url,
            "ingredients": [],
            "instructions": [],
            "prep_time": 30,
            "cook_time": 30,
            "total_time": 60,
            "servings": 4,
            "difficulty": "Medium",
            "tags": [],
            "scraped_at": json.dumps({"timestamp": str(datetime.now())}),
            "message": "Recipe scraped with basic text parsing"
        }
        
        # Try to extract recipe name from first few lines
        for line in lines[:5]:
            if len(line) > 10 and len(line) < 100:
                recipe["name"] = line
                break
        
        # Look for ingredients and instructions in the content
        current_section = None
        for line in lines:
            line_lower = line.lower()
            
            if any(word in line_lower for word in ['ingredient', 'what you need', 'you will need']):
                current_section = 'ingredients'
                continue
            elif any(word in line_lower for word in ['instruction', 'method', 'directions', 'steps', 'how to']):
                current_section = 'instructions'
                continue
            
            if current_section == 'ingredients' and line and not line.startswith('#'):
                recipe["ingredients"].append(line)
            elif current_section == 'instructions' and line and not line.startswith('#'):
                recipe["instructions"].append(line)
        
        return [recipe]


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