"""
Assign globally unique IDs to extracted documents (AAs and BPDs).

Post-processes v3 extraction output to generate IDs deterministically:

For AAs (Adoption Agreements):
- Election IDs: election_p{page:03d}_seq{seq:02d}
- Option IDs: {election_id}_opt_{label}
- Fill-in IDs: {option_id}_fill{seq:02d}

For BPDs (Basic Plan Documents):
- Provision IDs: provision_p{page:03d}_seq{seq:02d}

Usage:
    python scripts/assign_unique_ids.py input.json output.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List


def assign_election_id(page: int, sequence: int) -> str:
    """Generate globally unique election ID from page + sequence"""
    return f"election_p{page:03d}_seq{sequence:02d}"


def assign_option_ids(election_id: str, options: List[Dict[str, Any]]) -> None:
    """
    Assign option IDs in-place.

    Modifies options list to add option_id fields.
    """
    for option in options:
        label = option["label"]
        option["option_id"] = f"{election_id}_opt_{label}"

        # Also assign fill-in IDs if present
        if option.get("fill_ins"):
            assign_fillin_ids(option["option_id"], option["fill_ins"])


def assign_fillin_ids(parent_id: str, fill_ins: List[Dict[str, Any]]) -> None:
    """
    Assign fill-in IDs in-place.

    Modifies fill_ins list to add id fields.
    """
    for fill_in in fill_ins:
        seq = fill_in["fill_in_sequence"]
        fill_in["id"] = f"{parent_id}_fill{seq:02d}"


def convert_value_structure(election: Dict[str, Any]) -> None:
    """
    Convert value structure from labels to IDs.

    v3 extraction uses selected_label/selected_labels.
    Convert to option_id/option_ids for backward compatibility.
    """
    kind = election["kind"]

    if kind == "text":
        # Text elections have value: null or value: "some text" - no conversion needed
        return

    if kind == "single_select":
        if not election["value"]:
            # Value is null - initialize it
            election["value"] = {"option_id": None}
            return

        selected_label = election["value"].get("selected_label")
        if selected_label:
            # Find the option with this label
            for option in election["options"]:
                if option["label"] == selected_label:
                    election["value"]["option_id"] = option["option_id"]
                    break
            else:
                # Label not found in options (shouldn't happen)
                election["value"]["option_id"] = None
        else:
            election["value"]["option_id"] = None

        # Remove selected_label field
        if "selected_label" in election["value"]:
            del election["value"]["selected_label"]

    elif kind == "multi_select":
        if not election["value"]:
            # Value is null - initialize it
            election["value"] = {"option_ids": []}
            return

        selected_labels = election["value"].get("selected_labels", [])
        option_ids = []

        # Find options with these labels
        for label in selected_labels:
            for option in election["options"]:
                if option["label"] == label:
                    option_ids.append(option["option_id"])
                    break

        election["value"]["option_ids"] = option_ids

        # Remove selected_labels field
        if "selected_labels" in election["value"]:
            del election["value"]["selected_labels"]


def assign_provision_id(provision: Dict[str, Any], page: int) -> str:
    """Generate globally unique provision ID from page + sequence"""
    seq = provision["page_sequence"]
    return f"provision_p{page:03d}_seq{seq:02d}"


def process_bpd_document(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process BPD document to assign provision IDs"""
    stats = {
        "total_provisions": len(data.get("bpds", [])),
        "duplicate_check": set()
    }

    # BPDs don't have provenance.page in v3, need to infer from position
    # Group by page_sequence resets to detect page boundaries
    current_page = 1
    last_sequence = 0

    for provision in data.get("bpds", []):
        seq = provision["page_sequence"]

        # If sequence resets or decreases, we've moved to a new page
        if seq <= last_sequence:
            current_page += 1
        last_sequence = seq

        # Assign provision ID
        provision_id = assign_provision_id(provision, current_page)

        # Check for duplicates
        if provision_id in stats["duplicate_check"]:
            print(f"WARNING: Duplicate provision ID: {provision_id}")
        stats["duplicate_check"].add(provision_id)

        provision["id"] = provision_id
        provision["provenance"] = {"page": current_page, "sequence": seq}

    stats["unique_provision_ids"] = len(stats["duplicate_check"])
    del stats["duplicate_check"]

    return stats


def process_aa_document(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process AA document to assign election IDs"""
    stats = {
        "total_elections": len(data.get("aas", [])),
        "elections_with_options": 0,
        "total_options": 0,
        "total_fillins": 0,
        "duplicate_check": set()
    }

    # Group elections by page and assign sequential IDs within each page
    from collections import defaultdict
    elections_by_page = defaultdict(list)

    for election in data.get("aas", []):
        page = election["provenance"]["page"]
        elections_by_page[page].append(election)

    # Process each page's elections
    for page in sorted(elections_by_page.keys()):
        for seq, election in enumerate(elections_by_page[page], start=1):
            # Assign election ID based on page and position
            election_id = assign_election_id(page, seq)

            # Check for duplicates
            if election_id in stats["duplicate_check"]:
                print(f"WARNING: Duplicate election ID: {election_id}")
            stats["duplicate_check"].add(election_id)

            election["id"] = election_id

        # Assign option IDs if applicable
        if election["kind"] in ["single_select", "multi_select"]:
            options = election.get("options", [])
            if options:
                assign_option_ids(election_id, options)
                stats["elections_with_options"] += 1
                stats["total_options"] += len(options)

                # Count fill-ins
                for option in options:
                    stats["total_fillins"] += len(option.get("fill_ins", []))

            # Convert value structure (labels → IDs)
            convert_value_structure(election)

    stats["unique_election_ids"] = len(stats["duplicate_check"])
    del stats["duplicate_check"]

    return stats


def assign_unique_ids(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Assign globally unique IDs to v3 extraction output.

    Returns statistics about ID assignment.
    """
    # Load v3 extraction output
    with open(input_path, 'r') as f:
        data = json.load(f)

    # Detect document type
    is_bpd = "bpds" in data
    is_aa = "aas" in data

    if is_bpd:
        print(f"Detected BPD document")
        stats = process_bpd_document(data)
        data["model"] = data.get("model", "unknown") + " + id_assignment_v1"
        data["total_provisions"] = stats["total_provisions"]
    elif is_aa:
        print(f"Detected AA document")
        stats = process_aa_document(data)
        data["model"] = data.get("model", "unknown") + " + id_assignment_v1"
        data["total_elections"] = stats["total_elections"]
    else:
        raise ValueError("Unknown document type - expected 'aas' or 'bpds' key in JSON")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    stats["unique_election_ids"] = len(stats["duplicate_check"])
    del stats["duplicate_check"]

    return stats


def main():
    """Main entry point"""
    if len(sys.argv) != 3:
        print("Usage: python scripts/assign_unique_ids.py input.json output.json")
        print()
        print("Example:")
        print("  python scripts/assign_unique_ids.py \\")
        print("    test_data/extracted_vision_v3/source_aa_raw.json \\")
        print("    test_data/extracted_vision/source_aa_elections.json")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    print(f"Assigning unique IDs...")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print()

    stats = assign_unique_ids(input_path, output_path)

    print("✅ ID assignment complete")
    print()
    print("Statistics:")
    if "total_elections" in stats:
        # AA document
        print(f"  Elections processed: {stats['total_elections']}")
        print(f"  Unique election IDs: {stats['unique_election_ids']}")
        print(f"  Elections with options: {stats['elections_with_options']}")
        print(f"  Total options: {stats['total_options']}")
        print(f"  Total fill-ins: {stats['total_fillins']}")
    else:
        # BPD document
        print(f"  Provisions processed: {stats['total_provisions']}")
        print(f"  Unique provision IDs: {stats['unique_provision_ids']}")


if __name__ == "__main__":
    main()
