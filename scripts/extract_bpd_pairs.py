#!/usr/bin/env python3
"""
Extract BPD (Basic Plan Document) pairs using parallel vision extraction

Extracts both source and target BPD documents with 16 parallel workers.
Uses provision_extraction_v2.txt prompt.
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
    print("BPD EXTRACTION (Parallel Vision)")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Prompt: provision_extraction_v2.txt")
    print("  - Model: gpt-5-nano")
    print("  - Workers: 16 (parallel)")
    print("  - Batch size: 1 page/request")
    print()

    documents = [
        ("test_data/raw/source/bpd/source_bpd_01.pdf", "BPD", "test_data/extracted_vision/source_bpd_01_provisions.json"),
        ("test_data/raw/target/bpd/target_bpd_05.pdf", "BPD", "test_data/extracted_vision/target_bpd_05_provisions.json"),
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
    print("Output files:")
    print("  - test_data/extracted_vision/source_bpd_01_provisions.json")
    print("  - test_data/extracted_vision/target_bpd_05_provisions.json")
    print()
    print("Next steps:")
    print("  - Run semantic BPD crosswalk: python scripts/build_bpd_crosswalk.py")
    print("  - Or extract AAs: python scripts/extract_aa_pairs.py")
    print("="*80)


if __name__ == "__main__":
    main()
