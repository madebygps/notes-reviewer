# Code Review Fixes Checklist

Track progress on addressing code review findings.

---

## 🚨 Critical Issues (Priority: URGENT)

### Issue #1: Blocking I/O in Async Functions
- [ ] Fix `EmbeddingService.generate_embedding()` to use `run_in_executor`
- [ ] Fix `EmbeddingService.generate_embeddings_batch()` to use `run_in_executor`
- [ ] Fix `SearchService.search()` to wrap ChromaDB calls
- [ ] Fix `SearchService.add_document()` to wrap ChromaDB calls
- [ ] Fix `SearchService.add_documents_batch()` to wrap ChromaDB calls
- [ ] Fix `LLMService.summarize_search_results()` to use `run_in_executor`
- [ ] Test async performance under concurrent load
- [ ] Verify event loop is not blocked

**Files to Update**:
- `services/embedding_service.py`
- `services/search_service.py`
- `services/llm_service.py`

**Estimated Time**: 4-6 hours

---

### Issue #2: Missing Structured Logging
- [ ] Add logging configuration to `config.py`
- [ ] Replace all `print()` statements with `logger` calls in `main.py`
- [ ] Add logger to `EmbeddingService`
- [ ] Add logger to `SearchService`
- [ ] Add logger to `OCRService`
- [ ] Add logger to `LLMService`
- [ ] Add logger to `routers/api.py`
- [ ] Add logger to all scripts
- [ ] Configure log levels via environment variable
- [ ] Test logging output in different environments

**Files to Update**:
- `config.py`
- `main.py`
- `services/embedding_service.py`
- `services/search_service.py`
- `services/ocr_service.py`
- `services/llm_service.py`
- `routers/api.py`
- `scripts/*.py`

**Estimated Time**: 3-4 hours

---

## ⚠️ High Priority Issues (Priority: HIGH)

### Issue #3: Type Safety Gaps
- [ ] Create `SearchResults` TypedDict in `models.py`
- [ ] Update `SearchService.search()` return type
- [ ] Create `OCRResult` TypedDict
- [ ] Update `OCRService.extract_text_from_image()` return type
- [ ] Review all service methods for proper return types
- [ ] Add type hints to all helper functions
- [ ] Run mypy to verify type safety

**Files to Update**:
- `models.py`
- `services/search_service.py`
- `services/ocr_service.py`

**Estimated Time**: 2-3 hours

---

### Issue #4: Insufficient Input Validation
- [ ] Add `max_file_size_mb` to `Config`
- [ ] Add file size validation in `upload_photo` endpoint
- [ ] Add empty string validation in services
- [ ] Add text length limits (prevent 100MB+ strings)
- [ ] Add batch size limits for bulk operations
- [ ] Add metadata structure validation
- [ ] Update `.env.example` with new config options
- [ ] Test with edge cases (empty, huge, malformed inputs)

**Files to Update**:
- `config.py`
- `routers/api.py`
- `services/*.py`
- `.env.example`

**Estimated Time**: 3-4 hours

---

### Issue #5: Inconsistent Error Handling
- [ ] Create `exceptions.py` with custom exception classes
- [ ] Define `ServiceError` base exception
- [ ] Define `EmbeddingError` exception
- [ ] Define `SearchError` exception
- [ ] Define `OCRError` exception
- [ ] Define `LLMError` exception
- [ ] Define `ValidationError` exception
- [ ] Update all services to use custom exceptions
- [ ] Update routers to catch and convert custom exceptions
- [ ] Test error handling with invalid inputs

**Files to Create/Update**:
- `exceptions.py` (new)
- `services/*.py`
- `routers/api.py`

**Estimated Time**: 3-4 hours

---

### Issue #6: Missing Async Safety in ChromaDB
- [ ] Wrap `collection.query()` calls in executor
- [ ] Wrap `collection.add()` calls in executor
- [ ] Wrap `collection.get()` calls in executor
- [ ] Wrap `collection.count()` calls in executor
- [ ] Wrap `client.delete_collection()` calls in executor
- [ ] Test ChromaDB operations under load

**Files to Update**:
- `services/search_service.py`

**Estimated Time**: 2-3 hours

---

## 📋 Medium Priority Issues (Priority: MEDIUM)

### Issue #7: Code Duplication in Scripts
- [ ] Create `scripts/common.py` module
- [ ] Add `init_services()` helper function
- [ ] Add `setup_logging()` helper function
- [ ] Update `index_documents.py` to use helpers
- [ ] Update `ingest_photos.py` to use helpers
- [ ] Update `view_collection.py` to use helpers
- [ ] Test all scripts still work correctly

**Files to Create/Update**:
- `scripts/common.py` (new)
- `scripts/index_documents.py`
- `scripts/ingest_photos.py`
- `scripts/view_collection.py`

**Estimated Time**: 2-3 hours

---

### Issue #8: Missing Rate Limiting
- [ ] Add `slowapi` dependency: `uv add slowapi`
- [ ] Configure rate limiter in `main.py`
- [ ] Add rate limiting to `/api/v1/search` endpoint
- [ ] Add rate limiting to `/api/v1/upload/photo` endpoint
- [ ] Configure rate limits via environment variables
- [ ] Test rate limiting behavior
- [ ] Document rate limits in README

**Files to Update**:
- `pyproject.toml`
- `main.py`
- `routers/api.py`
- `README.md`

**Estimated Time**: 2-3 hours

---

### Issue #9: Incomplete Health Check
- [ ] Update `/health` endpoint to check Ollama connection
- [ ] Update `/health` endpoint to check ChromaDB connection
- [ ] Return 503 if any dependency is unhealthy
- [ ] Add detailed health check response with sub-checks
- [ ] Test health endpoint with services down
- [ ] Document health check response format

**Files to Update**:
- `main.py`
- `README.md`

**Estimated Time**: 2-3 hours

---

### Issue #10: Missing OpenAPI Examples
- [ ] Add request example for `/api/v1/search` endpoint
- [ ] Add response examples for `/api/v1/search` endpoint
- [ ] Add request example for `/api/v1/upload/photo` endpoint
- [ ] Add response examples for `/api/v1/upload/photo` endpoint
- [ ] Add error response examples
- [ ] Verify examples appear in `/docs` UI

**Files to Update**:
- `routers/api.py`

**Estimated Time**: 1-2 hours

---

## 🧪 Testing Tasks

### Unit Tests
- [ ] Set up pytest infrastructure: `uv add --dev pytest pytest-asyncio pytest-cov httpx`
- [ ] Create `tests/` directory structure
- [ ] Write tests for `EmbeddingService`
- [ ] Write tests for `SearchService`
- [ ] Write tests for `OCRService`
- [ ] Write tests for `LLMService`
- [ ] Achieve 70%+ code coverage
- [ ] Add tests to CI pipeline

**Estimated Time**: 2-3 days

---

### Integration Tests
- [ ] Write API endpoint tests
- [ ] Test `/api/v1/search` with mock data
- [ ] Test `/api/v1/upload/photo` with test images
- [ ] Test error handling paths
- [ ] Test concurrent request handling
- [ ] Test rate limiting behavior

**Estimated Time**: 1-2 days

---

## 🔒 Security Tasks

### Authentication & Authorization
- [ ] Design API key authentication strategy
- [ ] Implement API key validation middleware
- [ ] Add API key to configuration
- [ ] Update all endpoints to require authentication
- [ ] Document authentication in README
- [ ] Test authentication behavior

**Estimated Time**: 1-2 days

---

### Security Hardening
- [ ] Add request size limits globally
- [ ] Validate and sanitize all metadata inputs
- [ ] Add HTTPS enforcement in production
- [ ] Review CORS configuration for production
- [ ] Implement secrets management solution
- [ ] Run security audit on dependencies: `uv add --dev safety && uv run safety check`
- [ ] Document security best practices

**Estimated Time**: 2-3 days

---

## 📊 Progress Tracking

### Overall Progress
- Critical Issues: 0/2 (0%)
- High Priority: 0/4 (0%)
- Medium Priority: 0/4 (0%)
- Testing: 0/2 (0%)
- Security: 0/2 (0%)

**Total**: 0/14 (0%)

---

## 📅 Suggested Timeline

### Week 1: Critical Fixes
- Days 1-2: Fix blocking I/O issues
- Days 3-4: Add structured logging
- Day 5: Testing and verification

### Week 2: High Priority Fixes
- Days 1-2: Type safety and input validation
- Days 3-4: Error handling improvements
- Day 5: Testing and verification

### Week 3: Medium Priority & Testing
- Days 1-2: Code cleanup and rate limiting
- Days 3-5: Unit and integration tests

### Week 4: Security & Documentation
- Days 1-3: Authentication and security hardening
- Days 4-5: Documentation updates and final testing

---

## 🎯 Definition of Done

For each issue, consider it "done" when:
- [ ] Code changes implemented
- [ ] Code reviewed by team member
- [ ] Unit tests added (where applicable)
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] Changes tested in dev environment
- [ ] No regressions in existing functionality
- [ ] Code follows project style guide

---

## 📝 Notes

- Update this checklist as you complete tasks
- Add any additional tasks discovered during implementation
- Link PRs to specific checklist items
- Celebrate progress! 🎉

---

*Last Updated: 2025-10-18*  
*Next Review: After Phase 1 completion*
