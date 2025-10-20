#!/usr/bin/env python3
"""
Test vision extraction on a single document with live progress updates.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.vision_extractor import VisionExtractor
from config import settings

def main():
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)

    print("=" * 80)
    print("VISION EXTRACTION TEST - Single Document (GPT-5-MINI)")
    print("=" * 80)
    print(f"Model: gpt-5-mini (faster & cheaper for structured extraction)")
    print(f"Processing: test_data/raw/target/aa/target_aa.pdf (45 pages)")
    print("=" * 80)
    print()

    # Initialize extractor with GPT-5-mini vision
    extractor = VisionExtractor(model="gpt-5-mini")

    # Process single document
    pdf_path = Path("test_data/raw/target/aa/target_aa.pdf")
    output_dir = Path("test_data/extracted_vision")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting extraction...")
    print()

    # Extract elections from AA
    result = extractor.extract_aa(
        pdf_path=pdf_path,
        output_path=output_dir / "target_aa_elections.json"
    )

    print()
    print("=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Total elections extracted: {len(result.get('elections', []))}")
    print(f"Output saved to: {output_dir / 'target_aa_elections.json'}")
    print()

if __name__ == "__main__":
    main()
