"""Service for generating embeddings using Ollama."""

from __future__ import annotations

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
            response: Any = self.client.embed(model=self.model, input=text)
            
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
            response: Any = self.client.embed(model=self.model, input=texts)
            
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
