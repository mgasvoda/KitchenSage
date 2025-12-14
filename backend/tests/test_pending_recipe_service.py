"""
Tests for PendingRecipeService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.pending_recipe_service import PendingRecipeService
from src.models import (
    PendingRecipe, PendingRecipeCreate, PendingRecipeIngredient,
    PendingRecipeStatus
)


@pytest.fixture
def service():
    """Create a PendingRecipeService instance with mocked dependencies."""
    with patch('src.services.pending_recipe_service.PendingRecipeRepository'), \
         patch('src.services.pending_recipe_service.WebScrapingTool'), \
         patch('src.services.pending_recipe_service.WebSearchTool'):
        service = PendingRecipeService()
        service.repository = Mock()
        service.scraping_tool = Mock()
        service.search_tool = Mock()
        return service


@pytest.fixture
def sample_scraped_data():
    """Sample scraped recipe data."""
    return {
        'name': 'Scraped Recipe',
        'description': 'A recipe from the web',
        'prep_time': 10,
        'cook_time': 30,
        'servings': 4,
        'difficulty': 'Medium',
        'cuisine': 'Italian',
        'ingredients': [
            {'name': 'flour', 'quantity': 2, 'unit': 'cups'},
            'salt',
            {'name': 'water', 'quantity': 1, 'unit': 'cup'}
        ],
        'instructions': ['Mix ingredients', 'Knead dough', 'Bake'],
        'tags': ['vegetarian'],
        'image_url': 'https://example.com/image.jpg',
        'url': 'https://example.com/recipe'
    }


class TestPendingRecipeService:
    """Tests for PendingRecipeService."""
    
    def test_parse_url_success(self, service, sample_scraped_data):
        """Test successful URL parsing."""
        # Mock repository to return no duplicates
        service.repository.check_duplicate.return_value = None
        
        # Mock scraping tool
        service.scraping_tool._run.return_value = [sample_scraped_data]
        
        # Mock repository create
        mock_pending = Mock()
        mock_pending.id = 1
        mock_pending.name = 'Scraped Recipe'
        mock_pending.status = PendingRecipeStatus.PENDING
        service.repository.create_pending.return_value = mock_pending
        
        # Mock _pending_to_dict
        with patch.object(service, '_pending_to_dict', return_value={'id': 1, 'name': 'Scraped Recipe'}):
            result = service.parse_url('https://example.com/recipe')
        
        assert result['status'] == 'success'
        assert 'pending_recipe' in result
        service.scraping_tool._run.assert_called_once_with('https://example.com/recipe')
    
    def test_parse_url_duplicate(self, service):
        """Test handling duplicate URL detection."""
        # Mock existing pending recipe
        mock_existing = Mock()
        mock_existing.id = 1
        service.repository.check_duplicate.return_value = mock_existing
        
        # Mock _pending_to_dict
        with patch.object(service, '_pending_to_dict', return_value={'id': 1}):
            result = service.parse_url('https://example.com/recipe')
        
        assert result['status'] == 'duplicate'
        assert 'message' in result
        assert 'pending_recipe' in result
        # Should not call scraping tool
        service.scraping_tool._run.assert_not_called()
    
    def test_parse_url_invalid(self, service):
        """Test handling invalid/unparseable URLs."""
        service.repository.check_duplicate.return_value = None
        service.scraping_tool._run.return_value = []
        
        result = service.parse_url('https://invalid-url.com/recipe')
        
        assert result['status'] == 'error'
        assert 'message' in result
    
    def test_parse_url_error_handling(self, service):
        """Test error handling during URL parsing."""
        service.repository.check_duplicate.return_value = None
        service.scraping_tool._run.side_effect = Exception("Network error")
        
        result = service.parse_url('https://example.com/recipe')
        
        assert result['status'] == 'error'
        assert 'message' in result
    
    def test_parse_url_scraping_error(self, service):
        """Test handling scraping tool errors."""
        service.repository.check_duplicate.return_value = None
        service.scraping_tool._run.return_value = [{'error': 'Failed to scrape'}]
        
        result = service.parse_url('https://example.com/recipe')
        
        assert result['status'] == 'error'
        assert 'failed' in result['message'].lower()
    
    def test_discover_recipes_success(self, service, sample_scraped_data):
        """Test successful recipe discovery."""
        search_results = [
            sample_scraped_data,
            {**sample_scraped_data, 'name': 'Recipe 2', 'url': 'https://example.com/recipe2'}
        ]
        
        service.search_tool._run.return_value = search_results
        service.repository.check_duplicate.return_value = None
        
        # Mock created pending recipes
        mock_pending1 = Mock()
        mock_pending1.id = 1
        mock_pending2 = Mock()
        mock_pending2.id = 2
        service.repository.create_pending.side_effect = [mock_pending1, mock_pending2]
        
        # Mock _pending_to_dict
        with patch.object(service, '_pending_to_dict', side_effect=[
            {'id': 1, 'name': 'Scraped Recipe'},
            {'id': 2, 'name': 'Recipe 2'}
        ]):
            result = service.discover_recipes('pasta recipes')
        
        assert result['status'] == 'success'
        assert len(result['pending_recipes']) == 2
        assert result['query'] == 'pasta recipes'
        service.search_tool._run.assert_called_once()
    
    def test_discover_recipes_with_filters(self, service, sample_scraped_data):
        """Test recipe discovery with cuisine and dietary filters."""
        service.search_tool._run.return_value = [sample_scraped_data]
        service.repository.check_duplicate.return_value = None
        
        mock_pending = Mock()
        mock_pending.id = 1
        service.repository.create_pending.return_value = mock_pending
        
        with patch.object(service, '_pending_to_dict', return_value={'id': 1}):
            result = service.discover_recipes(
                'healthy dinner',
                cuisine='Italian',
                dietary_restrictions=['vegetarian', 'gluten_free'],
                max_results=5
            )
        
        assert result['status'] == 'success'
        # Verify search query was enhanced
        call_args = service.search_tool._run.call_args[0]
        call_kwargs = service.search_tool._run.call_args[1]
        assert 'Italian' in call_args[0]
        assert 'vegetarian' in call_args[0]
        assert call_kwargs['max_results'] == 5
    
    def test_discover_recipes_empty_results(self, service):
        """Test handling empty search results."""
        service.search_tool._run.return_value = []
        
        result = service.discover_recipes('nonexistent recipe')
        
        assert result['status'] == 'error'
        assert 'message' in result
    
    def test_discover_recipes_duplicate_handling(self, service, sample_scraped_data):
        """Test handling duplicates during discovery."""
        # First recipe is new, second is duplicate
        mock_existing = Mock()
        mock_existing.id = 1
        service.repository.check_duplicate.side_effect = [None, mock_existing]
        
        service.search_tool._run.return_value = [
            sample_scraped_data,
            {**sample_scraped_data, 'name': 'Duplicate Recipe'}
        ]
        
        mock_pending = Mock()
        mock_pending.id = 2
        service.repository.create_pending.return_value = mock_pending
        
        with patch.object(service, '_pending_to_dict', side_effect=[
            {'id': 2, 'name': 'Scraped Recipe'},
            {'id': 1, 'name': 'Duplicate Recipe', 'is_duplicate': True}
        ]):
            result = service.discover_recipes('recipes')
        
        assert result['status'] == 'success'
        assert len(result['pending_recipes']) == 2
        # One should be marked as duplicate
        duplicates = [r for r in result['pending_recipes'] if r.get('is_duplicate')]
        assert len(duplicates) == 1
    
    def test_list_pending_recipes(self, service):
        """Test listing all pending recipes."""
        mock_pending1 = Mock()
        mock_pending1.id = 1
        mock_pending2 = Mock()
        mock_pending2.id = 2
        service.repository.get_all_pending.return_value = [mock_pending1, mock_pending2]
        
        with patch.object(service, '_pending_to_dict', side_effect=[
            {'id': 1}, {'id': 2}
        ]):
            result = service.list_pending(limit=50)
        
        assert result['status'] == 'success'
        assert len(result['pending_recipes']) == 2
        assert result['total'] == 2
    
    def test_get_pending_recipe(self, service):
        """Test getting a single pending recipe."""
        mock_pending = Mock()
        mock_pending.id = 1
        service.repository.get_by_id.return_value = mock_pending
        
        with patch.object(service, '_pending_to_dict', return_value={'id': 1}):
            result = service.get_pending(1)
        
        assert result['status'] == 'success'
        assert 'pending_recipe' in result
    
    def test_get_pending_recipe_not_found(self, service):
        """Test getting a non-existent pending recipe."""
        service.repository.get_by_id.return_value = None
        
        result = service.get_pending(999)
        
        assert result['status'] == 'error'
        assert 'not found' in result['message'].lower()
    
    def test_update_pending_recipe(self, service):
        """Test updating a pending recipe."""
        mock_pending = Mock()
        mock_pending.id = 1
        service.repository.update_pending.return_value = mock_pending
        
        with patch.object(service, '_pending_to_dict', return_value={'id': 1}):
            result = service.update_pending(1, {'name': 'Updated Name'})
        
        assert result['status'] == 'success'
        assert 'pending_recipe' in result
        service.repository.update_pending.assert_called_once()
    
    def test_update_pending_recipe_not_found(self, service):
        """Test updating a non-existent pending recipe."""
        service.repository.update_pending.return_value = None
        
        result = service.update_pending(999, {'name': 'New Name'})
        
        assert result['status'] == 'error'
        assert 'not found' in result['message'].lower()
    
    def test_approve_pending_recipe(self, service):
        """Test approving a pending recipe."""
        service.repository.approve.return_value = {
            'status': 'success',
            'recipe_id': 1,
            'message': 'Recipe approved'
        }
        
        result = service.approve(1)
        
        assert result['status'] == 'success'
        assert result['recipe_id'] == 1
        service.repository.approve.assert_called_once_with(1)
    
    def test_approve_pending_recipe_error(self, service):
        """Test approving with validation error."""
        from src.database.connection import ValidationError
        service.repository.approve.side_effect = ValidationError("Invalid recipe data")
        
        result = service.approve(1)
        
        assert result['status'] == 'error'
        assert 'message' in result
    
    def test_reject_pending_recipe(self, service):
        """Test rejecting a pending recipe."""
        service.repository.reject.return_value = {
            'status': 'success',
            'message': 'Recipe rejected'
        }
        
        result = service.reject(1)
        
        assert result['status'] == 'success'
        service.repository.reject.assert_called_once_with(1)
    
    def test_reject_pending_recipe_not_found(self, service):
        """Test rejecting a non-existent pending recipe."""
        from src.database.connection import RecordNotFoundError
        service.repository.reject.side_effect = RecordNotFoundError("Not found")
        
        result = service.reject(999)
        
        assert result['status'] == 'error'
        assert 'message' in result
    
    def test_scraped_to_pending_create_conversion(self, service, sample_scraped_data):
        """Test conversion of scraped data to PendingRecipeCreate."""
        result = service._scraped_to_pending_create(
            sample_scraped_data,
            source_url='https://example.com/recipe'
        )
        
        assert isinstance(result, PendingRecipeCreate)
        assert result.name == 'Scraped Recipe'
        assert result.source_url == 'https://example.com/recipe'
        assert len(result.ingredients) == 3
        assert len(result.instructions) == 3
        assert 'vegetarian' in result.dietary_tags
    
    def test_scraped_to_pending_create_string_ingredients(self, service):
        """Test conversion with string ingredients."""
        scraped = {
            'name': 'Simple Recipe',
            'ingredients': ['flour', 'water', 'salt'],
            'instructions': 'Mix everything'
        }
        
        result = service._scraped_to_pending_create(scraped)
        
        assert len(result.ingredients) == 3
        assert all(isinstance(ing, PendingRecipeIngredient) for ing in result.ingredients)
        assert result.ingredients[0].name == 'flour'
    
    def test_scraped_to_pending_create_string_instructions(self, service):
        """Test conversion with string instructions."""
        scraped = {
            'name': 'Recipe',
            'instructions': 'Step 1\nStep 2\nStep 3'
        }
        
        result = service._scraped_to_pending_create(scraped)
        
        assert len(result.instructions) == 3
        assert result.instructions[0] == 'Step 1'
    
    def test_pending_to_dict_conversion(self, service):
        """Test conversion of PendingRecipe to dictionary."""
        from datetime import datetime
        mock_pending = Mock()
        mock_pending.id = 1
        mock_pending.name = 'Test Recipe'
        mock_pending.description = 'Description'
        mock_pending.prep_time = 10
        mock_pending.cook_time = 20
        mock_pending.servings = 4
        mock_pending.difficulty = 'Easy'
        mock_pending.cuisine = 'Italian'
        mock_pending.dietary_tags = ['vegetarian']
        mock_pending.ingredients = [
            PendingRecipeIngredient(name='flour', quantity=2, unit='cups')
        ]
        mock_pending.instructions = ['Step 1', 'Step 2']
        mock_pending.notes = 'Notes'
        mock_pending.image_url = 'https://example.com/image.jpg'
        mock_pending.nutritional_info = {'calories': 300}
        mock_pending.source_url = 'https://example.com/recipe'
        mock_pending.discovery_query = 'pasta'
        mock_pending.status = PendingRecipeStatus.PENDING
        mock_pending.created_at = datetime.now()
        
        result = service._pending_to_dict(mock_pending)
        
        assert result['id'] == 1
        assert result['name'] == 'Test Recipe'
        assert len(result['ingredients']) == 1
        assert result['ingredients'][0]['name'] == 'flour'
        assert result['status'] == 'pending'
        assert 'created_at' in result

