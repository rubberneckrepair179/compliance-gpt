#!/usr/bin/env python3
"""
Extract Relius AA using v5.1 prompt with Atomic Field Rule

v5.1 fixes hierarchy extraction:
- Each labeled field (Name, City, TIN) is a separate child provision
- local_ordinal for unlabeled children (1..N)
- field_label for field-like provisions
- Nested checkbox hierarchy (2.d → 2.d.1)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Extract full Relius AA with v5.1 prompt"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("V5.1 AA EXTRACTION - ASCENSUS (FULL DOCUMENT)")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Prompt: aa_extraction_v5.1.txt (Atomic Field Rule)")
    print("  - Model: gpt-5-mini (complex forms require mini)")
    print("  - Workers: 16 (parallel)")
    print("  - Batch size: 1 page/request")
    print("  - Retry logic: 3 attempts (repair only, no model escalation)")
    print("  - Validation: JSON schema + page numbers + form_elements + local_ordinal + field_label")
    print("  - Sorting: Automatic by page + section number")
    print()
    print("Expected improvements over v5:")
    print("  - Question 1: 9 child provisions (not 1 parent with 8 unlabeled elements)")
    print("  - Nested checkboxes: 2.d → 2.d.1, 2.d.2, 2.d.3 hierarchy")
    print("  - Field labels: Each text field has semantic label")
    print("  - Local ordinals: Deterministic ordering for unlabeled children")
    print()

    extract_document_parallel(
        pdf_path=Path("test_data/raw/ascensus/ascensus_aa_profit_sharing.pdf"),
        doc_type="AA",
        output_path=Path("test_data/extracted_vision_v5.1/ascensus_aa_provisions.json"),
        batch_size=1,
        max_workers=16
    )

    print()
    print("="*80)
    print("V5.1 AA EXTRACTION COMPLETE")
    print("="*80)
    print("Check output: test_data/extracted_vision_v5.1/ascensus_aa_provisions.json")
    print()
    print("Success criteria:")
    print("  - 98%+ success rate (per expert recommendation)")
    print("  - All provisions have pdf_page, local_ordinal, field_label fields")
    print("  - Question 1 has ~9 children (Name, Address, Street, City, State, Zip, Telephone, TIN, Fiscal Year)")
    print("  - Nested checkboxes have correct parent_section hierarchy")
    print("  - Combined checkbox+text options have 2 form_elements")
    print("="*80)


if __name__ == "__main__":
    main()
