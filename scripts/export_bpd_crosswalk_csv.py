#!/usr/bin/env python3
"""
Export BPD Crosswalk to CSV

Converts BPD crosswalk JSON to human-readable CSV format.
"""

import json
import csv
from pathlib import Path
from rich.console import Console

console = Console()


def load_provisions(path: Path) -> dict:
    """Load provisions from JSON file and build lookup dict."""
    with open(path, 'r') as f:
        data = json.load(f)
    return {p['id']: p for p in data['bpds']}


def export_to_csv(crosswalk_path: Path, output_path: Path):
    """Export crosswalk to CSV."""
    # Load crosswalk
    with open(crosswalk_path, 'r') as f:
        crosswalk = json.load(f)

    # Load source and target provisions for full details
    source_provisions = load_provisions(Path("test_data/extracted/relius_bpd_provisions.json"))
    target_provisions = load_provisions(Path("test_data/extracted/ascensus_bpd_provisions.json"))

    # Prepare CSV rows
    rows = []
    for mapping in crosswalk['mappings']:
        # Note: We need to find provisions by UUID, but extracted data has simple IDs
        # For now, just use the mapping data we have
        row = {
            'Match Status': 'MATCH' if mapping['is_match'] else 'NO MATCH',
            'Confidence': f"{mapping['confidence_score']:.0%}",
            'Source Provision ID': mapping['source_provision_id'],
            'Target Provision ID': mapping['target_provision_id'],
            'Embedding Similarity': f"{mapping['embedding_similarity']:.0%}",
            'LLM Similarity': f"{mapping['llm_similarity']:.0%}",
            'Variance Type': mapping.get('variance_type', 'none').upper(),
            'Impact Level': mapping.get('impact_level', 'none').upper(),
            'Reasoning': mapping['reasoning'][:200],
        }
        rows.append(row)

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    console.print(f"[green]✓ Exported {len(rows)} mappings to {output_path}[/green]")


def main():
    console.print("\n[cyan bold]BPD Crosswalk CSV Export[/cyan bold]\n")

    crosswalk_path = Path("test_data/crosswalks/bpd_crosswalk.json")
    output_path = Path("test_data/crosswalks/bpd_crosswalk.csv")

    export_to_csv(crosswalk_path, output_path)

    console.print("\n[green bold]✓ CSV Export Complete[/green bold]\n")


if __name__ == "__main__":
    main()
