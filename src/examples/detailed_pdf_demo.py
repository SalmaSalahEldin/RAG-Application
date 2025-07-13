#!/usr/bin/env python3
"""
Detailed PDF Processing Demo

This script demonstrates step-by-step PDF processing with detailed output
showing exactly what happens at each stage.

Usage:
    python src/examples/detailed_pdf_demo.py <pdf_path> [--strategy=unstructured|hybrid|content_aware]
"""

import sys
import os
import argparse
import logging
import time
from typing import List, Dict, Any
import json
from pathlib import Path

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pdf_processing_debug.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def demo_unstructured_approach(pdf_path: str):
    """Demonstrate the unstructured library approach with detailed output."""
    
    print("\n" + "="*80)
    print("🔍 UNSTRUCTURED LIBRARY APPROACH - DETAILED DEMO")
    print("="*80)
    
    try:
        from unstructured.partition.pdf import partition_pdf
        from unstructured.staging.base import convert_to_dict
        
        print(f"📄 Processing PDF: {pdf_path}")
        print(f"📁 File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
        
        # Step 1: Basic partitioning
        print("\n🔄 Step 1: Basic PDF partitioning...")
        start_time = time.time()
        
        elements = partition_pdf(
            filename=pdf_path,
            strategy="fast",  # Start with fast strategy
            infer_table_structure=False,
            extract_images_in_pdf=False
        )
        
        basic_time = time.time() - start_time
        print(f"✅ Basic partitioning completed in {basic_time:.2f} seconds")
        print(f"📊 Found {len(elements)} elements")
        
        # Show element types found
        element_types = {}
        for element in elements:
            elem_dict = convert_to_dict(element)
            elem_type = elem_dict.get('type', 'Unknown')
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        print("📋 Element types found:")
        for elem_type, count in element_types.items():
            print(f"   • {elem_type}: {count}")
        
        # Step 2: High-resolution processing with OCR
        print("\n🔄 Step 2: High-resolution processing with OCR...")
        start_time = time.time()
        
        elements_hi_res = partition_pdf(
            filename=pdf_path,
            strategy="hi_res",  # High resolution for better OCR
            infer_table_structure=True,
            extract_images_in_pdf=True,
            extract_image_block_types=["Image", "Table"]
        )
        
        hi_res_time = time.time() - start_time
        print(f"✅ Hi-res processing completed in {hi_res_time:.2f} seconds")
        print(f"📊 Found {len(elements_hi_res)} elements (hi-res)")
        
        # Show detailed breakdown of hi-res results
        hi_res_types = {}
        total_text_length = 0
        
        for element in elements_hi_res:
            elem_dict = convert_to_dict(element)
            elem_type = elem_dict.get('type', 'Unknown')
            text = elem_dict.get('text', '')
            
            hi_res_types[elem_type] = hi_res_types.get(elem_type, 0) + 1
            total_text_length += len(text)
        
        print("📋 Hi-res element types:")
        for elem_type, count in hi_res_types.items():
            print(f"   • {elem_type}: {count}")
        
        print(f"📝 Total extracted text: {total_text_length} characters")
        
        # Step 3: Show sample content from each type
        print("\n🔍 Step 3: Sample content from each element type...")
        
        for element in elements_hi_res[:10]:  # Show first 10 elements
            elem_dict = convert_to_dict(element)
            elem_type = elem_dict.get('type', 'Unknown')
            text = elem_dict.get('text', '')
            
            print(f"\n📄 {elem_type}:")
            if text:
                preview = text[:150] + "..." if len(text) > 150 else text
                print(f"   Content: {preview}")
                print(f"   Length: {len(text)} characters")
            else:
                print("   Content: [No text content]")
        
        # Step 4: Save detailed results
        output_file = f"unstructured_results_{Path(pdf_path).stem}.json"
        results = []
        
        for i, element in enumerate(elements_hi_res):
            elem_dict = convert_to_dict(element)
            results.append({
                'index': i,
                'type': elem_dict.get('type', 'Unknown'),
                'text': elem_dict.get('text', ''),
                'metadata': elem_dict.get('metadata', {})
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        return {
            'basic_time': basic_time,
            'hi_res_time': hi_res_time,
            'total_elements': len(elements_hi_res),
            'total_text_length': total_text_length,
            'element_types': hi_res_types
        }
        
    except ImportError:
        print("❌ Error: unstructured library not installed")
        print("Run: pip install 'unstructured[pdf]'")
        return None
    except Exception as e:
        print(f"❌ Error processing with unstructured: {str(e)}")
        return None

def demo_hybrid_approach(pdf_path: str):
    """Demonstrate the hybrid approach with step-by-step output."""
    
    print("\n" + "="*80)
    print("🔧 HYBRID MULTI-LIBRARY APPROACH - DETAILED DEMO")
    print("="*80)
    
    try:
        import fitz  # PyMuPDF
        import pdfplumber
        import pytesseract
        from PIL import Image
        import io
        
        print(f"📄 Processing PDF: {pdf_path}")
        
        # Step 1: Open with both libraries
        print("\n🔄 Step 1: Opening PDF with multiple libraries...")
        fitz_doc = fitz.open(pdf_path)
        plumber_doc = pdfplumber.open(pdf_path)
        
        print(f"✅ Opened with PyMuPDF: {len(fitz_doc)} pages")
        print(f"✅ Opened with pdfplumber: {len(plumber_doc.pages)} pages")
        
        all_results = []
        
        for page_num in range(len(fitz_doc)):
            print(f"\n📄 Processing Page {page_num + 1}/{len(fitz_doc)}...")
            
            fitz_page = fitz_doc[page_num]
            plumber_page = plumber_doc.pages[page_num]
            
            page_result = {
                'page': page_num + 1,
                'regular_text': '',
                'tables': [],
                'images': [],
                'processing_log': []
            }
            
            # Step 2: Extract regular text
            print("   🔄 Extracting regular text...")
            start_time = time.time()
            regular_text = fitz_page.get_text("text")
            text_time = time.time() - start_time
            
            page_result['regular_text'] = regular_text.strip()
            page_result['processing_log'].append(f"Text extraction: {text_time:.3f}s, {len(regular_text)} chars")
            
            print(f"   ✅ Extracted {len(regular_text)} characters in {text_time:.3f}s")
            if regular_text.strip():
                preview = regular_text.strip()[:100] + "..." if len(regular_text) > 100 else regular_text.strip()
                print(f"   📝 Preview: {preview}")
            
            # Step 3: Extract tables
            print("   🔄 Detecting and extracting tables...")
            start_time = time.time()
            tables = plumber_page.extract_tables()
            table_time = time.time() - start_time
            
            print(f"   ✅ Found {len(tables)} tables in {table_time:.3f}s")
            page_result['processing_log'].append(f"Table detection: {table_time:.3f}s, {len(tables)} tables")
            
            for i, table in enumerate(tables):
                if table:
                    # Check if table needs OCR enhancement
                    non_empty_cells = sum(1 for row in table for cell in row if cell and str(cell).strip())
                    total_cells = sum(len(row) for row in table)
                    completeness = non_empty_cells / total_cells if total_cells > 0 else 0
                    
                    table_info = {
                        'index': i + 1,
                        'rows': len(table),
                        'total_cells': total_cells,
                        'non_empty_cells': non_empty_cells,
                        'completeness': completeness,
                        'needs_ocr': completeness < 0.7,
                        'content': table
                    }
                    
                    print(f"      📊 Table {i+1}: {len(table)} rows, {completeness:.1%} complete")
                    if table_info['needs_ocr']:
                        print(f"         ⚠️  Table seems incomplete, would benefit from OCR")
                    
                    page_result['tables'].append(table_info)
            
            # Step 4: Extract and analyze images
            print("   🔄 Extracting and analyzing images...")
            start_time = time.time()
            images = fitz_page.get_images()
            image_time = time.time() - start_time
            
            print(f"   ✅ Found {len(images)} images in {image_time:.3f}s")
            page_result['processing_log'].append(f"Image detection: {image_time:.3f}s, {len(images)} images")
            
            for img_idx, img in enumerate(images):
                try:
                    xref = img[0]
                    base_image = fitz_page.parent.extract_image(xref)
                    
                    image_info = {
                        'index': img_idx + 1,
                        'width': base_image["width"],
                        'height': base_image["height"],
                        'size_kb': len(base_image["image"]) / 1024,
                        'ext': base_image["ext"],
                        'should_ocr': (base_image["width"] >= 100 and base_image["height"] >= 100)
                    }
                    
                    print(f"      🖼️  Image {img_idx+1}: {image_info['width']}x{image_info['height']}, "
                          f"{image_info['size_kb']:.1f}KB ({image_info['ext']})")
                    
                    if image_info['should_ocr']:
                        print(f"         ✅ Suitable for OCR processing")
                        # Here you would actually do OCR in a real implementation
                        image_info['ocr_text'] = "[OCR would be applied here]"
                    else:
                        print(f"         ⏭️  Too small for OCR (likely decorative)")
                        image_info['ocr_text'] = ""
                    
                    page_result['images'].append(image_info)
                    
                except Exception as e:
                    print(f"         ❌ Error processing image {img_idx+1}: {str(e)}")
            
            all_results.append(page_result)
        
        # Close documents
        fitz_doc.close()
        plumber_doc.close()
        
        # Step 5: Generate summary
        print(f"\n📊 PROCESSING SUMMARY:")
        total_text = sum(len(r['regular_text']) for r in all_results)
        total_tables = sum(len(r['tables']) for r in all_results)
        total_images = sum(len(r['images']) for r in all_results)
        
        print(f"   📝 Total text extracted: {total_text} characters")
        print(f"   📊 Total tables found: {total_tables}")
        print(f"   🖼️  Total images found: {total_images}")
        
        # Save detailed results
        output_file = f"hybrid_results_{Path(pdf_path).stem}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        return {
            'total_pages': len(all_results),
            'total_text': total_text,
            'total_tables': total_tables,
            'total_images': total_images
        }
        
    except ImportError as e:
        print(f"❌ Error: Missing required library: {str(e)}")
        print("Run: pip install PyMuPDF pdfplumber pytesseract pillow")
        return None
    except Exception as e:
        print(f"❌ Error processing with hybrid approach: {str(e)}")
        return None

def demo_content_aware_approach(pdf_path: str):
    """Demonstrate content-aware processing with detailed analysis."""
    
    print("\n" + "="*80)
    print("🧠 CONTENT-AWARE PROCESSING - DETAILED DEMO")
    print("="*80)
    
    try:
        import fitz
        
        print(f"📄 Processing PDF: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        all_results = []
        
        for page_num in range(len(doc)):
            print(f"\n📄 Analyzing Page {page_num + 1}/{len(doc)}...")
            
            page = doc[page_num]
            
            # Step 1: Analyze page layout
            print("   🔍 Step 1: Analyzing page layout...")
            
            # Get basic page info
            page_rect = page.rect
            page_area = page_rect.width * page_rect.height
            
            # Get text and analyze density
            text = page.get_text("text")
            text_density = len(text) / page_area if page_area > 0 else 0
            
            # Count images
            images = page.get_images()
            
            # Simple table detection (looking for tabular patterns)
            lines = text.split('\n')
            tabular_lines = sum(1 for line in lines if '\t' in line or '  ' in line)
            table_indicator = tabular_lines / len(lines) if lines else 0
            
            # Analyze layout
            layout_analysis = {
                'page_area': page_area,
                'text_length': len(text),
                'text_density': text_density,
                'image_count': len(images),
                'tabular_lines': tabular_lines,
                'table_indicator': table_indicator,
                'line_count': len(lines)
            }
            
            # Determine page type
            if len(images) > 3:
                page_type = "image_heavy"
                processing_strategy = "OCR-focused for images"
            elif table_indicator > 0.3:
                page_type = "table_heavy"
                processing_strategy = "Enhanced table extraction with OCR fallback"
            elif text_density < 0.01:
                page_type = "sparse_content"
                processing_strategy = "Full-page OCR"
            else:
                page_type = "text_document"
                processing_strategy = "Standard text extraction"
            
            layout_analysis.update({
                'page_type': page_type,
                'processing_strategy': processing_strategy
            })
            
            print(f"   📊 Page analysis:")
            print(f"      • Page type: {page_type}")
            print(f"      • Text density: {text_density:.4f} chars/pixel²")
            print(f"      • Images: {len(images)}")
            print(f"      • Text lines: {len(lines)}")
            print(f"      • Tabular content: {table_indicator:.1%}")
            print(f"      • Processing strategy: {processing_strategy}")
            
            # Step 2: Apply appropriate processing
            print(f"   🔄 Step 2: Applying {processing_strategy}...")
            
            start_time = time.time()
            
            if page_type == "image_heavy":
                content = f"[IMAGE-HEAVY PAGE - Would apply OCR to {len(images)} images]\n" + text
                processing_notes = f"Would OCR {len(images)} images for text extraction"
            elif page_type == "table_heavy":
                content = f"[TABLE-HEAVY PAGE - Would apply enhanced table extraction]\n" + text
                processing_notes = f"Would use specialized table extraction with OCR fallback"
            elif page_type == "sparse_content":
                content = f"[SPARSE CONTENT - Would apply full-page OCR]\n" + text
                processing_notes = "Would OCR entire page for better text capture"
            else:
                content = text
                processing_notes = "Standard text extraction sufficient"
            
            processing_time = time.time() - start_time
            
            print(f"   ✅ Processing completed in {processing_time:.3f}s")
            print(f"   📝 Extracted {len(content)} characters")
            print(f"   💡 {processing_notes}")
            
            page_result = {
                'page': page_num + 1,
                'layout_analysis': layout_analysis,
                'content': content,
                'processing_time': processing_time,
                'processing_notes': processing_notes
            }
            
            all_results.append(page_result)
        
        doc.close()
        
        # Generate summary
        print(f"\n📊 CONTENT-AWARE PROCESSING SUMMARY:")
        page_types = {}
        total_content = 0
        
        for result in all_results:
            page_type = result['layout_analysis']['page_type']
            page_types[page_type] = page_types.get(page_type, 0) + 1
            total_content += len(result['content'])
        
        print(f"   📄 Total pages: {len(all_results)}")
        print(f"   📝 Total content: {total_content} characters")
        print(f"   📊 Page type distribution:")
        for ptype, count in page_types.items():
            print(f"      • {ptype}: {count} pages")
        
        # Save results
        output_file = f"content_aware_results_{Path(pdf_path).stem}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        return {
            'total_pages': len(all_results),
            'total_content': total_content,
            'page_types': page_types
        }
        
    except Exception as e:
        print(f"❌ Error with content-aware processing: {str(e)}")
        return None

def main():
    """Main function with argument parsing and strategy selection."""
    
    parser = argparse.ArgumentParser(description='Detailed PDF Processing Demo')
    parser.add_argument('pdf_path', help='Path to the PDF file to process')
    parser.add_argument('--strategy', 
                       choices=['unstructured', 'hybrid', 'content_aware', 'all'],
                       default='all',
                       help='Processing strategy to demonstrate')
    parser.add_argument('--save-debug', action='store_true',
                       help='Save debug information to files')
    
    args = parser.parse_args()
    
    # Validate PDF file
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    if not args.pdf_path.lower().endswith('.pdf'):
        print(f"❌ Error: File must be a PDF: {args.pdf_path}")
        sys.exit(1)
    
    print("🚀 SMART PDF PROCESSING - DETAILED DEMONSTRATION")
    print(f"📁 File: {args.pdf_path}")
    print(f"🔧 Strategy: {args.strategy}")
    print(f"🐛 Debug logging: {'Enabled' if args.save_debug else 'Console only'}")
    
    results = {}
    
    # Run selected strategy
    if args.strategy in ['unstructured', 'all']:
        results['unstructured'] = demo_unstructured_approach(args.pdf_path)
    
    if args.strategy in ['hybrid', 'all']:
        results['hybrid'] = demo_hybrid_approach(args.pdf_path)
    
    if args.strategy in ['content_aware', 'all']:
        results['content_aware'] = demo_content_aware_approach(args.pdf_path)
    
    # Final summary
    print("\n" + "="*80)
    print("📊 FINAL COMPARISON SUMMARY")
    print("="*80)
    
    for strategy, result in results.items():
        if result:
            print(f"\n🔧 {strategy.upper()} APPROACH:")
            for key, value in result.items():
                print(f"   • {key}: {value}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print(f"   • For ease of use: Choose 'unstructured' approach")
    print(f"   • For fine control: Choose 'hybrid' approach")
    print(f"   • For optimization: Choose 'content_aware' approach")
    
    print(f"\n📁 Check generated files:")
    print(f"   • JSON results: *_results_*.json")
    print(f"   • Debug log: pdf_processing_debug.log")

if __name__ == "__main__":
    main() 