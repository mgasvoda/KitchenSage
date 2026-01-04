"""
Tests for GroceryConsolidationService covering known failure modes.

Test Categories:
1. Container size consolidation - different can sizes should combine
2. Cross-metric consolidation - pieces vs cups should convert to pieces
3. Fraction parsing - 1/4, 1/2, mixed numbers should parse correctly
4. Derivative matching - zest, juice, crumbled should merge with base ingredient
5. Regression tests - ensure existing functionality still works
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.consolidation_service import GroceryConsolidationService


@pytest.fixture
def service():
    """Create a GroceryConsolidationService instance."""
    return GroceryConsolidationService()


@pytest.fixture
def mock_openai_response():
    """Factory for creating mock OpenAI responses."""
    def _create_response(content):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(content)
        return mock_response
    return _create_response


class TestContainerSizeConsolidation:
    """Tests for handling different container sizes of same ingredient."""

    def test_same_ingredient_different_can_sizes_oz(self, service, mock_openai_response):
        """10 oz and 28 oz cans of crushed tomatoes should consolidate."""
        raw_items = [
            {'name': 'crushed tomatoes (10 oz can)', 'quantity': 1, 'unit': 'can'},
            {'name': 'crushed tomatoes (28 oz can)', 'quantity': 1, 'unit': 'can'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["crushed tomatoes", 38, "oz"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'tomato' in result[0]['name'].lower()
        # Should have combined to total ounces
        assert result[0]['quantity'] == pytest.approx(38, rel=0.1)

    def test_same_ingredient_different_can_sizes_ounces_spelling(self, service, mock_openai_response):
        """Handle different spellings: oz vs ounces."""
        raw_items = [
            {'name': 'crushed tomatoes (10 oz)', 'quantity': 1, 'unit': 'can'},
            {'name': 'crushed tomatoes (28-ounces)', 'quantity': 1, 'unit': 'can'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["crushed tomatoes", 38, "oz"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'tomato' in result[0]['name'].lower()

    def test_diced_tomatoes_different_sizes(self, service, mock_openai_response):
        """Diced tomatoes in different can sizes should merge."""
        raw_items = [
            {'name': 'diced tomatoes', 'quantity': 14.5, 'unit': 'oz'},
            {'name': 'diced tomatoes', 'quantity': 28, 'unit': 'oz'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["diced tomatoes", 42.5, "oz"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert result[0]['quantity'] == pytest.approx(42.5, rel=0.1)

    def test_oz_and_lb_conversion(self, service, mock_openai_response):
        """Ounces and pounds should convert (1 lb = 16 oz)."""
        raw_items = [
            {'name': 'ground beef', 'quantity': 8, 'unit': 'oz'},
            {'name': 'ground beef', 'quantity': 1, 'unit': 'lb'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            # Should combine to 24 oz or 1.5 lb
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["ground beef", 1.5, "lb"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'beef' in result[0]['name'].lower()


class TestCrossMetricConsolidation:
    """Tests for handling ingredients measured in incompatible units."""

    def test_onion_pieces_vs_cups(self, service, mock_openai_response):
        """1.5 onions and 0.25 cups onion should convert to pieces."""
        raw_items = [
            {'name': 'onion', 'quantity': 1.5, 'unit': 'piece'},
            {'name': 'onion, diced', 'quantity': 0.25, 'unit': 'cup'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            # 0.25 cup ~= 0.25 onion, so total ~1.75-2 onions
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["onion", 2, "piece"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'onion' in result[0]['name'].lower()
        # Should have converted to pieces and combined
        assert result[0]['quantity'] >= 1.5

    def test_garlic_cloves_vs_minced(self, service, mock_openai_response):
        """Garlic cloves and minced garlic should consolidate."""
        raw_items = [
            {'name': 'garlic', 'quantity': 4, 'unit': 'clove'},
            {'name': 'garlic, minced', 'quantity': 2, 'unit': 'tbsp'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            # 1 clove ~= 0.5 tbsp, so 2 tbsp ~= 4 cloves
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["garlic", 8, "clove"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'garlic' in result[0]['name'].lower()

    def test_bell_pepper_pieces_vs_cups(self, service, mock_openai_response):
        """Bell pepper pieces and diced cups should consolidate."""
        raw_items = [
            {'name': 'bell pepper', 'quantity': 2, 'unit': 'piece'},
            {'name': 'bell pepper, diced', 'quantity': 0.5, 'unit': 'cup'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["bell pepper", 3, "piece"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'pepper' in result[0]['name'].lower()

    def test_carrot_pieces_vs_cups(self, service, mock_openai_response):
        """Carrots in pieces and cups should consolidate to pieces."""
        raw_items = [
            {'name': 'carrot', 'quantity': 3, 'unit': 'piece'},
            {'name': 'carrots, sliced', 'quantity': 1, 'unit': 'cup'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["carrot", 4, "piece"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'carrot' in result[0]['name'].lower()


class TestFractionParsing:
    """Tests for handling fractional quantities."""

    def test_quarter_values_sum_correctly(self, service):
        """Verify 0.25 + 0.5 sums correctly in pre-grouping."""
        raw_items = [
            {'name': 'flour', 'quantity': 0.25, 'unit': 'cup'},
            {'name': 'flour', 'quantity': 0.5, 'unit': 'cup'},
        ]

        # Pre-grouping should sum these
        grouped, _ = service._pregroup_exact_matches(raw_items)

        assert len(grouped) == 1
        assert grouped[0]['quantity'] == pytest.approx(0.75, rel=0.01)

    def test_mixed_decimal_values(self, service):
        """Handle mixed decimal quantities like 1.5 + 0.5."""
        raw_items = [
            {'name': 'butter', 'quantity': 1.5, 'unit': 'cup'},
            {'name': 'butter', 'quantity': 0.5, 'unit': 'cup'},
        ]

        grouped, _ = service._pregroup_exact_matches(raw_items)

        assert len(grouped) == 1
        assert grouped[0]['quantity'] == pytest.approx(2.0, rel=0.01)

    def test_small_fractions_accumulate(self, service):
        """Small fractions like 0.125 (1/8) should accumulate."""
        raw_items = [
            {'name': 'vanilla extract', 'quantity': 0.125, 'unit': 'tsp'},
            {'name': 'vanilla extract', 'quantity': 0.125, 'unit': 'tsp'},
            {'name': 'vanilla extract', 'quantity': 0.25, 'unit': 'tsp'},
        ]

        grouped, _ = service._pregroup_exact_matches(raw_items)

        assert len(grouped) == 1
        assert grouped[0]['quantity'] == pytest.approx(0.5, rel=0.01)

    def test_thirds_sum_correctly(self, service):
        """Handle third fractions (0.33, 0.67)."""
        raw_items = [
            {'name': 'milk', 'quantity': 0.33, 'unit': 'cup'},
            {'name': 'milk', 'quantity': 0.67, 'unit': 'cup'},
        ]

        grouped, _ = service._pregroup_exact_matches(raw_items)

        assert len(grouped) == 1
        assert grouped[0]['quantity'] == pytest.approx(1.0, rel=0.05)


class TestDerivativeMatching:
    """Tests for ingredient derivatives (zest, juice, crumbled, etc.)."""

    def test_lemon_and_lemon_zest(self, service, mock_openai_response):
        """Lemon zest should increase the lemon count."""
        raw_items = [
            {'name': 'lemon', 'quantity': 2, 'unit': 'piece'},
            {'name': 'lemon zest', 'quantity': 1, 'unit': 'tbsp'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            # 1 tbsp zest ~= 1 lemon, so need 3 total
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["lemon", 3, "piece"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'lemon' in result[0]['name'].lower()
        assert result[0]['quantity'] >= 2  # At least original count

    def test_lemon_and_lemon_juice(self, service, mock_openai_response):
        """Lemon juice should increase the lemon count."""
        raw_items = [
            {'name': 'lemon', 'quantity': 1, 'unit': 'piece'},
            {'name': 'lemon juice', 'quantity': 3, 'unit': 'tbsp'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            # 3 tbsp juice ~= 1 lemon
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["lemon", 2, "piece"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'lemon' in result[0]['name'].lower()

    def test_lime_zest_and_juice(self, service, mock_openai_response):
        """Lime with both zest and juice should consolidate."""
        raw_items = [
            {'name': 'lime', 'quantity': 2, 'unit': 'piece'},
            {'name': 'lime zest', 'quantity': 1, 'unit': 'tsp'},
            {'name': 'lime juice', 'quantity': 2, 'unit': 'tbsp'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["lime", 4, "piece"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'lime' in result[0]['name'].lower()

    def test_blue_cheese_and_crumbled(self, service, mock_openai_response):
        """Blue cheese and crumbled blue cheese are the same."""
        raw_items = [
            {'name': 'blue cheese', 'quantity': 4, 'unit': 'oz'},
            {'name': 'crumbled blue cheese', 'quantity': 2, 'unit': 'oz'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["blue cheese", 6, "oz"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'blue cheese' in result[0]['name'].lower()
        assert result[0]['quantity'] == pytest.approx(6, rel=0.1)

    def test_parmesan_grated_and_block(self, service, mock_openai_response):
        """Grated parmesan and parmesan block should consolidate."""
        raw_items = [
            {'name': 'parmesan cheese, grated', 'quantity': 0.5, 'unit': 'cup'},
            {'name': 'parmesan', 'quantity': 2, 'unit': 'oz'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["parmesan cheese", 4, "oz"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'parmesan' in result[0]['name'].lower()

    def test_cheddar_shredded_and_block(self, service, mock_openai_response):
        """Shredded cheddar and cheddar block should consolidate."""
        raw_items = [
            {'name': 'cheddar cheese', 'quantity': 4, 'unit': 'oz'},
            {'name': 'shredded cheddar', 'quantity': 1, 'unit': 'cup'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["cheddar cheese", 8, "oz"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'cheddar' in result[0]['name'].lower()

    def test_orange_and_orange_zest(self, service, mock_openai_response):
        """Orange zest should increase orange count."""
        raw_items = [
            {'name': 'orange', 'quantity': 2, 'unit': 'piece'},
            {'name': 'orange zest', 'quantity': 2, 'unit': 'tbsp'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["orange", 4, "piece"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'orange' in result[0]['name'].lower()


class TestRegressionCases:
    """Regression tests for cases that should already work."""

    def test_exact_matches_combine(self, service):
        """Exact name + unit matches should combine via pre-grouping."""
        raw_items = [
            {'name': 'chicken breast', 'quantity': 1, 'unit': 'lb'},
            {'name': 'chicken breast', 'quantity': 2, 'unit': 'lb'},
        ]

        grouped, _ = service._pregroup_exact_matches(raw_items)

        assert len(grouped) == 1
        assert grouped[0]['quantity'] == 3

    def test_water_removed(self, service, mock_openai_response):
        """Water should be removed from grocery list."""
        raw_items = [
            {'name': 'water', 'quantity': 2, 'unit': 'cup'},
            {'name': 'chicken', 'quantity': 1, 'unit': 'lb'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["chicken", 1, "lb"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'chicken' in result[0]['name'].lower()
        assert not any('water' in item['name'].lower() for item in result)

    def test_ice_removed(self, service, mock_openai_response):
        """Ice should be removed from grocery list."""
        raw_items = [
            {'name': 'ice', 'quantity': 1, 'unit': 'cup'},
            {'name': 'ice cubes', 'quantity': 4, 'unit': 'piece'},
            {'name': 'salmon', 'quantity': 1, 'unit': 'lb'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["salmon", 1, "lb"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert 'salmon' in result[0]['name'].lower()

    def test_empty_list_handling(self, service):
        """Empty input should return empty output."""
        result = service.consolidate_ingredients([])
        assert result == []

    def test_single_item_passthrough(self, service, mock_openai_response):
        """Single item should pass through correctly."""
        raw_items = [
            {'name': 'salt', 'quantity': 1, 'unit': 'tsp'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_openai_response({
                "items": [["salt", 1, "tsp"]]
            })

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert result[0]['name'] == 'salt'
        assert result[0]['quantity'] == 1
        assert result[0]['unit'] == 'tsp'

    def test_case_insensitive_matching(self, service):
        """Pre-grouping should be case insensitive."""
        raw_items = [
            {'name': 'Chicken Breast', 'quantity': 1, 'unit': 'lb'},
            {'name': 'chicken breast', 'quantity': 1, 'unit': 'lb'},
            {'name': 'CHICKEN BREAST', 'quantity': 1, 'unit': 'lb'},
        ]

        grouped, _ = service._pregroup_exact_matches(raw_items)

        assert len(grouped) == 1
        assert grouped[0]['quantity'] == 3

    def test_unit_case_insensitive(self, service):
        """Pre-grouping should handle unit case variations."""
        raw_items = [
            {'name': 'flour', 'quantity': 1, 'unit': 'Cup'},
            {'name': 'flour', 'quantity': 1, 'unit': 'cup'},
            {'name': 'flour', 'quantity': 1, 'unit': 'CUP'},
        ]

        grouped, _ = service._pregroup_exact_matches(raw_items)

        assert len(grouped) == 1
        assert grouped[0]['quantity'] == 3

    def test_preserves_original_name_case(self, service):
        """Pre-grouping should preserve the original name case."""
        raw_items = [
            {'name': 'Olive Oil', 'quantity': 2, 'unit': 'tbsp'},
            {'name': 'olive oil', 'quantity': 1, 'unit': 'tbsp'},
        ]

        grouped, _ = service._pregroup_exact_matches(raw_items)

        assert len(grouped) == 1
        # Should preserve the first item's case
        assert grouped[0]['name'] == 'Olive Oil'


class TestCompactFormatConversion:
    """Tests for the compact format conversion methods."""

    def test_to_compact_format(self, service):
        """Test conversion to compact array format."""
        items = [
            {'name': 'chicken', 'quantity': 2.5, 'unit': 'lb'},
            {'name': 'salt', 'quantity': 1, 'unit': 'tsp'},
        ]

        compact = service._to_compact_format(items)

        assert len(compact) == 2
        assert compact[0] == ['chicken', 2.5, 'lb']
        assert compact[1] == ['salt', 1, 'tsp']

    def test_from_compact_format(self, service):
        """Test conversion from compact array format."""
        compact = [
            ['chicken', 2.5, 'lb'],
            ['salt', 1, 'tsp'],
        ]

        items = service._from_compact_format(compact)

        assert len(items) == 2
        assert items[0] == {'name': 'chicken', 'quantity': 2.5, 'unit': 'lb'}
        assert items[1] == {'name': 'salt', 'quantity': 1.0, 'unit': 'tsp'}

    def test_compact_format_skips_empty_names(self, service):
        """Empty names should be skipped in compact format."""
        items = [
            {'name': '', 'quantity': 1, 'unit': 'cup'},
            {'name': 'flour', 'quantity': 2, 'unit': 'cup'},
        ]

        compact = service._to_compact_format(items)

        assert len(compact) == 1
        assert compact[0][0] == 'flour'

    def test_compact_format_rounds_quantities(self, service):
        """Quantities should be rounded to 2 decimal places."""
        items = [
            {'name': 'milk', 'quantity': 1.666666, 'unit': 'cup'},
        ]

        compact = service._to_compact_format(items)

        assert compact[0][1] == 1.67


class TestAPIFallback:
    """Tests for fallback behavior when API is unavailable."""

    def test_no_api_key_returns_original(self, service):
        """When no API key, should return items without consolidation."""
        raw_items = [
            {'name': 'chicken', 'quantity': 1, 'unit': 'lb'},
            {'name': 'chicken', 'quantity': 2, 'unit': 'lb'},
        ]

        with patch.object(service, '_get_client', return_value=None):
            result = service.consolidate_ingredients(raw_items)

        # Should return original items (not consolidated by LLM)
        assert len(result) == 2

    def test_api_error_returns_original(self, service):
        """When API errors, should return original items."""
        raw_items = [
            {'name': 'chicken', 'quantity': 1, 'unit': 'lb'},
        ]

        with patch.object(service, '_get_client') as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("API Error")

            result = service.consolidate_ingredients(raw_items)

        assert len(result) == 1
        assert result[0]['name'] == 'chicken'


# Integration tests - require real API key
@pytest.mark.integration
class TestLLMIntegration:
    """Integration tests with real LLM (requires OPENAI_API_KEY)."""

    @pytest.fixture(autouse=True)
    def skip_if_no_api_key(self):
        """Skip these tests if no API key is set."""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set")

    def test_real_container_size_consolidation(self, service):
        """Integration test for container size handling."""
        raw_items = [
            {'name': 'crushed tomatoes (10 oz)', 'quantity': 1, 'unit': 'can'},
            {'name': 'crushed tomatoes (28 oz)', 'quantity': 1, 'unit': 'can'},
        ]

        result = service.consolidate_ingredients(raw_items)

        # Should have consolidated
        assert len(result) <= 2
        assert any('tomato' in item['name'].lower() for item in result)

    def test_real_derivative_matching(self, service):
        """Integration test for derivative matching."""
        raw_items = [
            {'name': 'lemon', 'quantity': 2, 'unit': 'piece'},
            {'name': 'lemon zest', 'quantity': 1, 'unit': 'tbsp'},
        ]

        result = service.consolidate_ingredients(raw_items)

        # Should recognize lemon zest comes from lemons
        assert any('lemon' in item['name'].lower() for item in result)

    def test_real_cross_metric(self, service):
        """Integration test for cross-metric consolidation."""
        raw_items = [
            {'name': 'onion', 'quantity': 2, 'unit': 'piece'},
            {'name': 'onion, diced', 'quantity': 0.5, 'unit': 'cup'},
        ]

        result = service.consolidate_ingredients(raw_items)

        assert any('onion' in item['name'].lower() for item in result)
