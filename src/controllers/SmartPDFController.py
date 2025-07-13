import os
import io
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
import numpy as np

from .BaseController import BaseController
from langchain_core.documents import Document

@dataclass
class ContentRegion:
    """Represents a region of content in a PDF page"""
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    content_type: str  # 'text', 'image', 'table'
    content: str
    metadata: Dict[str, Any]

class SmartPDFController(BaseController):
    """
    Advanced PDF processor that intelligently applies OCR to images and tables
    while using normal text extraction for regular text content.
    """
    
    def __init__(self, project_id: str = None):
        super().__init__()
        self.project_id = project_id
        self.logger = logging.getLogger(__name__)
        
        # OCR Configuration
        self.ocr_config = {
            'lang': 'eng',  # Language for OCR
            'config': '--oem 3 --psm 6',  # OCR Engine Mode and Page Segmentation Mode
            'dpi': 300,  # DPI for image conversion
        }
        
        # Content detection thresholds
        self.table_detection_threshold = 0.7
        self.image_min_size = (50, 50)  # Minimum image size to process
        
    def process_pdf_with_smart_ocr(self, file_path: str, 
                                  ocr_images: bool = True, 
                                  ocr_tables: bool = True,
                                  extract_table_structure: bool = True) -> List[Document]:
        """
        Process PDF with intelligent OCR application.
        
        Args:
            file_path: Path to the PDF file
            ocr_images: Whether to apply OCR to images
            ocr_tables: Whether to apply OCR to tables
            extract_table_structure: Whether to preserve table structure
            
        Returns:
            List of Document objects with processed content
        """
        documents = []
        
        try:
            # Open PDF with both PyMuPDF and pdfplumber for different capabilities
            pdf_doc = fitz.open(file_path)
            plumber_pdf = pdfplumber.open(file_path)
            
            for page_num in range(len(pdf_doc)):
                fitz_page = pdf_doc[page_num]
                plumber_page = plumber_pdf.pages[page_num]
                
                # Process page content intelligently
                page_content = self._process_page_intelligent(
                    fitz_page, plumber_page, page_num,
                    ocr_images, ocr_tables, extract_table_structure
                )
                
                # Create document for this page
                metadata = {
                    'source': file_path,
                    'page': page_num,
                    'total_pages': len(pdf_doc),
                    'processing_method': 'smart_ocr'
                }
                
                document = Document(
                    page_content=page_content,
                    metadata=metadata
                )
                documents.append(document)
                
            pdf_doc.close()
            plumber_pdf.close()
            
        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise
            
        return documents
    
    def _process_page_intelligent(self, fitz_page, plumber_page, page_num: int,
                                ocr_images: bool, ocr_tables: bool, 
                                extract_table_structure: bool) -> str:
        """Process a single page with intelligent content type detection."""
        
        page_content_parts = []
        
        # 1. Extract tables first (they take priority)
        if ocr_tables or extract_table_structure:
            table_content = self._extract_tables_intelligently(
                plumber_page, fitz_page, page_num, ocr_tables, extract_table_structure
            )
            if table_content:
                page_content_parts.append("## Tables ##\n" + table_content)
        
        # 2. Extract images with OCR if requested
        if ocr_images:
            image_content = self._extract_images_with_ocr(fitz_page, page_num)
            if image_content:
                page_content_parts.append("## Images ##\n" + image_content)
        
        # 3. Extract regular text (excluding areas covered by tables/images)
        regular_text = self._extract_regular_text(fitz_page, plumber_page)
        if regular_text.strip():
            page_content_parts.append("## Text ##\n" + regular_text)
        
        return "\n\n".join(page_content_parts)
    
    def _extract_tables_intelligently(self, plumber_page, fitz_page, page_num: int,
                                    apply_ocr: bool, preserve_structure: bool) -> str:
        """Extract tables with intelligent processing."""
        table_content = []
        
        try:
            # Use pdfplumber for initial table detection
            tables = plumber_page.extract_tables()
            
            for i, table in enumerate(tables):
                if not table:
                    continue
                    
                if preserve_structure:
                    # Convert table to structured format
                    table_text = self._format_table_structure(table, f"Table {i+1}")
                else:
                    # Flatten table to text
                    table_text = self._flatten_table_to_text(table)
                
                # If OCR is requested and table seems incomplete, apply OCR
                if apply_ocr and self._should_apply_ocr_to_table(table):
                    bbox = plumber_page.within_bbox(self._get_table_bbox(plumber_page, i))
                    ocr_text = self._ocr_region(fitz_page, bbox.bbox, page_num)
                    if ocr_text.strip():
                        table_text += f"\n[OCR Enhancement]: {ocr_text}"
                
                table_content.append(table_text)
                
        except Exception as e:
            self.logger.warning(f"Error extracting tables from page {page_num}: {str(e)}")
            
        return "\n\n".join(table_content)
    
    def _extract_images_with_ocr(self, fitz_page, page_num: int) -> str:
        """Extract images and apply OCR to them."""
        image_content = []
        
        try:
            # Get list of images on the page
            image_list = fitz_page.get_images()
            
            for img_index, img in enumerate(image_list):
                # Extract image data
                xref = img[0]
                base_image = fitz_page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Filter out very small images (likely decorative)
                if base_image["width"] < self.image_min_size[0] or base_image["height"] < self.image_min_size[1]:
                    continue
                
                # Apply OCR to image
                ocr_text = self._ocr_image_bytes(image_bytes)
                if ocr_text.strip():
                    image_content.append(f"Image {img_index + 1}: {ocr_text}")
                    
        except Exception as e:
            self.logger.warning(f"Error extracting images from page {page_num}: {str(e)}")
            
        return "\n\n".join(image_content)
    
    def _extract_regular_text(self, fitz_page, plumber_page) -> str:
        """Extract regular text content, excluding tables and images."""
        try:
            # Use PyMuPDF for basic text extraction
            # This could be enhanced to exclude table/image regions
            text = fitz_page.get_text("text")
            return text
        except Exception as e:
            self.logger.warning(f"Error extracting regular text: {str(e)}")
            return ""
    
    def _ocr_image_bytes(self, image_bytes: bytes) -> str:
        """Apply OCR to image bytes."""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply OCR
            custom_config = f"-l {self.ocr_config['lang']} {self.ocr_config['config']}"
            text = pytesseract.image_to_string(image, config=custom_config)
            
            return text.strip()
            
        except Exception as e:
            self.logger.warning(f"Error applying OCR to image: {str(e)}")
            return ""
    
    def _ocr_region(self, fitz_page, bbox: Tuple[float, float, float, float], page_num: int) -> str:
        """Apply OCR to a specific region of the page."""
        try:
            # Create a pixmap for the region
            mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
            pix = fitz_page.get_pixmap(matrix=mat, clip=fitz.Rect(bbox))
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")
            image = Image.open(io.BytesIO(img_data))
            
            # Apply OCR
            custom_config = f"-l {self.ocr_config['lang']} {self.ocr_config['config']}"
            text = pytesseract.image_to_string(image, config=custom_config)
            
            return text.strip()
            
        except Exception as e:
            self.logger.warning(f"Error applying OCR to region on page {page_num}: {str(e)}")
            return ""
    
    def _format_table_structure(self, table: List[List], title: str) -> str:
        """Format table data preserving structure."""
        if not table:
            return ""
            
        formatted_lines = [f"### {title} ###"]
        
        for row_idx, row in enumerate(table):
            if row_idx == 0:  # Header row
                formatted_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in row) + " |")
                formatted_lines.append("|" + "|".join("---" for _ in row) + "|")
            else:
                formatted_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in row) + " |")
        
        return "\n".join(formatted_lines)
    
    def _flatten_table_to_text(self, table: List[List]) -> str:
        """Convert table to flat text."""
        if not table:
            return ""
            
        text_lines = []
        for row in table:
            row_text = " ".join(str(cell) if cell else "" for cell in row)
            if row_text.strip():
                text_lines.append(row_text.strip())
        
        return "\n".join(text_lines)
    
    def _should_apply_ocr_to_table(self, table: List[List]) -> bool:
        """Determine if a table needs OCR enhancement."""
        if not table:
            return True
        
        # Count empty cells
        total_cells = sum(len(row) for row in table)
        empty_cells = sum(1 for row in table for cell in row if not cell or not str(cell).strip())
        
        # If too many empty cells, might need OCR
        return (empty_cells / total_cells) > 0.3 if total_cells > 0 else True
    
    def _get_table_bbox(self, plumber_page, table_index: int) -> Tuple[float, float, float, float]:
        """Get bounding box for a table."""
        # This is a simplified implementation
        # In practice, you'd need to implement table boundary detection
        return (0, 0, plumber_page.width, plumber_page.height)

# Integration with existing ProcessController
class EnhancedProcessController(BaseController):
    """Enhanced version of ProcessController with smart PDF processing."""
    
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.smart_pdf_controller = SmartPDFController(project_id)
    
    def get_enhanced_file_content(self, file_id: str, use_smart_ocr: bool = True) -> Optional[List[Document]]:
        """Get file content with enhanced PDF processing capabilities."""
        
        file_ext = os.path.splitext(file_id)[-1].lower()
        file_path = os.path.join(self.get_project_path(), file_id)
        
        if not os.path.exists(file_path):
            return None
        
        if file_ext == '.pdf' and use_smart_ocr:
            # Use smart OCR processing for PDFs
            return self.smart_pdf_controller.process_pdf_with_smart_ocr(
                file_path, 
                ocr_images=True, 
                ocr_tables=True,
                extract_table_structure=True
            )
        else:
            # Fall back to regular processing
            from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
            
            if file_ext == '.txt':
                loader = TextLoader(file_path, encoding="utf-8")
            elif file_ext == '.pdf':
                loader = PyMuPDFLoader(file_path)
            else:
                return None
                
            return loader.load()
    
    def get_project_path(self) -> str:
        """Get the project path - implement based on your existing logic."""
        # This should match your existing ProjectController logic
        return f"/path/to/projects/{self.project_id}" 