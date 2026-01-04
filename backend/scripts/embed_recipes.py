#!/usr/bin/env python3
"""
Recipe embedding script for KitchenSage.

This script generates embeddings for all existing recipes that don't have them.
Run this after deploying the search feature or when you want to update embeddings.

Usage:
    uv run python scripts/embed_recipes.py [--all] [--batch-size N]

Options:
    --all           Re-embed all recipes, even those with existing embeddings
    --batch-size N  Number of recipes to process per API batch (default: 50)
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import RecipeRepository
from src.services import EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def embed_recipes(all_recipes: bool = False, batch_size: int = 50):
    """
    Generate embeddings for recipes.
    
    Args:
        all_recipes: If True, re-embed all recipes. If False, only embed recipes without embeddings.
        batch_size: Number of recipes to process in each API batch.
    """
    start_time = datetime.now()
    
    logger.info("=" * 60)
    logger.info("KitchenSage Recipe Embedding Script")
    logger.info("=" * 60)
    logger.info(f"Mode: {'All recipes' if all_recipes else 'Only missing embeddings'}")
    logger.info(f"Batch size: {batch_size}")
    logger.info("")
    
    # Initialize services
    recipe_repo = RecipeRepository()
    embedding_service = EmbeddingService()
    
    # Get recipes to embed
    if all_recipes:
        logger.info("Fetching all recipes...")
        recipes = recipe_repo.search_recipes(limit=10000)
        logger.info(f"Found {len(recipes)} total recipes")
    else:
        logger.info("Finding recipes without embeddings...")
        recipe_ids = embedding_service.get_recipes_without_embeddings(limit=10000)
        logger.info(f"Found {len(recipe_ids)} recipes without embeddings")
        
        if not recipe_ids:
            logger.info("All recipes already have embeddings!")
            return
        
        # Load full recipes
        recipes = []
        for recipe_id in recipe_ids:
            recipe = recipe_repo.get_recipe_with_ingredients(recipe_id)
            if recipe:
                recipes.append(recipe)
    
    if not recipes:
        logger.info("No recipes to embed")
        return
    
    # Convert to dicts for embedding
    logger.info("Preparing recipe data for embedding...")
    recipe_dicts = []
    for recipe in recipes:
        if hasattr(recipe, 'model_dump'):
            recipe_dict = recipe.model_dump()
        else:
            recipe_dict = dict(recipe)
        recipe_dicts.append(recipe_dict)
    
    # Generate embeddings
    logger.info("")
    logger.info(f"Generating embeddings for {len(recipe_dicts)} recipes...")
    logger.info("-" * 40)
    
    try:
        embedded_count = embedding_service.embed_recipes_batch(recipe_dicts, batch_size=batch_size)
        
        elapsed_time = datetime.now() - start_time
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Embedding Complete!")
        logger.info("-" * 40)
        logger.info(f"Total recipes processed: {len(recipe_dicts)}")
        logger.info(f"Successfully embedded: {embedded_count}")
        logger.info(f"Failed: {len(recipe_dicts) - embedded_count}")
        logger.info(f"Time elapsed: {elapsed_time}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during embedding: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Generate embeddings for recipes in KitchenSage"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Re-embed all recipes, even those with existing embeddings'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of recipes to process per API batch (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OPENAI_API_KEY environment variable is not set!")
        logger.error("Please set it before running this script.")
        sys.exit(1)
    
    embed_recipes(all_recipes=args.all, batch_size=args.batch_size)


if __name__ == "__main__":
    main()

