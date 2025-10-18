---
mode: agent
---

Build the frontend for notes search application with local vector storage and OCR capabilities:


**Frontend (Angular 20):**

- Modern Angular with standalone components (no NgModules)
- Signal-based reactive state management
- Two main routes:
  - `/` (Search) - Vector search interface with reactive forms
  - `/upload` - Photo upload with drag-and-drop support
- Search features:
  - Query input with validation (min 2 chars)
  - Configurable top_k results (1-50)
  - Results table: document name, content preview, relevance score
  - Error handling with user-friendly messages
  - Loading states and empty state handling
- Upload features:
  - File validation (type and size < 10MB)
  - Real-time upload progress
  - OCR results display (extracted text, confidence, metadata)
  - Immediate search availability after upload
- Styling:
  - Gradient backgrounds and modern UI
  - Responsive design with mobile breakpoints
  - Sticky navigation header
  - Active route highlighting
