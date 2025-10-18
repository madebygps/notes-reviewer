#!/usr/bin/env python3
"""Script to index text documents or JSON documents into ChromaDB."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from services.search_service import get_search_service


async def index_text_file(file_path: Path, search_service) -> str:
    """Index a single text file.

    Args:
        file_path: Path to text file
        search_service: Search service instance

    Returns:
        Document ID
    """
    with open(file_path, encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        raise ValueError(f"Empty file: {file_path}")

    metadata = {
        "source_type": "text_file",
        "filename": file_path.name,
        "file_path": str(file_path.absolute()),
    }

    document_id = await search_service.add_document(
        text=text,
        metadata=metadata,
    )

    return document_id


async def index_json_file(file_path: Path, search_service) -> list[str]:
    """Index documents from a JSON file.

    Expected JSON format:
    [
        {"text": "content", "metadata": {...}},
        {"text": "content", "metadata": {...}}
    ]

    Args:
        file_path: Path to JSON file
        search_service: Search service instance

    Returns:
        List of document IDs
    """
    with open(file_path, encoding="utf-8") as f:
        documents = json.load(f)

    if not isinstance(documents, list):
        raise ValueError("JSON file must contain a list of documents")

    texts = []
    metadatas = []

    for i, doc in enumerate(documents):
        if not isinstance(doc, dict) or "text" not in doc:
            raise ValueError(f"Invalid document at index {i}: missing 'text' field")

        texts.append(doc["text"])
        metadata = doc.get("metadata", {})
        metadata.update(
            {
                "source_type": "json_file",
                "filename": file_path.name,
                "file_path": str(file_path.absolute()),
                "document_index": i,
            }
        )
        metadatas.append(metadata)

    document_ids = await search_service.add_documents_batch(
        texts=texts,
        metadatas=metadatas,
    )

    return document_ids


async def index_directory(directory: Path, search_service, pattern: str = "*.txt") -> list[str]:
    """Index all matching files in a directory.

    Args:
        directory: Directory path
        search_service: Search service instance
        pattern: File pattern to match

    Returns:
        List of document IDs
    """
    files = list(directory.glob(pattern))

    if not files:
        print(f"No files matching '{pattern}' found in {directory}")
        return []

    document_ids = []

    for file_path in files:
        try:
            if file_path.suffix == ".json":
                ids = await index_json_file(file_path, search_service)
                document_ids.extend(ids)
                print(f"✓ Indexed {len(ids)} documents from {file_path.name}")
            else:
                doc_id = await index_text_file(file_path, search_service)
                document_ids.append(doc_id)
                print(f"✓ Indexed {file_path.name} (ID: {doc_id[:8]}...)")
        except Exception as e:
            print(f"✗ Failed to index {file_path.name}: {e}")

    return document_ids


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Index text documents or JSON documents into ChromaDB"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to file or directory to index",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.txt",
        help="File pattern for directory indexing (default: *.txt)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset collection before indexing",
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)

    # Initialize services
    config = get_config()
    search_service = get_search_service()

    print(f"Using collection: {config.chroma_collection_name}")
    print(f"ChromaDB path: {config.chroma_db_path}")

    # Reset collection if requested
    if args.reset:
        print("\nResetting collection...")
        search_service.reset_collection()
        print("✓ Collection reset")

    # Show initial count
    info = search_service.get_collection_info()
    print(f"\nDocuments before indexing: {info['count']}")

    # Index based on path type
    print("\nIndexing documents...")
    document_ids = []

    try:
        if args.path.is_file():
            if args.path.suffix == ".json":
                document_ids = await index_json_file(args.path, search_service)
                print(f"✓ Indexed {len(document_ids)} documents from {args.path.name}")
            else:
                doc_id = await index_text_file(args.path, search_service)
                document_ids.append(doc_id)
                print(f"✓ Indexed {args.path.name} (ID: {doc_id[:8]}...)")
        elif args.path.is_dir():
            document_ids = await index_directory(
                args.path,
                search_service,
                args.pattern,
            )
        else:
            print(f"Error: Invalid path type: {args.path}")
            sys.exit(1)

        # Show final count
        info = search_service.get_collection_info()
        print(f"\nDocuments after indexing: {info['count']}")
        print(f"Successfully indexed {len(document_ids)} document(s)")

    except Exception as e:
        print(f"\nError during indexing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
