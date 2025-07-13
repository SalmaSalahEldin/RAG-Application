#!/usr/bin/env python3
"""
Simple PDF Processing Test - Works with current dependencies

This shows you exactly how PDF processing works step-by-step
without requiring heavy AI/ML dependencies.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

def test_basic_pymupdf(pdf_path: str):
    """Test basic PyMuPDF processing with detailed output."""
    
    print("\n" + "🔍 TESTING BASIC PYMUPDF PROCESSING")
    print("=" * 60)
    
    try:
        import fitz
        
        print(f"📄 Opening PDF: {pdf_path}")
        start_time = time.time()
        
        doc = fitz.open(pdf_path)
        open_time = time.time() - start_time
        
        print(f"✅ Opened in {open_time:.3f}s - Found {len(doc)} pages")
        print(f"📊 PDF Info:")
        print(f"   • Title: {doc.metadata.get('title', 'No title')}")
        print(f"   • Author: {doc.metadata.get('author', 'No author')}")
        print(f"   • Pages: {len(doc)}")
        
        all_content = []
        total_chars = 0
        total_images = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            print(f"\n🔄 Processing page {page_num + 1}...")
            
            # Get page dimensions
            rect = page.rect
            print(f"   📐 Page size: {rect.width:.1f} x {rect.height:.1f}")
            
            # Extract text with timing
            text_start = time.time()
            text = page.get_text()
            text_time = time.time() - text_start
            
            print(f"   📝 Text extraction: {len(text)} chars in {text_time:.3f}s")
            
            # Count images
            images = page.get_images()
            print(f"   🖼️  Found {len(images)} images")
            
            # Show image details
            for i, img in enumerate(images):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    print(f"      Image {i+1}: {base_image['width']}x{base_image['height']}, "
                          f"{len(base_image['image'])/1024:.1f}KB, {base_image['ext']}")
                except Exception as e:
                    print(f"      Image {i+1}: Error - {str(e)}")
            
            # Show text preview
            if text.strip():
                preview = text.strip()[:150] + "..." if len(text) > 150 else text.strip()
                print(f"   📄 Content preview: {preview}")
            else:
                print(f"   📄 No text content found")
            
            all_content.append(f"=== Page {page_num + 1} ===\n{text}\n")
            total_chars += len(text)
            total_images += len(images)
        
        doc.close()
        
        # Save results
        output_file = f"basic_pdf_output.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_content))
        
        print(f"\n📊 SUMMARY:")
        print(f"   📝 Total text: {total_chars} characters")
        print(f"   🖼️  Total images: {total_images}")
        print(f"   💾 Output saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_pdfplumber_tables(pdf_path: str):
    """Test pdfplumber for table detection with detailed output."""
    
    print("\n" + "🔍 TESTING PDFPLUMBER TABLE DETECTION")
    print("=" * 60)
    
    try:
        import pdfplumber
        
        print(f"📄 Opening PDF with pdfplumber: {pdf_path}")
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"✅ Opened successfully - {len(pdf.pages)} pages")
            
            all_tables = []
            
            for page_num, page in enumerate(pdf.pages):
                print(f"\n🔄 Analyzing page {page_num + 1}...")
                
                # Get page info
                print(f"   📐 Page size: {page.width:.1f} x {page.height:.1f}")
                
                # Extract tables
                start_time = time.time()
                tables = page.extract_tables()
                table_time = time.time() - start_time
                
                print(f"   📊 Table detection: {len(tables)} tables in {table_time:.3f}s")
                
                if tables:
                    for i, table in enumerate(tables):
                        if table:
                            rows = len(table)
                            cols = len(table[0]) if table[0] else 0
                            
                            # Count non-empty cells
                            non_empty = sum(1 for row in table for cell in row 
                                          if cell and str(cell).strip())
                            total_cells = sum(len(row) for row in table)
                            completeness = non_empty / total_cells if total_cells > 0 else 0
                            
                            print(f"      📊 Table {i+1}: {rows} rows × {cols} cols, "
                                  f"{completeness:.1%} filled")
                            
                            # Show sample data
                            if table and table[0]:
                                header_sample = " | ".join(str(cell)[:20] if cell else "" 
                                                         for cell in table[0][:3])
                                print(f"         Header sample: {header_sample}")
                            
                            all_tables.append({
                                'page': page_num + 1,
                                'table_index': i + 1,
                                'rows': rows,
                                'cols': cols,
                                'completeness': completeness,
                                'data': table
                            })
                
                # Extract text for comparison
                text = page.extract_text()
                if text:
                    print(f"   📝 Text length: {len(text)} characters")
                else:
                    print(f"   📝 No text found")
            
            # Save table results
            if all_tables:
                output_file = f"table_analysis_output.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("TABLE ANALYSIS RESULTS\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for table_info in all_tables:
                        f.write(f"Page {table_info['page']}, Table {table_info['table_index']}:\n")
                        f.write(f"Size: {table_info['rows']} rows × {table_info['cols']} cols\n")
                        f.write(f"Completeness: {table_info['completeness']:.1%}\n")
                        f.write("\nData:\n")
                        
                        for row in table_info['data']:
                            row_text = " | ".join(str(cell) if cell else "" for cell in row)
                            f.write(f"{row_text}\n")
                        f.write("\n" + "-" * 50 + "\n\n")
                
                print(f"\n📊 TABLE SUMMARY:")
                print(f"   📊 Total tables found: {len(all_tables)}")
                print(f"   💾 Details saved to: {output_file}")
            else:
                print(f"\n📊 No tables detected in document")
        
        return True
        
    except ImportError:
        print("❌ pdfplumber not available")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def analyze_pdf_content_types(pdf_path: str):
    """Analyze what types of content are in the PDF."""
    
    print("\n" + "🔍 CONTENT TYPE ANALYSIS")
    print("=" * 60)
    
    try:
        import fitz
        import pdfplumber
        
        doc = fitz.open(pdf_path)
        
        analysis = {
            'total_pages': len(doc),
            'pages_with_images': 0,
            'pages_with_text': 0,
            'pages_with_tables': 0,
            'total_images': 0,
            'total_text_length': 0,
            'page_analysis': []
        }
        
        print(f"📄 Analyzing content types in {pdf_path}")
        
        with pdfplumber.open(pdf_path) as plumber_pdf:
            for page_num in range(len(doc)):
                fitz_page = doc[page_num]
                plumber_page = plumber_pdf.pages[page_num]
                
                print(f"\n🔍 Page {page_num + 1} analysis:")
                
                # Check for text
                text = fitz_page.get_text()
                has_text = len(text.strip()) > 0
                
                # Check for images
                images = fitz_page.get_images()
                has_images = len(images) > 0
                
                # Check for tables
                tables = plumber_page.extract_tables()
                has_tables = len(tables) > 0 and any(table for table in tables)
                
                # Update counters
                if has_text:
                    analysis['pages_with_text'] += 1
                    analysis['total_text_length'] += len(text)
                
                if has_images:
                    analysis['pages_with_images'] += 1
                    analysis['total_images'] += len(images)
                
                if has_tables:
                    analysis['pages_with_tables'] += 1
                
                # Determine page type
                page_type = []
                if has_text:
                    page_type.append("text")
                if has_images:
                    page_type.append("images")
                if has_tables:
                    page_type.append("tables")
                
                page_type_str = ", ".join(page_type) if page_type else "empty"
                
                print(f"   📊 Content types: {page_type_str}")
                print(f"   📝 Text: {len(text)} chars")
                print(f"   🖼️  Images: {len(images)}")
                print(f"   📊 Tables: {len(tables)}")
                
                analysis['page_analysis'].append({
                    'page': page_num + 1,
                    'has_text': has_text,
                    'has_images': has_images,
                    'has_tables': has_tables,
                    'text_length': len(text),
                    'image_count': len(images),
                    'table_count': len(tables),
                    'content_types': page_type_str
                })
        
        doc.close()
        
        # Summary
        print(f"\n📊 DOCUMENT ANALYSIS SUMMARY:")
        print(f"   📄 Total pages: {analysis['total_pages']}")
        print(f"   📝 Pages with text: {analysis['pages_with_text']}")
        print(f"   🖼️  Pages with images: {analysis['pages_with_images']}")
        print(f"   📊 Pages with tables: {analysis['pages_with_tables']}")
        print(f"   📝 Total text: {analysis['total_text_length']} characters")
        print(f"   🖼️  Total images: {analysis['total_images']}")
        
        # Recommend processing strategy
        print(f"\n💡 RECOMMENDED PROCESSING STRATEGY:")
        if analysis['pages_with_tables'] > 0:
            print(f"   📊 Use table-aware processing (pdfplumber + OCR fallback)")
        if analysis['pages_with_images'] > 0:
            print(f"   🖼️  Use image OCR processing")
        if analysis['pages_with_text'] > analysis['pages_with_images']:
            print(f"   📝 Standard text extraction is sufficient for most content")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Main test function with step-by-step output."""
    
    if len(sys.argv) != 2:
        print("Usage: python simple_pdf_test.py <pdf_file>")
        print("\nThis script demonstrates PDF processing with detailed output")
        print("showing exactly what happens at each step.")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    if not pdf_path.lower().endswith('.pdf'):
        print(f"❌ File must be a PDF: {pdf_path}")
        sys.exit(1)
    
    print("🚀 SIMPLE PDF PROCESSING TEST SUITE")
    print(f"📁 File: {pdf_path}")
    print(f"📏 Size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    # Test 1: Basic PyMuPDF processing
    print("\n" + "🔸" * 80)
    success1 = test_basic_pymupdf(pdf_path)
    
    # Test 2: Table detection with pdfplumber
    print("\n" + "🔸" * 80)
    success2 = test_pdfplumber_tables(pdf_path)
    
    # Test 3: Content analysis
    print("\n" + "🔸" * 80)
    analysis = analyze_pdf_content_types(pdf_path)
    
    # Final summary
    print("\n" + "🎯" * 80)
    print("TESTING COMPLETE - SUMMARY")
    print("🎯" * 80)
    
    print(f"✅ Basic text extraction: {'Success' if success1 else 'Failed'}")
    print(f"✅ Table detection: {'Success' if success2 else 'Failed'}")
    print(f"✅ Content analysis: {'Success' if analysis else 'Failed'}")
    
    print(f"\n📁 Generated files:")
    if os.path.exists("basic_pdf_output.txt"):
        print(f"   • basic_pdf_output.txt - Extracted text content")
    if os.path.exists("table_analysis_output.txt"):
        print(f"   • table_analysis_output.txt - Table detection results")
    
    print(f"\n🔍 To see OCR in action:")
    print(f"   1. Install tesseract: sudo apt-get install tesseract-ocr")
    print(f"   2. Try the smart PDF processor with OCR enabled")
    
    print(f"\n📖 Next steps:")
    print(f"   • Review the generated files to see what was extracted")
    print(f"   • Compare different processing approaches")
    print(f"   • Integrate the best approach into your application")

if __name__ == "__main__":
    main() 