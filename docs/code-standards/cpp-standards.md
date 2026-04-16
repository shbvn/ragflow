# C++ Code Standards

## File Organization

**File Structure:**
```
internal/cpp/
├── rag_tokenizer.cpp    # Implementation
├── rag_tokenizer.h      # Header
└── CMakeLists.txt       # Build config
```

**Naming Convention:**
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Macros: `RAG_<FEATURE_NAME>`

## Memory Management

**RAII pattern (stack allocation preferred):**
```cpp
// Good: Stack allocation, automatic cleanup
class TokenizerPool {
private:
    std::vector<Analyzer> analyzers; // Auto-freed
    
public:
    TokenizerPool(size_t pool_size) {
        for (size_t i = 0; i < pool_size; ++i) {
            analyzers.emplace_back();
        }
    }
};

// Acceptable: Smart pointers
auto analyzer = std::make_unique<Analyzer>();
auto shared = std::make_shared<Dictionary>();
```

**No manual `new`/`delete`:**
```cpp
// Bad
Analyzer* a = new Analyzer();
// ...
delete a; // Easy to leak

// Good
auto a = std::make_unique<Analyzer>();
// Auto-deleted at scope exit
```

## Error Handling

**Exceptions for exceptional cases:**
```cpp
class TokenizeError : public std::runtime_error {
public:
    TokenizeError(const std::string& msg)
        : std::runtime_error(msg) {}
};

std::vector<std::string> tokenize(const std::string& text) {
    if (text.empty()) {
        throw TokenizeError("Empty text");
    }
    // Process...
}
```

## Testing

**Google Test framework:**
```cpp
#include <gtest/gtest.h>
#include "rag_tokenizer.h"

TEST(TokenizerTest, TokenizesSimpleText) {
    Analyzer analyzer;
    auto tokens = analyzer.tokenize("hello world");
    ASSERT_EQ(tokens.size(), 2);
    EXPECT_EQ(tokens[0], "hello");
}

TEST(TokenizerTest, HandlesChineseText) {
    Analyzer analyzer;
    auto tokens = analyzer.tokenize("你好世界");
    ASSERT_EQ(tokens.size(), 4); // One char per token
}
```

---

**Version:** 0.24.0  
**Last Updated:** 2026-04-16
