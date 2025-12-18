"""
Tests for pending recipes API endpoints.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def sample_pending_recipe():
    """Sample pending recipe data."""
    return {
        'id': 1,
        'name': 'Test Recipe',
        'description': 'A test recipe',
        'prep_time': 10,
        'cook_time': 20,
        'servings': 4,
        'difficulty': 'Easy',
        'cuisine': 'Italian',
        'dietary_tags': ['vegetarian'],
        'ingredients': [
            {'name': 'flour', 'quantity': 2, 'unit': 'cups'}
        ],
        'instructions': ['Step 1', 'Step 2'],
        'status': 'pending',
        'source_url': 'https://example.com/recipe'
    }


class TestParseUrlEndpoint:
    """Tests for POST /pending-recipes/parse endpoint."""
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_parse_url_endpoint(self, mock_service_class, client, sample_pending_recipe):
        """Test successful URL parsing."""
        mock_service = Mock()
        mock_service.parse_url.return_value = {
            'status': 'success',
            'message': 'Recipe parsed successfully',
            'pending_recipe': sample_pending_recipe
        }
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/pending-recipes/parse",
            json={"url": "https://example.com/recipe"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'pending_recipe' in data
        mock_service.parse_url.assert_called_once_with("https://example.com/recipe")
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_parse_url_validation(self, mock_service_class, client):
        """Test URL validation."""
        response = client.post(
            "/api/pending-recipes/parse",
            json={}  # Missing url field
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_parse_url_error(self, mock_service_class, client):
        """Test error handling in URL parsing."""
        mock_service = Mock()
        mock_service.parse_url.return_value = {
            'status': 'error',
            'message': 'Failed to parse URL'
        }
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/pending-recipes/parse",
            json={"url": "https://invalid-url.com"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_parse_url_duplicate(self, mock_service_class, client, sample_pending_recipe):
        """Test duplicate URL detection."""
        mock_service = Mock()
        mock_service.parse_url.return_value = {
            'status': 'duplicate',
            'message': 'A recipe from this URL is already pending review',
            'pending_recipe': sample_pending_recipe
        }
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/pending-recipes/parse",
            json={"url": "https://example.com/recipe"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'duplicate'


class TestDiscoverRecipesEndpoint:
    """Tests for POST /pending-recipes/discover endpoint."""
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_discover_recipes_endpoint(self, mock_service_class, client, sample_pending_recipe):
        """Test successful recipe discovery."""
        mock_service = Mock()
        mock_service.discover_recipes.return_value = {
            'status': 'success',
            'message': 'Found 2 recipes',
            'pending_recipes': [sample_pending_recipe, {**sample_pending_recipe, 'id': 2}],
            'query': 'pasta recipes'
        }
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/pending-recipes/discover",
            json={"query": "pasta recipes", "max_results": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['pending_recipes']) == 2
        mock_service.discover_recipes.assert_called_once()
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_discover_recipes_with_params(self, mock_service_class, client, sample_pending_recipe):
        """Test discovery with query parameters."""
        mock_service = Mock()
        mock_service.discover_recipes.return_value = {
            'status': 'success',
            'pending_recipes': [sample_pending_recipe],
            'query': 'pasta'
        }
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/pending-recipes/discover",
            json={
                "query": "pasta",
                "cuisine": "Italian",
                "dietary_restrictions": ["vegetarian"],
                "max_results": 10
            }
        )
        
        assert response.status_code == 200
        call_args = mock_service.discover_recipes.call_args
        assert call_args[1]['cuisine'] == 'Italian'
        assert call_args[1]['dietary_restrictions'] == ['vegetarian']
        assert call_args[1]['max_results'] == 10
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_discover_recipes_validation(self, mock_service_class, client):
        """Test query validation."""
        # Empty query
        response = client.post(
            "/api/pending-recipes/discover",
            json={"query": ""}
        )
        assert response.status_code == 422
        
        # Missing query
        response = client.post(
            "/api/pending-recipes/discover",
            json={}
        )
        assert response.status_code == 422
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_discover_recipes_error(self, mock_service_class, client):
        """Test error handling in discovery."""
        mock_service = Mock()
        mock_service.discover_recipes.return_value = {
            'status': 'error',
            'message': 'Discovery failed'
        }
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/pending-recipes/discover",
            json={"query": "nonexistent recipe"}
        )
        
        assert response.status_code == 400


class TestListPendingRecipesEndpoint:
    """Tests for GET /pending-recipes endpoint."""
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_list_pending_recipes_endpoint(self, mock_service_class, client, sample_pending_recipe):
        """Test listing pending recipes."""
        mock_service = Mock()
        mock_service.list_pending.return_value = {
            'status': 'success',
            'pending_recipes': [sample_pending_recipe],
            'total': 1
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/pending-recipes")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['pending_recipes']) == 1
        mock_service.list_pending.assert_called_once()
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_list_pending_recipes_with_limit(self, mock_service_class, client):
        """Test listing with limit parameter."""
        mock_service = Mock()
        mock_service.list_pending.return_value = {
            'status': 'success',
            'pending_recipes': [],
            'total': 0
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/pending-recipes?limit=10")
        
        assert response.status_code == 200
        call_args = mock_service.list_pending.call_args
        assert call_args[1]['limit'] == 10


class TestGetPendingRecipeEndpoint:
    """Tests for GET /pending-recipes/{id} endpoint."""
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_get_pending_recipe_endpoint(self, mock_service_class, client, sample_pending_recipe):
        """Test getting a specific pending recipe."""
        mock_service = Mock()
        mock_service.get_pending.return_value = {
            'status': 'success',
            'pending_recipe': sample_pending_recipe
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/pending-recipes/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['pending_recipe']['id'] == 1
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_get_pending_recipe_not_found(self, mock_service_class, client):
        """Test getting a non-existent pending recipe."""
        mock_service = Mock()
        mock_service.get_pending.return_value = {
            'status': 'error',
            'message': 'Pending recipe with ID 999 not found'
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/pending-recipes/999")
        
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data


class TestUpdatePendingRecipeEndpoint:
    """Tests for PUT /pending-recipes/{id} endpoint."""
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_update_pending_recipe_endpoint(self, mock_service_class, client, sample_pending_recipe):
        """Test updating a pending recipe."""
        updated_recipe = {**sample_pending_recipe, 'name': 'Updated Recipe'}
        mock_service = Mock()
        mock_service.update_pending.return_value = {
            'status': 'success',
            'message': 'Pending recipe updated',
            'pending_recipe': updated_recipe
        }
        mock_service_class.return_value = mock_service
        
        response = client.put(
            "/api/pending-recipes/1",
            json={"name": "Updated Recipe", "prep_time": 15}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['pending_recipe']['name'] == 'Updated Recipe'
        mock_service.update_pending.assert_called_once()
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_update_pending_recipe_not_found(self, mock_service_class, client):
        """Test updating a non-existent pending recipe."""
        mock_service = Mock()
        mock_service.update_pending.return_value = {
            'status': 'error',
            'message': 'Pending recipe with ID 999 not found'
        }
        mock_service_class.return_value = mock_service
        
        response = client.put(
            "/api/pending-recipes/999",
            json={"name": "New Name"}
        )
        
        assert response.status_code == 404


class TestApprovePendingRecipeEndpoint:
    """Tests for POST /pending-recipes/{id}/approve endpoint."""
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_approve_pending_recipe_endpoint(self, mock_service_class, client):
        """Test approving a pending recipe."""
        mock_service = Mock()
        mock_service.approve.return_value = {
            'status': 'success',
            'message': 'Recipe "Test Recipe" approved and added to collection',
            'recipe_id': 1,
            'pending_id': 1
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/pending-recipes/1/approve")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['recipe_id'] == 1
        mock_service.approve.assert_called_once_with(1)
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_approve_pending_recipe_error(self, mock_service_class, client):
        """Test approving with validation error."""
        mock_service = Mock()
        mock_service.approve.return_value = {
            'status': 'error',
            'message': 'Failed to approve recipe: Invalid data'
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/pending-recipes/1/approve")
        
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data


class TestRejectPendingRecipeEndpoint:
    """Tests for DELETE /pending-recipes/{id} endpoint."""
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_reject_pending_recipe_endpoint(self, mock_service_class, client):
        """Test rejecting a pending recipe."""
        mock_service = Mock()
        mock_service.reject.return_value = {
            'status': 'success',
            'message': 'Pending recipe "Test Recipe" rejected and removed',
            'pending_id': 1
        }
        mock_service_class.return_value = mock_service
        
        response = client.delete("/api/pending-recipes/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        mock_service.reject.assert_called_once_with(1)
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_reject_pending_recipe_not_found(self, mock_service_class, client):
        """Test rejecting a non-existent pending recipe."""
        mock_service = Mock()
        mock_service.reject.return_value = {
            'status': 'error',
            'message': 'Pending recipe with ID 999 not found'
        }
        mock_service_class.return_value = mock_service
        
        response = client.delete("/api/pending-recipes/999")
        
        assert response.status_code == 404


class TestErrorResponses:
    """Tests for error response handling."""
    
    @patch('src.api.routes.pending_recipes.PendingRecipeService')
    def test_error_status_codes(self, mock_service_class, client):
        """Test that error responses have correct status codes."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Test 400 for parse error
        mock_service.parse_url.return_value = {
            'status': 'error',
            'message': 'Parse failed'
        }
        response = client.post(
            "/api/pending-recipes/parse",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 400
        
        # Test 404 for not found
        mock_service.get_pending.return_value = {
            'status': 'error',
            'message': 'Not found'
        }
        response = client.get("/api/pending-recipes/999")
        assert response.status_code == 404
    
    def test_invalid_json(self, client):
        """Test handling invalid JSON in request body."""
        response = client.post(
            "/api/pending-recipes/parse",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422



