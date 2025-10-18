---
applyTo: '**.py'
---

# Python & FastAPI Development Rules

## Project Setup (uv)

- Use `uv init` to create a new project
- Use `uv add <package>` to add dependencies
- Use `uv sync` to install dependencies after cloning
- Use `uv run <command>` to execute commands in the project environment
- Use `uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload` for development server
- Do NOT use pip, conda, or poetry for dependency management

## Type Safety

- Use type hints for ALL function parameters and return values
- Use `from __future__ import annotations` for forward references
- Prefer `dataclass(frozen=True)` for immutable configuration objects
- Use Pydantic models for request and response validation
- Use Field() for validation, defaults, and documentation

## Routing & Endpoints

- Use appropriate HTTP methods with path operation decorators (@router.get, @router.post, etc.)
- Use APIRouter for organizing routes by feature or resource
- Use proper status codes for responses (201 for creation, 404 for not found, 400 for validation, 503 for service unavailable)
- Use path parameters for resource identifiers, query parameters for filters/options
- Group related endpoints under a common prefix (e.g., `/api/v1/resource`)

## Dependency Injection

- Use FastAPI's Depends() for shared logic like database connections, authentication, and service instances
- Use `@lru_cache` for singleton pattern with factory functions
- Use `Annotated[Type, Depends(func)]` for cleaner dependency declarations
- Implement proper cleanup in lifespan context managers

## Architecture Patterns

- Separate concerns: routers → services → data layer
- Create service classes for business logic
- Use dependency injection to wire services together
- Keep routers thin - delegate complex logic to services
- Centralize configuration in a dedicated module (environment variables, app settings)
- Create a dedicated module for shared dependency factories

## Error Handling

- Raise HTTPException with appropriate status codes and detail messages
- Use try/except blocks to catch service-level errors
- Convert service exceptions to HTTPException in routers
- Provide user-friendly error messages in the `detail` field

## Async/Sync

- Use `async def` for I/O-bound operations (database queries, HTTP calls, file operations)
- Use regular `def` for CPU-bound operations
- Use background tasks for non-blocking operations that don't need to return immediately
- Do NOT mix blocking I/O in async functions

## Request/Response Models

- Define Pydantic models in a `models.py` file
- Use descriptive model names with suffixes like `Request`, `Response`, `Payload`
- Use separate models for requests and responses (don't reuse)

## File Uploads

- Add `python-multipart` dependency for form data and file uploads
- Use `UploadFile` type for file upload parameters
- Validate file types and sizes before processing
- Handle large files with streaming when possible

## CORS Configuration

- Configure CORS explicitly with CORSMiddleware
- Specify exact origins instead of using `allow_origins=["*"]` in production
- Set appropriate `allow_methods` and `allow_headers`

## Code Style

- Follow PEP 8 style guidelines
- Use descriptive variable and function names
- Keep functions focused and under 50 lines when possible
- Add docstrings to classes and public methods
- Use f-strings for string formatting
- Prefer explicit imports over wildcard imports

