# Notes Reviewer Backend

Backend API for a notes search application with local vector storage and OCR capabilities.

## Features

- **Vector Search**: ChromaDB for local persistent vector storage with cosine similarity
- **Embeddings**: Ollama with `embeddinggemma:latest` model (768 dimensions)
- **OCR Processing**: Tesseract OCR for text extraction from images
- **Quality Validation**: Minimum text length and confidence scoring
- **REST API**: FastAPI with automatic OpenAPI documentation
- **CORS Enabled**: Configured for Angular dev server (localhost:4200)

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- [Ollama](https://ollama.ai/) running locally with `embeddinggemma:latest` model
- Tesseract OCR installed on your system

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Install Ollama and Pull Model

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the embedding model
ollama pull embeddinggemma:latest
```

## Setup

1. **Install dependencies:**
   ```bash
   cd backend
   uv sync
   ```

2. **Configure environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env to customize settings
   ```

   Default configuration:
   - Ollama model: `embeddinggemma:latest`
   - ChromaDB path: `./chroma_db`
   - Collection name: `notes`
   - Min text length: 10 chars
   - Min OCR confidence: 0.5

## Running the Server

**Development mode with auto-reload:**
```bash
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Production mode:**
```bash
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Search Documents
```http
POST /api/v1/search
Content-Type: application/json

{
  "query": "search text",
  "top_k": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "doc-id",
      "text": "document content",
      "distance": 0.123,
      "metadata": {...}
    }
  ],
  "query": "search text",
  "total_results": 5
}
```

### Upload Photo
```http
POST /api/v1/upload/photo
Content-Type: multipart/form-data

file: <image file>
```

**Supported formats**: JPG, PNG, TIFF, BMP

**Response:**
```json
{
  "success": true,
  "document_id": "uuid",
  "extracted_text": "text from image",
  "confidence": 0.95,
  "message": "Photo processed and indexed successfully",
  "metadata": {
    "source_type": "photo",
    "filename": "image.jpg",
    "confidence": 0.95,
    "text_length": 123,
    "image_width": 1920,
    "image_height": 1080,
    "word_count": 20,
    "timestamp": "2025-10-17T12:00:00"
  }
}
```

### Health Check
```http
GET /health
```

## Utility Scripts

### Index Documents

Index text files or JSON documents:

```bash
# Index a single text file
uv run python scripts/index_documents.py path/to/file.txt

# Index all text files in a directory
uv run python scripts/index_documents.py path/to/directory/

# Index JSON documents
uv run python scripts/index_documents.py path/to/documents.json

# Reset collection before indexing
uv run python scripts/index_documents.py path/to/directory/ --reset

# Custom file pattern
uv run python scripts/index_documents.py path/to/directory/ --pattern "*.md"
```

**JSON format for batch indexing:**
```json
[
  {
    "text": "Document content here",
    "metadata": {
      "title": "Document Title",
      "author": "Author Name"
    }
  }
]
```

### Ingest Photos

Batch process photos with OCR:

```bash
# Process a single photo
uv run python scripts/ingest_photos.py path/to/photo.jpg

# Process all photos in a directory
uv run python scripts/ingest_photos.py path/to/photos/

# Process recursively
uv run python scripts/ingest_photos.py path/to/photos/ --recursive

# Reset collection before processing
uv run python scripts/ingest_photos.py path/to/photos/ --reset
```

### View Collection

View and search collection contents:

```bash
# Show collection info (default)
uv run python scripts/view_collection.py

# Show detailed statistics
uv run python scripts/view_collection.py --stats

# View all documents
uv run python scripts/view_collection.py --all

# Search for documents
uv run python scripts/view_collection.py --search "query text"

# Search with custom top_k
uv run python scripts/view_collection.py --search "query text" --top-k 10
```

## Architecture

### Services

- **EmbeddingService** (`services/embedding_service.py`)
  - Wraps Ollama client for embedding generation
  - Supports single and batch embedding generation
  - Configurable model via environment variables

- **SearchService** (`services/search_service.py`)
  - Manages ChromaDB collection
  - Handles document indexing and similarity search
  - Supports batch operations
  - Persistent storage with automatic collection creation

- **OCRService** (`services/ocr_service.py`)
  - Text extraction using Tesseract OCR
  - Quality validation (text length, confidence)
  - Metadata tracking (dimensions, format, timestamps)
  - Supports multiple image formats

### Models

All request/response models use Pydantic for validation:
- `SearchRequest` / `SearchResponse`
- `UploadPhotoResponse`
- `ErrorResponse`

### Configuration

Environment-based configuration with sensible defaults:
- Loads from `.env` file if present
- Falls back to hardcoded defaults
- Immutable config object with `@dataclass(frozen=True)`

## Development

### Project Structure

```
backend/
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── models.py              # Pydantic models
├── routers/
│   └── api.py            # API endpoints
├── services/
│   ├── embedding_service.py
│   ├── search_service.py
│   └── ocr_service.py
├── scripts/
│   ├── index_documents.py
│   ├── ingest_photos.py
│   └── view_collection.py
├── .env.example          # Example environment variables
└── pyproject.toml        # Project dependencies
```

### Adding Dependencies

```bash
uv add package-name
```

### Code Style

- Type hints for all function parameters and return values
- Docstrings for classes and public methods
- Async/await for I/O operations
- Dependency injection via FastAPI's `Depends()`
- Service layer pattern for business logic

## Troubleshooting

### Ollama Connection Issues

Ensure Ollama is running:
```bash
ollama serve
```

Check if model is available:
```bash
ollama list
```

### ChromaDB Errors

Reset the collection:
```bash
uv run python scripts/view_collection.py
# Then use index_documents.py with --reset flag
```

### Tesseract Not Found

Verify Tesseract installation:
```bash
tesseract --version
```

If installed but not found, set the path in environment:
```bash
export TESSERACT_PATH=/usr/local/bin/tesseract
```

### Low OCR Quality

Adjust quality thresholds in `.env`:
```bash
MIN_TEXT_LENGTH=5
MIN_OCR_CONFIDENCE=0.3
```

## License

MIT
