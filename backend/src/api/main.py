"""
FastAPI application setup with CORS and route registration.
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure the backend directory is in the path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Load environment variables
load_dotenv(os.path.join(backend_dir, '..', '.env'))
load_dotenv()

from src.api.routes import recipes, meal_plans, grocery_lists, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print("🍳 KitchenSage API starting up...")
    
    # Initialize telemetry if available
    try:
        from src.utils.telemetry import initialize_phoenix_tracing
        initialize_phoenix_tracing(project_name="kitchensage-api")
        print("📊 Phoenix telemetry initialized")
    except Exception as e:
        print(f"⚠️  Telemetry initialization skipped: {e}")
    
    yield
    
    # Shutdown
    print("🍳 KitchenSage API shutting down...")


app = FastAPI(
    title="KitchenSage API",
    description="AI-powered cooking assistant API with recipe management, meal planning, and grocery list generation.",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(recipes.router, prefix="/api/recipes", tags=["Recipes"])
app.include_router(meal_plans.router, prefix="/api/meal-plans", tags=["Meal Plans"])
app.include_router(grocery_lists.router, prefix="/api/grocery-lists", tags=["Grocery Lists"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "KitchenSage API",
        "version": "0.2.0",
        "status": "running",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

