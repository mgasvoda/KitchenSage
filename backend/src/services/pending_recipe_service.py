"""
Pending recipe service for URL parsing and AI discovery.
"""

import logging
from typing import Dict, Any, List, Optional

from src.database import PendingRecipeRepository, RecordNotFoundError, ValidationError
from src.models import (
    PendingRecipe, PendingRecipeCreate, PendingRecipeUpdate,
    PendingRecipeStatus, PendingRecipeIngredient
)
from src.tools.web_tools import WebScrapingTool, WebSearchTool

logger = logging.getLogger(__name__)


class PendingRecipeService:
    """
    Service layer for pending recipe operations.
    
    Handles URL parsing, AI discovery, and management of pending recipes
    awaiting user approval.
    """
    
    def __init__(self):
        self.repository = PendingRecipeRepository()
        self.scraping_tool = WebScrapingTool()
        self.search_tool = WebSearchTool()
    
    def parse_url(self, url: str) -> Dict[str, Any]:
        """
        Parse a recipe from a URL and save it as pending.
        
        Args:
            url: URL of the recipe to parse
            
        Returns:
            Dictionary with status and the parsed pending recipe
        """
        try:
            logger.info(f"Parsing recipe from URL: {url}")
            
            # Check for existing pending recipe with same URL
            existing = self.repository.check_duplicate(name="", source_url=url)
            if existing:
                return {
                    'status': 'duplicate',
                    'message': 'A recipe from this URL is already pending review',
                    'pending_recipe': self._pending_to_dict(existing)
                }
            
            # Use the web scraping tool to extract recipe data
            scraped_results = self.scraping_tool._run(url)
            
            if not scraped_results:
                return {
                    'status': 'error',
                    'message': 'No recipe data could be extracted from the URL'
                }
            
            # Get the first result (URL typically has one recipe)
            scraped_data = scraped_results[0] if isinstance(scraped_results, list) else scraped_results
            
            # Check for errors in scraped data
            if 'error' in scraped_data:
                return {
                    'status': 'error',
                    'message': scraped_data.get('error', 'Failed to parse recipe')
                }
            
            # Convert scraped data to PendingRecipeCreate
            pending_create = self._scraped_to_pending_create(scraped_data, source_url=url)
            
            # Save as pending recipe
            pending = self.repository.create_pending(pending_create)
            
            logger.info(f"Created pending recipe {pending.id} from URL: {url}")
            
            return {
                'status': 'success',
                'message': f'Recipe "{pending.name}" parsed successfully',
                'pending_recipe': self._pending_to_dict(pending)
            }
            
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to parse recipe: {str(e)}'
            }
    
    def discover_recipes(
        self,
        query: str,
        cuisine: Optional[str] = None,
        dietary_restrictions: Optional[List[str]] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Discover recipes using AI search and save them as pending.
        
        Args:
            query: Natural language search query
            cuisine: Optional cuisine filter
            dietary_restrictions: Optional dietary restrictions
            max_results: Maximum number of recipes to discover
            
        Returns:
            Dictionary with status and list of pending recipes
        """
        try:
            logger.info(f"Discovering recipes with query: {query}")
            
            # Build enhanced search query
            search_query = query
            if cuisine:
                search_query = f"{cuisine} {search_query}"
            if dietary_restrictions:
                search_query = f"{' '.join(dietary_restrictions)} {search_query}"
            
            # Use the web search tool
            search_results = self.search_tool._run(search_query, max_results=max_results)
            
            if not search_results:
                return {
                    'status': 'error',
                    'message': 'No recipes found for the given query'
                }
            
            # Check for errors
            if isinstance(search_results, list) and len(search_results) == 1:
                if 'error' in search_results[0]:
                    return {
                        'status': 'error',
                        'message': search_results[0].get('error', 'Search failed')
                    }
            
            # Convert each result to pending recipe
            pending_recipes = []
            for result in search_results:
                if isinstance(result, dict) and 'name' in result:
                    # Check for duplicates
                    existing = self.repository.check_duplicate(
                        name=result.get('name', ''),
                        source_url=result.get('url')
                    )
                    
                    if existing:
                        pending_recipes.append({
                            **self._pending_to_dict(existing),
                            'is_duplicate': True
                        })
                        continue
                    
                    # Create pending recipe
                    pending_create = self._scraped_to_pending_create(
                        result,
                        discovery_query=query
                    )
                    
                    try:
                        pending = self.repository.create_pending(pending_create)
                        pending_recipes.append(self._pending_to_dict(pending))
                    except Exception as e:
                        logger.warning(f"Failed to save pending recipe: {e}")
                        continue
            
            logger.info(f"Discovered {len(pending_recipes)} recipes for query: {query}")
            
            return {
                'status': 'success',
                'message': f'Found {len(pending_recipes)} recipes',
                'pending_recipes': pending_recipes,
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error discovering recipes: {e}")
            return {
                'status': 'error',
                'message': f'Recipe discovery failed: {str(e)}'
            }
    
    def list_pending(self, limit: int = 50) -> Dict[str, Any]:
        """
        List all pending recipes awaiting review.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            Dictionary with pending recipes
        """
        try:
            pending_recipes = self.repository.get_all_pending(limit=limit)
            
            return {
                'status': 'success',
                'pending_recipes': [self._pending_to_dict(p) for p in pending_recipes],
                'total': len(pending_recipes)
            }
            
        except Exception as e:
            logger.error(f"Error listing pending recipes: {e}")
            return {
                'status': 'error',
                'message': f'Failed to list pending recipes: {str(e)}'
            }
    
    def get_pending(self, pending_id: int) -> Dict[str, Any]:
        """
        Get a single pending recipe by ID.
        
        Args:
            pending_id: ID of the pending recipe
            
        Returns:
            Dictionary with the pending recipe or error
        """
        try:
            pending = self.repository.get_by_id(pending_id)
            
            if not pending:
                return {
                    'status': 'error',
                    'message': f'Pending recipe with ID {pending_id} not found'
                }
            
            return {
                'status': 'success',
                'pending_recipe': self._pending_to_dict(pending)
            }
            
        except Exception as e:
            logger.error(f"Error getting pending recipe {pending_id}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to get pending recipe: {str(e)}'
            }
    
    def update_pending(self, pending_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a pending recipe before approval.
        
        Args:
            pending_id: ID of the pending recipe
            update_data: Fields to update
            
        Returns:
            Dictionary with the updated pending recipe or error
        """
        try:
            # Convert update_data to PendingRecipeUpdate
            pending_update = PendingRecipeUpdate(**update_data)
            
            pending = self.repository.update_pending(pending_id, pending_update)
            
            if not pending:
                return {
                    'status': 'error',
                    'message': f'Pending recipe with ID {pending_id} not found'
                }
            
            return {
                'status': 'success',
                'message': 'Pending recipe updated',
                'pending_recipe': self._pending_to_dict(pending)
            }
            
        except Exception as e:
            logger.error(f"Error updating pending recipe {pending_id}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to update pending recipe: {str(e)}'
            }
    
    def approve(self, pending_id: int) -> Dict[str, Any]:
        """
        Approve a pending recipe and add it to the main recipe collection.
        
        Args:
            pending_id: ID of the pending recipe to approve
            
        Returns:
            Dictionary with status and the new recipe ID
        """
        try:
            result = self.repository.approve(pending_id)
            return result
            
        except RecordNotFoundError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            logger.error(f"Error approving pending recipe {pending_id}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to approve recipe: {str(e)}'
            }
    
    def reject(self, pending_id: int) -> Dict[str, Any]:
        """
        Reject and delete a pending recipe.
        
        Args:
            pending_id: ID of the pending recipe to reject
            
        Returns:
            Dictionary with status message
        """
        try:
            result = self.repository.reject(pending_id)
            return result
            
        except RecordNotFoundError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            logger.error(f"Error rejecting pending recipe {pending_id}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to reject recipe: {str(e)}'
            }
    
    def _scraped_to_pending_create(
        self,
        scraped_data: Dict[str, Any],
        source_url: Optional[str] = None,
        discovery_query: Optional[str] = None
    ) -> PendingRecipeCreate:
        """
        Convert scraped recipe data to PendingRecipeCreate model.
        
        Args:
            scraped_data: Raw scraped recipe data
            source_url: Original URL if from URL parsing
            discovery_query: Search query if from AI discovery
            
        Returns:
            PendingRecipeCreate instance
        """
        # Extract ingredients
        raw_ingredients = scraped_data.get('ingredients', [])
        ingredients = []
        for ing in raw_ingredients:
            if isinstance(ing, str):
                ingredients.append(PendingRecipeIngredient(name=ing))
            elif isinstance(ing, dict):
                ingredients.append(PendingRecipeIngredient(
                    name=ing.get('name', ing.get('ingredient', str(ing))),
                    quantity=ing.get('quantity'),
                    unit=ing.get('unit'),
                    notes=ing.get('notes')
                ))
        
        # Extract instructions
        raw_instructions = scraped_data.get('instructions', [])
        if isinstance(raw_instructions, str):
            instructions = [step.strip() for step in raw_instructions.split('\n') if step.strip()]
        else:
            instructions = [str(step) for step in raw_instructions if step]
        
        # Extract dietary tags
        raw_tags = scraped_data.get('tags', scraped_data.get('dietary_tags', []))
        dietary_tags = [str(tag) for tag in raw_tags] if raw_tags else []
        
        # Extract nutritional info
        nutrition = scraped_data.get('nutrition', scraped_data.get('nutritional_info'))
        
        return PendingRecipeCreate(
            name=scraped_data.get('name', 'Untitled Recipe'),
            description=scraped_data.get('description'),
            prep_time=scraped_data.get('prep_time'),
            cook_time=scraped_data.get('cook_time'),
            servings=scraped_data.get('servings'),
            difficulty=scraped_data.get('difficulty'),
            cuisine=scraped_data.get('cuisine'),
            dietary_tags=dietary_tags,
            ingredients=ingredients,
            instructions=instructions,
            notes=scraped_data.get('tips', scraped_data.get('notes')),
            image_url=scraped_data.get('image_url', scraped_data.get('image')),
            nutritional_info=nutrition,
            source_url=source_url or scraped_data.get('url', scraped_data.get('source')),
            discovery_query=discovery_query
        )
    
    def _pending_to_dict(self, pending: PendingRecipe) -> Dict[str, Any]:
        """
        Convert PendingRecipe to dictionary for API response.
        
        Args:
            pending: PendingRecipe instance
            
        Returns:
            Dictionary representation
        """
        return {
            'id': pending.id,
            'name': pending.name,
            'description': pending.description,
            'prep_time': pending.prep_time,
            'cook_time': pending.cook_time,
            'servings': pending.servings,
            'difficulty': pending.difficulty,
            'cuisine': pending.cuisine,
            'dietary_tags': pending.dietary_tags,
            'ingredients': [
                {
                    'name': ing.name,
                    'quantity': ing.quantity,
                    'unit': ing.unit,
                    'notes': ing.notes
                }
                for ing in pending.ingredients
            ],
            'instructions': pending.instructions,
            'notes': pending.notes,
            'image_url': pending.image_url,
            'nutritional_info': pending.nutritional_info,
            'source_url': pending.source_url,
            'discovery_query': pending.discovery_query,
            'status': pending.status.value if pending.status else 'pending',
            'created_at': pending.created_at.isoformat() if pending.created_at else None
        }

