#!/usr/bin/env python3
"""
Extract single BPD document using v5 prompt with full retry/repair logic

Tests the complete production extraction pipeline on one document.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Extract Relius BPD with v5 prompt"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("V5 BPD EXTRACTION - SINGLE DOCUMENT TEST")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Prompt: provision_extraction_v5.txt")
    print("  - Model: gpt-5-nano (with mini fallback)")
    print("  - Workers: 16 (parallel)")
    print("  - Batch size: 1 page/request")
    print("  - Retry logic: 3 attempts (repair + mini fallback)")
    print("  - Validation: JSON schema + page numbers")
    print()

    extract_document_parallel(
        pdf_path=Path("test_data/raw/relius/relius_bpd_cycle3.pdf"),
        doc_type="BPD",
        output_path=Path("test_data/extracted_vision_v5/relius_bpd_provisions.json"),
        batch_size=1,
        max_workers=16
    )

    print()
    print("="*80)
    print("V5 EXTRACTION COMPLETE")
    print("="*80)
    print("Check output: test_data/extracted_vision_v5/relius_bpd_provisions.json")
    print()
    print("Success criteria:")
    print("  - 98%+ success rate (failed_pages_count < 2%)")
    print("  - 100% of provisions have pdf_page field")
    print("  - All provision_type values valid (definition|operational|regulatory|unknown)")
    print("="*80)


if __name__ == "__main__":
    main()
