"""Service for OCR text extraction from images using Tesseract."""

from __future__ import annotations

import io
from datetime import datetime
from functools import lru_cache

import pytesseract
from PIL import Image

from config import Config, get_config


class OCRService:
    """Handles OCR text extraction with quality validation."""

    # Supported image formats
    SUPPORTED_FORMATS = {"jpg", "jpeg", "png", "tiff", "tif", "bmp"}

    def __init__(self, config: Config) -> None:
        """Initialize the OCR service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.min_text_length = config.min_text_length
        self.min_confidence = config.min_ocr_confidence

    async def extract_text_from_image(
        self,
        image_bytes: bytes,
        filename: str,
    ) -> dict:
        """Extract text from image using OCR.

        Args:
            image_bytes: Image file bytes
            filename: Original filename for metadata

        Returns:
            Dictionary containing extracted text, confidence, and metadata

        Raises:
            ValueError: If image format is not supported or quality is too low
            Exception: If OCR processing fails
        """
        try:
            # Validate file format
            file_extension = filename.lower().split(".")[-1]
            if file_extension not in self.SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported image format: {file_extension}. "
                    f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                )

            # Load image
            image = Image.open(io.BytesIO(image_bytes))

            # Perform OCR with detailed output
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
            )

            # Extract text
            text = pytesseract.image_to_string(image).strip()

            # Calculate average confidence
            confidences = [
                int(conf) for conf in ocr_data["conf"] if int(conf) > 0
            ]
            avg_confidence = (
                sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            )

            # Validate text quality
            if len(text) < self.min_text_length:
                raise ValueError(
                    f"Extracted text too short ({len(text)} chars). "
                    f"Minimum required: {self.min_text_length} chars"
                )

            if avg_confidence < self.min_confidence:
                raise ValueError(
                    f"OCR confidence too low ({avg_confidence:.2%}). "
                    f"Minimum required: {self.min_confidence:.2%}"
                )

            # Prepare metadata
            metadata = {
                "source_type": "photo",
                "filename": filename,
                "confidence": avg_confidence,
                "text_length": len(text),
                "image_width": image.width,
                "image_height": image.height,
                "image_format": image.format or file_extension.upper(),
                "timestamp": datetime.utcnow().isoformat(),
                "word_count": len([w for w in ocr_data["text"] if w.strip()]),
            }

            return {
                "text": text,
                "confidence": avg_confidence,
                "metadata": metadata,
            }

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}") from e

    def validate_image_format(self, filename: str) -> bool:
        """Check if the image format is supported.

        Args:
            filename: Filename to validate

        Returns:
            True if format is supported, False otherwise
        """
        file_extension = filename.lower().split(".")[-1]
        return file_extension in self.SUPPORTED_FORMATS


@lru_cache
def get_ocr_service() -> OCRService:
    """Get cached OCR service instance.

    Returns:
        OCRService instance
    """
    config = get_config()
    return OCRService(config)
