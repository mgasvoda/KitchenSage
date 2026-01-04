"""
Tests for KitchenSage API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Set up path before imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


class TestRootEndpoints:
    """Tests for root API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "KitchenSage API"
        assert "version" in data
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRecipeEndpoints:
    """Tests for recipe API endpoints."""
    
    @patch('src.api.routes.recipes.RecipeSearchService')
    def test_list_recipes_empty(self, mock_service_class, client):
        """Test listing recipes when empty."""
        mock_service = Mock()
        mock_service.search_dict.return_value = {
            "status": "success",
            "recipes": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/recipes")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["recipes"] == []
    
    @patch('src.api.routes.recipes.RecipeSearchService')
    def test_list_recipes_with_filters(self, mock_service_class, client):
        """Test listing recipes with query filters."""
        mock_service = Mock()
        mock_service.search_dict.return_value = {
            "status": "success",
            "recipes": [{"recipe": {"id": 1, "name": "Pasta"}, "relevance_score": 0.9}],
            "total": 1,
            "limit": 20,
            "offset": 0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/recipes?search=pasta&cuisine=italian")
        assert response.status_code == 200
        mock_service.search_dict.assert_called_once()
    
    @patch('src.api.routes.recipes.RecipeService')
    def test_get_recipe_success(self, mock_service_class, client):
        """Test getting a recipe by ID."""
        mock_service = Mock()
        mock_service.get_recipe.return_value = {
            "status": "success",
            "recipe": {"id": 1, "name": "Test Recipe"},
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/recipes/1")
        assert response.status_code == 200
        data = response.json()
        assert data["recipe"]["id"] == 1
    
    @patch('src.api.routes.recipes.RecipeService')
    def test_get_recipe_not_found(self, mock_service_class, client):
        """Test getting a non-existent recipe."""
        mock_service = Mock()
        mock_service.get_recipe.return_value = {
            "status": "error",
            "message": "Recipe not found",
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/recipes/999")
        assert response.status_code == 404
    
    @patch('src.api.routes.recipes.RecipeService')
    def test_create_recipe(self, mock_service_class, client):
        """Test creating a new recipe."""
        mock_service = Mock()
        mock_service.create_recipe.return_value = {
            "status": "success",
            "recipe_id": 1,
            "message": "Recipe created",
        }
        mock_service_class.return_value = mock_service
        
        recipe_data = {
            "name": "Test Recipe",
            "prep_time": 10,
            "cook_time": 20,
            "servings": 4,
            "instructions": ["Step 1", "Step 2"],
        }
        
        response = client.post("/api/recipes", json=recipe_data)
        assert response.status_code == 201
    
    @patch('src.api.routes.recipes.RecipeService')
    def test_delete_recipe(self, mock_service_class, client):
        """Test deleting a recipe."""
        mock_service = Mock()
        mock_service.delete_recipe.return_value = {
            "status": "success",
            "message": "Recipe deleted",
        }
        mock_service_class.return_value = mock_service
        
        response = client.delete("/api/recipes/1")
        assert response.status_code == 200


class TestRecipeSearchEndpoints:
    """Tests for recipe search API endpoints."""
    
    @patch('src.api.routes.recipes.RecipeSearchService')
    def test_search_recipes_basic(self, mock_service_class, client):
        """Test basic recipe search endpoint."""
        mock_service = Mock()
        mock_service.search_dict.return_value = {
            "status": "success",
            "recipes": [
                {
                    "recipe": {"id": 1, "name": "Chicken Pasta"},
                    "relevance_score": 0.95,
                    "match_reasons": ["Name matches"]
                }
            ],
            "total": 1,
            "limit": 20,
            "offset": 0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/recipes/search", json={
            "name": "chicken",
            "limit": 20
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["recipes"]) == 1
    
    @patch('src.api.routes.recipes.RecipeSearchService')
    def test_search_recipes_with_semantic_query(self, mock_service_class, client):
        """Test recipe search with semantic query."""
        mock_service = Mock()
        mock_service.search_dict.return_value = {
            "status": "success",
            "recipes": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
            "query": "quick weeknight dinners"
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/recipes/search", json={
            "query": "quick weeknight dinners",
            "use_semantic": True
        })
        
        assert response.status_code == 200
        mock_service.search_dict.assert_called_once()
    
    @patch('src.api.routes.recipes.RecipeSearchService')
    def test_search_recipes_with_filters(self, mock_service_class, client):
        """Test recipe search with structured filters."""
        mock_service = Mock()
        mock_service.search_dict.return_value = {
            "status": "success",
            "recipes": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/recipes/search", json={
            "meal_types": ["dinner", "lunch"],
            "cuisine": "italian",
            "difficulty": "easy",
            "max_prep_time": 30,
            "limit": 10
        })
        
        assert response.status_code == 200
        
        # Verify the service was called with correct filters
        call_args = mock_service.search_dict.call_args
        filters = call_args.kwargs.get('filters', {})
        assert 'italian' in str(filters)
    
    @patch('src.api.routes.recipes.RecipeSearchService')
    def test_search_recipes_with_dietary_tags(self, mock_service_class, client):
        """Test recipe search with dietary restrictions."""
        mock_service = Mock()
        mock_service.search_dict.return_value = {
            "status": "success",
            "recipes": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/recipes/search", json={
            "dietary_tags": ["vegetarian", "gluten_free"],
        })
        
        assert response.status_code == 200
    
    @patch('src.api.routes.recipes.RecipeSearchService')
    def test_search_recipes_hybrid(self, mock_service_class, client):
        """Test hybrid search with both filters and semantic query."""
        mock_service = Mock()
        mock_service.search_dict.return_value = {
            "status": "success",
            "recipes": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
            "query": "healthy options",
            "filters_applied": {"cuisine": "mediterranean"}
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/recipes/search", json={
            "cuisine": "mediterranean",
            "query": "healthy options",
            "use_semantic": True,
            "limit": 15
        })
        
        assert response.status_code == 200
    
    @patch('src.api.routes.recipes.RecipeSearchService')
    def test_search_recipes_pagination(self, mock_service_class, client):
        """Test recipe search pagination."""
        mock_service = Mock()
        mock_service.search_dict.return_value = {
            "status": "success",
            "recipes": [],
            "total": 50,
            "limit": 10,
            "offset": 20,
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/recipes/search", json={
            "limit": 10,
            "offset": 20
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 20
    
    @patch('src.api.routes.recipes.RecipeSearchService')
    def test_list_recipes_uses_search_service(self, mock_service_class, client):
        """Test that GET /recipes also uses the search service."""
        mock_service = Mock()
        mock_service.search_dict.return_value = {
            "status": "success",
            "recipes": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/recipes?search=pasta&meal_types=dinner")
        
        assert response.status_code == 200
        mock_service.search_dict.assert_called_once()


class TestRecipeEmbeddingEndpoints:
    """Tests for recipe embedding API endpoints."""
    
    @patch('src.api.routes.recipes.EmbeddingService')
    @patch('src.api.routes.recipes.RecipeService')
    def test_embed_recipe_success(self, mock_recipe_service, mock_embedding_service, client):
        """Test embedding a single recipe."""
        mock_recipe = Mock()
        mock_recipe.get_recipe.return_value = {
            "status": "success",
            "recipe": {"id": 1, "name": "Test Recipe"}
        }
        mock_recipe_service.return_value = mock_recipe
        
        mock_embedding = Mock()
        mock_embedding.embed_recipe.return_value = [0.1] * 1536
        mock_embedding_service.return_value = mock_embedding
        
        response = client.post("/api/recipes/1/embed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["recipe_id"] == 1
    
    @patch('src.api.routes.recipes.RecipeService')
    def test_embed_recipe_not_found(self, mock_recipe_service, client):
        """Test embedding a non-existent recipe."""
        mock_recipe = Mock()
        mock_recipe.get_recipe.return_value = {
            "status": "error",
            "message": "Recipe not found"
        }
        mock_recipe_service.return_value = mock_recipe
        
        response = client.post("/api/recipes/999/embed")
        
        assert response.status_code == 404
    
    @patch('src.database.RecipeRepository')
    @patch('src.api.routes.recipes.EmbeddingService')
    def test_embed_all_recipes(self, mock_embedding_service, mock_recipe_repo, client):
        """Test embedding all recipes."""
        mock_repo = Mock()
        mock_repo.search_recipes.return_value = [
            Mock(id=1, model_dump=Mock(return_value={"id": 1, "name": "Recipe 1"})),
            Mock(id=2, model_dump=Mock(return_value={"id": 2, "name": "Recipe 2"})),
        ]
        mock_repo.get_recipe_with_ingredients.return_value = None
        mock_recipe_repo.return_value = mock_repo
        
        mock_embedding = Mock()
        mock_embedding.embed_recipes_batch.return_value = 2
        mock_embedding_service.return_value = mock_embedding
        
        response = client.post("/api/recipes/embed-all")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["embedded_count"] == 2


class TestMealPlanEndpoints:
    """Tests for meal plan API endpoints."""
    
    @patch('src.api.routes.meal_plans.MealPlanService')
    def test_list_meal_plans(self, mock_service_class, client):
        """Test listing meal plans."""
        mock_service = Mock()
        mock_service.list_meal_plans.return_value = {
            "status": "success",
            "meal_plans": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/meal-plans")
        assert response.status_code == 200
    
    @patch('src.api.routes.meal_plans.MealPlanService')
    def test_get_meal_plan_not_found(self, mock_service_class, client):
        """Test getting a non-existent meal plan."""
        mock_service = Mock()
        mock_service.get_meal_plan.return_value = {
            "status": "error",
            "message": "Meal plan not found",
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/meal-plans/999")
        assert response.status_code == 404


class TestGroceryListEndpoints:
    """Tests for grocery list API endpoints."""
    
    @patch('src.api.routes.grocery_lists.GroceryService')
    def test_list_grocery_lists(self, mock_service_class, client):
        """Test listing grocery lists."""
        mock_service = Mock()
        mock_service.list_grocery_lists.return_value = {
            "status": "success",
            "grocery_lists": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/grocery-lists")
        assert response.status_code == 200
    
    @patch('src.api.routes.grocery_lists.GroceryService')
    def test_get_grocery_list_not_found(self, mock_service_class, client):
        """Test getting a non-existent grocery list."""
        mock_service = Mock()
        mock_service.get_grocery_list.return_value = {
            "status": "error",
            "message": "Grocery list not found",
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/grocery-lists/999")
        assert response.status_code == 404


class TestChatEndpoints:
    """Tests for chat API endpoints."""
    
    @patch('src.api.routes.chat.ChatService')
    def test_chat_sync(self, mock_service_class, client):
        """Test synchronous chat endpoint."""
        mock_service = Mock()
        mock_service.process_message = AsyncMock(return_value={
            "status": "success",
            "response": "Hello! How can I help you?",
            "intent": "greeting",
        })
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/chat/sync", json={
            "message": "Hello",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_chat_streaming_requires_message(self, client):
        """Test that chat endpoint requires a message."""
        response = client.post("/api/chat", json={})
        assert response.status_code == 422  # Validation error

