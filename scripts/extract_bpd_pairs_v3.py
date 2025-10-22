#!/usr/bin/env python3
"""
Extract BPD (Basic Plan Document) pairs using parallel vision extraction with v3 prompts

Extracts both source and target BPD documents with 16 parallel workers.
Uses provision_extraction_v3.txt prompt with page_sequence (no ID generation).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Extract both BPD documents in parallel"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("BPD EXTRACTION (Parallel Vision - v3 Page Sequence Model)")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Prompt: provision_extraction_v3.txt (page_sequence, no ID generation)")
    print("  - Model: gpt-5-nano")
    print("  - Workers: 16 (parallel)")
    print("  - Batch size: 1 page/request")
    print()
    print("Purpose:")
    print("  - Extract provisions with page_sequence for deterministic IDs")
    print("  - Enable provenance tracking for BPD+AA merger")
    print("  - Support compliance-on-compliance audit trail")
    print()

    documents = [
        ("test_data/raw/source/bpd/source_bpd_01.pdf", "BPD", "test_data/extracted_vision_v3/source_bpd_raw.json"),
        ("test_data/raw/target/bpd/target_bpd_05.pdf", "BPD", "test_data/extracted_vision_v3/target_bpd_raw.json"),
    ]

    total_start = time.time()

    for pdf_path, doc_type, output_path in documents:
        extract_document_parallel(
            pdf_path=Path(pdf_path),
            doc_type=doc_type,
            output_path=Path(output_path),
            batch_size=1,  # 1 page per request (prevents JSON parse failures)
            max_workers=16  # 16 parallel workers
        )

    total_elapsed = time.time() - total_start

    print()
    print("="*80)
    print("BPD EXTRACTION COMPLETE")
    print("="*80)
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print()
    print("Output files (raw v3 extraction - NO IDs yet):")
    print("  - test_data/extracted_vision_v3/source_bpd_raw.json")
    print("  - test_data/extracted_vision_v3/target_bpd_raw.json")
    print()
    print("Next steps:")
    print("  1. Run ID assignment post-processing:")
    print("     python scripts/assign_unique_ids.py \\")
    print("       test_data/extracted_vision_v3/source_bpd_raw.json \\")
    print("       test_data/extracted_vision/source_bpd_01_provisions.json")
    print("  2. Validate 100% unique IDs")
    print("  3. Verify no regressions in provision detection")
    print("  4. Resume BPD+AA merger workflow")
    print("="*80)


if __name__ == "__main__":
    main()
