#!/usr/bin/env python3
"""
Extract Ascensus BPD using v5 prompt with hierarchy support

Uses the production v5 extraction pipeline with parent_section support,
automatic sorting, and retry logic.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Extract Ascensus BPD with v5 prompt"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("V5 BPD EXTRACTION - ASCENSUS")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Prompt: provision_extraction_v5.txt")
    print("  - Model: gpt-5-nano (with mini fallback)")
    print("  - Workers: 16 (parallel)")
    print("  - Batch size: 1 page/request")
    print("  - Retry logic: 3 attempts (repair + mini fallback)")
    print("  - Validation: JSON schema + page numbers + parent_section")
    print("  - Sorting: Automatic by page + section number")
    print()

    extract_document_parallel(
        pdf_path=Path("test_data/raw/ascensus/ascensus_bpd.pdf"),
        doc_type="BPD",
        output_path=Path("test_data/extracted_vision_v5/ascensus_bpd_provisions.json"),
        batch_size=1,
        max_workers=16
    )

    print()
    print("="*80)
    print("V5 EXTRACTION COMPLETE")
    print("="*80)
    print("Check output: test_data/extracted_vision_v5/ascensus_bpd_provisions.json")
    print()
    print("Success criteria:")
    print("  - 98%+ success rate (failed_pages_count < 2%)")
    print("  - 100% of provisions have pdf_page field")
    print("  - 100% of provisions have parent_section field")
    print("  - All provision_type values valid (definition|operational|regulatory|unknown)")
    print("  - Provisions sorted by page + section number")
    print("="*80)


if __name__ == "__main__":
    main()
