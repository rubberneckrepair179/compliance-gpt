#!/usr/bin/env python3
"""
Test AA PDF Extraction
Check if AAs are locked/encrypted and test extraction methods
"""

import pymupdf
from pathlib import Path

def test_pdf_extraction(pdf_path: Path):
    """Test if PDF can be extracted and check for encryption"""

    print(f"\n{'='*80}")
    print(f"Testing: {pdf_path.name}")
    print('='*80)

    try:
        doc = pymupdf.open(pdf_path)

        # Check encryption
        is_encrypted = doc.is_encrypted
        print(f"Encrypted: {is_encrypted}")
        print(f"Pages: {len(doc)}")

        # Try to extract text from first page
        if len(doc) > 0:
            page = doc[0]
            text = page.get_text()

            if text.strip():
                print(f"✅ Text extraction SUCCESSFUL")
                print(f"   First 200 chars: {text[:200]}")

                # Count checkboxes and fill-in fields
                checkbox_count = text.count("[   ]") + text.count("[ ]") + text.count("[X]") + text.count("[x]")
                blank_line_count = text.count("___")

                print(f"   Checkboxes found: {checkbox_count}")
                print(f"   Blank fill-in lines: {blank_line_count}")
            else:
                print(f"❌ Text extraction FAILED - empty text (likely locked/encrypted)")
                print(f"   Will need VISION fallback")

        doc.close()
        return not is_encrypted and text.strip()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Test both AA documents"""

    source_aa = Path("test_data/raw/source/aa/source_aa.pdf")
    target_aa = Path("test_data/raw/target/aa/target_aa.pdf")

    print("\n" + "="*80)
    print("AA PDF EXTRACTION TEST")
    print("="*80)

    source_ok = test_pdf_extraction(source_aa)
    target_ok = test_pdf_extraction(target_aa)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if source_ok and target_ok:
        print("✅ Both AAs can be extracted with standard text API")
        print("   No vision fallback needed")
    elif source_ok or target_ok:
        print("⚠️  One AA is locked, vision fallback needed for:")
        if not source_ok:
            print("   - source_aa.pdf")
        if not target_ok:
            print("   - target_aa.pdf")
    else:
        print("❌ Both AAs are locked")
        print("   Vision extraction required for both documents")

    print()

if __name__ == "__main__":
    main()
