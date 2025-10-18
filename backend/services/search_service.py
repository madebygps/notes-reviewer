"""Service for vector similarity search using ChromaDB."""

from __future__ import annotations

import uuid
from functools import lru_cache

import chromadb
from chromadb.config import Settings

from config import Config, get_config
from services.embedding_service import EmbeddingService, get_embedding_service


class SearchService:
    """Handles ChromaDB queries and result formatting."""

    def __init__(
        self,
        config: Config,
        embedding_service: EmbeddingService,
    ) -> None:
        """Initialize the search service.

        Args:
            config: Application configuration
            embedding_service: Service for generating embeddings
        """
        self.config = config
        self.embedding_service = embedding_service

        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=config.chroma_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=config.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

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

            # Perform similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
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

            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}],
                ids=[document_id],
            )

            return document_id

        except Exception as e:
            raise Exception(f"Failed to add document: {str(e)}") from e

    async def add_documents_batch(
        self,
        texts: list[str],
        metadatas: list[dict] | None = None,
        document_ids: list[str] | None = None,
    ) -> list[str]:
        """Add multiple documents to the collection.

        Args:
            texts: List of document texts
            metadatas: Optional list of metadata dictionaries
            document_ids: Optional list of document IDs (generated if not provided)

        Returns:
            List of document IDs

        Raises:
            Exception: If adding documents fails
        """
        try:
            # Generate document IDs if not provided
            if document_ids is None:
                document_ids = [str(uuid.uuid4()) for _ in texts]

            # Generate embeddings for all documents
            embeddings = await self.embedding_service.generate_embeddings_batch(texts)

            # Prepare metadatas
            if metadatas is None:
                metadatas = [{} for _ in texts]

            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=document_ids,
            )

            return document_ids

        except Exception as e:
            raise Exception(f"Failed to add documents batch: {str(e)}") from e

    def get_collection_info(self) -> dict:
        """Get information about the collection.

        Returns:
            Dictionary with collection count and metadata
        """
        return {
            "name": self.collection.name,
            "count": self.collection.count(),
            "metadata": self.collection.metadata,
        }

    def delete_collection(self) -> None:
        """Delete the collection."""
        self.client.delete_collection(name=self.config.chroma_collection_name)

    def reset_collection(self) -> None:
        """Reset the collection by deleting and recreating it."""
        self.delete_collection()
        self.collection = self.client.get_or_create_collection(
            name=self.config.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )


@lru_cache
def get_search_service() -> SearchService:
    """Get cached search service instance.

    Returns:
        SearchService instance
    """
    config = get_config()
    embedding_service = get_embedding_service()
    return SearchService(config, embedding_service)
