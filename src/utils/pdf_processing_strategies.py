"""
PDF Processing Strategies - Different approaches for handling PDFs with mixed content
"""

import os
from typing import List, Dict, Optional, Union
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import pytesseract
import io
import logging
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

def strategy_1_unstructured_library(file_path: str) -> List[Document]:
    """
    Strategy 1: Using the unstructured library (Recommended)
    
    The unstructured library automatically detects content types and applies
    appropriate processing strategies.
    """
    try:
        from unstructured.partition.pdf import partition_pdf
        from unstructured.staging.base import convert_to_dict
        
        # Partition PDF with automatic content detection
        elements = partition_pdf(
            filename=file_path,
            strategy="hi_res",  # High resolution for better OCR
            infer_table_structure=True,  # Detect and preserve table structure
            extract_images_in_pdf=True,  # Extract and OCR images
            extract_image_block_types=["Image", "Table"],  # What to OCR
            extract_image_block_to_payload=False,  # Don't include raw image data
        )
        
        documents = []
        current_content = []
        
        for element in elements:
            element_dict = convert_to_dict(element)
            content_type = element_dict.get('type', 'Unknown')
            text = element_dict.get('text', '')
            
            if text.strip():
                if content_type == 'Table':
                    current_content.append(f"[TABLE]\n{text}\n[/TABLE]")
                elif content_type == 'Image':
                    current_content.append(f"[IMAGE CONTENT]\n{text}\n[/IMAGE CONTENT]")
                else:
                    current_content.append(text)
        
        # Combine all content into a single document or split by pages
        full_content = "\n\n".join(current_content)
        
        document = Document(
            page_content=full_content,
            metadata={
                'source': file_path,
                'processing_strategy': 'unstructured_hi_res',
                'content_types_detected': list(set(elem.get('type', 'Unknown') for elem in [convert_to_dict(e) for e in elements]))
            }
        )
        documents.append(document)
        
        return documents
        
    except ImportError:
        logger.error("unstructured library not installed. Run: pip install unstructured[pdf]")
        raise
    except Exception as e:
        logger.error(f"Error with unstructured strategy: {str(e)}")
        raise

def strategy_2_hybrid_approach(file_path: str) -> List[Document]:
    """
    Strategy 2: Hybrid approach using multiple libraries
    
    Uses different libraries for their strengths:
    - pdfplumber for table detection and extraction
    - PyMuPDF for images and general text
    - pytesseract for OCR on images and complex tables
    """
    documents = []
    
    try:
        pdf_doc = fitz.open(file_path)
        plumber_pdf = pdfplumber.open(file_path)
        
        for page_num in range(len(pdf_doc)):
            fitz_page = pdf_doc[page_num]
            plumber_page = plumber_pdf.pages[page_num]
            
            page_content_parts = []
            
            # 1. Extract tables using pdfplumber
            tables = plumber_page.extract_tables()
            if tables:
                table_content = process_tables_with_ocr_fallback(tables, fitz_page, page_num)
                if table_content:
                    page_content_parts.append(f"## Tables on Page {page_num + 1} ##\n{table_content}")
            
            # 2. Extract and OCR images
            image_content = extract_and_ocr_images(fitz_page, page_num)
            if image_content:
                page_content_parts.append(f"## Images on Page {page_num + 1} ##\n{image_content}")
            
            # 3. Extract regular text
            regular_text = fitz_page.get_text()
            if regular_text.strip():
                page_content_parts.append(f"## Text Content ##\n{regular_text}")
            
            # Combine all content for this page
            full_page_content = "\n\n".join(page_content_parts)
            
            document = Document(
                page_content=full_page_content,
                metadata={
                    'source': file_path,
                    'page': page_num,
                    'total_pages': len(pdf_doc),
                    'processing_strategy': 'hybrid_approach',
                    'has_tables': len(tables) > 0 if tables else False,
                    'has_images': len(fitz_page.get_images()) > 0
                }
            )
            documents.append(document)
        
        pdf_doc.close()
        plumber_pdf.close()
        
    except Exception as e:
        logger.error(f"Error with hybrid approach: {str(e)}")
        raise
    
    return documents

def strategy_3_content_aware_processing(file_path: str) -> List[Document]:
    """
    Strategy 3: Content-aware processing
    
    Analyzes page layout first, then applies appropriate processing based on
    content density and type.
    """
    documents = []
    
    try:
        pdf_doc = fitz.open(file_path)
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            # Analyze page layout
            layout_analysis = analyze_page_layout(page)
            
            # Process based on layout
            if layout_analysis['is_image_heavy']:
                content = process_image_heavy_page(page, page_num)
            elif layout_analysis['has_complex_tables']:
                content = process_table_heavy_page(page, page_num)
            else:
                content = process_text_page(page, page_num)
            
            document = Document(
                page_content=content,
                metadata={
                    'source': file_path,
                    'page': page_num,
                    'total_pages': len(pdf_doc),
                    'processing_strategy': 'content_aware',
                    'layout_analysis': layout_analysis
                }
            )
            documents.append(document)
        
        pdf_doc.close()
        
    except Exception as e:
        logger.error(f"Error with content-aware processing: {str(e)}")
        raise
    
    return documents

def process_tables_with_ocr_fallback(tables: List, fitz_page, page_num: int) -> str:
    """Process tables with OCR fallback for incomplete extractions."""
    table_contents = []
    
    for i, table in enumerate(tables):
        if not table or not any(any(cell for cell in row if cell) for row in table):
            # Table is empty or mostly empty, try OCR
            # This is a simplified approach - you'd need to get actual table coordinates
            ocr_content = ocr_page_region(fitz_page, None, page_num)  # OCR entire page as fallback
            if ocr_content.strip():
                table_contents.append(f"Table {i+1} (OCR): {ocr_content}")
        else:
            # Format table normally
            formatted_table = format_table_as_markdown(table, f"Table {i+1}")
            table_contents.append(formatted_table)
    
    return "\n\n".join(table_contents)

def extract_and_ocr_images(fitz_page, page_num: int) -> str:
    """Extract images from page and apply OCR."""
    image_contents = []
    
    image_list = fitz_page.get_images()
    
    for img_index, img in enumerate(image_list):
        try:
            # Extract image
            xref = img[0]
            base_image = fitz_page.parent.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Skip very small images (likely decorative)
            if base_image["width"] < 100 or base_image["height"] < 100:
                continue
            
            # Apply OCR
            ocr_text = ocr_image_bytes(image_bytes)
            if ocr_text.strip():
                image_contents.append(f"Image {img_index + 1}: {ocr_text}")
                
        except Exception as e:
            logger.warning(f"Error processing image {img_index} on page {page_num}: {str(e)}")
    
    return "\n\n".join(image_contents)

def ocr_image_bytes(image_bytes: bytes) -> str:
    """Apply OCR to image bytes."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode not in ['RGB', 'L']:
            image = image.convert('RGB')
        
        # Apply OCR with optimized settings
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-=[]{}|;:,.<>?/~` '
        text = pytesseract.image_to_string(image, config=custom_config)
        
        return text.strip()
        
    except Exception as e:
        logger.warning(f"Error applying OCR to image: {str(e)}")
        return ""

def ocr_page_region(fitz_page, bbox: Optional[fitz.Rect], page_num: int) -> str:
    """Apply OCR to a specific region or entire page."""
    try:
        # Create pixmap with higher resolution for better OCR
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
        
        if bbox:
            pix = fitz_page.get_pixmap(matrix=mat, clip=bbox)
        else:
            pix = fitz_page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data))
        
        # Apply OCR
        text = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
        
        return text.strip()
        
    except Exception as e:
        logger.warning(f"Error applying OCR to page region {page_num}: {str(e)}")
        return ""

def analyze_page_layout(page) -> Dict:
    """Analyze page layout to determine processing strategy."""
    analysis = {
        'is_image_heavy': False,
        'has_complex_tables': False,
        'text_density': 0,
        'image_count': 0,
        'estimated_table_count': 0
    }
    
    try:
        # Count images
        images = page.get_images()
        analysis['image_count'] = len(images)
        analysis['is_image_heavy'] = len(images) > 3
        
        # Estimate text density
        text = page.get_text()
        page_area = page.rect.width * page.rect.height
        analysis['text_density'] = len(text) / page_area if page_area > 0 else 0
        
        # Simple table detection (this could be more sophisticated)
        # Look for repeated whitespace patterns that might indicate tables
        lines = text.split('\n')
        tabular_lines = sum(1 for line in lines if len(line.split()) > 3 and '\t' in line or '  ' in line)
        analysis['estimated_table_count'] = tabular_lines // 3  # Rough estimate
        analysis['has_complex_tables'] = analysis['estimated_table_count'] > 2
        
    except Exception as e:
        logger.warning(f"Error analyzing page layout: {str(e)}")
    
    return analysis

def process_image_heavy_page(page, page_num: int) -> str:
    """Process pages with many images using OCR-focused approach."""
    content_parts = []
    
    # Extract all images with OCR
    image_content = extract_and_ocr_images(page, page_num)
    if image_content:
        content_parts.append(f"## Image Content ##\n{image_content}")
    
    # Extract any remaining text
    text_content = page.get_text()
    if text_content.strip():
        content_parts.append(f"## Text Content ##\n{text_content}")
    
    return "\n\n".join(content_parts)

def process_table_heavy_page(page, page_num: int) -> str:
    """Process pages with complex tables using OCR enhancement."""
    # For table-heavy pages, we might want to OCR the entire page
    # to catch table content that normal extraction might miss
    
    ocr_content = ocr_page_region(page, None, page_num)
    regular_content = page.get_text()
    
    content_parts = []
    
    if regular_content.strip():
        content_parts.append(f"## Extracted Text ##\n{regular_content}")
    
    if ocr_content.strip() and ocr_content != regular_content:
        content_parts.append(f"## OCR Enhanced Content ##\n{ocr_content}")
    
    return "\n\n".join(content_parts)

def process_text_page(page, page_num: int) -> str:
    """Process regular text pages with standard extraction."""
    return page.get_text()

def format_table_as_markdown(table: List, title: str) -> str:
    """Format table data as markdown."""
    if not table or not any(table):
        return ""
    
    lines = [f"### {title} ###", ""]
    
    for i, row in enumerate(table):
        if not row:
            continue
            
        # Clean up cell content
        clean_row = [str(cell).strip() if cell else "" for cell in row]
        
        if i == 0:  # Header row
            lines.append("| " + " | ".join(clean_row) + " |")
            lines.append("|" + "|".join("---" for _ in clean_row) + "|")
        else:
            lines.append("| " + " | ".join(clean_row) + " |")
    
    return "\n".join(lines)

# Usage example function
def process_pdf_intelligently(file_path: str, strategy: str = "unstructured") -> List[Document]:
    """
    Main function to process PDF with intelligent OCR application.
    
    Args:
        file_path: Path to PDF file
        strategy: Processing strategy ("unstructured", "hybrid", "content_aware")
    
    Returns:
        List of processed documents
    """
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    if strategy == "unstructured":
        return strategy_1_unstructured_library(file_path)
    elif strategy == "hybrid":
        return strategy_2_hybrid_approach(file_path)
    elif strategy == "content_aware":
        return strategy_3_content_aware_processing(file_path)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

# Example usage
if __name__ == "__main__":
    # Example of how to use the different strategies
    pdf_path = "example.pdf"
    
    try:
        # Try unstructured approach first (recommended)
        documents = process_pdf_intelligently(pdf_path, "unstructured")
        print(f"Processed {len(documents)} documents using unstructured library")
        
        for i, doc in enumerate(documents):
            print(f"\nDocument {i+1}:")
            print(f"Content length: {len(doc.page_content)}")
            print(f"Metadata: {doc.metadata}")
            print(f"Preview: {doc.page_content[:200]}...")
            
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        
        # Fallback to hybrid approach
        try:
            documents = process_pdf_intelligently(pdf_path, "hybrid")
            print(f"Fallback: Processed {len(documents)} documents using hybrid approach")
        except Exception as e2:
            print(f"Fallback also failed: {str(e2)}") 