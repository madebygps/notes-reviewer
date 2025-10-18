"""API router with search and upload endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

from models import (
    ErrorResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    UploadPhotoResponse,
)
from services.llm_service import LLMService, get_llm_service
from services.ocr_service import OCRService, get_ocr_service
from services.search_service import SearchService, get_search_service

router = APIRouter(prefix="/api/v1", tags=["api"])


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)
async def search(
    request: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
) -> SearchResponse:
    """Perform vector similarity search with optional AI summarization.

    Args:
        request: Search request with query, top_k, and summarize flag
        search_service: Search service instance
        llm_service: LLM service instance

    Returns:
        Search response with results and optional summary

    Raises:
        HTTPException: If search fails
    """
    try:
        logger.info(f"Search request: query='{request.query}', top_k={request.top_k}, summarize={request.summarize}")

        # Perform search
        results = await search_service.search(
            query=request.query,
            top_k=request.top_k,
        )

        # Format response
        search_results = [
            SearchResultItem(
                id=result_id,
                text=document,
                distance=distance,
                metadata=metadata,
            )
            for result_id, document, distance, metadata in zip(
                results["ids"],
                results["documents"],
                results["distances"],
                results["metadatas"],
            )
        ]

        # Generate summary if requested
        summary = None
        if request.summarize and search_results:
            try:
                summary = await llm_service.summarize_search_results(
                    query=request.query,
                    results=[
                        {
                            "text": result.text,
                            "metadata": result.metadata,
                        }
                        for result in search_results
                    ],
                )
            except (ValueError, RuntimeError) as e:
                # Log error but don't fail the request
                logger.warning(f"Summary generation failed: {e}")
                summary = None

        logger.info(f"Search completed: {len(search_results)} results")

        return SearchResponse(
            results=search_results,
            query=request.query,
            total_results=len(search_results),
            summary=summary,
        )

    except ValueError as e:
        logger.error(f"Validation error in search: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RuntimeError as e:
        logger.error(f"Search service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search service error: {str(e)}",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error in search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e


@router.post(
    "/upload/photo",
    response_model=UploadPhotoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
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
    try:
        logger.info(f"Upload photo request: {file.filename}")

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

        # Read file content
        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file",
            )

        logger.debug(f"Processing {file.filename}: {len(image_bytes)} bytes")

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

        logger.info(f"Successfully processed and indexed {file.filename}: {document_id[:8]}...")

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
        logger.warning(f"Validation error for {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RuntimeError as e:
        # Service errors
        logger.error(f"Service error processing {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Upload processing error: {str(e)}",
        ) from e
    except Exception as e:
        # Other unexpected errors
        logger.exception(f"Unexpected error processing {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e
