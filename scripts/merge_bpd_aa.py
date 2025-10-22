"""
Merge BPD provisions with AA elections to create complete provisions.

The merged provision is the unit of compliance - it combines:
- BPD template language ("as elected in the Adoption Agreement")
- AA election values (actual employer choices)

Provenance tracks both sides for compliance-on-compliance audit trail.

Usage:
    python scripts/merge_bpd_aa.py
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import re

def load_json(path: Path) -> Dict:
    """Load JSON file"""
    with open(path) as f:
        return json.load(f)


def merge_provision_with_elections(
    provision: Dict[str, Any],
    elections_by_id: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Merge a BPD provision with relevant AA elections.

    For POC, we'll do simple text substitution where we find
    "as elected in the Adoption Agreement" patterns.

    Returns merged provision with:
    - merged_text: Complete text with elections substituted
    - referenced_elections: List of election IDs used
    - provenance: {bpd_id, election_ids[]}
    """
    provision_text = provision["provision_text"]

    # For POC: Just identify provisions that reference AA
    # Full implementation would do actual substitution
    references_aa = bool(re.search(
        r"(as elected in|in accordance with|pursuant to).*adoption agreement",
        provision_text,
        re.IGNORECASE
    ))

    merged = {
        "id": f"merged_{provision['id']}",
        "bpd_provision_id": provision["id"],
        "bpd_section_number": provision.get("section_number", ""),
        "bpd_section_title": provision.get("section_title", ""),
        "original_text": provision_text,
        "merged_text": provision_text,  # For POC, keep original
        "references_aa": references_aa,
        "referenced_elections": [],  # TODO: Actually identify which elections
        "provision_type": provision.get("provision_type", "unknown"),
        "provenance": {
            "bpd_id": provision["id"],
            "election_ids": []
        }
    }

    return merged


def merge_bpd_aa(
    bpd_path: Path,
    aa_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Merge BPD and AA to create complete provisions.

    Returns statistics about the merge.
    """
    print(f"Loading BPD provisions from {bpd_path}...")
    bpd_data = load_json(bpd_path)
    provisions = bpd_data["bpds"]

    print(f"Loading AA elections from {aa_path}...")
    aa_data = load_json(aa_path)
    elections = aa_data["aas"]

    # Index elections by ID for quick lookup
    elections_by_id = {e["id"]: e for e in elections}

    print(f"Merging {len(provisions)} BPD provisions with {len(elections)} AA elections...")

    # Merge each provision
    merged_provisions = []
    stats = {
        "total_provisions": len(provisions),
        "references_aa": 0,
        "standalone": 0
    }

    for provision in provisions:
        merged = merge_provision_with_elections(provision, elections_by_id)
        merged_provisions.append(merged)

        if merged["references_aa"]:
            stats["references_aa"] += 1
        else:
            stats["standalone"] += 1

    # Create output
    output_data = {
        "source_bpd": str(bpd_path),
        "source_aa": str(aa_path),
        "total_provisions": stats["total_provisions"],
        "provisions_referencing_aa": stats["references_aa"],
        "standalone_provisions": stats["standalone"],
        "merged_provisions": merged_provisions
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    return stats


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent

    bpd_path = project_root / "test_data/extracted_vision/source_bpd_01_provisions.json"
    aa_path = project_root / "test_data/synthetic/source_aa_filled.json"
    output_path = project_root / "test_data/merged/source_merged_provisions.json"

    print("="*80)
    print("BPD+AA MERGER")
    print("="*80)
    print()
    print("Creating complete provisions by merging BPD templates with AA elections")
    print("The merged provision is the unit of compliance.")
    print()

    stats = merge_bpd_aa(bpd_path, aa_path, output_path)

    print()
    print("="*80)
    print("MERGE COMPLETE")
    print("="*80)
    print()
    print("Statistics:")
    print(f"  Total provisions: {stats['total_provisions']}")
    print(f"  Reference AA elections: {stats['references_aa']} ({stats['references_aa']/stats['total_provisions']*100:.1f}%)")
    print(f"  Standalone (no AA ref): {stats['standalone']} ({stats['standalone']/stats['total_provisions']*100:.1f}%)")
    print()
    print(f"Output: {output_path}")
    print()
    print("Next steps:")
    print("  1. Inspect merged provisions")
    print("  2. Implement actual election substitution (currently placeholder)")
    print("  3. Generate target merged provisions")
    print("  4. Run merged crosswalk (source ↔ target)")
    print("="*80)


if __name__ == "__main__":
    main()
