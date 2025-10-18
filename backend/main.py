"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_config
from routers import api


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    print("Starting Notes Reviewer API...")
    config = get_config()
    print(f"Using Ollama model: {config.ollama_model}")
    print(f"ChromaDB path: {config.chroma_db_path}")
    print(f"Collection name: {config.chroma_collection_name}")

    yield

    # Shutdown
    print("Shutting down Notes Reviewer API...")


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
