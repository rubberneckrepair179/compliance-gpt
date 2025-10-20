#!/usr/bin/env python3
"""
Verify whether source AA has actual elections or is a blank template
"""

import pymupdf
from pathlib import Path

def check_for_elections(pdf_path: Path, sample_pages=5):
    """Check if AA has filled elections or is blank template"""

    doc = pymupdf.open(pdf_path)

    print(f"Analyzing: {pdf_path.name}")
    print(f"Total pages: {len(doc)}\n")

    # Check first few pages for evidence of elections
    for page_num in range(min(sample_pages, len(doc))):
        page = doc[page_num]
        text = page.get_text()

        print(f"--- Page {page_num + 1} ---")

        # Look for common patterns
        unchecked_boxes = text.count("[   ]") + text.count("[ ]")
        checked_boxes = text.count("[X]") + text.count("[x]")
        blank_lines = text.count("___")

        # Show a sample of the text
        print(f"Unchecked boxes: {unchecked_boxes}")
        print(f"Checked boxes: {checked_boxes}")
        print(f"Blank fill-in lines: {blank_lines}")

        # Show first 500 chars to see if there's actual data
        print(f"\nFirst 500 chars:")
        print(text[:500])
        print("\n" + "="*80 + "\n")

    doc.close()

if __name__ == "__main__":
    source_aa = Path("test_data/raw/source/aa/source_aa_elections.pdf")
    target_aa = Path("test_data/raw/target/aa/target_aa_template.pdf")

    print("SOURCE AA (supposedly filled elections):")
    print("="*80)
    check_for_elections(source_aa)

    print("\n\nTARGET AA (known blank template):")
    print("="*80)
    check_for_elections(target_aa)
