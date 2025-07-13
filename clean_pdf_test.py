#!/usr/bin/env python3
"""
Clean PDF Processing Test - No Debug Noise

Shows only the essential results without overwhelming debug output.
"""

import sys
import os
import logging
import time

# Set logging to only show errors, not debug info
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('pdfminer').setLevel(logging.ERROR)
logging.getLogger('pdfplumber').setLevel(logging.ERROR)

def test_pdf_clean(pdf_path: str):
    """Test PDF processing with clean, minimal output."""
    
    print(f"🔍 Processing: {pdf_path}")
    print(f"📏 Size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    try:
        import fitz
        import pdfplumber
        
        # Basic processing
        start_time = time.time()
        
        # Open with PyMuPDF
        fitz_doc = fitz.open(pdf_path)
        total_pages = len(fitz_doc)
        total_text = 0
        total_images = 0
        
        print(f"📄 Pages: {total_pages}")
        
        # Process each page
        for page_num in range(total_pages):
            page = fitz_doc[page_num]
            
            # Get text
            text = page.get_text()
            text_length = len(text.strip())
            
            # Get images
            images = page.get_images()
            image_count = len(images)
            
            # Show page summary
            content_types = []
            if text_length > 0:
                content_types.append(f"text({text_length} chars)")
            if image_count > 0:
                content_types.append(f"images({image_count})")
            
            content_str = ", ".join(content_types) if content_types else "empty"
            print(f"   Page {page_num + 1}: {content_str}")
            
            total_text += text_length
            total_images += image_count
        
        fitz_doc.close()
        
        # Check for tables with pdfplumber
        table_count = 0
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        table_count += len([t for t in tables if t])
        except:
            pass
        
        processing_time = time.time() - start_time
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   ⏱️  Processing time: {processing_time:.2f}s")
        print(f"   📝 Total text: {total_text} characters")
        print(f"   🖼️  Total images: {total_images}")
        print(f"   📊 Total tables: {table_count}")
        
        # Save clean output
        output_file = f"clean_output_{os.path.basename(pdf_path).replace('.pdf', '.txt')}"
        
        with fitz.open(pdf_path) as doc:
            with open(output_file, 'w', encoding='utf-8') as f:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        f.write(f"=== Page {page_num + 1} ===\n")
                        f.write(text + "\n\n")
        
        print(f"   💾 Text saved to: {output_file}")
        
        # Recommend processing strategy
        if total_images > 0:
            print(f"   💡 Recommendation: Use OCR for {total_images} images")
        if table_count > 0:
            print(f"   💡 Recommendation: Use table-aware processing for {table_count} tables")
        if total_text > total_images * 100:
            print(f"   💡 Recommendation: Standard text extraction works well")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python clean_pdf_test.py <pdf_file>")
        print("Example: python clean_pdf_test.py 'salem.pdf'")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    success = test_pdf_clean(pdf_path)
    
    if success:
        print("\n✅ Processing completed successfully!")
    else:
        print("\n❌ Processing failed!")

if __name__ == "__main__":
    main() 