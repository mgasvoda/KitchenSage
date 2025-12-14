"""
Tests for PendingRecipeRepository.
"""

import pytest
import sqlite3
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.pending_recipe_repository import PendingRecipeRepository
from src.database.connection import get_db_session, RecordNotFoundError, ValidationError
from src.models import (
    PendingRecipe, PendingRecipeCreate, PendingRecipeUpdate,
    PendingRecipeStatus, PendingRecipeIngredient
)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Create a temporary in-memory database for testing."""
    db_path = tmp_path / "test_kitchen_crew.db"
    
    # Patch the database config to use our test database
    from src.database import connection
    original_db_path = connection.config.db_path
    connection.config.db_path = str(db_path)
    
    # Create tables
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        
        # Create pending_recipes table
        cursor.execute('''
            CREATE TABLE pending_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                prep_time INTEGER,
                cook_time INTEGER,
                servings INTEGER,
                difficulty TEXT,
                cuisine TEXT,
                dietary_tags TEXT,
                ingredients TEXT,
                instructions TEXT,
                notes TEXT,
                image_url TEXT,
                nutritional_info TEXT,
                source_url TEXT,
                discovery_query TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create recipes table for approval testing
        cursor.execute('''
            CREATE TABLE recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                prep_time INTEGER,
                cook_time INTEGER,
                servings INTEGER,
                difficulty TEXT,
                cuisine TEXT,
                dietary_tags TEXT,
                instructions TEXT,
                notes TEXT,
                image_url TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create ingredients table
        cursor.execute('''
            CREATE TABLE ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                common_unit TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create recipe_ingredients table
        cursor.execute('''
            CREATE TABLE recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL,
                unit TEXT,
                notes TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
    
    yield db_path
    
    # Restore original database path
    connection.config.db_path = original_db_path


@pytest.fixture
def repo(test_db):
    """Create a PendingRecipeRepository instance."""
    return PendingRecipeRepository()


@pytest.fixture
def sample_pending_create():
    """Sample pending recipe creation data."""
    return PendingRecipeCreate(
        name="Test Pasta Recipe",
        description="A delicious pasta dish",
        prep_time=15,
        cook_time=20,
        servings=4,
        difficulty="Easy",
        cuisine="Italian",
        dietary_tags=["vegetarian"],
        ingredients=[
            PendingRecipeIngredient(name="pasta", quantity=400, unit="g"),
            PendingRecipeIngredient(name="tomato sauce", quantity=1, unit="cup")
        ],
        instructions=["Boil pasta", "Heat sauce", "Combine and serve"],
        notes="Great for weeknights",
        source_url="https://example.com/recipe",
        discovery_query=None
    )


class TestPendingRecipeRepository:
    """Tests for PendingRecipeRepository."""
    
    def test_create_pending_recipe(self, repo, sample_pending_create):
        """Test creating a pending recipe."""
        pending = repo.create_pending(sample_pending_create)
        
        assert pending.id is not None
        assert pending.name == "Test Pasta Recipe"
        assert pending.status == PendingRecipeStatus.PENDING
        assert len(pending.ingredients) == 2
        assert len(pending.instructions) == 3
    
    def test_get_pending_by_id(self, repo, sample_pending_create):
        """Test retrieving a pending recipe by ID."""
        created = repo.create_pending(sample_pending_create)
        retrieved = repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
    
    def test_get_pending_by_id_not_found(self, repo):
        """Test retrieving a non-existent pending recipe."""
        result = repo.get_by_id(999)
        assert result is None
    
    def test_get_all_pending(self, repo, sample_pending_create):
        """Test listing all pending recipes."""
        # Create multiple pending recipes
        repo.create_pending(sample_pending_create)
        repo.create_pending(sample_pending_create)
        
        all_pending = repo.get_all_pending()
        
        assert len(all_pending) == 2
        assert all(p.status == PendingRecipeStatus.PENDING for p in all_pending)
    
    def test_get_pending_by_status(self, repo, sample_pending_create):
        """Test filtering pending recipes by status."""
        # Create pending recipes
        pending1 = repo.create_pending(sample_pending_create)
        pending2 = repo.create_pending(sample_pending_create)
        
        # Update one to approved
        repo.update(pending2.id, {'status': PendingRecipeStatus.APPROVED.value})
        
        # Get only pending
        pending_only = repo.get_pending_by_status(PendingRecipeStatus.PENDING)
        assert len(pending_only) == 1
        assert pending_only[0].id == pending1.id
        
        # Get approved
        approved = repo.get_pending_by_status(PendingRecipeStatus.APPROVED)
        assert len(approved) == 1
        assert approved[0].id == pending2.id
    
    def test_update_pending_recipe(self, repo, sample_pending_create):
        """Test updating a pending recipe."""
        created = repo.create_pending(sample_pending_create)
        
        update = PendingRecipeUpdate(
            name="Updated Recipe Name",
            prep_time=20,
            servings=6
        )
        
        updated = repo.update_pending(created.id, update)
        
        assert updated is not None
        assert updated.name == "Updated Recipe Name"
        assert updated.prep_time == 20
        assert updated.servings == 6
        # Unchanged fields should remain
        assert updated.description == sample_pending_create.description
    
    def test_update_pending_recipe_not_found(self, repo):
        """Test updating a non-existent pending recipe."""
        update = PendingRecipeUpdate(name="New Name")
        result = repo.update_pending(999, update)
        assert result is None
    
    def test_check_duplicate_by_name(self, repo, sample_pending_create):
        """Test duplicate detection by name."""
        created = repo.create_pending(sample_pending_create)
        
        duplicate = repo.check_duplicate(name="Test Pasta Recipe")
        
        assert duplicate is not None
        assert duplicate.id == created.id
    
    def test_check_duplicate_by_url(self, repo, sample_pending_create):
        """Test duplicate detection by source URL."""
        created = repo.create_pending(sample_pending_create)
        
        duplicate = repo.check_duplicate(name="Different Name", source_url="https://example.com/recipe")
        
        assert duplicate is not None
        assert duplicate.id == created.id
    
    def test_check_duplicate_no_match(self, repo, sample_pending_create):
        """Test duplicate check when no duplicate exists."""
        repo.create_pending(sample_pending_create)
        
        duplicate = repo.check_duplicate(name="Completely Different Recipe")
        
        assert duplicate is None
    
    def test_reject_pending_recipe(self, repo, sample_pending_create):
        """Test rejecting a pending recipe."""
        created = repo.create_pending(sample_pending_create)
        
        result = repo.reject(created.id)
        
        assert result['status'] == 'success'
        assert 'message' in result
        
        # Verify it's deleted
        retrieved = repo.get_by_id(created.id)
        assert retrieved is None
    
    def test_reject_pending_recipe_not_found(self, repo):
        """Test rejecting a non-existent pending recipe."""
        with pytest.raises(RecordNotFoundError):
            repo.reject(999)
    
    @patch('src.database.pending_recipe_repository.RecipeRepository')
    def test_approve_pending_recipe(self, mock_recipe_repo_class, repo, sample_pending_create, test_db):
        """Test approving a pending recipe."""
        # Mock RecipeRepository
        mock_recipe_repo = Mock()
        mock_recipe_repo_class.return_value = mock_recipe_repo
        
        # Create a mock recipe
        mock_recipe = Mock()
        mock_recipe.id = 1
        mock_recipe_repo.create_recipe.return_value = mock_recipe
        
        # Replace the recipe_repo property
        repo._recipe_repo = mock_recipe_repo
        
        # Create pending recipe
        created = repo.create_pending(sample_pending_create)
        
        # Approve it
        result = repo.approve(created.id)
        
        assert result['status'] == 'success'
        assert 'recipe_id' in result
        assert result['recipe_id'] == 1
        
        # Verify pending recipe is deleted
        retrieved = repo.get_by_id(created.id)
        assert retrieved is None
    
    def test_approve_pending_recipe_not_found(self, repo):
        """Test approving a non-existent pending recipe."""
        with pytest.raises(RecordNotFoundError):
            repo.approve(999)
    
    @patch('src.database.pending_recipe_repository.RecipeRepository')
    def test_approve_invalid_recipe(self, mock_recipe_repo_class, repo, test_db):
        """Test approving a recipe with invalid data."""
        # Create pending recipe without instructions (required)
        invalid_create = PendingRecipeCreate(
            name="Invalid Recipe",
            instructions=[]  # No instructions
        )
        created = repo.create_pending(invalid_create)
        
        with pytest.raises(ValidationError):
            repo.approve(created.id)
    
    @patch('src.database.pending_recipe_repository.RecipeRepository')
    def test_approve_creates_recipe_with_ingredients(self, mock_recipe_repo_class, repo, sample_pending_create, test_db):
        """Test that approval creates recipe with proper ingredient linking."""
        mock_recipe_repo = Mock()
        mock_recipe_repo_class.return_value = mock_recipe_repo
        
        mock_recipe = Mock()
        mock_recipe.id = 1
        mock_recipe_repo.create_recipe.return_value = mock_recipe
        
        repo._recipe_repo = mock_recipe_repo
        
        created = repo.create_pending(sample_pending_create)
        repo.approve(created.id)
        
        # Verify create_recipe was called with ingredients
        assert mock_recipe_repo.create_recipe.called
        call_args = mock_recipe_repo.create_recipe.call_args
        
        # Check that ingredients_data was passed
        assert len(call_args[0]) == 2  # recipe_create, ingredients_data
        ingredients_data = call_args[0][1]
        assert len(ingredients_data) == 2
        assert ingredients_data[0]['name'] == "pasta"
        assert ingredients_data[1]['name'] == "tomato sauce"
    
    def test_pending_recipe_ingredients_serialization(self, repo, sample_pending_create):
        """Test that ingredients are properly serialized/deserialized."""
        created = repo.create_pending(sample_pending_create)
        retrieved = repo.get_by_id(created.id)
        
        assert len(retrieved.ingredients) == 2
        assert retrieved.ingredients[0].name == "pasta"
        assert retrieved.ingredients[0].quantity == 400.0
        assert retrieved.ingredients[0].unit == "g"
    
    def test_pending_recipe_instructions_serialization(self, repo, sample_pending_create):
        """Test that instructions are properly serialized/deserialized."""
        created = repo.create_pending(sample_pending_create)
        retrieved = repo.get_by_id(created.id)
        
        assert len(retrieved.instructions) == 3
        assert "Boil pasta" in retrieved.instructions
        assert "Combine and serve" in retrieved.instructions

