#!/usr/bin/env python3
"""
Test AA v5 extraction on first 5 pages of Relius AA

This validates the new provisions + form_elements model before running full extraction.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Test AA v5 on sample pages"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("AA V5 SAMPLE TEST - First 5 Pages")
    print("="*80)
    print()
    print("Testing provisions + form_elements model:")
    print("  - Prompt: aa_extraction_v5.txt (314 words)")
    print("  - Model: gpt-5-mini")
    print("  - Pages: 1-5 of Relius AA (45 pages total)")
    print("  - Validation: status field + form_elements array")
    print()

    # Extract first 5 pages using a temporary PDF
    source_pdf = Path("test_data/raw/relius/relius_aa_cycle3.pdf")
    temp_pdf = Path("/tmp/relius_aa_sample_5pages.pdf")
    output_path = Path("test_data/extracted_vision_v5/relius_aa_sample_5pages.json")

    # Create 5-page PDF
    doc = pymupdf.open(source_pdf)
    sample_doc = pymupdf.open()
    for page_num in range(min(5, len(doc))):
        sample_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
    sample_doc.save(temp_pdf)
    sample_doc.close()
    doc.close()

    print(f"Created sample PDF: {temp_pdf}")
    print()

    # Extract
    result = extract_document_parallel(
        pdf_path=temp_pdf,
        doc_type="AA",
        output_path=output_path,
        batch_size=1,
        max_workers=4  # Fewer workers for small test
    )

    print()
    print("="*80)
    print("SAMPLE TEST RESULTS")
    print("="*80)
    print(f"Total pages: {result['total_pages']}")
    print(f"Successful: {result['successful_pages']} ({result['success_rate_percent']}%)")
    print(f"Failed: {result['failed_pages_count']}")
    print(f"Provisions extracted: {len(result['aas'])}")
    print()

    if len(result['aas']) > 0:
        print("Sample provision structure:")
        sample = result['aas'][0]
        print(json.dumps(sample, indent=2))
        print()

        # Validate structure
        has_status = all('status' in p for p in result['aas'])
        has_form_elements = all('form_elements' in p for p in result['aas'])
        has_page = all('pdf_page' in p for p in result['aas'])

        print("Validation:")
        print(f"  ✓ All provisions have 'status' field: {has_status}")
        print(f"  ✓ All provisions have 'form_elements' field: {has_form_elements}")
        print(f"  ✓ All provisions have 'pdf_page' field: {has_page}")
        print()

        # Count provisions with form elements
        with_elements = sum(1 for p in result['aas'] if len(p.get('form_elements', [])) > 0)
        print(f"Provisions with form elements: {with_elements}/{len(result['aas'])}")

        if with_elements > 0:
            print()
            print("Sample provision with form elements:")
            with_elem = next(p for p in result['aas'] if len(p.get('form_elements', [])) > 0)
            print(json.dumps(with_elem, indent=2))
    else:
        print("⚠ WARNING: 0 provisions extracted!")
        print("This matches v4's failure. Check extractor logic.")

    print()
    print("="*80)
    print(f"Output saved to: {output_path}")
    print("="*80)


if __name__ == "__main__":
    main()
