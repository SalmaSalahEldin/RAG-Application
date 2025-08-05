# Semantic Chunking Implementation Guide

## 🎯 Overview

This guide explains the semantic chunking implementation in the RAG project, which uses LangChain's `SemanticChunker` to create more intelligent text chunks based on semantic meaning rather than just character count.

## 🏗️ Architecture

### Components

1. **`SemanticChunkerUtility`** (`src/utils/semantic_chunker.py`)
   - Core semantic chunking functionality
   - Integration with LangChain's `SemanticChunker`
   - Fallback mechanisms for robustness

2. **Enhanced `ProcessController`** (`src/controllers/ProcessController.py`)
   - Backward-compatible integration
   - Multiple chunking methods support
   - Statistics and monitoring

3. **Updated API Endpoints** (`src/routes/data.py`)
   - New `chunking_method` parameter
   - Enhanced processing options

## 🚀 Features

### Multiple Chunking Methods

#### 1. **Semantic Chunking** (Default)
- Uses LangChain's `SemanticChunker` with OpenAI embeddings
- Breaks text at semantic boundaries
- Maintains context and meaning
- **Best for**: Complex documents, research papers, technical content

#### 2. **Sentence-Based Chunking**
- Splits text at sentence boundaries
- Respects natural language structure
- **Best for**: General documents, articles, reports

#### 3. **Simple Chunking** (Fallback)
- Character-based splitting with overlap
- Robust fallback when semantic chunking fails
- **Best for**: Simple text, when API is unavailable

### Configuration Options

```python
# ProcessRequest schema
class ProcessRequest(BaseModel):
    file_id: str = None
    chunk_size: Optional[int] = 1000        # Maximum chunk size
    overlap_size: Optional[int] = 200       # Overlap between chunks
    do_reset: Optional[int] = 0             # Reset existing chunks
    chunking_method: Optional[str] = "semantic"  # "semantic", "sentence", "simple"
```

## 📋 Usage Examples

### 1. Basic Semantic Chunking

```python
from utils.semantic_chunker import SemanticChunkerUtility

# Initialize chunker
chunker = SemanticChunkerUtility()

# Sample text
texts = [
    "This is the first paragraph with important information.",
    "This is the second paragraph with additional context.",
    "This is the third paragraph concluding the topic."
]

# Perform semantic chunking
chunks = chunker.chunk_text_semantically(
    texts=texts,
    metadatas=[{"source": "document.pdf", "page": 1}],
    chunk_size=1000,
    overlap_size=200
)

# Get statistics
stats = chunker.get_chunking_stats(chunks)
print(f"Created {stats['total_chunks']} chunks using {stats['chunking_method']}")
```

### 2. Using ProcessController

```python
from controllers.ProcessController import ProcessController

# Initialize controller
process_controller = ProcessController(project_id="123")

# Process file with semantic chunking
chunks = process_controller.process_file_content(
    file_content=file_content,
    file_id="document.pdf",
    chunk_size=1000,
    overlap_size=200,
    chunking_method="semantic"  # or "sentence", "simple"
)

# Get available methods
methods = process_controller.get_chunking_methods()
print(f"Available methods: {methods}")
```

### 3. API Usage

```bash
# Process with semantic chunking
curl -X POST "http://localhost:8000/api/v1/data/process/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "chunk_size": 1000,
    "overlap_size": 200,
    "chunking_method": "semantic",
    "do_reset": 0
  }'

# Process with sentence-based chunking
curl -X POST "http://localhost:8000/api/v1/data/process/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "chunk_size": 800,
    "overlap_size": 100,
    "chunking_method": "sentence",
    "do_reset": 0
  }'
```

## 🔧 Configuration

### Environment Variables

```bash
# Required for semantic chunking
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Configure embedding model
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

### Semantic Chunker Settings

```python
# In SemanticChunkerUtility.__init__()
self.semantic_chunker = SemanticChunker(
    embeddings=self.embeddings,
    breakpoint_threshold_type="percentile",  # or "standard_deviation"
    breakpoint_threshold_amount=95,         # percentile threshold
    min_chunk_size=50,                     # minimum chunk size
    max_chunk_size=1000                    # maximum chunk size
)
```

## 📊 Monitoring and Statistics

### Chunking Statistics

Each chunking operation provides detailed statistics:

```python
stats = {
    "total_chunks": 15,           # Number of chunks created
    "avg_chunk_size": 245.6,      # Average characters per chunk
    "min_chunk_size": 120,        # Smallest chunk size
    "max_chunk_size": 450,        # Largest chunk size
    "chunking_method": "semantic", # Method used
    "total_characters": 3684      # Total characters processed
}
```

### Logging

The implementation includes comprehensive logging:

```python
# Log levels
logger.info("Semantic chunking completed: {stats}")
logger.warning("Using fallback chunking method")
logger.error("Error in semantic chunking: {error}")
```

## 🔄 Migration from Simple Chunking

### Backward Compatibility

The implementation maintains full backward compatibility:

1. **Default Behavior**: Uses semantic chunking if available, falls back to simple chunking
2. **API Compatibility**: Existing API calls continue to work
3. **Data Format**: Chunks maintain the same structure

### Migration Steps

1. **Install Dependencies**:
   ```bash
   pip install langchain-experimental==0.0.60 langchain-openai==0.1.25
   ```

2. **Configure API Key**:
   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```

3. **Test Implementation**:
   ```bash
   python src/test_semantic_chunking.py
   ```

4. **Update Processing Calls** (Optional):
   ```python
   # Old way (still works)
   chunks = process_controller.process_file_content(file_content, file_id)
   
   # New way with explicit method
   chunks = process_controller.process_file_content(
       file_content, file_id, 
       chunking_method="semantic"
   )
   ```

## 🛠️ Troubleshooting

### Common Issues

#### 1. **OpenAI API Key Not Configured**
```
Error: Semantic chunker initialization failed: No API key provided
```
**Solution**: Set `OPENAI_API_KEY` environment variable

#### 2. **Semantic Chunking Fails**
```
Warning: Using fallback chunking method
```
**Solution**: Check API key, network connectivity, or use fallback methods

#### 3. **Memory Issues with Large Documents**
```
Error: Out of memory during chunking
```
**Solution**: Reduce `chunk_size` or use sentence-based chunking

### Debugging

#### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Test Individual Components
```python
# Test semantic chunker
from utils.semantic_chunker import SemanticChunkerUtility
chunker = SemanticChunkerUtility()
chunks = chunker.chunk_text_semantically(["test text"])

# Test ProcessController
from controllers.ProcessController import ProcessController
controller = ProcessController("test")
methods = controller.get_chunking_methods()
```

## 📈 Performance Considerations

### Memory Usage
- **Semantic chunking**: Higher memory usage due to embeddings
- **Sentence chunking**: Moderate memory usage
- **Simple chunking**: Low memory usage

### Processing Speed
- **Semantic chunking**: Slower (API calls for embeddings)
- **Sentence chunking**: Fast
- **Simple chunking**: Fastest

### Recommendations
- **Small documents**: Use semantic chunking for best quality
- **Large documents**: Consider sentence-based chunking for speed
- **Batch processing**: Use simple chunking for efficiency

## 🔮 Future Enhancements

### Planned Features
1. **Multiple Embedding Providers**: Support for Cohere, HuggingFace, etc.
2. **Custom Chunking Strategies**: User-defined chunking rules
3. **Chunking Analytics**: Detailed performance metrics
4. **Adaptive Chunking**: Automatic method selection based on content

### Extensibility
The modular design allows easy addition of new chunking methods:

```python
class CustomChunkerUtility:
    def chunk_text_custom(self, texts, metadatas, **kwargs):
        # Custom chunking logic
        pass
```

## 📚 References

- [LangChain SemanticChunker Documentation](https://python.langchain.com/docs/modules/data_connection/document_transformers/semantic_chunker)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [LangChain Experimental Features](https://python.langchain.com/docs/langchain_experimental)

---

The semantic chunking implementation provides intelligent text processing while maintaining full backward compatibility with the existing Mini-RAG architecture. 