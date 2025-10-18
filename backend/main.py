"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_config
from routers import api
from services.search_service import get_search_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info("Starting Notes Reviewer API...")
    config = get_config()
    logger.info(f"Using Ollama model: {config.ollama_model}")
    logger.info(f"ChromaDB path: {config.chroma_db_path}")
    logger.info(f"Collection name: {config.chroma_collection_name}")

    yield

    # Shutdown
    logger.info("Shutting down Notes Reviewer API...")
    try:
        search_service = get_search_service()
        search_service.close()
        logger.info("ChromaDB client closed successfully")
    except Exception as e:
        logger.error(f"Error closing ChromaDB client: {e}")


# Create FastAPI app
app = FastAPI(
    title="Notes Reviewer API",
    description="Backend API for notes search with vector storage and OCR capabilities",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api.router)


@app.get("/")
async def root() -> dict:
    """Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "message": "Notes Reviewer API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}
