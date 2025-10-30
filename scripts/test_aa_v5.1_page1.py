#!/usr/bin/env python3
"""
Quick test: Extract just page 1 of Relius AA with v5.1 prompt
To inspect the Atomic Field Rule behavior on Question 1
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Extract page 1 only for quick inspection"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("AA V5.1 - SINGLE PAGE TEST (Page 1)")
    print("="*80)
    print()

    # Extract just page 1
    source_pdf = Path("test_data/raw/relius/relius_aa_cycle3.pdf")
    temp_pdf = Path("/tmp/relius_aa_page1_v5.1.pdf")
    output_path = Path("test_data/extracted_vision_v5/relius_aa_page1_v5.1.json")

    # Create 1-page PDF
    doc = pymupdf.open(source_pdf)
    sample_doc = pymupdf.open()
    sample_doc.insert_pdf(doc, from_page=0, to_page=0)
    sample_doc.save(temp_pdf)
    sample_doc.close()
    doc.close()

    print("Extracting page 1 with v5.1 prompt...")
    print()

    # Extract
    result = extract_document_parallel(
        pdf_path=temp_pdf,
        doc_type="AA",
        output_path=output_path,
        batch_size=1,
        max_workers=1
    )

    print()
    print("="*80)
    print("RESULTS")
    print("="*80)
    print(f"Success: {result['success_rate_percent']}%")
    print(f"Provisions extracted: {len(result['aas'])}")
    print()

    if len(result['aas']) > 0:
        # Pretty print the full output
        print("Full JSON output:")
        print("="*80)
        print(json.dumps(result['aas'], indent=2))
        print("="*80)
        print()

        # Specific check for Question 1
        q1_parent = next((p for p in result['aas'] if p.get('section_number') == '1' or p.get('section_number') == '1.'), None)
        q1_children = [p for p in result['aas'] if p.get('parent_section') in ['1', '1.']]

        if q1_parent:
            print("Question 1 Parent:")
            print(f"  section_number: '{q1_parent['section_number']}'")
            print(f"  section_title: '{q1_parent['section_title']}'")
            print(f"  form_elements: {len(q1_parent.get('form_elements', []))}")
            print()

        print(f"Question 1 Children: {len(q1_children)}")
        for i, child in enumerate(q1_children, 1):
            print(f"  {i}. section_number='{child['section_number']}' section_title='{child['section_title']}'")
            print(f"     parent_section='{child['parent_section']}' local_ordinal={child.get('local_ordinal')}")
            print(f"     field_label='{child.get('field_label')}' form_elements={len(child.get('form_elements', []))}")
            print()

    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
