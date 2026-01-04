"""
Unified recipe search service combining structured filters with semantic search.

This service provides a single interface for searching recipes that can be used
by both the frontend API and CrewAI agent tools, ensuring consistent behavior.
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from src.database import RecipeRepository
from src.models import Recipe, DifficultyLevel, CuisineType, DietaryTag, MealType
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class RecipeSearchFilters:
    """
    Structured search filters for recipe queries.
    
    Attributes:
        name: Search in recipe name
        ingredients: List of ingredient names to search for
        meal_types: Filter by meal types (breakfast, lunch, dinner, etc.)
        cuisine: Filter by cuisine type
        dietary_tags: Filter by dietary restrictions
        difficulty: Filter by difficulty level
        max_prep_time: Maximum prep time in minutes
        max_cook_time: Maximum cook time in minutes
        max_total_time: Maximum total time in minutes
    """
    name: Optional[str] = None
    ingredients: Optional[List[str]] = None
    meal_types: Optional[List[MealType]] = None
    cuisine: Optional[CuisineType] = None
    dietary_tags: Optional[List[DietaryTag]] = None
    difficulty: Optional[DifficultyLevel] = None
    max_prep_time: Optional[int] = None
    max_cook_time: Optional[int] = None
    max_total_time: Optional[int] = None


@dataclass 
class RecipeSearchResult:
    """
    Result from a recipe search query.
    
    Attributes:
        recipe: The recipe object
        relevance_score: Combined relevance score (0-1)
        match_reasons: List of reasons why this recipe matched
    """
    recipe: Recipe
    relevance_score: float = 0.0
    match_reasons: List[str] = field(default_factory=list)


@dataclass
class RecipeSearchResponse:
    """
    Response from a recipe search query.
    
    Attributes:
        results: List of search results
        total_count: Total number of matching recipes
        query: The original query (if semantic search was used)
        filters: The filters that were applied
    """
    results: List[RecipeSearchResult]
    total_count: int
    query: Optional[str] = None
    filters: Optional[RecipeSearchFilters] = None


class RecipeSearchService:
    """
    Unified recipe search service.
    
    Provides a single search method that supports:
    - Structured field filters (name, cuisine, difficulty, etc.)
    - Ingredient-based search
    - Semantic/natural language search
    - Hybrid search combining structured and semantic
    
    This service ensures equivalent search functionality between
    the human-facing UI and agent-facing tools.
    """
    
    def __init__(self):
        """Initialize the search service."""
        self.recipe_repo = RecipeRepository()
        self._embedding_service: Optional[EmbeddingService] = None
    
    @property
    def embedding_service(self) -> EmbeddingService:
        """Lazy-load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    def search(
        self,
        filters: Optional[RecipeSearchFilters] = None,
        query: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        use_semantic: bool = True
    ) -> RecipeSearchResponse:
        """
        Search for recipes using filters and/or semantic query.
        
        This is the main entry point for recipe search. It supports:
        - Structured filters only
        - Semantic query only  
        - Hybrid (both filters and semantic query)
        
        Args:
            filters: Structured search filters
            query: Natural language search query for semantic search
            limit: Maximum number of results (capped at 100)
            offset: Offset for pagination
            use_semantic: Whether to use semantic search when query is provided
            
        Returns:
            RecipeSearchResponse with matching recipes
        """
        # Cap limit at 100 for performance
        limit = min(limit, 100)
        
        # If no filters or query, return recent recipes
        if not filters and not query:
            return self._get_recent_recipes(limit, offset)
        
        # If only semantic query provided
        if query and not filters:
            if use_semantic:
                return self._semantic_search(query, limit, offset)
            else:
                # Treat query as a name search
                filters = RecipeSearchFilters(name=query)
        
        # If only filters provided
        if filters and not query:
            return self._structured_search(filters, limit, offset)
        
        # Hybrid search: combine structured and semantic
        return self._hybrid_search(filters, query, limit, offset, use_semantic)
    
    def _get_recent_recipes(self, limit: int, offset: int) -> RecipeSearchResponse:
        """Get recent recipes when no search criteria provided."""
        try:
            recipes = self.recipe_repo.search_recipes(limit=limit + offset)
            
            # Apply offset
            paginated = recipes[offset:offset + limit]
            
            results = [
                RecipeSearchResult(recipe=r, relevance_score=1.0, match_reasons=["Recent recipe"])
                for r in paginated
            ]
            
            return RecipeSearchResponse(
                results=results,
                total_count=len(recipes),
                query=None,
                filters=None
            )
            
        except Exception as e:
            logger.error(f"Error getting recent recipes: {e}")
            return RecipeSearchResponse(results=[], total_count=0)
    
    def _structured_search(
        self, 
        filters: RecipeSearchFilters, 
        limit: int, 
        offset: int
    ) -> RecipeSearchResponse:
        """
        Perform structured search using database filters.
        
        Args:
            filters: The search filters
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Search response
        """
        try:
            # Get recipes matching structured filters
            recipes = self.recipe_repo.search_recipes(
                search_term=filters.name,
                cuisine=filters.cuisine,
                dietary_tags=filters.dietary_tags,
                meal_types=filters.meal_types,
                max_prep_time=filters.max_prep_time,
                max_cook_time=filters.max_cook_time,
                difficulty=filters.difficulty,
                limit=limit + offset + 100  # Get extra for ingredient filtering
            )
            
            # Apply ingredient filter if specified
            if filters.ingredients:
                recipes = self._filter_by_ingredients(recipes, filters.ingredients)
            
            # Apply total time filter if specified
            if filters.max_total_time is not None:
                recipes = [
                    r for r in recipes 
                    if (r.prep_time or 0) + (r.cook_time or 0) <= filters.max_total_time
                ]
            
            # Build match reasons
            results = []
            for recipe in recipes:
                reasons = self._get_match_reasons(recipe, filters)
                results.append(RecipeSearchResult(
                    recipe=recipe,
                    relevance_score=self._calculate_structured_score(recipe, filters),
                    match_reasons=reasons
                ))
            
            # Sort by relevance score
            results.sort(key=lambda r: r.relevance_score, reverse=True)
            
            # Apply pagination
            total_count = len(results)
            paginated = results[offset:offset + limit]
            
            return RecipeSearchResponse(
                results=paginated,
                total_count=total_count,
                query=None,
                filters=filters
            )
            
        except Exception as e:
            logger.error(f"Error in structured search: {e}")
            return RecipeSearchResponse(results=[], total_count=0, filters=filters)
    
    def _semantic_search(
        self, 
        query: str, 
        limit: int, 
        offset: int
    ) -> RecipeSearchResponse:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: Natural language query
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Search response
        """
        try:
            # Get semantic matches
            semantic_results = self.embedding_service.semantic_search(
                query=query,
                limit=limit + offset,
                min_similarity=0.25
            )
            
            if not semantic_results:
                # Fall back to text search if no semantic results
                filters = RecipeSearchFilters(name=query)
                return self._structured_search(filters, limit, offset)
            
            # Load full recipe objects
            results = []
            for recipe_id, similarity in semantic_results:
                try:
                    recipe = self.recipe_repo.get_recipe_with_ingredients(recipe_id)
                    if recipe:
                        results.append(RecipeSearchResult(
                            recipe=recipe,
                            relevance_score=similarity,
                            match_reasons=[f"Semantic match ({similarity:.0%} similar)"]
                        ))
                except Exception as e:
                    logger.warning(f"Error loading recipe {recipe_id}: {e}")
                    continue
            
            # Apply pagination
            total_count = len(results)
            paginated = results[offset:offset + limit]
            
            return RecipeSearchResponse(
                results=paginated,
                total_count=total_count,
                query=query,
                filters=None
            )
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            # Fall back to text search
            filters = RecipeSearchFilters(name=query)
            return self._structured_search(filters, limit, offset)
    
    def _hybrid_search(
        self,
        filters: RecipeSearchFilters,
        query: str,
        limit: int,
        offset: int,
        use_semantic: bool
    ) -> RecipeSearchResponse:
        """
        Combine structured filters with semantic search.
        
        First applies structured filters, then re-ranks by semantic similarity.
        
        Args:
            filters: Structured filters
            query: Semantic query
            limit: Maximum results
            offset: Pagination offset
            use_semantic: Whether to use semantic search
            
        Returns:
            Search response
        """
        try:
            # Get structured results (without pagination to allow re-ranking)
            structured_response = self._structured_search(
                filters, 
                limit=100,  # Get more for re-ranking
                offset=0
            )
            
            if not structured_response.results:
                return RecipeSearchResponse(
                    results=[],
                    total_count=0,
                    query=query,
                    filters=filters
                )
            
            # If semantic search is disabled, just return structured results
            if not use_semantic:
                paginated = structured_response.results[offset:offset + limit]
                return RecipeSearchResponse(
                    results=paginated,
                    total_count=structured_response.total_count,
                    query=query,
                    filters=filters
                )
            
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Re-rank by combining structured and semantic scores
            for result in structured_response.results:
                recipe_embedding = self.embedding_service.get_embedding(result.recipe.id)
                
                if recipe_embedding:
                    semantic_score = self.embedding_service.cosine_similarity(
                        query_embedding, recipe_embedding
                    )
                    # Combine scores: 40% structured, 60% semantic
                    result.relevance_score = (
                        0.4 * result.relevance_score + 
                        0.6 * semantic_score
                    )
                    result.match_reasons.append(f"Query relevance: {semantic_score:.0%}")
            
            # Re-sort by combined score
            structured_response.results.sort(key=lambda r: r.relevance_score, reverse=True)
            
            # Apply pagination
            paginated = structured_response.results[offset:offset + limit]
            
            return RecipeSearchResponse(
                results=paginated,
                total_count=structured_response.total_count,
                query=query,
                filters=filters
            )
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fall back to structured search
            return self._structured_search(filters, limit, offset)
    
    def _filter_by_ingredients(
        self, 
        recipes: List[Recipe], 
        ingredients: List[str]
    ) -> List[Recipe]:
        """
        Filter recipes that contain the specified ingredients.
        
        Args:
            recipes: List of recipes to filter
            ingredients: List of ingredient names to match
            
        Returns:
            Filtered list of recipes
        """
        filtered = []
        search_ingredients = {ing.lower().strip() for ing in ingredients}
        
        for recipe in recipes:
            # Get full recipe with ingredients
            full_recipe = self.recipe_repo.get_recipe_with_ingredients(recipe.id)
            if not full_recipe:
                continue
            
            # Get recipe ingredient names
            recipe_ingredients = set()
            for ri in full_recipe.ingredients:
                if ri.ingredient:
                    recipe_ingredients.add(ri.ingredient.name.lower())
            
            # Check if any search ingredient matches
            if any(
                any(search_ing in recipe_ing for recipe_ing in recipe_ingredients)
                for search_ing in search_ingredients
            ):
                filtered.append(full_recipe)
        
        return filtered
    
    def _get_match_reasons(
        self, 
        recipe: Recipe, 
        filters: RecipeSearchFilters
    ) -> List[str]:
        """Generate human-readable match reasons."""
        reasons = []
        
        if filters.name and filters.name.lower() in recipe.name.lower():
            reasons.append(f"Name matches '{filters.name}'")
        
        if filters.cuisine and recipe.cuisine == filters.cuisine:
            reasons.append(f"Cuisine: {filters.cuisine.value}")
        
        if filters.difficulty and recipe.difficulty == filters.difficulty:
            reasons.append(f"Difficulty: {filters.difficulty.value}")
        
        if filters.dietary_tags:
            matching_tags = [
                tag.value for tag in filters.dietary_tags 
                if tag in recipe.dietary_tags
            ]
            if matching_tags:
                reasons.append(f"Dietary: {', '.join(matching_tags)}")
        
        if filters.meal_types:
            matching_types = [
                mt.value for mt in filters.meal_types 
                if mt in recipe.meal_types
            ]
            if matching_types:
                reasons.append(f"Meal type: {', '.join(matching_types)}")
        
        if not reasons:
            reasons.append("Matches search criteria")
        
        return reasons
    
    def _calculate_structured_score(
        self, 
        recipe: Recipe, 
        filters: RecipeSearchFilters
    ) -> float:
        """
        Calculate a relevance score based on how well a recipe matches filters.
        
        Returns a score between 0 and 1.
        """
        score = 0.0
        total_weight = 0.0
        
        # Name match (highest weight)
        if filters.name:
            total_weight += 3.0
            name_lower = filters.name.lower()
            recipe_name_lower = recipe.name.lower()
            if name_lower == recipe_name_lower:
                score += 3.0
            elif name_lower in recipe_name_lower:
                score += 2.0
            elif any(word in recipe_name_lower for word in name_lower.split()):
                score += 1.0
        
        # Cuisine match
        if filters.cuisine:
            total_weight += 1.0
            if recipe.cuisine == filters.cuisine:
                score += 1.0
        
        # Difficulty match
        if filters.difficulty:
            total_weight += 1.0
            if recipe.difficulty == filters.difficulty:
                score += 1.0
        
        # Dietary tags (partial matches count)
        if filters.dietary_tags:
            total_weight += 1.0
            matching = sum(1 for tag in filters.dietary_tags if tag in recipe.dietary_tags)
            score += matching / len(filters.dietary_tags)
        
        # Meal types (any match counts)
        if filters.meal_types:
            total_weight += 1.0
            if any(mt in recipe.meal_types for mt in filters.meal_types):
                score += 1.0
        
        # Normalize to 0-1 range
        if total_weight > 0:
            return score / total_weight
        
        # No filters means everything matches equally
        return 1.0
    
    def search_dict(
        self,
        filters: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        use_semantic: bool = True
    ) -> Dict[str, Any]:
        """
        Search for recipes and return results as dictionaries.
        
        This is a convenience method for API endpoints and agent tools.
        
        Args:
            filters: Dictionary of filter values
            query: Natural language search query
            limit: Maximum number of results
            offset: Pagination offset
            use_semantic: Whether to use semantic search
            
        Returns:
            Dictionary with search results
        """
        # Convert filters dict to RecipeSearchFilters
        search_filters = None
        if filters:
            search_filters = RecipeSearchFilters(
                name=filters.get('name'),
                ingredients=filters.get('ingredients'),
                meal_types=[MealType(mt) for mt in filters.get('meal_types', [])] if filters.get('meal_types') else None,
                cuisine=CuisineType(filters['cuisine']) if filters.get('cuisine') else None,
                dietary_tags=[DietaryTag(dt) for dt in filters.get('dietary_tags', [])] if filters.get('dietary_tags') else None,
                difficulty=DifficultyLevel(filters['difficulty']) if filters.get('difficulty') else None,
                max_prep_time=filters.get('max_prep_time'),
                max_cook_time=filters.get('max_cook_time'),
                max_total_time=filters.get('max_total_time')
            )
        
        # Perform search
        response = self.search(
            filters=search_filters,
            query=query,
            limit=limit,
            offset=offset,
            use_semantic=use_semantic
        )
        
        # Convert to dictionary format
        return {
            "status": "success",
            "recipes": [
                {
                    "recipe": result.recipe.model_dump() if hasattr(result.recipe, 'model_dump') else dict(result.recipe),
                    "relevance_score": result.relevance_score,
                    "match_reasons": result.match_reasons
                }
                for result in response.results
            ],
            "total": response.total_count,
            "limit": limit,
            "offset": offset,
            "query": response.query,
            "filters_applied": filters or {}
        }

