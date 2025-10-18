"""Service for generating embeddings using Ollama."""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any

from ollama import Client

from config import Config, get_config

logger = logging.getLogger(__name__)


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

    def _parse_embed_response(self, response: Any, is_batch: bool = False) -> list[float] | list[list[float]]:
        """Parse Ollama embed response.

        Args:
            response: Ollama API response
            is_batch: Whether this is a batch response

        Returns:
            Embedding vector(s)

        Raises:
            ValueError: If response format is unexpected
        """
        # Handle EmbedResponse object (has 'embeddings' attribute)
        if hasattr(response, "embeddings"):
            return response.embeddings if is_batch else response.embeddings[0]
        
        # Handle dict response
        if isinstance(response, dict) and "embeddings" in response:
            return response["embeddings"] if is_batch else response["embeddings"][0]
        
        # Fallback for direct list response
        if isinstance(response, list):
            return response
        
        raise ValueError(f"Unexpected response format: {type(response)}")

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for given text.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector

        Raises:
            ValueError: If response format is unexpected
            RuntimeError: If embedding generation fails
        """
        try:
            logger.debug(f"Generating embedding for text of length {len(text)}")
            # Run sync Ollama call in thread pool to avoid blocking event loop
            response: Any = await asyncio.to_thread(
                self.client.embed,
                model=self.model,
                input=text,
            )
            return self._parse_embed_response(response, is_batch=False)
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {str(e)}") from e

    async def generate_embeddings_batch(
        self, texts: list[str]
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If response format is unexpected
            RuntimeError: If embedding generation fails
        """
        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")
            # Run sync Ollama call in thread pool to avoid blocking event loop
            response: Any = await asyncio.to_thread(
                self.client.embed,
                model=self.model,
                input=texts,
            )
            return self._parse_embed_response(response, is_batch=True)
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise RuntimeError(f"Failed to generate batch embeddings: {str(e)}") from e


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Get cached embedding service instance.

    Returns:
        EmbeddingService instance
    """
    config = get_config()
    return EmbeddingService(config)
