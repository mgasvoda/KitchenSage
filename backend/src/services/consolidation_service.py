"""
LLM-powered grocery list consolidation service.

Uses direct OpenAI API calls to intelligently consolidate grocery items by:
- Merging semantically similar items
- Combining quantities with unit handling
- Filtering out non-grocery items (water, ice, etc.)
"""

import os
import json
import logging
import re
from typing import List, Dict, Any, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

CONSOLIDATION_SYSTEM_PROMPT = """You are a grocery list optimizer. Given ingredients, output ONLY a JSON object with an "items" array.

Rules:
1. MERGE similar items (e.g., "chicken breast" + "boneless chicken" = "chicken breast")
2. SUM quantities for merged items
3. REMOVE: water, ice, items with no quantity
4. KEEP the ingredient_id from the larger quantity item when merging

Output format: {"items": [{"name": "...", "quantity": 1.0, "unit": "...", "ingredient_id": 123}, ...]}"""


class GroceryConsolidationService:
    """
    Service for consolidating grocery list items using LLM.

    Provides intelligent deduplication and consolidation of grocery items
    that goes beyond simple exact-match grouping.
    """

    def __init__(self):
        self._client: Optional[OpenAI] = None
        self.model = "gpt-4o-mini"

    def _get_client(self) -> Optional[OpenAI]:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and not api_key.startswith('sk-placeholder'):
                self._client = OpenAI(api_key=api_key)
        return self._client

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from text that might have markdown or extra content."""
        if not text:
            return None

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def consolidate_ingredients(
        self,
        raw_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Consolidate a list of raw grocery items using LLM.

        Args:
            raw_items: List of dicts with keys: name, quantity, unit, ingredient_id

        Returns:
            Consolidated list with merged quantities and filtered non-groceries.
            Falls back to original items on any error.
        """
        if not raw_items:
            return []

        client = self._get_client()
        if not client:
            logger.warning("OpenAI API key not available, skipping LLM consolidation")
            return raw_items

        try:
            # Prepare items for LLM - compact format to save tokens
            items_for_llm = [
                {
                    'name': item.get('name', ''),
                    'quantity': round(item.get('quantity', 0), 2),
                    'unit': item.get('unit', 'piece'),
                    'ingredient_id': item.get('ingredient_id')
                }
                for item in raw_items
            ]

            # Use compact JSON to reduce input tokens
            items_json = json.dumps(items_for_llm, separators=(',', ':'))

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CONSOLIDATION_SYSTEM_PROMPT},
                    {"role": "user", "content": items_json}
                ],
                temperature=0.1,
                max_tokens=4000,  # Increased for large meal plans
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = self._extract_json(result_text)

            if result is None:
                logger.error(f"Could not extract JSON from LLM response (length={len(result_text or '')})")
                return raw_items

            # Handle both {"items": [...]} and direct array formats
            if isinstance(result, dict):
                items = result.get("items", [])
            elif isinstance(result, list):
                items = result
            else:
                logger.warning(f"Unexpected LLM response format: {type(result)}")
                return raw_items

            # Validate each item has required fields
            validated_items = []
            for item in items:
                if 'name' in item and 'quantity' in item:
                    validated_item = {
                        'name': item['name'],
                        'quantity': float(item['quantity']),
                        'unit': item.get('unit', 'piece'),
                    }
                    # Only include ingredient_id if present
                    if item.get('ingredient_id') is not None:
                        validated_item['ingredient_id'] = item['ingredient_id']
                    validated_items.append(validated_item)

            logger.info(f"Consolidated {len(raw_items)} items into {len(validated_items)} items")
            return validated_items

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM consolidation response: {e}")
            return raw_items
        except Exception as e:
            logger.error(f"LLM consolidation failed: {e}")
            return raw_items  # Graceful degradation
