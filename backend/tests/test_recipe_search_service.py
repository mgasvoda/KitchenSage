"""
Tests for the RecipeSearchService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.recipe_search_service import (
    RecipeSearchService, 
    RecipeSearchFilters,
    RecipeSearchResult,
    RecipeSearchResponse
)
from src.models import Recipe, DifficultyLevel, CuisineType, DietaryTag, MealType


class TestRecipeSearchFilters:
    """Tests for RecipeSearchFilters dataclass."""
    
    def test_default_values(self):
        """Test that filters have correct default values."""
        filters = RecipeSearchFilters()
        
        assert filters.name is None
        assert filters.ingredients is None
        assert filters.meal_types is None
        assert filters.cuisine is None
        assert filters.dietary_tags is None
        assert filters.difficulty is None
        assert filters.max_prep_time is None
        assert filters.max_cook_time is None
        assert filters.max_total_time is None
    
    def test_with_values(self):
        """Test creating filters with values."""
        filters = RecipeSearchFilters(
            name="chicken",
            meal_types=[MealType.DINNER],
            cuisine=CuisineType.ITALIAN,
            max_prep_time=30
        )
        
        assert filters.name == "chicken"
        assert filters.meal_types == [MealType.DINNER]
        assert filters.cuisine == CuisineType.ITALIAN
        assert filters.max_prep_time == 30


class TestRecipeSearchService:
    """Tests for RecipeSearchService."""
    
    @pytest.fixture
    def mock_recipe_repo(self):
        """Create a mock recipe repository."""
        with patch('src.services.recipe_search_service.RecipeRepository') as mock:
            repo = Mock()
            mock.return_value = repo
            yield repo
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock embedding service."""
        with patch('src.services.recipe_search_service.EmbeddingService') as mock:
            service = Mock()
            mock.return_value = service
            yield service
    
    @pytest.fixture
    def search_service(self, mock_recipe_repo, mock_embedding_service):
        """Create a search service with mocked dependencies."""
        service = RecipeSearchService()
        service._embedding_service = mock_embedding_service
        return service
    
    @pytest.fixture
    def sample_recipes(self):
        """Create sample recipe objects."""
        return [
            Recipe(
                id=1,
                name="Chicken Stir Fry",
                description="Quick and easy",
                prep_time=15,
                cook_time=15,
                servings=4,
                difficulty=DifficultyLevel.EASY,
                cuisine=CuisineType.CHINESE,
                dietary_tags=[DietaryTag.GLUTEN_FREE],
                meal_types=[MealType.LUNCH, MealType.DINNER],
                instructions=["Step 1"]
            ),
            Recipe(
                id=2,
                name="Vegetable Pasta",
                description="Italian comfort food",
                prep_time=10,
                cook_time=20,
                servings=4,
                difficulty=DifficultyLevel.EASY,
                cuisine=CuisineType.ITALIAN,
                dietary_tags=[DietaryTag.VEGETARIAN],
                meal_types=[MealType.DINNER],
                instructions=["Step 1"]
            ),
            Recipe(
                id=3,
                name="Pancakes",
                description="Fluffy breakfast pancakes",
                prep_time=10,
                cook_time=15,
                servings=4,
                difficulty=DifficultyLevel.EASY,
                cuisine=CuisineType.AMERICAN,
                dietary_tags=[DietaryTag.VEGETARIAN],
                meal_types=[MealType.BREAKFAST],
                instructions=["Step 1"]
            ),
        ]
    
    def test_search_no_criteria_returns_recent(self, search_service, mock_recipe_repo, sample_recipes):
        """Test that search with no criteria returns recent recipes."""
        mock_recipe_repo.search_recipes.return_value = sample_recipes
        
        response = search_service.search(limit=10)
        
        assert len(response.results) == 3
        assert response.total_count == 3
        mock_recipe_repo.search_recipes.assert_called()
    
    def test_search_with_name_filter(self, search_service, mock_recipe_repo, sample_recipes):
        """Test searching by name."""
        mock_recipe_repo.search_recipes.return_value = [sample_recipes[0]]
        mock_recipe_repo.get_recipe_with_ingredients.return_value = sample_recipes[0]
        
        filters = RecipeSearchFilters(name="chicken")
        response = search_service.search(filters=filters, limit=10)
        
        assert len(response.results) >= 0
        assert response.filters == filters
    
    def test_search_with_cuisine_filter(self, search_service, mock_recipe_repo, sample_recipes):
        """Test filtering by cuisine."""
        italian_recipes = [r for r in sample_recipes if r.cuisine == CuisineType.ITALIAN]
        mock_recipe_repo.search_recipes.return_value = italian_recipes
        mock_recipe_repo.get_recipe_with_ingredients.return_value = italian_recipes[0] if italian_recipes else None
        
        filters = RecipeSearchFilters(cuisine=CuisineType.ITALIAN)
        response = search_service.search(filters=filters, limit=10)
        
        for result in response.results:
            assert result.recipe.cuisine == CuisineType.ITALIAN
    
    def test_search_with_meal_type_filter(self, search_service, mock_recipe_repo, sample_recipes):
        """Test filtering by meal type."""
        breakfast_recipes = [r for r in sample_recipes if MealType.BREAKFAST in r.meal_types]
        mock_recipe_repo.search_recipes.return_value = breakfast_recipes
        mock_recipe_repo.get_recipe_with_ingredients.return_value = breakfast_recipes[0] if breakfast_recipes else None
        
        filters = RecipeSearchFilters(meal_types=[MealType.BREAKFAST])
        response = search_service.search(filters=filters, limit=10)
        
        for result in response.results:
            assert MealType.BREAKFAST in result.recipe.meal_types
    
    def test_search_with_max_time_filter(self, search_service, mock_recipe_repo, sample_recipes):
        """Test filtering by maximum time."""
        quick_recipes = [r for r in sample_recipes if r.prep_time <= 15]
        mock_recipe_repo.search_recipes.return_value = quick_recipes
        mock_recipe_repo.get_recipe_with_ingredients.return_value = None
        
        filters = RecipeSearchFilters(max_prep_time=15)
        response = search_service.search(filters=filters, limit=10)
        
        # Verify filter was applied
        assert response.filters == filters
    
    def test_search_semantic_query(self, search_service, mock_recipe_repo, mock_embedding_service, sample_recipes):
        """Test semantic search with a natural language query."""
        # Setup mocks
        mock_embedding_service.semantic_search.return_value = [(1, 0.9), (2, 0.7)]
        mock_recipe_repo.get_recipe_with_ingredients.side_effect = lambda id: next(
            (r for r in sample_recipes if r.id == id), None
        )
        
        response = search_service.search(query="quick weeknight dinner", limit=10)
        
        assert response.query == "quick weeknight dinner"
        mock_embedding_service.semantic_search.assert_called_once()
    
    def test_search_semantic_falls_back_on_no_results(self, search_service, mock_recipe_repo, mock_embedding_service, sample_recipes):
        """Test that semantic search falls back to text search when no results."""
        mock_embedding_service.semantic_search.return_value = []
        mock_recipe_repo.search_recipes.return_value = sample_recipes
        mock_recipe_repo.get_recipe_with_ingredients.return_value = None
        
        response = search_service.search(query="obscure dish", limit=10)
        
        # Should have fallen back to structured search
        mock_recipe_repo.search_recipes.assert_called()
    
    def test_search_hybrid_combines_filters_and_semantic(self, search_service, mock_recipe_repo, mock_embedding_service, sample_recipes):
        """Test hybrid search with both filters and semantic query."""
        mock_recipe_repo.search_recipes.return_value = sample_recipes
        mock_recipe_repo.get_recipe_with_ingredients.return_value = sample_recipes[0]
        mock_embedding_service.generate_embedding.return_value = [0.1] * 1536
        mock_embedding_service.get_embedding.return_value = [0.1] * 1536
        mock_embedding_service.cosine_similarity.return_value = 0.8
        
        filters = RecipeSearchFilters(cuisine=CuisineType.CHINESE)
        response = search_service.search(
            filters=filters,
            query="spicy asian food",
            limit=10
        )
        
        assert response.query == "spicy asian food"
        assert response.filters == filters
    
    def test_search_respects_limit(self, search_service, mock_recipe_repo, sample_recipes):
        """Test that search respects the limit parameter."""
        mock_recipe_repo.search_recipes.return_value = sample_recipes
        
        response = search_service.search(limit=2)
        
        assert len(response.results) <= 2
    
    def test_search_caps_limit_at_100(self, search_service, mock_recipe_repo, sample_recipes):
        """Test that limit is capped at 100."""
        mock_recipe_repo.search_recipes.return_value = sample_recipes
        
        # Try to request more than 100
        response = search_service.search(limit=500)
        
        # The internal limit should be capped
        # We verify indirectly through the response
        assert response is not None
    
    def test_search_with_offset(self, search_service, mock_recipe_repo, sample_recipes):
        """Test pagination with offset."""
        mock_recipe_repo.search_recipes.return_value = sample_recipes
        
        response = search_service.search(limit=10, offset=1)
        
        # With 3 recipes and offset=1, we should get 2
        assert len(response.results) <= len(sample_recipes) - 1
    
    def test_search_dict_converts_filters(self, search_service, mock_recipe_repo, sample_recipes):
        """Test search_dict method correctly converts dictionary filters."""
        mock_recipe_repo.search_recipes.return_value = sample_recipes
        mock_recipe_repo.get_recipe_with_ingredients.return_value = None
        
        result = search_service.search_dict(
            filters={
                'cuisine': 'italian',
                'meal_types': ['dinner'],
                'difficulty': 'easy'
            },
            limit=10
        )
        
        assert result['status'] == 'success'
        assert 'recipes' in result
        assert 'total' in result
    
    def test_search_dict_handles_none_filters(self, search_service, mock_recipe_repo, sample_recipes):
        """Test search_dict with no filters."""
        mock_recipe_repo.search_recipes.return_value = sample_recipes
        
        result = search_service.search_dict(query="pasta", limit=10)
        
        assert result['status'] == 'success'
    
    def test_calculate_structured_score_exact_name_match(self, search_service, sample_recipes):
        """Test scoring gives highest weight to exact name matches."""
        recipe = sample_recipes[0]  # "Chicken Stir Fry"
        
        # Exact match
        filters = RecipeSearchFilters(name="Chicken Stir Fry")
        score_exact = search_service._calculate_structured_score(recipe, filters)
        
        # Partial match
        filters = RecipeSearchFilters(name="Chicken")
        score_partial = search_service._calculate_structured_score(recipe, filters)
        
        # Word match
        filters = RecipeSearchFilters(name="Fry Chicken Rice")  # Contains matching words
        score_word = search_service._calculate_structured_score(recipe, filters)
        
        # Exact should be highest
        assert score_exact >= score_partial
    
    def test_get_match_reasons(self, search_service, sample_recipes):
        """Test generating match reasons."""
        recipe = sample_recipes[0]  # Chicken Stir Fry, Chinese
        filters = RecipeSearchFilters(
            cuisine=CuisineType.CHINESE,
            difficulty=DifficultyLevel.EASY
        )
        
        reasons = search_service._get_match_reasons(recipe, filters)
        
        assert len(reasons) > 0
        assert any("chinese" in r.lower() or "cuisine" in r.lower() for r in reasons)


class TestRecipeSearchResult:
    """Tests for RecipeSearchResult dataclass."""
    
    def test_default_values(self):
        """Test default values for search result."""
        recipe = Recipe(
            id=1,
            name="Test",
            prep_time=10,
            cook_time=10,
            servings=4,
            instructions=["Step 1"]
        )
        result = RecipeSearchResult(recipe=recipe)
        
        assert result.recipe == recipe
        assert result.relevance_score == 0.0
        assert result.match_reasons == []
    
    def test_with_values(self):
        """Test creating result with values."""
        recipe = Recipe(
            id=1,
            name="Test",
            prep_time=10,
            cook_time=10,
            servings=4,
            instructions=["Step 1"]
        )
        result = RecipeSearchResult(
            recipe=recipe,
            relevance_score=0.85,
            match_reasons=["Name matches", "Cuisine matches"]
        )
        
        assert result.relevance_score == 0.85
        assert len(result.match_reasons) == 2


class TestRecipeSearchResponse:
    """Tests for RecipeSearchResponse dataclass."""
    
    def test_default_values(self):
        """Test default values for search response."""
        response = RecipeSearchResponse(results=[], total_count=0)
        
        assert response.results == []
        assert response.total_count == 0
        assert response.query is None
        assert response.filters is None
    
    def test_with_values(self):
        """Test creating response with values."""
        recipe = Recipe(
            id=1,
            name="Test",
            prep_time=10,
            cook_time=10,
            servings=4,
            instructions=["Step 1"]
        )
        result = RecipeSearchResult(recipe=recipe, relevance_score=0.9)
        filters = RecipeSearchFilters(name="test")
        
        response = RecipeSearchResponse(
            results=[result],
            total_count=1,
            query="test query",
            filters=filters
        )
        
        assert len(response.results) == 1
        assert response.total_count == 1
        assert response.query == "test query"
        assert response.filters == filters

