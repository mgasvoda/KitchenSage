"""
Token-optimized LLM-powered grocery list consolidation service.

Uses ultra-compact format and intelligent pre-processing to minimize token usage
while maintaining high-quality semantic consolidation.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from openai import OpenAI
from src.config import settings

logger = logging.getLogger(__name__)

# Ultra-minimal system prompt
CONSOLIDATION_SYSTEM_PROMPT = """Merge similar groceries, sum quantities, remove water/ice. Output JSON array: [["name",qty,"unit"], ...]"""


class GroceryConsolidationService:
    """
    Service for consolidating grocery list items using LLM with optimized token usage.

    Key optimizations:
    - Ultra-compact array format instead of objects
    - Pre-grouping for exact matches
    - Batch processing for large lists
    - Minimal system prompt
    - No ingredient_id in LLM (reconnected after)
    """

    def __init__(self):
        self._client: Optional[OpenAI] = None
        self.model = settings.llm.consolidation_model

    def _get_client(self) -> Optional[OpenAI]:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and not api_key.startswith('sk-placeholder'):
                self._client = OpenAI(api_key=api_key)
        return self._client

    def _pregroup_exact_matches(
        self,
        raw_items: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[int]]]:
        """
        Pre-group items with exact name + unit matches to reduce LLM workload.

        Args:
            raw_items: List of raw grocery items

        Returns:
            Tuple of (grouped_items, name_to_original_indices)
        """
        # Group by (name_lower, unit) key
        groups = defaultdict(list)

        for idx, item in enumerate(raw_items):
            name = item.get('name', '').lower().strip()
            unit = item.get('unit', 'piece').lower().strip()
            key = (name, unit)
            groups[key].append((idx, item))

        # Create grouped items with summed quantities
        grouped_items = []
        name_to_indices = {}

        for (name, unit), items in groups.items():
            if not name:
                continue

            # Sum quantities for exact matches
            total_quantity = sum(item.get('quantity', 0) for _, item in items)

            # Use the first item's original name (preserve case)
            original_name = items[0][1].get('name', name)

            grouped_item = {
                'name': original_name,
                'quantity': round(total_quantity, 2),
                'unit': unit
            }
            grouped_items.append(grouped_item)

            # Track which original indices contributed to this grouped item
            name_key = f"{original_name}|{unit}"
            name_to_indices[name_key] = [idx for idx, _ in items]

        logger.info(f"Pre-grouping reduced {len(raw_items)} items to {len(grouped_items)} items")
        return grouped_items, name_to_indices

    def _to_compact_format(self, items: List[Dict[str, Any]]) -> List[List]:
        """
        Convert items to ultra-compact array format for minimal tokens.

        Args:
            items: List of item dicts with name, quantity, unit

        Returns:
            List of [name, quantity, unit] arrays
        """
        compact = []
        for item in items:
            name = item.get('name', '')
            quantity = item.get('quantity', 0)
            unit = item.get('unit', 'piece')

            if name:  # Skip empty names
                compact.append([name, round(quantity, 2), unit])

        return compact

    def _from_compact_format(self, compact_items: List[List]) -> List[Dict[str, Any]]:
        """
        Convert compact array format back to dictionary format.

        Args:
            compact_items: List of [name, quantity, unit] arrays

        Returns:
            List of item dictionaries
        """
        items = []
        for compact in compact_items:
            if len(compact) >= 3:
                items.append({
                    'name': compact[0],
                    'quantity': float(compact[1]),
                    'unit': compact[2]
                })
        return items

    def _consolidate_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Consolidate a single batch of items using LLM.

        Args:
            items: List of items to consolidate (should be pre-grouped)

        Returns:
            Consolidated list of items
        """
        if not items:
            return []

        client = self._get_client()
        if not client:
            logger.warning("OpenAI API key not available, skipping LLM consolidation")
            return items

        try:
            # Convert to ultra-compact format
            compact_items = self._to_compact_format(items)

            # Use compact JSON (no spaces)
            items_json = json.dumps(compact_items, separators=(',', ':'))

            logger.debug(f"Sending {len(compact_items)} items to LLM ({len(items_json)} chars)")

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CONSOLIDATION_SYSTEM_PROMPT},
                    {"role": "user", "content": items_json}
                ],
                temperature=settings.llm.consolidation_temperature,
                max_completion_tokens=settings.llm.consolidation_max_tokens,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content

            # Parse response
            result = json.loads(result_text)

            # Handle both direct array and {"items": [...]} formats
            if isinstance(result, dict):
                compact_result = result.get("items", result.get("data", []))
            elif isinstance(result, list):
                compact_result = result
            else:
                logger.warning(f"Unexpected LLM response format: {type(result)}")
                return items

            # Convert back from compact format
            consolidated = self._from_compact_format(compact_result)

            logger.info(f"LLM consolidated {len(items)} items to {len(consolidated)} items")
            return consolidated

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM consolidation response: {e}")
            return items
        except Exception as e:
            logger.error(f"LLM consolidation failed: {e}")
            return items

    def consolidate_ingredients(
        self,
        raw_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Consolidate a list of raw grocery items using optimized LLM processing.

        This is the main entry point. Handles:
        - Pre-grouping for exact matches (if list is large enough)
        - Batch processing for very large lists
        - Ultra-compact format for token efficiency

        NOTE: ingredient_id is NOT preserved during consolidation.
        Caller must reconnect IDs after using ingredient name lookup.

        Args:
            raw_items: List of dicts with keys: name, quantity, unit
                      (ingredient_id is ignored)

        Returns:
            Consolidated list with name, quantity, unit only.
            Falls back to original items on any error.
        """
        if not raw_items:
            return []

        client = self._get_client()
        if not client:
            logger.warning("OpenAI API key not available, skipping LLM consolidation")
            # Return items without ingredient_id (consistent with success path)
            return [
                {
                    'name': item.get('name', ''),
                    'quantity': item.get('quantity', 0),
                    'unit': item.get('unit', 'piece')
                }
                for item in raw_items
            ]

        try:
            logger.info(f"Starting LLM consolidation for {len(raw_items)} items")

            # Pre-group exact matches if list is large enough
            if len(raw_items) >= settings.llm.consolidation_pregroup_threshold:
                items_to_consolidate, _ = self._pregroup_exact_matches(raw_items)
            else:
                # Just strip ingredient_id
                items_to_consolidate = [
                    {
                        'name': item.get('name', ''),
                        'quantity': item.get('quantity', 0),
                        'unit': item.get('unit', 'piece')
                    }
                    for item in raw_items
                ]

            # Batch processing for very large lists
            batch_size = settings.llm.consolidation_batch_size

            if len(items_to_consolidate) <= batch_size:
                # Single batch
                consolidated = self._consolidate_batch(items_to_consolidate)
            else:
                # Multiple batches
                logger.info(f"Processing {len(items_to_consolidate)} items in batches of {batch_size}")
                all_consolidated = []

                for i in range(0, len(items_to_consolidate), batch_size):
                    batch = items_to_consolidate[i:i + batch_size]
                    batch_result = self._consolidate_batch(batch)
                    all_consolidated.extend(batch_result)

                # Final pass to merge across batches (exact matches only, no LLM)
                consolidated, _ = self._pregroup_exact_matches(all_consolidated)

            logger.info(f"Final result: {len(raw_items)} items → {len(consolidated)} items")
            return consolidated

        except Exception as e:
            logger.error(f"Consolidation pipeline failed: {e}")
            # Return items without ingredient_id
            return [
                {
                    'name': item.get('name', ''),
                    'quantity': item.get('quantity', 0),
                    'unit': item.get('unit', 'piece')
                }
                for item in raw_items
            ]
