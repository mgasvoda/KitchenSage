"""
Tests for Phoenix telemetry integration.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.telemetry import initialize_phoenix_tracing, is_tracing_enabled, get_tracing_info


class TestPhoenixTelemetry:
    """Test Phoenix telemetry functionality."""
    
    def test_is_tracing_enabled_no_api_key(self):
        """Test tracing disabled when no API key is set."""
        with patch.dict(os.environ, {}, clear=True):
            assert not is_tracing_enabled()
    
    def test_is_tracing_enabled_placeholder_api_key(self):
        """Test tracing disabled when API key is a placeholder."""
        with patch.dict(os.environ, {'PHOENIX_API_KEY': 'your_phoenix_api_key_here'}):
            assert not is_tracing_enabled()
    
    def test_is_tracing_enabled_valid_api_key(self):
        """Test tracing enabled when valid API key is set."""
        with patch.dict(os.environ, {'PHOENIX_API_KEY': 'px-abc123def456'}):
            assert is_tracing_enabled()
    
    def test_get_tracing_info_no_api_key(self):
        """Test tracing info when no API key is configured."""
        with patch.dict(os.environ, {}, clear=True):
            info = get_tracing_info()
            assert not info["enabled"]
            assert not info["api_key_configured"]
            assert info["project_name"] == "kitchencrew"
    
    def test_get_tracing_info_with_api_key(self):
        """Test tracing info when API key is configured."""
        with patch.dict(os.environ, {'PHOENIX_API_KEY': 'px-abc123def456'}):
            info = get_tracing_info()
            assert info["enabled"]
            assert info["api_key_configured"]
            assert info["project_name"] == "kitchencrew"
    
    def test_initialize_phoenix_tracing_success(self):
        """Test successful Phoenix tracing initialization."""
        mock_tracer = MagicMock()
        
        with patch.dict(os.environ, {'PHOENIX_API_KEY': 'px-abc123def456'}):
            with patch('phoenix.otel.register', return_value=mock_tracer) as mock_register:
                result = initialize_phoenix_tracing("test-project")
                
                assert result == mock_tracer
                mock_register.assert_called_once_with(
                    project_name="test-project",
                    auto_instrument=True
                )
                assert os.environ["PHOENIX_CLIENT_HEADERS"] == "api_key=px-abc123def456"
                assert os.environ["PHOENIX_COLLECTOR_ENDPOINT"] == "https://app.phoenix.arize.com"
    
    def test_initialize_phoenix_tracing_no_api_key(self):
        """Test Phoenix tracing initialization with no API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = initialize_phoenix_tracing()
            assert result is None
    
    def test_initialize_phoenix_tracing_import_error(self):
        """Test Phoenix tracing initialization with import error."""
        with patch.dict(os.environ, {'PHOENIX_API_KEY': 'px-abc123def456'}):
            with patch('builtins.__import__', side_effect=ImportError("Phoenix not installed")):
                result = initialize_phoenix_tracing()
                assert result is None
    
    def test_initialize_phoenix_tracing_general_error(self):
        """Test Phoenix tracing initialization with general error."""
        with patch.dict(os.environ, {'PHOENIX_API_KEY': 'px-abc123def456'}):
            with patch('phoenix.otel.register', side_effect=Exception("Connection failed")):
                result = initialize_phoenix_tracing()
                assert result is None 