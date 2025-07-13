#!/usr/bin/env python3
"""
Simple PDF Processing Test Script

This script demonstrates how to run PDF processing with detailed output.
Perfect for testing and seeing exactly what happens at each step.
"""

import sys
import os
import logging
from pathlib import Path

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

def test_unstructured_approach(pdf_path: str):
    """Test the unstructured library approach with detailed output."""
    
    print("\n" + "🔍 TESTING UNSTRUCTURED LIBRARY APPROACH")
    print("-" * 50)
    
    try:
        from unstructured.partition.pdf import partition_pdf
        from unstructured.staging.base import convert_to_dict
        
        print(f"📄 Processing: {pdf_path}")
        
        # Process with detailed strategy
        print("🔄 Starting PDF processing...")
        elements = partition_pdf(
            filename=pdf_path,
            strategy="hi_res",
            infer_table_structure=True,
            extract_images_in_pdf=True,
            extract_image_block_types=["Image", "Table"]
        )
        
        print(f"✅ Found {len(elements)} content elements")
        
        # Show detailed breakdown
        element_types = {}
        for element in elements:
            elem_dict = convert_to_dict(element)
            elem_type = elem_dict.get('type', 'Unknown')
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        print("\n📊 Content types detected:")
        for elem_type, count in element_types.items():
            print(f"   • {elem_type}: {count} items")
        
        # Show first few elements with details
        print(f"\n🔍 First 5 elements details:")
        for i, element in enumerate(elements[:5]):
            elem_dict = convert_to_dict(element)
            elem_type = elem_dict.get('type', 'Unknown')
            text = elem_dict.get('text', '')
            
            print(f"\n   Element {i+1} ({elem_type}):")
            if text:
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"   Content: {preview}")
                print(f"   Length: {len(text)} characters")
            else:
                print(f"   Content: [No text]")
        
        # Save results
        output_file = f"test_unstructured_output.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, element in enumerate(elements):
                elem_dict = convert_to_dict(element)
                f.write(f"=== Element {i+1} ({elem_dict.get('type', 'Unknown')}) ===\n")
                f.write(elem_dict.get('text', '') + '\n\n')
        
        print(f"\n💾 Full output saved to: {output_file}")
        return True
        
    except ImportError:
        print("❌ unstructured library not installed")
        print("Install with: pip install 'unstructured[pdf]'")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_simple_pymupdf(pdf_path: str):
    """Test simple PyMuPDF processing to compare."""
    
    print("\n" + "📄 TESTING SIMPLE PYMUPDF APPROACH")
    print("-" * 50)
    
    try:
        import fitz
        
        doc = fitz.open(pdf_path)
        print(f"📄 Opened PDF with {len(doc)} pages")
        
        all_content = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            print(f"\n🔄 Processing page {page_num + 1}...")
            
            # Extract text
            text = page.get_text()
            print(f"   📝 Extracted {len(text)} characters of text")
            
            # Check for images
            images = page.get_images()
            print(f"   🖼️  Found {len(images)} images")
            
            # Show text preview
            if text.strip():
                preview = text.strip()[:150] + "..." if len(text) > 150 else text.strip()
                print(f"   Preview: {preview}")
            
            all_content.append(f"=== Page {page_num + 1} ===\n{text}\n")
        
        doc.close()
        
        # Save simple output
        output_file = f"test_simple_output.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_content))
        
        print(f"\n💾 Simple output saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_with_debug_logging(pdf_path: str):
    """Test with maximum debug logging to see everything."""
    
    print("\n" + "🐛 TESTING WITH MAXIMUM DEBUG LOGGING")
    print("-" * 50)
    
    # Enable even more detailed logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Add file handler for debug log
    debug_handler = logging.FileHandler('debug_output.log', mode='w')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s'))
    logger.addHandler(debug_handler)
    
    try:
        import fitz
        import time
        
        print(f"📄 Opening {pdf_path} with debug logging...")
        
        start_time = time.time()
        doc = fitz.open(pdf_path)
        
        logging.info(f"PDF opened successfully: {len(doc)} pages")
        logging.debug(f"PDF metadata: {doc.metadata}")
        
        for page_num in range(min(3, len(doc))):  # Process first 3 pages only
            page = doc[page_num]
            logging.info(f"Processing page {page_num + 1}")
            
            # Get page info
            rect = page.rect
            logging.debug(f"Page {page_num + 1} dimensions: {rect.width} x {rect.height}")
            
            # Extract text with timing
            text_start = time.time()
            text = page.get_text()
            text_time = time.time() - text_start
            
            logging.info(f"Page {page_num + 1}: Extracted {len(text)} characters in {text_time:.3f}s")
            
            # Check images with details
            images = page.get_images()
            logging.info(f"Page {page_num + 1}: Found {len(images)} images")
            
            for img_idx, img in enumerate(images):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    logging.debug(f"Image {img_idx + 1}: {base_image['width']}x{base_image['height']}, "
                                f"{len(base_image['image'])} bytes, format: {base_image['ext']}")
                except Exception as e:
                    logging.warning(f"Could not extract image {img_idx + 1}: {str(e)}")
            
            print(f"   ✅ Page {page_num + 1}: {len(text)} chars, {len(images)} images")
        
        doc.close()
        total_time = time.time() - start_time
        
        logging.info(f"Total processing time: {total_time:.3f}s")
        print(f"\n💾 Debug log saved to: debug_output.log")
        
        return True
        
    except Exception as e:
        logging.error(f"Error in debug processing: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main test function."""
    
    if len(sys.argv) != 2:
        print("Usage: python test_pdf_processing.py <pdf_file>")
        print("\nThis script will test different PDF processing approaches")
        print("and show you detailed output from each step.")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    if not pdf_path.lower().endswith('.pdf'):
        print(f"❌ File must be a PDF: {pdf_path}")
        sys.exit(1)
    
    print("🚀 PDF PROCESSING TEST SUITE")
    print(f"📁 Testing file: {pdf_path}")
    print(f"📏 File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    # Test 1: Simple approach
    print("\n" + "="*60)
    test_simple_pymupdf(pdf_path)
    
    # Test 2: Advanced approach
    print("\n" + "="*60)
    test_unstructured_approach(pdf_path)
    
    # Test 3: Debug approach
    print("\n" + "="*60)
    test_with_debug_logging(pdf_path)
    
    print("\n" + "="*60)
    print("🎯 TESTING COMPLETE!")
    print("\nFiles created:")
    print("• test_simple_output.txt - Simple text extraction")
    print("• test_unstructured_output.txt - Advanced processing")
    print("• debug_output.log - Detailed debug information")
    print("\nCompare the files to see the differences between approaches!")

if __name__ == "__main__":
    main() 