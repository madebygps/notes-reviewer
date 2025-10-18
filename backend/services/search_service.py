"""Service for vector similarity search using ChromaDB."""

from __future__ import annotations

import logging
import uuid
from functools import lru_cache

import chromadb
from chromadb.config import Settings

from config import Config, get_config
from services.embedding_service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


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
            RuntimeError: If search fails
        """
        try:
            logger.info(f"Searching for: '{query}' (top_k={top_k})")

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

            # Log search results with distances for debugging
            logger.info(f"Found {len(formatted_results['ids'])} results")
            for i, (doc_id, distance, metadata) in enumerate(zip(
                formatted_results["ids"], 
                formatted_results["distances"],
                formatted_results["metadatas"]
            ), 1):
                filename = metadata.get("filename", "unknown")
                logger.info(f"  {i}. Distance: {distance:.4f} | File: {filename}")
            
            return formatted_results

        except (ValueError, RuntimeError):
            raise
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RuntimeError(f"Search failed: {str(e)}") from e

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
            RuntimeError: If adding document fails
        """
        try:
            # Generate document ID if not provided
            if document_id is None:
                document_id = str(uuid.uuid4())

            logger.info(f"Adding document {document_id[:8]}... ({len(text)} chars)")

            # Generate embedding for document
            embedding = await self.embedding_service.generate_embedding(text)

            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}],
                ids=[document_id],
            )

            logger.info(f"Successfully added document {document_id[:8]}...")
            return document_id

        except (ValueError, RuntimeError):
            raise
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise RuntimeError(f"Failed to add document: {str(e)}") from e

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
            RuntimeError: If adding documents fails
        """
        try:
            # Generate document IDs if not provided
            if document_ids is None:
                document_ids = [str(uuid.uuid4()) for _ in texts]

            logger.info(f"Adding batch of {len(texts)} documents")

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

            logger.info(f"Successfully added batch of {len(texts)} documents")
            return document_ids

        except (ValueError, RuntimeError):
            raise
        except Exception as e:
            logger.error(f"Failed to add documents batch: {e}")
            raise RuntimeError(f"Failed to add documents batch: {str(e)}") from e

    async def upsert_document(
        self,
        text: str,
        document_id: str,
        metadata: dict | None = None,
    ) -> str:
        """Add or update a document in the collection.

        Args:
            text: Document text content
            document_id: Document ID
            metadata: Optional metadata for the document

        Returns:
            Document ID

        Raises:
            RuntimeError: If upserting document fails
        """
        try:
            logger.info(f"Upserting document {document_id[:8]}...")

            # Generate embedding for document
            embedding = await self.embedding_service.generate_embedding(text)

            # Upsert to collection
            self.collection.upsert(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}],
                ids=[document_id],
            )

            logger.info(f"Successfully upserted document {document_id[:8]}...")
            return document_id

        except (ValueError, RuntimeError):
            raise
        except Exception as e:
            logger.error(f"Failed to upsert document: {e}")
            raise RuntimeError(f"Failed to upsert document: {str(e)}") from e

    def get_by_id(self, document_id: str) -> dict | None:
        """Get a document by ID.

        Args:
            document_id: Document ID to retrieve

        Returns:
            Dictionary with document data or None if not found
        """
        try:
            result = self.collection.get(ids=[document_id])
            
            if not result["ids"]:
                return None
            
            return {
                "id": result["ids"][0],
                "document": result["documents"][0],
                "metadata": result["metadatas"][0] if result["metadatas"] else {},
            }
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None

    def delete_by_id(self, document_id: str) -> bool:
        """Delete a document by ID.

        Args:
            document_id: Document ID to delete

        Returns:
            True if deleted, False if not found or error
        """
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted document {document_id[:8]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False

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

    def close(self) -> None:
        """Close the ChromaDB client and release resources."""
        try:
            # ChromaDB PersistentClient doesn't have explicit close,
            # but we can clear references to allow cleanup
            logger.info("Closing ChromaDB client")
            del self.collection
            del self.client
        except Exception as e:
            logger.warning(f"Error during ChromaDB cleanup: {e}")


@lru_cache
def get_search_service() -> SearchService:
    """Get cached search service instance.

    Returns:
        SearchService instance
    """
    config = get_config()
    embedding_service = get_embedding_service()
    return SearchService(config, embedding_service)
