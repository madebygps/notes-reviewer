"""Application configuration using environment variables with defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass(frozen=True)
class Config:
    """Application configuration with defaults."""

    # Ollama Configuration
    ollama_model: str = os.getenv("OLLAMA_MODEL", "embeddinggemma:latest")
    ollama_llm_model: str = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:latest")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # ChromaDB Configuration
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "notes")

    # OCR Configuration
    min_text_length: int = int(os.getenv("MIN_TEXT_LENGTH", "10"))
    min_ocr_confidence: float = float(os.getenv("MIN_OCR_CONFIDENCE", "0.5"))

    # API Configuration
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] | None = None

    def __post_init__(self) -> None:
        """Set default CORS origins if not provided."""
        if self.cors_origins is None:
            object.__setattr__(
                self,
                "cors_origins",
                ["http://localhost:4200", "http://127.0.0.1:4200"],
            )


@lru_cache
def get_config() -> Config:
    """Get cached configuration instance."""
    return Config()
