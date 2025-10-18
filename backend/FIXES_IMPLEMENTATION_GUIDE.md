# Implementation Guide for Code Review Fixes

This document provides detailed implementation steps for addressing the issues identified in the code review.

---

## Critical Fixes

### 1. Fix Blocking I/O in Async Functions

#### Problem
Ollama and ChromaDB clients use synchronous I/O but are called within async functions, blocking the event loop.

#### Solution: Wrap Blocking Calls with run_in_executor

**File: `services/embedding_service.py`**

```python
"""Service for generating embeddings using Ollama."""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

from ollama import Client

from config import Config, get_config


class EmbeddingService:
    """Wraps Ollama client for embedding generation."""

    def __init__(self, config: Config) -> None:
        """Initialize the embedding service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.client = Client(host=config.ollama_base_url)
        self.model = config.ollama_model

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for given text.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Run blocking Ollama call in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            response: Any = await loop.run_in_executor(
                None,
                lambda: self.client.embed(model=self.model, input=text)
            )
            
            # Handle EmbedResponse object (has 'embeddings' attribute)
            if hasattr(response, "embeddings"):
                return response.embeddings[0]
            
            # Handle dict response
            if isinstance(response, dict) and "embeddings" in response:
                return response["embeddings"][0]
            
            # Fallback for direct list response
            if isinstance(response, list):
                return response
            
            raise ValueError(f"Unexpected response format: {type(response)}")
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}") from e

    async def generate_embeddings_batch(
        self, texts: list[str]
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Run blocking Ollama call in executor
            loop = asyncio.get_event_loop()
            response: Any = await loop.run_in_executor(
                None,
                lambda: self.client.embed(model=self.model, input=texts)
            )
            
            # Handle EmbedResponse object (has 'embeddings' attribute)
            if hasattr(response, "embeddings"):
                return response.embeddings
            
            # Handle dict response
            if isinstance(response, dict) and "embeddings" in response:
                return response["embeddings"]
            
            # Fallback for direct list response
            if isinstance(response, list):
                return response
            
            raise ValueError(f"Unexpected response format: {type(response)}")
        except Exception as e:
            raise Exception(f"Failed to generate batch embeddings: {str(e)}") from e


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Get cached embedding service instance.

    Returns:
        EmbeddingService instance
    """
    config = get_config()
    return EmbeddingService(config)
```

**File: `services/search_service.py`**

```python
# Add asyncio import at top
import asyncio

# Update search method
async def search(
    self,
    query: str,
    top_k: int = 5,
) -> dict:
    """Perform vector similarity search.

    Args:
        query: Search query text
        top_k: Number of top results to return

    Returns:
        Dictionary containing search results with ids, documents, distances, and metadata

    Raises:
        Exception: If search fails
    """
    try:
        # Generate embedding for query
        query_embedding = await self.embedding_service.generate_embedding(query)

        # Perform similarity search (wrap blocking call)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
        )

        # Format results
        formatted_results = {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
        }

        return formatted_results

    except Exception as e:
        raise Exception(f"Search failed: {str(e)}") from e

# Update add_document method
async def add_document(
    self,
    text: str,
    metadata: dict | None = None,
    document_id: str | None = None,
) -> str:
    """Add a document to the collection.

    Args:
        text: Document text content
        metadata: Optional metadata for the document
        document_id: Optional document ID (generated if not provided)

    Returns:
        Document ID

    Raises:
        Exception: If adding document fails
    """
    try:
        # Generate document ID if not provided
        if document_id is None:
            document_id = str(uuid.uuid4())

        # Generate embedding for document
        embedding = await self.embedding_service.generate_embedding(text)

        # Add to collection (wrap blocking call)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}],
                ids=[document_id],
            )
        )

        return document_id

    except Exception as e:
        raise Exception(f"Failed to add document: {str(e)}") from e

# Similar updates for add_documents_batch
```

**File: `services/llm_service.py`**

```python
# Add asyncio import
import asyncio

# Update summarize_search_results
async def summarize_search_results(
    self,
    query: str,
    results: list[dict],
) -> str:
    """Generate a summary of search results using LLM.

    Args:
        query: Original search query
        results: List of search result dictionaries with 'text' and 'metadata'

    Returns:
        AI-generated summary of the findings

    Raises:
        Exception: If summarization fails
    """
    try:
        if not results:
            return "No results found to summarize."

        # Prepare context from results
        context_parts = []
        for i, result in enumerate(results, 1):
            text = result.get("text", "")
            metadata = result.get("metadata", {})
            source = metadata.get("filename", metadata.get("source_type", "Unknown"))
            
            # Truncate long texts
            text_preview = text[:500] + "..." if len(text) > 500 else text
            context_parts.append(
                f"Document {i} (Source: {source}):\n{text_preview}"
            )

        context = "\n\n".join(context_parts)

        # Create prompt for summarization
        prompt = f"""You are analyzing search results from a notes database. The user searched for: "{query}"

Here are the top {len(results)} most relevant documents found:

{context}

Please provide a concise summary of the key findings across these documents. Focus on:
1. Main themes and topics found
2. Important information related to the query
3. Any patterns or connections between the documents

Keep your summary clear, informative, and under 200 words."""

        # Generate summary using LLM (wrap blocking call)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                options={
                    "temperature": 0.7,
                    "num_predict": 300,
                },
            )
        )

        # Extract the summary text
        if hasattr(response, "message"):
            return response.message.content
        elif isinstance(response, dict) and "message" in response:
            return response["message"]["content"]
        else:
            raise ValueError(f"Unexpected response format: {type(response)}")

    except Exception as e:
        raise Exception(f"Failed to generate summary: {str(e)}") from e
```

---

### 2. Add Structured Logging

#### Problem
Using `print()` statements instead of proper logging.

#### Solution: Implement Python logging

**File: `config.py`** (Add logging configuration)

```python
"""Application configuration using environment variables with defaults."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)


@dataclass(frozen=True)
class Config:
    """Application configuration with defaults."""

    # Ollama Configuration
    ollama_model: str = os.getenv("OLLAMA_MODEL", "embeddinggemma:latest")
    ollama_llm_model: str = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:latest")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # ChromaDB Configuration
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "notes")

    # OCR Configuration
    min_text_length: int = int(os.getenv("MIN_TEXT_LENGTH", "10"))
    min_ocr_confidence: float = float(os.getenv("MIN_OCR_CONFIDENCE", "0.5"))
    
    # File Upload Configuration
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

    # API Configuration
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] | None = None
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self) -> None:
        """Set default CORS origins if not provided."""
        if self.cors_origins is None:
            object.__setattr__(
                self,
                "cors_origins",
                ["http://localhost:4200", "http://127.0.0.1:4200"],
            )
        
        # Set log level
        logging.getLogger().setLevel(self.log_level)


@lru_cache
def get_config() -> Config:
    """Get cached configuration instance."""
    return Config()
```

**File: `main.py`** (Update to use logging)

```python
"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_config
from routers import api

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
    config = get_config()
    logger.info("Starting Notes Reviewer API...")
    logger.info(f"Using Ollama model: {config.ollama_model}")
    logger.info(f"ChromaDB path: {config.chroma_db_path}")
    logger.info(f"Collection name: {config.chroma_collection_name}")

    yield

    # Shutdown
    logger.info("Shutting down Notes Reviewer API...")


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
```

**Update all services to use logging**:

```python
import logging

logger = logging.getLogger(__name__)

# In methods:
logger.info("Generating embedding for text of length %d", len(text))
logger.error("Failed to generate embedding", exc_info=True, extra={"text_length": len(text)})
logger.warning("OCR confidence below threshold: %.2f", confidence)
```

---

## High Priority Fixes

### 3. Add File Size Validation

**File: `routers/api.py`**

```python
@router.post(
    "/upload/photo",
    response_model=UploadPhotoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)
async def upload_photo(
    file: Annotated[UploadFile, File(..., description="Image file to process")],
    ocr_service: Annotated[OCRService, Depends(get_ocr_service)],
    search_service: Annotated[SearchService, Depends(get_search_service)],
) -> UploadPhotoResponse:
    """Upload photo, extract text via OCR, and auto-index.

    Args:
        file: Uploaded image file
        ocr_service: OCR service instance
        search_service: Search service instance

    Returns:
        Upload response with document ID and extracted text

    Raises:
        HTTPException: If upload or processing fails
    """
    config = get_config()
    max_size = config.max_file_size_mb * 1024 * 1024
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        # Validate file format
        if not ocr_service.validate_image_format(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image format. Supported formats: {', '.join(ocr_service.SUPPORTED_FORMATS)}",
            )

        # Read file with size limit
        image_bytes = await file.read(max_size + 1)
        
        if len(image_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {config.max_file_size_mb}MB",
            )

        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file",
            )
        
        logger.info(f"Processing upload: {file.filename}, size: {len(image_bytes)} bytes")

        # Extract text using OCR
        ocr_result = await ocr_service.extract_text_from_image(
            image_bytes=image_bytes,
            filename=file.filename,
        )

        # Index the document
        document_id = await search_service.add_document(
            text=ocr_result["text"],
            metadata=ocr_result["metadata"],
        )
        
        logger.info(f"Successfully indexed document: {document_id}")

        return UploadPhotoResponse(
            success=True,
            document_id=document_id,
            extracted_text=ocr_result["text"],
            confidence=ocr_result["confidence"],
            message="Photo processed and indexed successfully",
            metadata=ocr_result["metadata"],
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        # Validation errors (quality issues)
        logger.warning(f"Validation error during upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        # Other errors
        logger.error(f"Upload processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to process image. Please try again.",
        ) from e
```

---

### 4. Custom Exception Classes

**File: `exceptions.py`** (New file)

```python
"""Custom exception classes for the application."""

from __future__ import annotations


class ServiceError(Exception):
    """Base exception for service-level errors."""
    pass


class EmbeddingError(ServiceError):
    """Exception raised when embedding generation fails."""
    pass


class SearchError(ServiceError):
    """Exception raised when search operations fail."""
    pass


class OCRError(ServiceError):
    """Exception raised when OCR processing fails."""
    pass


class LLMError(ServiceError):
    """Exception raised when LLM operations fail."""
    pass


class ValidationError(ServiceError):
    """Exception raised when input validation fails."""
    pass
```

**Update services to use custom exceptions**:

```python
from exceptions import EmbeddingError

# In embedding_service.py
except Exception as e:
    logger.error("Failed to generate embedding", exc_info=True)
    raise EmbeddingError(f"Failed to generate embedding: {str(e)}") from e
```

---

### 5. Input Validation

**Add validation helpers in services**:

```python
def _validate_text_input(text: str) -> None:
    """Validate text input.
    
    Args:
        text: Text to validate
        
    Raises:
        ValidationError: If text is invalid
    """
    if not text or not text.strip():
        raise ValidationError("Text input cannot be empty")
    
    if len(text) > 100000:  # 100KB limit
        raise ValidationError("Text input too long (max 100KB)")
```

---

## Additional Improvements

### 6. Enhanced .env.example

```env
# Ollama Configuration
OLLAMA_MODEL=embeddinggemma:latest
OLLAMA_LLM_MODEL=llama3.1:latest
OLLAMA_BASE_URL=http://localhost:11434

# ChromaDB Configuration
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=notes

# OCR Configuration
MIN_TEXT_LENGTH=10
MIN_OCR_CONFIDENCE=0.5

# File Upload Configuration
MAX_FILE_SIZE_MB=10

# Logging Configuration
LOG_LEVEL=INFO
```

---

## Testing Recommendations

### Unit Tests Example

**File: `tests/test_embedding_service.py`**

```python
import pytest
from unittest.mock import Mock, patch
from services.embedding_service import EmbeddingService
from config import Config


@pytest.fixture
def config():
    return Config(
        ollama_model="test-model",
        ollama_base_url="http://localhost:11434",
    )


@pytest.fixture
def embedding_service(config):
    return EmbeddingService(config)


@pytest.mark.asyncio
async def test_generate_embedding(embedding_service):
    """Test embedding generation."""
    with patch.object(embedding_service.client, 'embed') as mock_embed:
        mock_embed.return_value = Mock(embeddings=[[0.1, 0.2, 0.3]])
        
        result = await embedding_service.generate_embedding("test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embedding_error(embedding_service):
    """Test embedding generation error handling."""
    with patch.object(embedding_service.client, 'embed') as mock_embed:
        mock_embed.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception) as exc_info:
            await embedding_service.generate_embedding("test text")
        
        assert "Failed to generate embedding" in str(exc_info.value)
```

---

## Summary

This guide provides complete implementation details for:

1. ✅ Fixing blocking I/O issues with run_in_executor
2. ✅ Adding structured logging throughout the application
3. ✅ Implementing file size validation
4. ✅ Creating custom exception classes
5. ✅ Adding input validation helpers
6. ✅ Enhancing configuration
7. ✅ Example tests

Follow these patterns consistently across all services and routers for a production-ready application.
