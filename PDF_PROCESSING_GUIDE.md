# Smart PDF Processing with Selective OCR

This guide explains different approaches for processing PDFs that contain mixed content (text, images, tables) where you want to apply OCR to images and tables while treating regular text normally.

## Overview

Your requirement is to:
1. **Apply OCR to images** - Extract text content from images within PDFs
2. **Apply OCR to tables** - Handle complex tables that normal extraction might miss
3. **Process regular text normally** - Fast, accurate extraction for standard text content
4. **Combine everything coherently** - Maintain document structure and context

## Recommended Approaches

### 🥇 Approach 1: Unstructured Library (Recommended)

**Best for**: Most use cases, especially when you want automatic content type detection

The `unstructured` library is specifically designed for this use case:

```python
from unstructured.partition.pdf import partition_pdf

# Automatic content detection and intelligent processing
elements = partition_pdf(
    filename="document.pdf",
    strategy="hi_res",  # High resolution for better OCR
    infer_table_structure=True,  # Detect and preserve tables
    extract_images_in_pdf=True,  # Extract and OCR images
    extract_image_block_types=["Image", "Table"]  # What to OCR
)
```

**Pros**:
- Automatic content type detection
- Built-in OCR for images and tables
- Preserves document structure
- Easy to use
- Handles multiple file formats

**Cons**:
- Additional dependency
- Less control over OCR parameters
- Can be slower for large documents

### 🥈 Approach 2: Hybrid Multi-Library

**Best for**: When you need fine control over the processing pipeline

Combines different libraries for their strengths:

```python
import fitz  # PyMuPDF for images and general handling
import pdfplumber  # For table detection
import pytesseract  # For OCR

def process_pdf_hybrid(pdf_path):
    fitz_doc = fitz.open(pdf_path)
    plumber_doc = pdfplumber.open(pdf_path)
    
    for page_num in range(len(fitz_doc)):
        fitz_page = fitz_doc[page_num]
        plumber_page = plumber_doc.pages[page_num]
        
        # Extract tables with pdfplumber
        tables = plumber_page.extract_tables()
        
        # Extract and OCR images with PyMuPDF + Tesseract
        images = fitz_page.get_images()
        for img in images:
            # Apply OCR to each image
            
        # Extract regular text with PyMuPDF
        regular_text = fitz_page.get_text()
```

**Pros**:
- Full control over each processing step
- Can optimize for specific document types
- Uses best library for each task
- Highly customizable

**Cons**:
- More complex implementation
- Need to handle integration between libraries
- More dependencies to manage

### 🥉 Approach 3: Content-Aware Processing

**Best for**: Documents with varying layouts and content types

Analyzes page layout first, then applies appropriate processing:

```python
def process_content_aware(pdf_path):
    doc = fitz.open(pdf_path)
    
    for page in doc:
        # Analyze page layout
        layout_analysis = analyze_page_layout(page)
        
        if layout_analysis['is_image_heavy']:
            content = process_image_heavy_page(page)
        elif layout_analysis['has_complex_tables']:
            content = process_table_heavy_page(page)
        else:
            content = process_text_page(page)
```

**Pros**:
- Optimized processing per page type
- Efficient resource usage
- Can handle mixed document types well

**Cons**:
- Complex layout analysis required
- More development time
- Potential for misclassification

## Implementation Details

### Required Dependencies

```bash
# System dependencies (Ubuntu/Debian)
sudo apt-get install tesseract-ocr poppler-utils

# Python packages
pip install PyMuPDF pdfplumber pytesseract pdf2image pillow
pip install "unstructured[pdf]"  # For approach 1
```

### OCR Configuration

For best results with Tesseract:

```python
# OCR settings for different content types
TEXT_OCR_CONFIG = '--oem 3 --psm 6'  # General text
TABLE_OCR_CONFIG = '--oem 3 --psm 6'  # Tables
IMAGE_OCR_CONFIG = '--oem 3 --psm 6'  # Images with text

# Language settings
LANGUAGES = 'eng+fra+deu'  # Multiple languages if needed
```

### Integration with Your Existing Code

Your current `ProcessController` can be enhanced:

```python
class EnhancedProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()
        self.smart_pdf_processor = SmartPDFProcessor()
    
    def get_file_content(self, file_id: str, use_smart_processing: bool = True):
        file_ext = self.get_file_extension(file_id)
        
        if file_ext == '.pdf' and use_smart_processing:
            return self.smart_pdf_processor.process_pdf_intelligent(file_path)
        else:
            # Fallback to existing processing
            return super().get_file_content(file_id)
```

## Performance Considerations

### Speed Optimization
1. **Skip small images** - Filter out decorative images
2. **Batch processing** - Process multiple pages in parallel
3. **Caching** - Cache OCR results for repeated processing
4. **Resolution tuning** - Balance OCR quality vs speed

### Memory Management
1. **Process page by page** - Don't load entire document in memory
2. **Clean up resources** - Close PDF documents properly
3. **Image size limits** - Resize very large images before OCR

## Best Practices

### 1. Content Type Detection
```python
def should_apply_ocr_to_table(table):
    """Determine if table needs OCR enhancement"""
    if not table:
        return True
    
    # Count empty cells
    total_cells = sum(len(row) for row in table)
    empty_cells = sum(1 for row in table for cell in row if not cell)
    
    # If >30% cells are empty, might need OCR
    return (empty_cells / total_cells) > 0.3
```

### 2. Error Handling
```python
def safe_ocr_processing(image_data):
    """OCR with graceful error handling"""
    try:
        return pytesseract.image_to_string(image_data)
    except Exception as e:
        logger.warning(f"OCR failed: {str(e)}")
        return ""  # Return empty rather than crash
```

### 3. Quality Control
```python
def validate_ocr_output(text):
    """Basic validation of OCR results"""
    # Filter out very short results (likely noise)
    if len(text.strip()) < 10:
        return False
    
    # Check for reasonable character distribution
    alpha_chars = sum(c.isalpha() for c in text)
    return alpha_chars > len(text) * 0.3
```

## Usage Examples

### Quick Start
```bash
# Setup dependencies
./setup_pdf_processing.sh

# Process a PDF
python src/examples/smart_pdf_example.py document.pdf
```

### Custom Processing
```python
from controllers.SmartPDFController import SmartPDFController

processor = SmartPDFController()
documents = processor.process_pdf_with_smart_ocr(
    "document.pdf",
    ocr_images=True,
    ocr_tables=True,
    extract_table_structure=True
)

for doc in documents:
    print(f"Page {doc.metadata['page']}: {len(doc.page_content)} characters")
```

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   ```bash
   sudo apt-get install tesseract-ocr
   ```

2. **Poor OCR quality**
   - Increase image resolution (DPI)
   - Improve image preprocessing
   - Try different PSM modes

3. **Table detection fails**
   - Use multiple table detection methods
   - Fall back to OCR for entire page regions

4. **Memory issues**
   - Process one page at a time
   - Reduce image resolution
   - Use generators instead of loading all content

### Performance Tuning

1. **For speed**: Use `strategy="fast"` with unstructured
2. **For accuracy**: Use `strategy="hi_res"` with unstructured
3. **For custom control**: Use the hybrid approach

## Conclusion

For most use cases, **start with the unstructured library approach** as it provides the best balance of ease-of-use and functionality. If you need more control or have specific performance requirements, consider the hybrid approach.

The key is to:
1. Detect content types automatically
2. Apply appropriate processing for each type
3. Handle errors gracefully
4. Maintain document structure and context

Your existing LangChain integration will work well with any of these approaches, as they all return standard Document objects that can be processed by your existing pipeline. 