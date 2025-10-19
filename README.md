# Notes Reviewer

A full-stack application for searching and managing handwritten notes using OCR and vector search. Built as a demo for ngConf, showcasing AI-assisted development with Claude Code.

## What It Does

Notes Reviewer lets you:
- Upload photos of handwritten notes
- Extract text using OCR (Tesseract)
- Store notes in a vector database for semantic search
- Search your notes using natural language queries

The backend uses FastAPI with ChromaDB for vector storage and Ollama for embeddings. The frontend is built with Angular 20.

## How It Works

1. User uploads a photo of handwritten notes through the Angular frontend
2. Backend processes the image with Tesseract OCR to extract text
3. Text is converted to embeddings using Ollama's embeddinggemma model
4. Embeddings are stored in ChromaDB (local vector database)
5. Users can search notes semantically - similar concepts match even with different words
6. Results are ranked by cosine similarity and returned to the frontend

## Development Notes

This project was built using AI-assisted development:
- Backend: Generated using the backend prompt file with Claude Code
- Frontend: Generated using the frontend prompt file with Claude Code

## Prerequisites

**Backend:**
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- [Ollama](https://ollama.ai/) with `embeddinggemma:latest` model
- Tesseract OCR

**Frontend:**
- Node.js 18+
- Angular CLI

## Setup & Installation

### Backend Setup

1. Install Tesseract OCR:
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   ```

2. Install Ollama and pull the embedding model:
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh

   # Pull the model
   ollama pull embeddinggemma:latest
   ```

3. Install Python dependencies:
   ```bash
   cd backend
   uv sync
   ```

4. (Optional) Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

### Frontend Setup

```bash
npm install
```

## Running the Application

### 1. Start the Backend

```bash
cd backend
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- http://localhost:8000
- API docs: http://localhost:8000/docs

### 2. Start the Frontend

```bash
ng serve
```

The application will be available at http://localhost:4200

## Project Structure

```
notes-reviewer/
├── backend/              # FastAPI backend
│   ├── main.py          # Application entry point
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic (OCR, embeddings, search)
│   └── scripts/         # Utility scripts for indexing
└── src/                 # Angular frontend
    ├── app/
    │   ├── pages/       # Page components
    │   ├── services/    # API services
    │   └── components/  # Reusable components
    └── styles/          # Global styles
```

## API Endpoints

- `POST /api/v1/upload/photo` - Upload and process a photo of notes
- `POST /api/v1/search` - Search notes using natural language
- `GET /health` - Health check

## Additional Commands

### Backend Utility Scripts

Index text files:
```bash
cd backend
uv run python scripts/index_documents.py path/to/files/
```

Batch process photos:
```bash
uv run python scripts/ingest_photos.py path/to/photos/
```

View collection contents:
```bash
uv run python scripts/view_collection.py --stats
```

### Frontend Build

```bash
ng build
```

Production build will be in `dist/` directory.

## License

MIT
