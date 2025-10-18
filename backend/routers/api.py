"""API router with search and upload endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

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
            except Exception as e:
                # Log error but don't fail the request
                print(f"Warning: Summary generation failed: {e}")
                summary = "Summary generation failed. Please try again."

        return SearchResponse(
            results=search_results,
            query=request.query,
            total_results=len(search_results),
            summary=summary,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search service error: {str(e)}",
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        # Other errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Upload processing error: {str(e)}",
        ) from e
