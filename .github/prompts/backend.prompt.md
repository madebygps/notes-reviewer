---
mode: agent
---

Build the backend for a notes search application with local vector storage and OCR capabilities:


**Backend (FastAPI with uv):**

- Use ChromaDB as the local vector database (persistent storage in `./chroma_db`)
- Use Ollama with `embeddinggemma:latest` model (768 dimensions) for generating embeddings
- Environment configuration via python-dotenv (`.env` file)
  - Defaults in code: `embeddinggemma:latest`, `./chroma_db`, `notes` collection
  - Override via `.env` file for custom configurations
- Two main endpoints:
  - `POST /api/v1/search` - Vector similarity search with configurable top_k
  - `POST /api/v1/upload/photo` - Upload photos, extract text via OCR, and auto-index
- Services architecture:
  - `EmbeddingService` - Wraps Ollama client for embedding generation
  - `SearchService` - Handles ChromaDB queries and result formatting
- CORS enabled for Angular dev server (localhost:4200)

**OCR Processing:**

- Tesseract OCR for local text extraction from images
- Supported formats: JPG, PNG, TIFF, BMP
- Quality validation: minimum text length, OCR confidence scoring
- Metadata tracking: source type, confidence %, file info, timestamps
- Scripts:
  - `scripts/index_documents.py` - Index text files or JSON documents
  - `scripts/ingest_photos.py` - Batch process photos from directories
  - `scripts/view_collection.py` - View/search ChromaDB contents