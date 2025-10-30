#!/usr/bin/env python3
"""
Extract Relius AA using v5 prompt with provisions + form_elements model

Uses GPT-5-mini exclusively for AA (complex forms with checkboxes/text fields).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Extract Relius AA with v5 prompt"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("V5 AA EXTRACTION - RELIUS")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Prompt: aa_extraction_v5.txt")
    print("  - Model: gpt-5-mini (complex forms require mini)")
    print("  - Workers: 16 (parallel)")
    print("  - Batch size: 1 page/request")
    print("  - Retry logic: 3 attempts (repair only, no model escalation)")
    print("  - Validation: JSON schema + page numbers + form_elements")
    print("  - Sorting: Automatic by page + section number")
    print()

    extract_document_parallel(
        pdf_path=Path("test_data/raw/relius/relius_aa_cycle3.pdf"),
        doc_type="AA",
        output_path=Path("test_data/extracted_vision_v5/relius_aa_provisions.json"),
        batch_size=1,
        max_workers=16
    )

    print()
    print("="*80)
    print("V5 AA EXTRACTION COMPLETE")
    print("="*80)
    print("Check output: test_data/extracted_vision_v5/relius_aa_provisions.json")
    print()
    print("Success criteria:")
    print("  - 98%+ success rate (per expert recommendation)")
    print("  - All provisions have pdf_page field")
    print("  - All provisions have parent_section field")
    print("  - All provisions have status field (unanswered|answered|ambiguous|conflict)")
    print("  - All provisions have form_elements array")
    print("  - Form elements validated (element_type, element_sequence, confidence)")
    print("="*80)


if __name__ == "__main__":
    main()
