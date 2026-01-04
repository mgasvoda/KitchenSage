"""
Embedding service for generating and managing recipe embeddings.

Uses OpenAI's text-embedding-3-small model for generating vector embeddings
that enable semantic search functionality.
"""

import logging
import json
import struct
import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

import numpy as np
from openai import OpenAI

from src.database.connection import get_db_session

logger = logging.getLogger(__name__)

# Constants
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small dimensions


class EmbeddingService:
    """
    Service for generating and managing recipe embeddings.
    
    Handles:
    - Generating embeddings using OpenAI's API
    - Storing embeddings in the database
    - Retrieving embeddings for similarity search
    - Batch embedding operations
    """
    
    def __init__(self):
        """Initialize the embedding service."""
        self.client = OpenAI()
        self.model = EMBEDDING_MODEL
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Truncate text if too long (model has token limits)
            # text-embedding-3-small has 8191 token limit, rough estimate 4 chars per token
            max_chars = 30000
            if len(text) > max_chars:
                text = text[:max_chars]
            
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_recipe_text(self, recipe: Dict[str, Any]) -> str:
        """
        Generate text representation of a recipe for embedding.
        
        Combines relevant recipe fields into a single text that captures
        the recipe's semantic meaning for search purposes.
        
        Args:
            recipe: Recipe dictionary with fields like name, description, ingredients, etc.
            
        Returns:
            Combined text representation of the recipe
        """
        parts = []
        
        # Recipe name is most important
        if recipe.get('name'):
            parts.append(f"Recipe: {recipe['name']}")
        
        # Description provides context
        if recipe.get('description'):
            parts.append(f"Description: {recipe['description']}")
        
        # Cuisine type
        if recipe.get('cuisine'):
            cuisine = recipe['cuisine']
            if hasattr(cuisine, 'value'):
                cuisine = cuisine.value
            parts.append(f"Cuisine: {cuisine}")
        
        # Meal types
        if recipe.get('meal_types'):
            meal_types = recipe['meal_types']
            if isinstance(meal_types, list):
                mt_values = [mt.value if hasattr(mt, 'value') else mt for mt in meal_types]
                parts.append(f"Suitable for: {', '.join(mt_values)}")
        
        # Dietary tags
        if recipe.get('dietary_tags'):
            tags = recipe['dietary_tags']
            if isinstance(tags, list):
                tag_values = [t.value if hasattr(t, 'value') else t for t in tags]
                parts.append(f"Dietary: {', '.join(tag_values)}")
        
        # Ingredients (just names for semantic matching)
        if recipe.get('ingredients'):
            ingredient_names = []
            for ing in recipe['ingredients']:
                if isinstance(ing, dict):
                    if 'ingredient' in ing and isinstance(ing['ingredient'], dict):
                        ingredient_names.append(ing['ingredient'].get('name', ''))
                    elif 'name' in ing:
                        ingredient_names.append(ing['name'])
                elif hasattr(ing, 'ingredient') and ing.ingredient:
                    ingredient_names.append(ing.ingredient.name)
                elif hasattr(ing, 'name'):
                    ingredient_names.append(ing.name)
            if ingredient_names:
                parts.append(f"Ingredients: {', '.join(ingredient_names)}")
        
        # Difficulty
        if recipe.get('difficulty'):
            difficulty = recipe['difficulty']
            if hasattr(difficulty, 'value'):
                difficulty = difficulty.value
            parts.append(f"Difficulty: {difficulty}")
        
        # Notes (might contain useful context)
        if recipe.get('notes'):
            parts.append(f"Notes: {recipe['notes']}")
        
        return "\n".join(parts)
    
    def _serialize_embedding(self, embedding: List[float]) -> bytes:
        """
        Serialize embedding to bytes for database storage.
        
        Args:
            embedding: List of floats
            
        Returns:
            Bytes representation of the embedding
        """
        return struct.pack(f'{len(embedding)}f', *embedding)
    
    def _deserialize_embedding(self, data: bytes) -> List[float]:
        """
        Deserialize embedding from bytes.
        
        Args:
            data: Bytes representation of the embedding
            
        Returns:
            List of floats
        """
        num_floats = len(data) // 4  # 4 bytes per float
        return list(struct.unpack(f'{num_floats}f', data))
    
    def store_embedding(self, recipe_id: int, embedding: List[float]) -> bool:
        """
        Store or update an embedding for a recipe.
        
        Args:
            recipe_id: The ID of the recipe
            embedding: The embedding vector
            
        Returns:
            True if successful
        """
        try:
            embedding_bytes = self._serialize_embedding(embedding)
            now = datetime.now().isoformat()
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                
                # Use INSERT OR REPLACE to handle both new and existing embeddings
                cursor.execute("""
                    INSERT INTO recipe_embeddings (recipe_id, embedding, model, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(recipe_id) DO UPDATE SET
                        embedding = excluded.embedding,
                        model = excluded.model,
                        updated_at = excluded.updated_at
                """, (recipe_id, embedding_bytes, self.model, now, now))
                
                logger.info(f"Stored embedding for recipe {recipe_id}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Database error storing embedding: {e}")
            raise
    
    def get_embedding(self, recipe_id: int) -> Optional[List[float]]:
        """
        Retrieve the embedding for a recipe.
        
        Args:
            recipe_id: The ID of the recipe
            
        Returns:
            The embedding vector, or None if not found
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT embedding FROM recipe_embeddings WHERE recipe_id = ?",
                    (recipe_id,)
                )
                row = cursor.fetchone()
                
                if row and row['embedding']:
                    return self._deserialize_embedding(row['embedding'])
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving embedding: {e}")
            raise
    
    def get_all_embeddings(self) -> List[Tuple[int, List[float]]]:
        """
        Retrieve all recipe embeddings from the database.
        
        Returns:
            List of tuples (recipe_id, embedding)
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT recipe_id, embedding FROM recipe_embeddings")
                rows = cursor.fetchall()
                
                return [
                    (row['recipe_id'], self._deserialize_embedding(row['embedding']))
                    for row in rows
                ]
                
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving embeddings: {e}")
            raise
    
    def delete_embedding(self, recipe_id: int) -> bool:
        """
        Delete the embedding for a recipe.
        
        Args:
            recipe_id: The ID of the recipe
            
        Returns:
            True if an embedding was deleted
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM recipe_embeddings WHERE recipe_id = ?",
                    (recipe_id,)
                )
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Database error deleting embedding: {e}")
            raise
    
    def embed_recipe(self, recipe: Dict[str, Any]) -> List[float]:
        """
        Generate and store an embedding for a recipe.
        
        Args:
            recipe: Recipe dictionary (must include 'id')
            
        Returns:
            The generated embedding vector
        """
        recipe_id = recipe.get('id')
        if not recipe_id:
            raise ValueError("Recipe must have an 'id' field")
        
        # Generate text representation
        text = self.generate_recipe_text(recipe)
        
        # Generate embedding
        embedding = self.generate_embedding(text)
        
        # Store in database
        self.store_embedding(recipe_id, embedding)
        
        return embedding
    
    def embed_recipes_batch(self, recipes: List[Dict[str, Any]], batch_size: int = 100) -> int:
        """
        Generate and store embeddings for multiple recipes.
        
        Args:
            recipes: List of recipe dictionaries
            batch_size: Number of recipes to process in each API batch
            
        Returns:
            Number of recipes successfully embedded
        """
        embedded_count = 0
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            
            # Generate texts for batch
            texts = [self.generate_recipe_text(r) for r in batch]
            
            try:
                # Make batch API call
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                
                # Store each embedding
                for j, embedding_data in enumerate(response.data):
                    recipe = batch[j]
                    recipe_id = recipe.get('id')
                    
                    if recipe_id:
                        self.store_embedding(recipe_id, embedding_data.embedding)
                        embedded_count += 1
                        
            except Exception as e:
                logger.error(f"Error embedding batch starting at index {i}: {e}")
                # Continue with next batch
                continue
        
        logger.info(f"Embedded {embedded_count} recipes")
        return embedded_count
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        a = np.array(vec1)
        b = np.array(vec2)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def find_similar_recipes(
        self, 
        query_embedding: List[float], 
        limit: int = 20,
        min_similarity: float = 0.0
    ) -> List[Tuple[int, float]]:
        """
        Find recipes similar to the query embedding.
        
        Args:
            query_embedding: The embedding to search with
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            List of tuples (recipe_id, similarity_score) sorted by similarity
        """
        all_embeddings = self.get_all_embeddings()
        
        # Calculate similarities
        similarities = []
        for recipe_id, embedding in all_embeddings:
            similarity = self.cosine_similarity(query_embedding, embedding)
            if similarity >= min_similarity:
                similarities.append((recipe_id, similarity))
        
        # Sort by similarity (descending) and limit
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def semantic_search(
        self, 
        query: str, 
        limit: int = 20,
        min_similarity: float = 0.3
    ) -> List[Tuple[int, float]]:
        """
        Perform semantic search using a text query.
        
        Args:
            query: The search query text
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of tuples (recipe_id, similarity_score) sorted by similarity
        """
        # Generate embedding for the query
        query_embedding = self.generate_embedding(query)
        
        # Find similar recipes
        return self.find_similar_recipes(query_embedding, limit, min_similarity)
    
    def has_embedding(self, recipe_id: int) -> bool:
        """
        Check if a recipe has an embedding.
        
        Args:
            recipe_id: The ID of the recipe
            
        Returns:
            True if the recipe has an embedding
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM recipe_embeddings WHERE recipe_id = ?",
                    (recipe_id,)
                )
                return cursor.fetchone() is not None
                
        except sqlite3.Error as e:
            logger.error(f"Database error checking embedding: {e}")
            raise
    
    def get_recipes_without_embeddings(self, limit: int = 100) -> List[int]:
        """
        Get recipe IDs that don't have embeddings.
        
        Args:
            limit: Maximum number of IDs to return
            
        Returns:
            List of recipe IDs without embeddings
        """
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.id 
                    FROM recipes r
                    LEFT JOIN recipe_embeddings re ON r.id = re.recipe_id
                    WHERE re.recipe_id IS NULL
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [row['id'] for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Database error finding recipes without embeddings: {e}")
            raise

