#!/usr/bin/env python3
"""Script to view and search ChromaDB collection contents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from services.search_service import get_search_service


def print_separator(char: str = "=", length: int = 80) -> None:
    """Print a separator line."""
    print(char * length)


def print_document(doc_id: str, text: str, metadata: dict, distance: float | None = None) -> None:
    """Print a document with formatting.

    Args:
        doc_id: Document ID
        text: Document text
        metadata: Document metadata
        distance: Optional similarity distance
    """
    print(f"\nDocument ID: {doc_id}")
    if distance is not None:
        print(f"Distance: {distance:.4f}")
    print(f"Text: {text[:200]}{'...' if len(text) > 200 else ''}")
    print("Metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    print_separator("-", 80)


async def view_all_documents(search_service) -> None:
    """View all documents in the collection.

    Args:
        search_service: Search service instance
    """
    collection = search_service.collection

    # Get all documents
    results = collection.get()

    if not results["ids"]:
        print("Collection is empty")
        return

    print(f"\nTotal documents: {len(results['ids'])}")
    print_separator()

    for doc_id, text, metadata in zip(
        results["ids"],
        results["documents"],
        results["metadatas"],
    ):
        print_document(doc_id, text, metadata)


async def search_documents(search_service, query: str, top_k: int = 5) -> None:
    """Search for documents.

    Args:
        search_service: Search service instance
        query: Search query
        top_k: Number of results to return
    """
    print(f"\nSearching for: '{query}'")
    print(f"Top {top_k} results:")
    print_separator()

    results = await search_service.search(query=query, top_k=top_k)

    if not results["ids"]:
        print("No results found")
        return

    for doc_id, text, distance, metadata in zip(
        results["ids"],
        results["documents"],
        results["distances"],
        results["metadatas"],
    ):
        print_document(doc_id, text, metadata, distance)


async def show_collection_info(search_service) -> None:
    """Show collection information.

    Args:
        search_service: Search service instance
    """
    info = search_service.get_collection_info()

    print("\nCollection Information:")
    print_separator()
    print(f"Name: {info['name']}")
    print(f"Document count: {info['count']}")
    print(f"Metadata: {info['metadata']}")


async def show_statistics(search_service) -> None:
    """Show collection statistics.

    Args:
        search_service: Search service instance
    """
    collection = search_service.collection

    # Get all documents
    results = collection.get()

    if not results["ids"]:
        print("\nCollection is empty")
        return

    print("\nCollection Statistics:")
    print_separator()
    print(f"Total documents: {len(results['ids'])}")

    # Calculate text statistics
    text_lengths = [len(text) for text in results["documents"]]
    print(f"Average text length: {sum(text_lengths) / len(text_lengths):.0f} chars")
    print(f"Min text length: {min(text_lengths)} chars")
    print(f"Max text length: {max(text_lengths)} chars")

    # Count by source type
    source_types = {}
    for metadata in results["metadatas"]:
        source_type = metadata.get("source_type", "unknown")
        source_types[source_type] = source_types.get(source_type, 0) + 1

    print("\nDocuments by source type:")
    for source_type, count in sorted(source_types.items()):
        print(f"  {source_type}: {count}")


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View and search ChromaDB collection contents"
    )
    parser.add_argument(
        "--search",
        "-s",
        type=str,
        help="Search query",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=5,
        help="Number of search results (default: 5)",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="View all documents",
    )
    parser.add_argument(
        "--info",
        "-i",
        action="store_true",
        help="Show collection information",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show collection statistics",
    )

    args = parser.parse_args()

    # Initialize services
    config = get_config()
    search_service = get_search_service()

    print(f"Collection: {config.chroma_collection_name}")
    print(f"ChromaDB path: {config.chroma_db_path}")

    try:
        if args.search:
            # Search mode
            await search_documents(search_service, args.search, args.top_k)
        elif args.all:
            # View all mode
            await view_all_documents(search_service)
        elif args.stats:
            # Statistics mode
            await show_statistics(search_service)
        else:
            # Default: show info
            await show_collection_info(search_service)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
