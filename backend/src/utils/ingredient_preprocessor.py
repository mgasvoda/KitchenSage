"""
Ingredient pre-processing utilities for normalization before LLM consolidation.

Handles:
- Fraction parsing (1/4 -> 0.25)
- Unit normalization (ounce -> oz)
- Container size extraction
- Quantity extraction from names
"""

import re
import logging
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


# Unit aliases mapping - normalize to standard abbreviations
UNIT_ALIASES = {
    # Volume - full words to abbreviations
    'ounce': 'oz',
    'ounces': 'oz',
    'fluid ounce': 'fl oz',
    'fluid ounces': 'fl oz',
    'tablespoon': 'tbsp',
    'tablespoons': 'tbsp',
    'teaspoon': 'tsp',
    'teaspoons': 'tsp',
    'cup': 'cup',
    'cups': 'cup',
    'pint': 'pint',
    'pints': 'pint',
    'quart': 'quart',
    'quarts': 'quart',
    'gallon': 'gallon',
    'gallons': 'gallon',
    'milliliter': 'ml',
    'milliliters': 'ml',
    'liter': 'liter',
    'liters': 'liter',
    'litre': 'liter',
    'litres': 'liter',

    # Weight
    'pound': 'lb',
    'pounds': 'lb',
    'gram': 'g',
    'grams': 'g',
    'kilogram': 'kg',
    'kilograms': 'kg',

    # Count
    'piece': 'piece',
    'pieces': 'piece',
    'item': 'item',
    'items': 'item',
    'clove': 'clove',
    'cloves': 'clove',
    'slice': 'slice',
    'slices': 'slice',
    'whole': 'piece',

    # Can/Container
    'can': 'can',
    'cans': 'can',
    'jar': 'jar',
    'jars': 'jar',
    'bottle': 'bottle',
    'bottles': 'bottle',
    'package': 'package',
    'packages': 'package',
    'pkg': 'package',
    'box': 'box',
    'boxes': 'box',
    'bunch': 'bunch',
    'bunches': 'bunch',
    'head': 'head',
    'heads': 'head',
    'stalk': 'stalk',
    'stalks': 'stalk',
    'sprig': 'sprig',
    'sprigs': 'sprig',
}


def parse_fraction(value: str) -> Optional[float]:
    """
    Parse a fraction string to a float.

    Examples:
        "1/4" -> 0.25
        "1 1/2" -> 1.5
        "3/4" -> 0.75
        "2" -> 2.0

    Args:
        value: String potentially containing a fraction

    Returns:
        Float value or None if parsing fails
    """
    if not value or not isinstance(value, str):
        return None

    value = value.strip()

    # Handle mixed numbers like "1 1/2"
    mixed_match = re.match(r'^(\d+)\s+(\d+)/(\d+)$', value)
    if mixed_match:
        whole = int(mixed_match.group(1))
        numerator = int(mixed_match.group(2))
        denominator = int(mixed_match.group(3))
        if denominator == 0:
            return None
        return whole + (numerator / denominator)

    # Handle simple fractions like "1/4"
    fraction_match = re.match(r'^(\d+)/(\d+)$', value)
    if fraction_match:
        numerator = int(fraction_match.group(1))
        denominator = int(fraction_match.group(2))
        if denominator == 0:
            return None
        return numerator / denominator

    # Handle decimal or integer
    try:
        return float(value)
    except ValueError:
        return None


def normalize_unit(unit: str) -> str:
    """
    Normalize unit to standard abbreviation.

    Examples:
        "ounces" -> "oz"
        "tablespoon" -> "tbsp"
        "pounds" -> "lb"

    Args:
        unit: Unit string to normalize

    Returns:
        Normalized unit string
    """
    if not unit:
        return 'piece'

    unit_lower = unit.lower().strip()
    return UNIT_ALIASES.get(unit_lower, unit_lower)


def extract_container_info(name: str) -> Tuple[str, Optional[float], Optional[str], Optional[str]]:
    """
    Extract container size information from ingredient name.

    Examples:
        "crushed tomatoes (28 oz can)" -> ("crushed tomatoes", 28.0, "oz", "can")
        "chicken broth (32 oz)" -> ("chicken broth", 32.0, "oz", None)
        "diced tomatoes" -> ("diced tomatoes", None, None, None)
        "crushed tomatoes (28-ounces)" -> ("crushed tomatoes", 28.0, "oz", None)

    Args:
        name: Ingredient name potentially containing container info

    Returns:
        Tuple of (clean_name, size, size_unit, container_type)
    """
    if not name:
        return (name, None, None, None)

    # Pattern for "(XX oz can)" or "(XX-oz)" or "(XX oz)" or "(XX-ounces)"
    # Supports: (28 oz can), (10 oz), (28-ounces), (14.5 oz can)
    container_pattern = r'\s*\((\d+(?:\.\d+)?)\s*-?\s*(oz|ounce|ounces|lb|pound|pounds|g|gram|grams|ml|liter|liters|fl oz)(?:\s+(can|cans|jar|jars|bottle|bottles|box|boxes|package|pkg))?\)'

    match = re.search(container_pattern, name, re.IGNORECASE)

    if match:
        clean_name = re.sub(container_pattern, '', name, flags=re.IGNORECASE).strip()
        size = float(match.group(1))
        size_unit = normalize_unit(match.group(2))
        container_type = normalize_unit(match.group(3)) if match.group(3) else None
        return (clean_name, size, size_unit, container_type)

    return (name, None, None, None)


def extract_quantity_from_name(name: str) -> Tuple[str, Optional[float], Optional[str]]:
    """
    Extract quantity embedded in ingredient name.

    Examples:
        "1/4 cup flour" -> ("flour", 0.25, "cup")
        "2 tbsp olive oil" -> ("olive oil", 2.0, "tbsp")
        "salt" -> ("salt", None, None)
        "1 1/2 cups sugar" -> ("sugar", 1.5, "cup")

    Args:
        name: Ingredient name potentially containing quantity

    Returns:
        Tuple of (clean_name, quantity, unit)
    """
    if not name:
        return (name, None, None)

    # Pattern for quantity at start: "1/4 cup flour" or "2 tbsp oil" or "1 1/2 cups sugar"
    # Matches: fraction, mixed number, or decimal followed by unit
    qty_pattern = r'^(\d+(?:/\d+)?(?:\s+\d+/\d+)?|\d+(?:\.\d+)?)\s+(cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons|oz|ounce|ounces|lb|pound|pounds|g|gram|grams|ml|liter|liters)\s+(.+)$'

    match = re.match(qty_pattern, name, re.IGNORECASE)

    if match:
        qty_str = match.group(1)
        unit = normalize_unit(match.group(2))
        clean_name = match.group(3).strip()
        quantity = parse_fraction(qty_str)
        return (clean_name, quantity, unit)

    return (name, None, None)


def clean_ingredient_name(name: str) -> str:
    """
    Clean ingredient name by removing common noise.

    - Removes leading/trailing whitespace
    - Removes multiple spaces
    - Removes trailing commas

    Args:
        name: Raw ingredient name

    Returns:
        Cleaned name
    """
    if not name:
        return name

    # Strip whitespace
    cleaned = name.strip()

    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # Remove trailing punctuation
    cleaned = cleaned.rstrip(',;:.')

    return cleaned


def preprocess_ingredient(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess a single ingredient item for consolidation.

    Applies:
    - Unit normalization
    - Container info extraction (converts container size to actual amount)
    - Quantity extraction from name if missing
    - Name cleaning

    Args:
        item: Dictionary with 'name', 'quantity', 'unit' keys

    Returns:
        Preprocessed item dictionary
    """
    result = item.copy()

    # Get original values
    name = result.get('name', '')
    quantity = result.get('quantity', 0)
    unit = result.get('unit', 'piece')

    # Clean the name
    name = clean_ingredient_name(name)

    # Normalize unit first
    normalized_unit = normalize_unit(unit)

    # Extract container info if present
    clean_name, container_size, size_unit, container_type = extract_container_info(name)

    if container_size is not None:
        # If we extracted container size and unit is a container type, convert
        if normalized_unit in ['can', 'jar', 'bottle', 'box', 'package']:
            # Convert: 2 cans of (28 oz) tomatoes = 56 oz tomatoes
            result['name'] = clean_name
            result['quantity'] = round(quantity * container_size, 2)
            result['unit'] = size_unit
            logger.debug(
                f"Converted container: {quantity} {unit} of '{name}' -> "
                f"{result['quantity']} {result['unit']} of '{clean_name}'"
            )
            return result
        else:
            # Just clean the name, keep original quantity/unit
            result['name'] = clean_name

    # If quantity is 0 or missing, try to extract from name
    if quantity == 0 or quantity is None:
        extracted_name, extracted_qty, extracted_unit = extract_quantity_from_name(name)
        if extracted_qty is not None:
            result['name'] = extracted_name
            result['quantity'] = extracted_qty
            result['unit'] = extracted_unit
            logger.debug(
                f"Extracted quantity from name: '{name}' -> "
                f"{extracted_qty} {extracted_unit} of '{extracted_name}'"
            )
            return result

    # Apply normalized unit
    result['unit'] = normalized_unit
    result['name'] = clean_name if container_size else name

    return result


def preprocess_ingredients(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Preprocess a list of ingredients.

    Args:
        items: List of ingredient dictionaries

    Returns:
        List of preprocessed ingredient dictionaries
    """
    return [preprocess_ingredient(item) for item in items]
