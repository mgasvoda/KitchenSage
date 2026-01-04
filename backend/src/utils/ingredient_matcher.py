"""
Utility for matching ingredient names to database ingredient IDs.

Provides fuzzy matching and caching for efficient ingredient lookups.
"""

import logging
from typing import Optional, Dict
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class IngredientMatcher:
    """
    Matches ingredient names to database ingredient IDs.

    Uses exact matching first, then fuzzy matching as fallback.
    Caches results for performance.
    """

    def __init__(self, ingredient_repo):
        """
        Initialize the matcher with an ingredient repository.

        Args:
            ingredient_repo: IngredientRepository instance
        """
        self.ingredient_repo = ingredient_repo
        self._cache: Dict[str, Optional[int]] = {}
        self._ingredients_by_name: Optional[Dict[str, int]] = None

    def _build_name_index(self):
        """Build an index of ingredient names to IDs."""
        if self._ingredients_by_name is not None:
            return

        self._ingredients_by_name = {}
        all_ingredients = self.ingredient_repo.get_all()

        for ingredient in all_ingredients:
            # Store with exact name (case-insensitive)
            name_lower = ingredient.name.lower().strip()
            self._ingredients_by_name[name_lower] = ingredient.id

    def find_ingredient_id(self, name: str, similarity_threshold: float = 0.85) -> Optional[int]:
        """
        Find ingredient ID by name using exact or fuzzy matching.

        Args:
            name: Ingredient name to look up
            similarity_threshold: Minimum similarity score for fuzzy matches (0.0-1.0)

        Returns:
            Ingredient ID if found, None otherwise
        """
        if not name:
            return None

        # Check cache
        name_key = name.lower().strip()
        if name_key in self._cache:
            return self._cache[name_key]

        # Build index if needed
        self._build_name_index()

        # Try exact match first
        if name_key in self._ingredients_by_name:
            ingredient_id = self._ingredients_by_name[name_key]
            self._cache[name_key] = ingredient_id
            return ingredient_id

        # Try fuzzy match
        best_match_id = None
        best_similarity = 0.0

        for db_name, db_id in self._ingredients_by_name.items():
            similarity = SequenceMatcher(None, name_key, db_name).ratio()

            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = db_id

        # Only use fuzzy match if above threshold
        if best_similarity >= similarity_threshold:
            logger.debug(f"Fuzzy matched '{name}' to ingredient ID {best_match_id} (similarity: {best_similarity:.2f})")
            self._cache[name_key] = best_match_id
            return best_match_id

        # No match found
        logger.warning(f"No ingredient match found for '{name}' (best similarity: {best_similarity:.2f})")
        self._cache[name_key] = None
        return None

    def clear_cache(self):
        """Clear the lookup cache and force re-indexing."""
        self._cache.clear()
        self._ingredients_by_name = None
