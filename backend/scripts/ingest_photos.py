#!/usr/bin/env python3
"""Script to batch process photos from directories using OCR."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from services.ocr_service import OCRService, get_ocr_service
from services.search_service import get_search_service


async def process_photo(
    file_path: Path,
    ocr_service: OCRService,
    search_service,
) -> tuple[str, dict]:
    """Process a single photo with OCR and index it.

    Args:
        file_path: Path to photo file
        ocr_service: OCR service instance
        search_service: Search service instance

    Returns:
        Tuple of (document_id, metadata)

    Raises:
        Exception: If processing fails
    """
    # Validate format
    if not ocr_service.validate_image_format(file_path.name):
        raise ValueError(f"Unsupported image format: {file_path.suffix}")

    # Read file
    with open(file_path, "rb") as f:
        image_bytes = f.read()

    if not image_bytes:
        raise ValueError("Empty file")

    # Extract text using OCR
    ocr_result = await ocr_service.extract_text_from_image(
        image_bytes=image_bytes,
        filename=file_path.name,
    )

    # Update metadata with file path
    ocr_result["metadata"]["file_path"] = str(file_path.absolute())

    # Index the document
    document_id = await search_service.add_document(
        text=ocr_result["text"],
        metadata=ocr_result["metadata"],
    )

    return document_id, ocr_result["metadata"]


async def process_directory(
    directory: Path,
    ocr_service: OCRService,
    search_service,
    recursive: bool = False,
) -> tuple[list[str], list[dict]]:
    """Process all images in a directory.

    Args:
        directory: Directory path
        ocr_service: OCR service instance
        search_service: Search service instance
        recursive: Whether to process subdirectories

    Returns:
        Tuple of (document_ids, failed_files)
    """
    # Find all image files
    patterns = [f"*.{ext}" for ext in ocr_service.SUPPORTED_FORMATS]
    files = []

    if recursive:
        for pattern in patterns:
            files.extend(directory.rglob(pattern))
    else:
        for pattern in patterns:
            files.extend(directory.glob(pattern))

    if not files:
        print(f"No image files found in {directory}")
        return [], []

    document_ids = []
    failed_files = []

    for i, file_path in enumerate(files, 1):
        print(f"\nProcessing [{i}/{len(files)}]: {file_path.name}")

        try:
            doc_id, metadata = await process_photo(
                file_path,
                ocr_service,
                search_service,
            )

            document_ids.append(doc_id)
            print(f"✓ Success (ID: {doc_id[:8]}...)")
            print(f"  Text length: {metadata['text_length']} chars")
            print(f"  Confidence: {metadata['confidence']:.2%}")
            print(f"  Word count: {metadata['word_count']}")

        except ValueError as e:
            # Validation errors
            failed_files.append({"file": file_path.name, "error": str(e)})
            print(f"✗ Validation failed: {e}")
        except Exception as e:
            # Other errors
            failed_files.append({"file": file_path.name, "error": str(e)})
            print(f"✗ Processing failed: {e}")

    return document_ids, failed_files


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch process photos from directories using OCR"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to photo file or directory",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Process subdirectories recursively",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset collection before processing",
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)

    # Initialize services
    config = get_config()
    ocr_service = get_ocr_service()
    search_service = get_search_service()

    print(f"Using collection: {config.chroma_collection_name}")
    print(f"ChromaDB path: {config.chroma_db_path}")
    print(f"Supported formats: {', '.join(ocr_service.SUPPORTED_FORMATS)}")

    # Reset collection if requested
    if args.reset:
        print("\nResetting collection...")
        search_service.reset_collection()
        print("✓ Collection reset")

    # Show initial count
    info = search_service.get_collection_info()
    print(f"\nDocuments before processing: {info['count']}")

    # Process based on path type
    document_ids = []
    failed_files = []

    try:
        if args.path.is_file():
            print(f"\nProcessing single file: {args.path.name}")
            doc_id, metadata = await process_photo(
                args.path,
                ocr_service,
                search_service,
            )
            document_ids.append(doc_id)
            print(f"✓ Success (ID: {doc_id[:8]}...)")
            print(f"  Text length: {metadata['text_length']} chars")
            print(f"  Confidence: {metadata['confidence']:.2%}")

        elif args.path.is_dir():
            print(f"\nProcessing directory: {args.path}")
            document_ids, failed_files = await process_directory(
                args.path,
                ocr_service,
                search_service,
                args.recursive,
            )
        else:
            print(f"Error: Invalid path type: {args.path}")
            sys.exit(1)

        # Show final count
        info = search_service.get_collection_info()
        print(f"\n{'=' * 60}")
        print(f"Documents after processing: {info['count']}")
        print(f"Successfully processed: {len(document_ids)} photo(s)")
        print(f"Failed: {len(failed_files)} photo(s)")

        if failed_files:
            print("\nFailed files:")
            for failed in failed_files:
                print(f"  ✗ {failed['file']}: {failed['error']}")

    except Exception as e:
        print(f"\nError during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
