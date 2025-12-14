#!/usr/bin/env python3
"""
Paprika Recipe Import Script for KitchenSage

Imports recipes from a Paprika .paprikarecipes export file into the KitchenSage database.
Each .paprikarecipe file in the archive is a gzipped JSON file.

Usage:
    uv run python scripts/import_paprika.py <paprika_file.paprikarecipes>
    uv run python scripts/import_paprika.py <paprika_file.paprikarecipes> --dry-run
    uv run python scripts/import_paprika.py <paprika_file.paprikarecipes> --skip-duplicates
"""

import sys
import os
import zipfile
import gzip
import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.recipe import DifficultyLevel, CuisineType, DietaryTag, RecipeCreate
from src.models.ingredient import IngredientCategory, MeasurementUnit
from src.database.recipe_repository import RecipeRepository


class PaprikaImporter:
    """Imports Paprika recipes into KitchenSage database."""

    # Mapping of common units to our MeasurementUnit enum
    UNIT_MAPPING = {
        'cup': MeasurementUnit.CUP,
        'cups': MeasurementUnit.CUP,
        'c': MeasurementUnit.CUP,
        'tablespoon': MeasurementUnit.TABLESPOON,
        'tablespoons': MeasurementUnit.TABLESPOON,
        'tbsp': MeasurementUnit.TABLESPOON,
        'tbs': MeasurementUnit.TABLESPOON,
        'tb': MeasurementUnit.TABLESPOON,
        'T': MeasurementUnit.TABLESPOON,
        'teaspoon': MeasurementUnit.TEASPOON,
        'teaspoons': MeasurementUnit.TEASPOON,
        'tsp': MeasurementUnit.TEASPOON,
        'ts': MeasurementUnit.TEASPOON,
        't': MeasurementUnit.TEASPOON,
        'ounce': MeasurementUnit.OUNCE,
        'ounces': MeasurementUnit.OUNCE,
        'oz': MeasurementUnit.OUNCE,
        'pound': MeasurementUnit.POUND,
        'pounds': MeasurementUnit.POUND,
        'lb': MeasurementUnit.POUND,
        'lbs': MeasurementUnit.POUND,
        'gram': MeasurementUnit.GRAM,
        'grams': MeasurementUnit.GRAM,
        'g': MeasurementUnit.GRAM,
        'kilogram': MeasurementUnit.KILOGRAM,
        'kilograms': MeasurementUnit.KILOGRAM,
        'kg': MeasurementUnit.KILOGRAM,
        'milliliter': MeasurementUnit.MILLILITER,
        'milliliters': MeasurementUnit.MILLILITER,
        'ml': MeasurementUnit.MILLILITER,
        'liter': MeasurementUnit.LITER,
        'liters': MeasurementUnit.LITER,
        'l': MeasurementUnit.LITER,
        'pint': MeasurementUnit.PINT,
        'pints': MeasurementUnit.PINT,
        'pt': MeasurementUnit.PINT,
        'quart': MeasurementUnit.QUART,
        'quarts': MeasurementUnit.QUART,
        'qt': MeasurementUnit.QUART,
        'gallon': MeasurementUnit.GALLON,
        'gallons': MeasurementUnit.GALLON,
        'gal': MeasurementUnit.GALLON,
        'fl oz': MeasurementUnit.FLUID_OUNCE,
        'fluid ounce': MeasurementUnit.FLUID_OUNCE,
        'fluid ounces': MeasurementUnit.FLUID_OUNCE,
        'clove': MeasurementUnit.CLOVE,
        'cloves': MeasurementUnit.CLOVE,
        'piece': MeasurementUnit.PIECE,
        'pieces': MeasurementUnit.PIECE,
        'slice': MeasurementUnit.SLICE,
        'slices': MeasurementUnit.SLICE,
        'pinch': MeasurementUnit.PINCH,
        'dash': MeasurementUnit.DASH,
        'to taste': MeasurementUnit.TO_TASTE,
    }

    # Mapping of keywords to dietary tags
    DIETARY_TAG_KEYWORDS = {
        'vegetarian': DietaryTag.VEGETARIAN,
        'vegan': DietaryTag.VEGAN,
        'gluten free': DietaryTag.GLUTEN_FREE,
        'gluten-free': DietaryTag.GLUTEN_FREE,
        'dairy free': DietaryTag.DAIRY_FREE,
        'dairy-free': DietaryTag.DAIRY_FREE,
        'nut free': DietaryTag.NUT_FREE,
        'nut-free': DietaryTag.NUT_FREE,
        'low carb': DietaryTag.LOW_CARB,
        'low-carb': DietaryTag.LOW_CARB,
        'keto': DietaryTag.KETO,
        'paleo': DietaryTag.PALEO,
        'whole30': DietaryTag.WHOLE30,
        'low sodium': DietaryTag.LOW_SODIUM,
        'low-sodium': DietaryTag.LOW_SODIUM,
        'low fat': DietaryTag.LOW_FAT,
        'low-fat': DietaryTag.LOW_FAT,
        'high protein': DietaryTag.HIGH_PROTEIN,
        'high-protein': DietaryTag.HIGH_PROTEIN,
    }

    # Mapping of cuisines
    CUISINE_KEYWORDS = {
        'american': CuisineType.AMERICAN,
        'italian': CuisineType.ITALIAN,
        'mexican': CuisineType.MEXICAN,
        'chinese': CuisineType.CHINESE,
        'japanese': CuisineType.JAPANESE,
        'indian': CuisineType.INDIAN,
        'french': CuisineType.FRENCH,
        'thai': CuisineType.THAI,
        'greek': CuisineType.GREEK,
        'mediterranean': CuisineType.MEDITERRANEAN,
        'spanish': CuisineType.SPANISH,
        'german': CuisineType.GERMAN,
        'korean': CuisineType.KOREAN,
        'vietnamese': CuisineType.VIETNAMESE,
        'middle eastern': CuisineType.MIDDLE_EASTERN,
        'middle-eastern': CuisineType.MIDDLE_EASTERN,
        'african': CuisineType.AFRICAN,
    }

    def __init__(self, dry_run: bool = False, skip_duplicates: bool = False):
        """
        Initialize the importer.

        Args:
            dry_run: If True, parse recipes but don't import to database
            skip_duplicates: If True, skip recipes with duplicate names
        """
        self.dry_run = dry_run
        self.skip_duplicates = skip_duplicates
        self.repo = None if dry_run else RecipeRepository()
        self.stats = {
            'total': 0,
            'imported': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }

    def import_from_file(self, paprika_file: str) -> Dict[str, Any]:
        """
        Import all recipes from a Paprika export file.

        Args:
            paprika_file: Path to .paprikarecipes file

        Returns:
            Dictionary with import statistics
        """
        print(f"{'=' * 60}")
        print(f"Paprika Recipe Import {'(DRY RUN)' if self.dry_run else ''}")
        print(f"{'=' * 60}")
        print(f"File: {paprika_file}")
        print(f"Skip duplicates: {self.skip_duplicates}")
        print()

        if not os.path.exists(paprika_file):
            raise FileNotFoundError(f"File not found: {paprika_file}")

        # Extract and process recipes
        with zipfile.ZipFile(paprika_file, 'r') as zip_ref:
            recipe_files = [f for f in zip_ref.namelist() if f.endswith('.paprikarecipe')]
            self.stats['total'] = len(recipe_files)

            print(f"Found {len(recipe_files)} recipes to import\n")

            for i, recipe_file in enumerate(recipe_files, 1):
                print(f"[{i}/{len(recipe_files)}] Processing: {recipe_file}")

                try:
                    # Extract and decompress recipe
                    with zip_ref.open(recipe_file) as compressed_file:
                        recipe_data = gzip.decompress(compressed_file.read())
                        paprika_recipe = json.loads(recipe_data.decode('utf-8'))

                    # Convert and import
                    self._import_recipe(paprika_recipe)

                except Exception as e:
                    self.stats['failed'] += 1
                    error_msg = f"Error importing {recipe_file}: {str(e)}"
                    self.stats['errors'].append(error_msg)
                    print(f"  ❌ {error_msg}")

        # Print summary
        self._print_summary()

        return self.stats

    def _import_recipe(self, paprika_recipe: Dict[str, Any]) -> None:
        """Import a single Paprika recipe."""
        try:
            # Convert Paprika format to KitchenSage format
            recipe_data = self._convert_recipe(paprika_recipe)

            if self.dry_run:
                print(f"  ✓ Parsed: {recipe_data['name']}")
                self.stats['imported'] += 1
                return

            # Check for duplicates
            if self.skip_duplicates:
                existing = self.repo.find_by_criteria({'name': recipe_data['name']})
                if existing:
                    print(f"  ⊘ Skipped (duplicate): {recipe_data['name']}")
                    self.stats['skipped'] += 1
                    return

            # Import to database
            ingredients = recipe_data.pop('ingredients_data', [])

            # Create RecipeCreate model from dictionary
            recipe_create = RecipeCreate(**recipe_data)
            recipe = self.repo.create_recipe(recipe_create, ingredients)

            print(f"  ✓ Imported: {recipe.name} (ID: {recipe.id})")
            self.stats['imported'] += 1

        except Exception as e:
            raise Exception(f"Failed to convert recipe: {str(e)}")

    def _convert_recipe(self, paprika: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a Paprika recipe to KitchenSage format.

        Args:
            paprika: Paprika recipe dictionary

        Returns:
            Dictionary compatible with RecipeCreate model
        """
        # Parse times
        prep_time, cook_time = self._parse_times(paprika)

        # Parse ingredients
        ingredients_data = self._parse_ingredients(paprika.get('ingredients', ''))

        # Parse instructions
        instructions = self._parse_instructions(paprika.get('directions', ''))

        # Detect dietary tags and cuisine
        dietary_tags = self._detect_dietary_tags(paprika)
        cuisine = self._detect_cuisine(paprika)

        # Detect difficulty
        difficulty = self._detect_difficulty(paprika)

        # Parse servings
        servings = self._parse_servings(paprika.get('servings', ''))

        # Parse and truncate notes and description if needed
        notes = paprika.get('notes', '').strip() or None
        if notes and len(notes) > 500:
            notes = notes[:497] + "..."

        description = paprika.get('description', '').strip() or None
        if description and len(description) > 1000:
            description = description[:997] + "..."

        # Build recipe data
        recipe_data = {
            'name': paprika.get('name', 'Untitled Recipe').strip(),
            'description': description,
            'prep_time': prep_time,
            'cook_time': cook_time,
            'servings': servings,
            'difficulty': difficulty,
            'cuisine': cuisine,
            'dietary_tags': dietary_tags,
            'instructions': instructions,
            'notes': notes,
            'source': paprika.get('source', '').strip() or None,
            'image_url': paprika.get('image_url') or paprika.get('source_url') or None,
            'ingredients_data': ingredients_data  # Temporary key for processing
        }

        return recipe_data

    def _parse_times(self, paprika: Dict[str, Any]) -> Tuple[int, int]:
        """
        Parse prep time and cook time from Paprika recipe.

        Returns:
            Tuple of (prep_time, cook_time) in minutes
        """
        prep_time = 0
        cook_time = 0

        # Try to parse prep_time field
        prep_str = paprika.get('prep_time', '').strip()
        if prep_str:
            prep_time = self._parse_time_string(prep_str)

        # Try to parse cook_time field
        cook_str = paprika.get('cook_time', '').strip()
        if cook_str:
            cook_time = self._parse_time_string(cook_str)

        # If neither is set, try to parse total_time and split it
        if prep_time == 0 and cook_time == 0:
            total_str = paprika.get('total_time', '').strip()
            if total_str:
                total_time = self._parse_time_string(total_str)
                # Estimate: 30% prep, 70% cook
                prep_time = int(total_time * 0.3)
                cook_time = int(total_time * 0.7)

        # Defaults if still zero
        if prep_time == 0:
            prep_time = 15
        if cook_time == 0:
            cook_time = 30

        return prep_time, cook_time

    def _parse_time_string(self, time_str: str) -> int:
        """
        Parse a time string like '1 hr 30 minutes' or '45 min' to minutes.

        Args:
            time_str: Time string

        Returns:
            Time in minutes
        """
        if not time_str:
            return 0

        time_str = time_str.lower()
        total_minutes = 0

        # Parse hours
        hours_match = re.search(r'(\d+)\s*(hr|hour|hours)', time_str)
        if hours_match:
            total_minutes += int(hours_match.group(1)) * 60

        # Parse minutes
        minutes_match = re.search(r'(\d+)\s*(min|minute|minutes)', time_str)
        if minutes_match:
            total_minutes += int(minutes_match.group(1))

        # If no match found, try to extract any number
        if total_minutes == 0:
            number_match = re.search(r'(\d+)', time_str)
            if number_match:
                total_minutes = int(number_match.group(1))

        return total_minutes

    def _parse_servings(self, servings_str: str) -> int:
        """
        Parse servings from string.

        Args:
            servings_str: Servings string

        Returns:
            Number of servings (defaults to 4)
        """
        if not servings_str:
            return 4

        # Try to extract a number
        match = re.search(r'(\d+)', str(servings_str))
        if match:
            servings = int(match.group(1))
            return max(1, min(50, servings))  # Clamp to valid range

        return 4

    def _parse_ingredients(self, ingredients_str: str) -> List[Dict[str, Any]]:
        """
        Parse Paprika ingredients string into structured ingredient data.

        Args:
            ingredients_str: Multi-line string with ingredients

        Returns:
            List of ingredient dictionaries
        """
        if not ingredients_str:
            return []

        ingredients = []
        lines = ingredients_str.split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('---') or line.startswith('**'):
                continue

            # Parse ingredient line (e.g., "2 cups flour, sifted")
            ingredient_data = self._parse_ingredient_line(line)
            if ingredient_data:
                ingredients.append(ingredient_data)

        return ingredients

    def _parse_ingredient_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single ingredient line.

        Args:
            line: Ingredient line like "2 cups flour, sifted"

        Returns:
            Dictionary with ingredient data or None if parsing fails
        """
        # Pattern: [quantity] [unit] ingredient [, notes]
        # Examples:
        # - "2 cups flour"
        # - "1/2 tsp salt"
        # - "3 chicken breasts, boneless"
        # - "pinch of sugar"

        # Special case: lines that are lists of ingredients without quantities
        # (e.g., "Cilantro, chopped onions, scallions, cheese for serving")
        # Take just the first item
        if ',' in line and not re.search(r'^\d', line):
            # Check if this looks like a list (multiple commas, no quantity at start)
            comma_count = line.count(',')
            if comma_count >= 2:
                # It's likely a list - take first item only, rest goes to notes
                first_item = line.split(',')[0].strip()
                rest_items = ', '.join(line.split(',')[1:]).strip()
                return {
                    'name': first_item.lower()[:100],  # Truncate if needed
                    'quantity': 1.0,
                    'unit': MeasurementUnit.TO_TASTE.value,
                    'notes': rest_items[:200] if rest_items else None,  # Truncate notes too
                    'category': self._detect_ingredient_category(first_item.lower())
                }

        # Try to extract quantity and unit
        pattern = r'^([\d\./\s]+)?\s*([a-zA-Z\s]+?)?\s+(.+)$'
        match = re.match(pattern, line)

        if not match:
            # No quantity/unit found, treat entire line as ingredient name
            name = line.lower()
            if len(name) > 100:
                name = name[:97] + "..."
            return {
                'name': name,
                'quantity': 1.0,
                'unit': MeasurementUnit.ITEM.value,
                'notes': None,
                'category': IngredientCategory.OTHER
            }

        quantity_str, unit_str, rest = match.groups()

        # Parse quantity (handle fractions like "1/2", "1 1/2")
        quantity = self._parse_quantity(quantity_str) if quantity_str else 1.0

        # Parse unit
        unit = self._parse_unit(unit_str) if unit_str else MeasurementUnit.ITEM

        # Split rest into name and notes
        if ',' in rest:
            name, notes = rest.split(',', 1)
            name = name.strip().lower()
            notes = notes.strip()
            # Truncate notes if too long
            if notes and len(notes) > 200:
                notes = notes[:197] + "..."
        else:
            name = rest.strip().lower()
            notes = None

        # Truncate long ingredient names (max 100 chars)
        if len(name) > 100:
            name = name[:97] + "..."

        # Detect ingredient category
        category = self._detect_ingredient_category(name)

        return {
            'name': name,
            'quantity': quantity,
            'unit': unit.value,
            'notes': notes,
            'category': category
        }

    def _parse_quantity(self, quantity_str: str) -> float:
        """
        Parse quantity string handling fractions.

        Args:
            quantity_str: Quantity like "2", "1/2", "1 1/2"

        Returns:
            Float quantity
        """
        quantity_str = quantity_str.strip()

        # Handle mixed fractions like "1 1/2"
        if ' ' in quantity_str:
            parts = quantity_str.split()
            if len(parts) == 2:
                whole = float(parts[0])
                fraction = self._parse_fraction(parts[1])
                return whole + fraction

        # Handle simple fractions
        if '/' in quantity_str:
            return self._parse_fraction(quantity_str)

        # Handle decimals and whole numbers
        try:
            return float(quantity_str)
        except ValueError:
            return 1.0

    def _parse_fraction(self, fraction_str: str) -> float:
        """Parse a fraction string like '1/2' to float."""
        try:
            parts = fraction_str.split('/')
            if len(parts) == 2:
                return float(parts[0]) / float(parts[1])
        except (ValueError, ZeroDivisionError):
            pass
        return 1.0

    def _parse_unit(self, unit_str: str) -> MeasurementUnit:
        """
        Parse unit string to MeasurementUnit enum.

        Args:
            unit_str: Unit string like "cup", "tbsp", etc.

        Returns:
            MeasurementUnit enum value
        """
        if not unit_str:
            return MeasurementUnit.ITEM

        unit_str = unit_str.strip().lower()

        # Direct mapping
        if unit_str in self.UNIT_MAPPING:
            return self.UNIT_MAPPING[unit_str]

        # Fuzzy matching (e.g., "cup" matches "cups")
        for key, value in self.UNIT_MAPPING.items():
            if unit_str.startswith(key) or key.startswith(unit_str):
                return value

        return MeasurementUnit.ITEM

    def _parse_instructions(self, directions_str: str) -> List[str]:
        """
        Parse instructions from Paprika directions.

        Args:
            directions_str: Multi-line directions string

        Returns:
            List of instruction steps
        """
        if not directions_str:
            return ["No instructions provided"]

        # Split by common delimiters
        instructions = []

        # Try splitting by numbered steps (1., 2., etc.)
        numbered_pattern = r'\d+\.\s+'
        if re.search(numbered_pattern, directions_str):
            steps = re.split(numbered_pattern, directions_str)
            instructions = [step.strip() for step in steps if step.strip()]
        # Try splitting by double newlines (paragraphs)
        elif '\n\n' in directions_str:
            instructions = [step.strip() for step in directions_str.split('\n\n') if step.strip()]
        # Try splitting by single newlines
        elif '\n' in directions_str:
            instructions = [step.strip() for step in directions_str.split('\n') if step.strip()]
        else:
            # Single paragraph - try to split by sentences
            sentences = re.split(r'(?<=[.!?])\s+', directions_str)
            instructions = [s.strip() for s in sentences if s.strip()]

        # Ensure we have at least one instruction
        if not instructions:
            instructions = [directions_str.strip()]

        return instructions

    def _detect_dietary_tags(self, paprika: Dict[str, Any]) -> List[DietaryTag]:
        """Detect dietary tags from recipe content."""
        tags = []

        # Search in name, description, notes, categories
        search_text = ' '.join([
            paprika.get('name', ''),
            paprika.get('description', ''),
            paprika.get('notes', ''),
            ' '.join(paprika.get('categories', []))
        ]).lower()

        for keyword, tag in self.DIETARY_TAG_KEYWORDS.items():
            if keyword in search_text:
                tags.append(tag)

        return tags

    def _detect_cuisine(self, paprika: Dict[str, Any]) -> CuisineType:
        """Detect cuisine type from recipe content."""
        search_text = ' '.join([
            paprika.get('name', ''),
            paprika.get('description', ''),
            ' '.join(paprika.get('categories', []))
        ]).lower()

        for keyword, cuisine in self.CUISINE_KEYWORDS.items():
            if keyword in search_text:
                return cuisine

        return CuisineType.OTHER

    def _detect_difficulty(self, paprika: Dict[str, Any]) -> DifficultyLevel:
        """Detect difficulty level from recipe."""
        difficulty_str = paprika.get('difficulty', '').lower()

        if 'easy' in difficulty_str or 'simple' in difficulty_str:
            return DifficultyLevel.EASY
        elif 'hard' in difficulty_str or 'difficult' in difficulty_str or 'advanced' in difficulty_str:
            return DifficultyLevel.HARD
        elif 'medium' in difficulty_str or 'moderate' in difficulty_str:
            return DifficultyLevel.MEDIUM

        # Heuristic: if many steps or long cook time, consider medium/hard
        directions = paprika.get('directions', '')
        instruction_count = len(directions.split('\n'))

        if instruction_count > 10:
            return DifficultyLevel.HARD
        elif instruction_count > 5:
            return DifficultyLevel.MEDIUM

        return DifficultyLevel.EASY

    def _detect_ingredient_category(self, name: str) -> IngredientCategory:
        """Detect ingredient category from name."""
        name = name.lower()

        # Meat keywords
        if any(word in name for word in ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'sausage', 'bacon', 'ham']):
            return IngredientCategory.MEAT

        # Seafood keywords
        if any(word in name for word in ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'seafood']):
            return IngredientCategory.SEAFOOD

        # Dairy keywords
        if any(word in name for word in ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'sour cream']):
            return IngredientCategory.DAIRY

        # Produce keywords
        if any(word in name for word in ['tomato', 'onion', 'garlic', 'pepper', 'lettuce', 'carrot', 'celery',
                                          'potato', 'spinach', 'broccoli', 'cucumber', 'zucchini', 'mushroom',
                                          'apple', 'banana', 'orange', 'lemon', 'lime', 'berry']):
            return IngredientCategory.PRODUCE

        # Spices
        if any(word in name for word in ['salt', 'pepper', 'paprika', 'cumin', 'oregano', 'basil', 'thyme',
                                          'rosemary', 'cinnamon', 'nutmeg', 'ginger', 'cayenne']):
            return IngredientCategory.SPICES

        # Grains
        if any(word in name for word in ['rice', 'pasta', 'noodle', 'bread', 'flour', 'oat', 'quinoa', 'barley']):
            return IngredientCategory.GRAINS

        # Legumes
        if any(word in name for word in ['bean', 'lentil', 'chickpea', 'pea']):
            return IngredientCategory.LEGUMES

        # Baking
        if any(word in name for word in ['sugar', 'baking powder', 'baking soda', 'yeast', 'vanilla']):
            return IngredientCategory.BAKING

        # Condiments
        if any(word in name for word in ['oil', 'vinegar', 'sauce', 'mustard', 'ketchup', 'mayo', 'soy sauce']):
            return IngredientCategory.CONDIMENTS

        # Canned
        if 'canned' in name or 'can of' in name:
            return IngredientCategory.CANNED

        # Frozen
        if 'frozen' in name:
            return IngredientCategory.FROZEN

        return IngredientCategory.OTHER

    def _print_summary(self) -> None:
        """Print import summary."""
        print()
        print(f"{'=' * 60}")
        print(f"Import Summary")
        print(f"{'=' * 60}")
        print(f"Total recipes: {self.stats['total']}")
        print(f"Imported: {self.stats['imported']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Failed: {self.stats['failed']}")
        print()

        if self.stats['errors']:
            print("Errors:")
            for error in self.stats['errors']:
                print(f"  - {error}")
            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Import recipes from Paprika export file to KitchenSage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import all recipes
  uv run python scripts/import_paprika.py recipes.paprikarecipes

  # Dry run (test import without writing to database)
  uv run python scripts/import_paprika.py recipes.paprikarecipes --dry-run

  # Skip recipes with duplicate names
  uv run python scripts/import_paprika.py recipes.paprikarecipes --skip-duplicates
        """
    )

    parser.add_argument('paprika_file', help='Path to .paprikarecipes file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Parse recipes but do not import to database')
    parser.add_argument('--skip-duplicates', action='store_true',
                       help='Skip recipes with duplicate names')

    args = parser.parse_args()

    try:
        importer = PaprikaImporter(
            dry_run=args.dry_run,
            skip_duplicates=args.skip_duplicates
        )
        importer.import_from_file(args.paprika_file)

        # Exit with error code if there were failures
        if importer.stats['failed'] > 0:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
