# Go Code Standards

## File Organization

**Naming Convention:**
- Files: `snake_case.go`
- Packages: Short, lowercase (e.g., `entity`, `service`, `handler`)
- Public types/functions: `PascalCase`
- Private functions: `camelCase`

**Directory Structure:**
```
internal/
├── service/        # Business logic (16+ services)
├── handler/        # HTTP handlers
├── dao/            # Data access (GORM)
├── entity/         # GORM models
├── cache/          # Redis wrappers
├── storage/        # MinIO, S3, etc.
├── admin/          # Admin service
└── cli/            # CLI tool
```

## Type System & Error Handling

**No panic in production code:**
```go
// Bad
func ProcessDocument(docID string) {
    doc := db.Get(docID) // Panics if not found
}

// Good
func ProcessDocument(docID string) error {
    doc, err := db.Get(docID)
    if err != nil {
        return fmt.Errorf("get document: %w", err)
    }
    return nil
}
```

**Error wrapping:**
```go
import "fmt"

if err != nil {
    return fmt.Errorf("process chunk %s: %w", chunkID, err)
}
```

**Logging with zap:**
```go
import "go.uber.org/zap"

logger.Info("document processed", zap.String("doc_id", docID))
logger.Error("parse failed", zap.Error(err), zap.String("file", filePath))
```

## Database Access (GORM)

**Pattern:**
```go
type Document struct {
    ID       string `gorm:"primaryKey"`
    KBId     string `gorm:"index"`
    Name     string
    Status   string
    CreatedAt time.Time
}

// DAO layer
func (d *DocumentDAO) Create(ctx context.Context, doc *Document) error {
    return d.db.WithContext(ctx).Create(doc).Error
}

func (d *DocumentDAO) BatchUpdate(
    ctx context.Context,
    docIDs []string,
    status string,
) error {
    return d.db.WithContext(ctx).
        Model(&Document{}).
        Where("id IN ?", docIDs).
        Update("status", status).
        Error
}
```

**Best Practices:**
- Use `context.Context` in all methods
- Transactions: `db.WithContext(ctx).BeginTx(...)`
- Indexes on frequently queried columns
- Avoid N+1 queries (use `Preload()`)

## Concurrent Programming

**Goroutines with context:**
```go
func ProcessDocuments(ctx context.Context, docIDs []string) error {
    sem := make(chan struct{}, 10) // Limit concurrency
    errChan := make(chan error, len(docIDs))
    
    for _, docID := range docIDs {
        go func(id string) {
            sem <- struct{}{}
            defer func() { <-sem }()
            
            if err := process(ctx, id); err != nil {
                errChan <- err
            }
        }(docID)
    }
    
    // Collect errors
    for range docIDs {
        if err := <-errChan; err != nil {
            return err
        }
    }
    return nil
}
```

## Testing

**File placement:**
- `*_test.go` in same package as code being tested

**Pattern:**
```go
func TestDocumentCreate(t *testing.T) {
    db := setupTestDB(t)
    defer db.Close()
    
    doc := &Document{ID: "doc-1", Name: "test.pdf"}
    err := dao.Create(context.Background(), doc)
    
    if err != nil {
        t.Fatalf("Create failed: %v", err)
    }
    
    result, _ := dao.Get(context.Background(), "doc-1")
    if result.Name != "test.pdf" {
        t.Errorf("got %s, want test.pdf", result.Name)
    }
}
```

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
