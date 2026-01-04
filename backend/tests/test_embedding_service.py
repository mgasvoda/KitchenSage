"""
Tests for the EmbeddingService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import struct

from src.services.embedding_service import EmbeddingService, EMBEDDING_DIMENSIONS


class TestEmbeddingService:
    """Tests for EmbeddingService."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        with patch('src.services.embedding_service.OpenAI') as mock:
            client = Mock()
            mock.return_value = client
            yield client
    
    @pytest.fixture
    def embedding_service(self, mock_openai_client):
        """Create an EmbeddingService with mocked dependencies."""
        return EmbeddingService()
    
    @pytest.fixture
    def sample_embedding(self):
        """Create a sample embedding vector."""
        return [0.1] * EMBEDDING_DIMENSIONS
    
    @pytest.fixture
    def sample_recipe(self):
        """Create a sample recipe dictionary."""
        return {
            'id': 1,
            'name': 'Chicken Stir Fry',
            'description': 'A quick and healthy chicken stir fry',
            'cuisine': 'chinese',
            'meal_types': ['lunch', 'dinner'],
            'dietary_tags': ['gluten_free', 'high_protein'],
            'difficulty': 'easy',
            'ingredients': [
                {'ingredient': {'name': 'chicken breast'}},
                {'ingredient': {'name': 'broccoli'}},
                {'ingredient': {'name': 'soy sauce'}},
            ],
            'notes': 'Can substitute with tofu'
        }
    
    def test_generate_recipe_text(self, embedding_service, sample_recipe):
        """Test generating text representation of a recipe."""
        text = embedding_service.generate_recipe_text(sample_recipe)
        
        assert 'Chicken Stir Fry' in text
        assert 'quick and healthy' in text
        assert 'chinese' in text
        assert 'lunch' in text or 'dinner' in text
        assert 'chicken breast' in text
        assert 'broccoli' in text
    
    def test_generate_recipe_text_minimal(self, embedding_service):
        """Test generating text with minimal recipe data."""
        minimal_recipe = {
            'id': 1,
            'name': 'Simple Dish'
        }
        
        text = embedding_service.generate_recipe_text(minimal_recipe)
        
        assert 'Simple Dish' in text
    
    def test_generate_embedding(self, embedding_service, mock_openai_client, sample_embedding):
        """Test generating an embedding vector."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        result = embedding_service.generate_embedding("test text")
        
        assert result == sample_embedding
        mock_openai_client.embeddings.create.assert_called_once()
    
    def test_generate_embedding_truncates_long_text(self, embedding_service, mock_openai_client, sample_embedding):
        """Test that very long text is truncated."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        # Create very long text
        long_text = "a" * 50000
        
        embedding_service.generate_embedding(long_text)
        
        # Verify the call was made with truncated text
        call_args = mock_openai_client.embeddings.create.call_args
        assert len(call_args.kwargs['input']) <= 30000
    
    def test_serialize_deserialize_embedding(self, embedding_service):
        """Test embedding serialization and deserialization."""
        original = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        serialized = embedding_service._serialize_embedding(original)
        deserialized = embedding_service._deserialize_embedding(serialized)
        
        assert len(deserialized) == len(original)
        for orig, deser in zip(original, deserialized):
            assert abs(orig - deser) < 1e-6
    
    def test_cosine_similarity_identical_vectors(self, embedding_service):
        """Test cosine similarity of identical vectors is 1.0."""
        vec = [0.1, 0.2, 0.3]
        
        similarity = embedding_service.cosine_similarity(vec, vec)
        
        assert abs(similarity - 1.0) < 1e-6
    
    def test_cosine_similarity_orthogonal_vectors(self, embedding_service):
        """Test cosine similarity of orthogonal vectors is 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        similarity = embedding_service.cosine_similarity(vec1, vec2)
        
        assert abs(similarity) < 1e-6
    
    def test_cosine_similarity_opposite_vectors(self, embedding_service):
        """Test cosine similarity of opposite vectors is -1.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        
        similarity = embedding_service.cosine_similarity(vec1, vec2)
        
        assert abs(similarity - (-1.0)) < 1e-6
    
    def test_cosine_similarity_zero_vector(self, embedding_service):
        """Test cosine similarity with zero vector returns 0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]
        
        similarity = embedding_service.cosine_similarity(vec1, vec2)
        
        assert similarity == 0.0
    
    @patch('src.services.embedding_service.get_db_session')
    def test_store_embedding(self, mock_db, embedding_service, sample_embedding):
        """Test storing an embedding in the database."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_db.return_value.__exit__ = Mock(return_value=None)
        
        result = embedding_service.store_embedding(1, sample_embedding)
        
        assert result is True
        mock_cursor.execute.assert_called_once()
    
    @patch('src.services.embedding_service.get_db_session')
    def test_get_embedding_found(self, mock_db, embedding_service, sample_embedding):
        """Test retrieving an existing embedding."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_row = {'embedding': embedding_service._serialize_embedding(sample_embedding)}
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_db.return_value.__exit__ = Mock(return_value=None)
        
        result = embedding_service.get_embedding(1)
        
        assert result is not None
        assert len(result) == len(sample_embedding)
    
    @patch('src.services.embedding_service.get_db_session')
    def test_get_embedding_not_found(self, mock_db, embedding_service):
        """Test retrieving a non-existent embedding."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_db.return_value.__exit__ = Mock(return_value=None)
        
        result = embedding_service.get_embedding(999)
        
        assert result is None
    
    @patch('src.services.embedding_service.get_db_session')
    def test_has_embedding_true(self, mock_db, embedding_service):
        """Test checking if recipe has embedding."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_db.return_value.__exit__ = Mock(return_value=None)
        
        result = embedding_service.has_embedding(1)
        
        assert result is True
    
    @patch('src.services.embedding_service.get_db_session')
    def test_has_embedding_false(self, mock_db, embedding_service):
        """Test checking if recipe has no embedding."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_db.return_value.__exit__ = Mock(return_value=None)
        
        result = embedding_service.has_embedding(999)
        
        assert result is False
    
    @patch('src.services.embedding_service.get_db_session')
    def test_delete_embedding(self, mock_db, embedding_service):
        """Test deleting an embedding."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_db.return_value.__exit__ = Mock(return_value=None)
        
        result = embedding_service.delete_embedding(1)
        
        assert result is True
    
    def test_embed_recipe_requires_id(self, embedding_service):
        """Test that embed_recipe raises error without recipe ID."""
        recipe = {'name': 'Test Recipe'}
        
        with pytest.raises(ValueError, match="must have an 'id' field"):
            embedding_service.embed_recipe(recipe)
    
    @patch.object(EmbeddingService, 'store_embedding')
    @patch.object(EmbeddingService, 'generate_embedding')
    def test_embed_recipe_success(self, mock_generate, mock_store, embedding_service, sample_recipe, sample_embedding):
        """Test successfully embedding a recipe."""
        mock_generate.return_value = sample_embedding
        mock_store.return_value = True
        
        result = embedding_service.embed_recipe(sample_recipe)
        
        assert result == sample_embedding
        mock_generate.assert_called_once()
        mock_store.assert_called_once_with(sample_recipe['id'], sample_embedding)
    
    @patch.object(EmbeddingService, 'get_all_embeddings')
    def test_find_similar_recipes(self, mock_get_all, embedding_service):
        """Test finding similar recipes by embedding."""
        # Setup: 3 recipes with embeddings
        mock_get_all.return_value = [
            (1, [1.0, 0.0, 0.0]),  # Will have high similarity to query
            (2, [0.0, 1.0, 0.0]),  # Will have low similarity
            (3, [0.9, 0.1, 0.0]),  # Will have medium-high similarity
        ]
        
        query_embedding = [1.0, 0.0, 0.0]
        
        results = embedding_service.find_similar_recipes(query_embedding, limit=3)
        
        assert len(results) == 3
        # First result should be recipe 1 (exact match)
        assert results[0][0] == 1
        assert abs(results[0][1] - 1.0) < 0.01
        # Recipe 3 should be second (high similarity)
        assert results[1][0] == 3
    
    @patch.object(EmbeddingService, 'generate_embedding')
    @patch.object(EmbeddingService, 'find_similar_recipes')
    def test_semantic_search(self, mock_find, mock_generate, embedding_service, sample_embedding):
        """Test semantic search with a text query."""
        mock_generate.return_value = sample_embedding
        mock_find.return_value = [(1, 0.9), (2, 0.7)]
        
        results = embedding_service.semantic_search("chicken dinner", limit=5)
        
        assert len(results) == 2
        mock_generate.assert_called_once_with("chicken dinner")
        mock_find.assert_called_once()

