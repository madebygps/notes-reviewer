"""Pydantic models for request and response validation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for vector similarity search."""

    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of top results to return",
    )
    summarize: bool = Field(
        default=False,
        description="Whether to generate AI summary of results",
    )


class SearchResultItem(BaseModel):
    """Individual search result item."""

    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text content")
    distance: float = Field(..., description="Similarity distance (lower is better)")
    metadata: dict = Field(default_factory=dict, description="Document metadata")


class SearchResponse(BaseModel):
    """Response model for search results."""

    results: list[SearchResultItem] = Field(
        default_factory=list,
        description="List of search results",
    )
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Total number of results returned")
    summary: str | None = Field(
        None,
        description="AI-generated summary of results (if requested)",
    )


class UploadPhotoResponse(BaseModel):
    """Response model for photo upload."""

    success: bool = Field(..., description="Whether upload was successful")
    document_id: str = Field(..., description="ID of the indexed document")
    extracted_text: str = Field(..., description="Text extracted from the image")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="OCR confidence score",
    )
    message: str = Field(..., description="Status message")
    metadata: dict = Field(default_factory=dict, description="Document metadata")


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error message")
    error_type: str | None = Field(None, description="Type of error")
