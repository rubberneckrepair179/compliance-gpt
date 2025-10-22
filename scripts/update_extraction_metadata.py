#!/usr/bin/env python3
"""
Update Extraction Metadata

Updates document paths in extraction JSON files to reflect correct vendor naming.
"""

import json
from pathlib import Path

def update_file(file_path: Path, old_path: str, new_path: str):
    """Update document path in JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)

    if 'document' in data:
        data['document'] = data['document'].replace(old_path, new_path)
        print(f"Updated {file_path.name}: {old_path} → {new_path}")

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    base = Path("test_data/extracted_vision")

    # Update extracted_vision files (now with correct source/target)
    # Relius (source) was extracted from what we called "target" PDFs (smaller files)
    # Ascensus (target) was extracted from what we called "source" PDFs (larger files)
    updates = [
        (base / "relius_bpd_provisions.json", "target/bpd/target_bpd_05.pdf", "source/bpd/relius_bpd_cycle3.pdf"),
        (base / "relius_aa_elections.json", "target/aa/target_aa.pdf", "source/aa/relius_aa_cycle3.pdf"),
        (base / "ascensus_bpd_provisions.json", "source/bpd/source_bpd_01.pdf", "target/bpd/ascensus_bpd.pdf"),
        (base / "ascensus_aa_elections.json", "source/aa/source_aa.pdf", "target/aa/ascensus_aa_profit_sharing.pdf"),
    ]

    for file_path, old_path, new_path in updates:
        if file_path.exists():
            update_file(file_path, old_path, new_path)

    # Update extracted_vision_v3 files
    base_v3 = Path("test_data/extracted_vision_v3")
    updates_v3 = [
        (base_v3 / "relius_bpd_raw.json", "target/bpd/target_bpd_05.pdf", "source/bpd/relius_bpd_cycle3.pdf"),
        (base_v3 / "relius_aa_raw.json", "target/aa/target_aa.pdf", "source/aa/relius_aa_cycle3.pdf"),
        (base_v3 / "ascensus_bpd_raw.json", "source/bpd/source_bpd_01.pdf", "target/bpd/ascensus_bpd.pdf"),
        (base_v3 / "ascensus_aa_raw.json", "source/aa/source_aa.pdf", "target/aa/ascensus_aa_profit_sharing.pdf"),
    ]

    for file_path, old_path, new_path in updates_v3:
        if file_path.exists():
            update_file(file_path, old_path, new_path)

    print("\n✓ All metadata updated")

if __name__ == "__main__":
    main()
