# Cross-Language Standards

## Documentation

**Python (Google style):**
```python
def search_chunks(
    query: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """Search knowledge base for relevant chunks.
    
    Args:
        query: Search query string.
        top_k: Number of results to return (default: 10).
    
    Returns:
        List of chunks with scores, sorted by relevance.
    
    Raises:
        SearchError: If search engine is unavailable.
    """
```

**Go (comment style):**
```go
// Search searches the knowledge base for relevant chunks.
// 
// top_k limits the number of results returned (default: 10).
// Returns an error if the search engine is unavailable.
func (s *Service) Search(ctx context.Context, query string, topK int) ([]Chunk, error) {
```

**TypeScript (JSDoc style):**
```typescript
/**
 * Search knowledge base for relevant chunks.
 * @param query - Search query string
 * @param topK - Number of results to return (default: 10)
 * @returns List of chunks sorted by relevance
 * @throws {SearchError} If search engine is unavailable
 */
export async function searchChunks(
    query: string,
    topK: number = 10
): Promise<Chunk[]> {
```

## Commit Message Format

**Conventional commits:**
```
feat: add GraphRAG entity extraction
fix: reject empty content in update_chunk API
docs: update deployment guide for Kubernetes
refactor: simplify search dealer logic
test: add integration tests for chunking
chore: upgrade dependencies
```

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, refactor, test, chore, perf, style  
**Scope (optional):** api, rag, agent, deepdoc, frontend  
**Subject:** Present tense, no period, capitalize first letter

## Security Best Practices

**Secrets Management:**
- Never commit `.env`, credentials, keys
- Use environment variables for all secrets
- `.env.example` for non-secret defaults

**Input Validation:**
```python
# Python
@beartype.beartype
def update_chunk(chunk_id: str, content: str) -> Chunk:
    if not content.strip():
        raise ValueError("Content cannot be empty or whitespace-only")
```

**SQL Injection Prevention:**
```python
# Good: Parameterized queries
documents = db.select(Document).where(Document.id == doc_id)

# Bad: String concatenation
documents = db.raw(f"SELECT * FROM documents WHERE id = '{doc_id}'")
```

## Performance Optimization

**Profiling Tools:**
- **Python:** `cProfile`, `memory_profiler`, `py-spy`
- **Go:** `pprof`, `benchstat`
- **TypeScript:** Chrome DevTools, Lighthouse

**Caching Patterns:**
```python
# Python LRU cache
from functools import lru_cache

@lru_cache(maxsize=1024)
def get_embedding_model(model_name: str):
    return load_model(model_name)
```

```go
// Go with time-based expiry
import "github.com/patrickmn/go-cache"

c := cache.New(5 * time.Minute, 10 * time.Minute)
c.Set("key", value, cache.DefaultExpiration)
```

## Architecture Principles

### YAGNI (You Aren't Gonna Need It)
- Don't build features "just in case"
- Wait for concrete requirements
- Delete unused code

### KISS (Keep It Simple, Stupid)
- Prefer simple solutions
- Avoid over-engineering
- Clear code > clever code

### DRY (Don't Repeat Yourself)
- Extract common patterns
- Use shared utilities
- Reduce duplication to <5%

### SOLID Principles
- **S:** Single Responsibility — one reason to change
- **O:** Open/Closed — open for extension, closed for modification
- **L:** Liskov Substitution — subtypes interchangeable
- **I:** Interface Segregation — small, specific interfaces
- **D:** Dependency Inversion — depend on abstractions

## Code Review Checklist

### Before Submitting PR
- [ ] Code follows language-specific standards
- [ ] Tests written and passing (>75% coverage)
- [ ] No hardcoded secrets, credentials
- [ ] Type hints/annotations complete
- [ ] Error handling explicit (no silent failures)
- [ ] Comments explain "why", not "what"
- [ ] Commit messages follow conventional format

### During Review
- [ ] Logic is correct and handles edge cases
- [ ] Performance impact assessed
- [ ] Backward compatibility maintained
- [ ] Documentation updated (if needed)
- [ ] No security vulnerabilities introduced
- [ ] Code is maintainable (readability > cleverness)

## Testing Standards

### Coverage Requirements
- **Critical paths:** >85% coverage
- **API endpoints:** >80% coverage
- **Utilities:** >75% coverage
- **UI components:** >70% coverage

### Test Types
- **Unit tests:** Individual functions/methods
- **Integration tests:** Cross-component interactions
- **API tests:** HTTP endpoint behavior
- **E2E tests:** Full user workflows

### Test Organization
```
test/
├── unit/           # Fast, isolated tests
├── integration/    # Cross-component tests
├── api/            # HTTP endpoint tests
└── e2e/            # Full workflow tests
```

## Performance Targets

| Layer | Metric | Target |
|-------|--------|--------|
| **Search** | Query latency (p95) | <1s |
| **API** | Response time (avg) | <500ms |
| **Database** | Query time (avg) | <100ms |
| **Frontend** | Page load time | <3s |
| **Embedding** | Throughput | 10K chunks/min |
| **Tokenizer** | Throughput | 50K tokens/sec |

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
