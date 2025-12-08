"""
Phoenix Telemetry Configuration for KitchenCrew

This module handles the initialization of Phoenix tracing for observability
of CrewAI agents and LLM interactions.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def initialize_phoenix_tracing(project_name: str = "kitchencrew") -> Optional[object]:
    """
    Initialize Phoenix tracing for the KitchenCrew application.
    
    Args:
        project_name: Name of the project for Phoenix tracing
        
    Returns:
        Tracer provider instance if successful, None otherwise
    """
    try:
        # Check if Phoenix API key is available
        phoenix_api_key = os.getenv('PHOENIX_API_KEY')
        
        if not phoenix_api_key:
            logger.warning("PHOENIX_API_KEY not found in environment variables. Skipping Phoenix tracing initialization.")
            return None
            
        if phoenix_api_key.startswith('your_') or phoenix_api_key == 'placeholder':
            logger.warning("PHOENIX_API_KEY appears to be a placeholder. Skipping Phoenix tracing initialization.")
            return None
        
        # Set Phoenix environment variables
        os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={phoenix_api_key}"
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com"
        
        # Import and register Phoenix tracing
        from phoenix.otel import register
        
        # Configure the Phoenix tracer with auto-instrumentation
        tracer_provider = register(
            project_name=project_name,
            auto_instrument=True  # Auto-instrument based on installed OI dependencies
        )
        
        logger.info(f"Phoenix tracing initialized successfully for project: {project_name}")
        logger.info("Tracing endpoint: https://app.phoenix.arize.com")
        
        return tracer_provider
        
    except ImportError as e:
        logger.error(f"Failed to import Phoenix dependencies: {e}")
        logger.error("Please install Phoenix dependencies: uv add arize-phoenix-otel openinference-instrumentation-crewai")
        return None
        
    except Exception as e:
        logger.error(f"Failed to initialize Phoenix tracing: {e}")
        return None


def is_tracing_enabled() -> bool:
    """
    Check if Phoenix tracing is properly configured and enabled.
    
    Returns:
        True if tracing is enabled, False otherwise
    """
    phoenix_api_key = os.getenv('PHOENIX_API_KEY')
    
    if not phoenix_api_key:
        return False
        
    if phoenix_api_key.startswith('your_') or phoenix_api_key == 'placeholder':
        return False
        
    return True


def get_tracing_info() -> dict:
    """
    Get information about the current tracing configuration.
    
    Returns:
        Dictionary with tracing configuration details
    """
    return {
        "enabled": is_tracing_enabled(),
        "endpoint": os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "Not set"),
        "project_name": "kitchencrew",
        "api_key_configured": bool(os.getenv('PHOENIX_API_KEY'))
    } 