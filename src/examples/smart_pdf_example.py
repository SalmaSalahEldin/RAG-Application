#!/usr/bin/env python3
"""
Smart PDF Processing Example

This script demonstrates how to process a PDF with selective OCR application:
- Extract images and apply OCR to them
- Detect tables and apply OCR if needed for better extraction
- Extract regular text normally (faster and more accurate)
- Combine everything into coherent documents

Usage:
    python smart_pdf_example.py <pdf_path>
"""

import sys
import os
import logging
from typing import List, Dict, Tuple, Optional
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
import io

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartPDFProcessor:
    """
    Intelligent PDF processor that applies OCR selectively to images and tables
    while using normal text extraction for regular content.
    """
    
    def __init__(self):
        self.min_image_size = (50, 50)  # Skip tiny images
        self.ocr_config = '--oem 3 --psm 6'  # Tesseract config
        
    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Process PDF with intelligent content type detection and selective OCR.
        
        Returns:
            List of page dictionaries with processed content
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        results = []
        
        # Open with both libraries for different capabilities
        fitz_doc = fitz.open(pdf_path)
        plumber_doc = pdfplumber.open(pdf_path)
        
        try:
            for page_num in range(len(fitz_doc)):
                logger.info(f"Processing page {page_num + 1}/{len(fitz_doc)}")
                
                fitz_page = fitz_doc[page_num]
                plumber_page = plumber_doc.pages[page_num]
                
                page_result = self._process_single_page(
                    fitz_page, plumber_page, page_num
                )
                results.append(page_result)
                
        finally:
            fitz_doc.close()
            plumber_doc.close()
        
        return results
    
    def _process_single_page(self, fitz_page, plumber_page, page_num: int) -> Dict:
        """Process a single page with intelligent content detection."""
        
        page_result = {
            'page_number': page_num + 1,
            'regular_text': '',
            'table_content': '',
            'image_content': '',
            'combined_content': '',
            'metadata': {
                'has_images': False,
                'has_tables': False,
                'processing_methods': []
            }
        }
        
        # 1. Extract regular text (fastest, most accurate for normal text)
        regular_text = fitz_page.get_text("text")
        page_result['regular_text'] = regular_text.strip()
        if regular_text.strip():
            page_result['metadata']['processing_methods'].append('text_extraction')
        
        # 2. Process tables with selective OCR
        table_content = self._process_tables(plumber_page, fitz_page, page_num)
        page_result['table_content'] = table_content
        if table_content:
            page_result['metadata']['has_tables'] = True
            page_result['metadata']['processing_methods'].append('table_extraction')
        
        # 3. Process images with OCR
        image_content = self._process_images(fitz_page, page_num)
        page_result['image_content'] = image_content
        if image_content:
            page_result['metadata']['has_images'] = True
            page_result['metadata']['processing_methods'].append('image_ocr')
        
        # 4. Combine all content intelligently
        page_result['combined_content'] = self._combine_content(
            regular_text, table_content, image_content
        )
        
        return page_result
    
    def _process_tables(self, plumber_page, fitz_page, page_num: int) -> str:
        """
        Extract tables using pdfplumber, with OCR fallback for incomplete tables.
        """
        table_results = []
        
        try:
            tables = plumber_page.extract_tables()
            
            for i, table in enumerate(tables):
                if not table:
                    continue
                
                # Check if table extraction was successful
                if self._is_table_extraction_complete(table):
                    # Normal table extraction worked well
                    formatted_table = self._format_table(table, f"Table {i+1}")
                    table_results.append(formatted_table)
                    logger.info(f"Page {page_num+1}: Table {i+1} extracted normally")
                else:
                    # Table seems incomplete, try OCR on the table region
                    logger.info(f"Page {page_num+1}: Table {i+1} needs OCR enhancement")
                    
                    # Get table bounding box (simplified - you might want more precise detection)
                    table_bbox = self._estimate_table_bbox(plumber_page, table)
                    ocr_content = self._ocr_region(fitz_page, table_bbox)
                    
                    if ocr_content.strip():
                        table_results.append(f"Table {i+1} (OCR Enhanced):\n{ocr_content}")
                    else:
                        # Fallback to whatever we could extract
                        formatted_table = self._format_table(table, f"Table {i+1} (Partial)")
                        table_results.append(formatted_table)
        
        except Exception as e:
            logger.warning(f"Error processing tables on page {page_num+1}: {str(e)}")
        
        return "\n\n".join(table_results)
    
    def _process_images(self, fitz_page, page_num: int) -> str:
        """Extract images and apply OCR to extract text content."""
        image_results = []
        
        try:
            images = fitz_page.get_images()
            
            for img_idx, img in enumerate(images):
                xref = img[0]
                
                try:
                    # Extract image data
                    base_image = fitz_page.parent.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Skip very small images (likely decorative)
                    if (base_image["width"] < self.min_image_size[0] or 
                        base_image["height"] < self.min_image_size[1]):
                        continue
                    
                    # Apply OCR to extract text from image
                    ocr_text = self._ocr_image_bytes(image_bytes)
                    
                    if ocr_text.strip():
                        image_results.append(
                            f"Image {img_idx+1} Text Content:\n{ocr_text}"
                        )
                        logger.info(f"Page {page_num+1}: Extracted text from image {img_idx+1}")
                
                except Exception as e:
                    logger.warning(f"Error processing image {img_idx+1} on page {page_num+1}: {str(e)}")
        
        except Exception as e:
            logger.warning(f"Error processing images on page {page_num+1}: {str(e)}")
        
        return "\n\n".join(image_results)
    
    def _is_table_extraction_complete(self, table: List[List]) -> bool:
        """
        Determine if table extraction was successful or needs OCR enhancement.
        """
        if not table:
            return False
        
        # Count non-empty cells
        total_cells = sum(len(row) for row in table)
        non_empty_cells = sum(
            1 for row in table 
            for cell in row 
            if cell and str(cell).strip()
        )
        
        # If more than 70% of cells are empty, extraction might be incomplete
        if total_cells == 0:
            return False
        
        completeness_ratio = non_empty_cells / total_cells
        return completeness_ratio > 0.3
    
    def _estimate_table_bbox(self, plumber_page, table: List[List]) -> Tuple[float, float, float, float]:
        """
        Estimate bounding box for a table (simplified implementation).
        In practice, you'd want more sophisticated table boundary detection.
        """
        # This is a simplified approach - for better results, you'd implement
        # proper table boundary detection using the table coordinates
        return (0, 0, plumber_page.width, plumber_page.height)
    
    def _ocr_region(self, fitz_page, bbox: Tuple[float, float, float, float]) -> str:
        """Apply OCR to a specific region of the page."""
        try:
            # Convert bbox to fitz.Rect and create high-res pixmap
            rect = fitz.Rect(bbox)
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR quality
            pix = fitz_page.get_pixmap(matrix=mat, clip=rect)
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")
            image = Image.open(io.BytesIO(img_data))
            
            # Apply OCR
            text = pytesseract.image_to_string(image, config=self.ocr_config)
            return text.strip()
        
        except Exception as e:
            logger.warning(f"Error applying OCR to region: {str(e)}")
            return ""
    
    def _ocr_image_bytes(self, image_bytes: bytes) -> str:
        """Apply OCR to image bytes."""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            
            # Apply OCR
            text = pytesseract.image_to_string(image, config=self.ocr_config)
            return text.strip()
        
        except Exception as e:
            logger.warning(f"Error applying OCR to image: {str(e)}")
            return ""
    
    def _format_table(self, table: List[List], title: str) -> str:
        """Format table as readable text."""
        if not table:
            return ""
        
        lines = [f"=== {title} ==="]
        
        for i, row in enumerate(table):
            if not row:
                continue
            
            # Clean up cells
            clean_row = [str(cell).strip() if cell else "" for cell in row]
            
            if i == 0:  # Header row
                lines.append(" | ".join(clean_row))
                lines.append("-" * 50)  # Separator
            else:
                lines.append(" | ".join(clean_row))
        
        return "\n".join(lines)
    
    def _combine_content(self, regular_text: str, table_content: str, image_content: str) -> str:
        """Combine different content types into a coherent document."""
        content_parts = []
        
        if regular_text.strip():
            content_parts.append("## Text Content ##\n" + regular_text)
        
        if table_content.strip():
            content_parts.append("## Tables ##\n" + table_content)
        
        if image_content.strip():
            content_parts.append("## Image Text Content ##\n" + image_content)
        
        return "\n\n".join(content_parts)


def main():
    """Main function to demonstrate smart PDF processing."""
    
    if len(sys.argv) != 2:
        print("Usage: python smart_pdf_example.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        # Initialize processor
        processor = SmartPDFProcessor()
        
        # Process PDF
        logger.info(f"Starting intelligent processing of: {pdf_path}")
        results = processor.process_pdf(pdf_path)
        
        # Display results
        print(f"\n{'='*60}")
        print(f"SMART PDF PROCESSING RESULTS")
        print(f"{'='*60}")
        print(f"File: {pdf_path}")
        print(f"Pages processed: {len(results)}")
        
        for page_result in results:
            print(f"\n{'-'*50}")
            print(f"PAGE {page_result['page_number']}")
            print(f"{'-'*50}")
            
            metadata = page_result['metadata']
            print(f"Processing methods used: {', '.join(metadata['processing_methods'])}")
            print(f"Has tables: {metadata['has_tables']}")
            print(f"Has images: {metadata['has_images']}")
            
            print(f"\nCombined content length: {len(page_result['combined_content'])} characters")
            
            # Show preview of content
            content = page_result['combined_content']
            if content:
                preview = content[:300] + "..." if len(content) > 300 else content
                print(f"\nContent preview:\n{preview}")
            
            # Optionally save full content to file
            output_file = f"page_{page_result['page_number']}_processed.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(page_result['combined_content'])
            print(f"Full content saved to: {output_file}")
        
        print(f"\n{'='*60}")
        print("Processing complete!")
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 