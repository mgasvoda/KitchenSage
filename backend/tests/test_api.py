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
    
    @patch('src.api.routes.recipes.RecipeService')
    def test_list_recipes_empty(self, mock_service_class, client):
        """Test listing recipes when empty."""
        mock_service = Mock()
        mock_service.search_recipes.return_value = {
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
    
    @patch('src.api.routes.recipes.RecipeService')
    def test_list_recipes_with_filters(self, mock_service_class, client):
        """Test listing recipes with query filters."""
        mock_service = Mock()
        mock_service.search_recipes.return_value = {
            "status": "success",
            "recipes": [{"id": 1, "name": "Pasta"}],
            "total": 1,
            "limit": 20,
            "offset": 0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/recipes?search=pasta&cuisine=italian")
        assert response.status_code == 200
        mock_service.search_recipes.assert_called_once()
    
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

