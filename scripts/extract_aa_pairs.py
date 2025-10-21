#!/usr/bin/env python3
"""
Extract AA (Adoption Agreement) pairs using parallel vision extraction

Extracts both source and target AA documents with 16 parallel workers.
Uses aa_extraction_v2.txt prompt with discriminated union model.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from src.extraction.parallel_vision_extractor import extract_document_parallel

def main():
    """Extract both AA documents in parallel"""
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("AA EXTRACTION (Parallel Vision - v2 Discriminated Union Model)")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Prompt: aa_extraction_v2.txt")
    print("  - Model: gpt-5-nano")
    print("  - Workers: 16 (parallel)")
    print("  - Batch size: 1 page/request")
    print()
    print("Expected for SAMPLE documents:")
    print("  - All elections: status = 'unanswered'")
    print("  - All text fields: value = null")
    print("  - All selections: option_id = null or option_ids = []")
    print("  - Zero false positives (v2 fix validated)")
    print()

    documents = [
        ("test_data/raw/source/aa/source_aa.pdf", "AA", "test_data/extracted_vision/source_aa_elections.json"),
        ("test_data/raw/target/aa/target_aa.pdf", "AA", "test_data/extracted_vision/target_aa_elections.json"),
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
    print("AA EXTRACTION COMPLETE")
    print("="*80)
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print()
    print("Output files:")
    print("  - test_data/extracted_vision/source_aa_elections.json")
    print("  - test_data/extracted_vision/target_aa_elections.json")
    print()
    print("Validation checks:")
    print("  1. Count elections by status (expect all 'unanswered' for SAMPLE docs)")
    print("  2. Verify zero false positives (no 'answered' elections)")
    print("  3. Spot-check elections across multiple pages")
    print("  4. Verify multi_select elections extracted correctly")
    print()
    print("Next steps:")
    print("  - Analyze election counts and quality")
    print("  - Build AA semantic crosswalk (when complete AAs available)")
    print("  - Update CLAUDE.md with validation results")
    print("="*80)


if __name__ == "__main__":
    main()
