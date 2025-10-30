#!/usr/bin/env python3
"""
Test AA v5.1 extraction on first 5 pages of Relius AA

v5.1 adds Atomic Field Rule to fix hierarchy extraction:
- Each labeled field (Name, City, TIN) is a separate child provision
- local_ordinal for unlabeled children (1..N)
- field_label for field-like provisions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Test AA v5.1 on sample pages"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("AA V5.1 SAMPLE TEST - First 5 Pages (Atomic Field Rule)")
    print("="*80)
    print()
    print("Testing hierarchy extraction fixes:")
    print("  - Prompt: aa_extraction_v5.1.txt")
    print("  - Model: gpt-5-mini")
    print("  - Pages: 1-5 of Relius AA (45 pages total)")
    print("  - NEW: local_ordinal field (0 for numbered, 1..N for unlabeled)")
    print("  - NEW: field_label field (e.g., 'Name', 'TIN')")
    print("  - FIX: Each labeled field is its own provision")
    print()

    # Extract first 5 pages using a temporary PDF
    source_pdf = Path("test_data/raw/relius/relius_aa_cycle3.pdf")
    temp_pdf = Path("/tmp/relius_aa_sample_5pages_v5.1.pdf")
    output_path = Path("test_data/extracted_vision_v5/relius_aa_sample_5pages_v5.1.json")

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
        # Check for Question 1 structure (was grouped in v5, should be split in v5.1)
        q1_parent = next((p for p in result['aas'] if p.get('section_number') == '1'), None)
        q1_children = [p for p in result['aas'] if p.get('parent_section') == '1']

        print("Question 1 Structure Check:")
        if q1_parent:
            print(f"  ✓ Parent provision found: section_number='1'")
            print(f"    form_elements count: {len(q1_parent.get('form_elements', []))}")
            if len(q1_parent.get('form_elements', [])) == 0:
                print(f"    ✓ Parent has no form_elements (correct - delegated to children)")
            else:
                print(f"    ⚠ Parent has form_elements (should be empty)")

        print(f"  Children under section '1': {len(q1_children)}")
        if len(q1_children) >= 8:
            print(f"    ✓ Expected ~8 children (Name, Address, City, State, Zip, Telephone, TIN, Fiscal Year)")
        else:
            print(f"    ⚠ Expected 8 children, got {len(q1_children)}")

        if q1_children:
            print()
            print("  Sample child provisions:")
            for child in q1_children[:3]:  # Show first 3
                print(f"    - section_number='{child.get('section_number')}'")
                print(f"      section_title='{child.get('section_title')}'")
                print(f"      parent_section='{child.get('parent_section')}'")
                print(f"      local_ordinal={child.get('local_ordinal')}")
                print(f"      field_label='{child.get('field_label')}'")
                print(f"      form_elements count: {len(child.get('form_elements', []))}")
                print()

        # Check for Question 2 nested checkboxes
        q2_provisions = [p for p in result['aas'] if p.get('section_number', '').startswith('2')]
        print(f"Question 2 Structure Check:")
        print(f"  Provisions with section_number starting with '2': {len(q2_provisions)}")

        # Look for nested structure (2.d → 2.d.1)
        nested = [p for p in result['aas'] if '.' in p.get('section_number', '') and p.get('section_number', '').startswith('2')]
        print(f"  Nested provisions (e.g., 2.d, 2.d.1): {len(nested)}")
        if nested:
            print()
            print("  Sample nested structure:")
            for prov in nested[:3]:
                print(f"    - section_number='{prov.get('section_number')}'")
                print(f"      parent_section='{prov.get('parent_section')}'")
                print(f"      local_ordinal={prov.get('local_ordinal')}")
                print(f"      form_elements: {len(prov.get('form_elements', []))} (checkboxes)")
                print()

        # Validation summary
        print()
        print("Validation:")
        has_local_ordinal = all('local_ordinal' in p for p in result['aas'])
        has_field_label = all('field_label' in p for p in result['aas'])
        print(f"  ✓ All provisions have 'local_ordinal' field: {has_local_ordinal}")
        print(f"  ✓ All provisions have 'field_label' field: {has_field_label}")

        # Count field-labeled provisions
        with_field_labels = sum(1 for p in result['aas'] if p.get('field_label') is not None)
        print(f"  Field-labeled provisions: {with_field_labels}/{len(result['aas'])}")

    else:
        print("⚠ WARNING: 0 provisions extracted!")

    print()
    print("="*80)
    print(f"Output saved to: {output_path}")
    print("="*80)
    print()
    print("Next: Review output and approve before full extraction")


if __name__ == "__main__":
    main()
