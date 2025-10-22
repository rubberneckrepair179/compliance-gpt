#!/usr/bin/env python3
"""
Export AA Crosswalk to CSV

Converts AA crosswalk JSON to human-readable CSV format.
"""

import json
import csv
from pathlib import Path
from rich.console import Console

console = Console()


def load_elections(path: Path) -> dict:
    """Load elections from JSON file and build lookup dict."""
    with open(path, 'r') as f:
        data = json.load(f)
    return {e['id']: e for e in data['aas']}


def export_to_csv(crosswalk_path: Path, output_path: Path):
    """Export crosswalk to CSV."""
    # Load crosswalk
    with open(crosswalk_path, 'r') as f:
        crosswalk = json.load(f)

    # Load source and target elections for full details
    source_elections = load_elections(Path("test_data/extracted_vision/source_aa_elections.json"))
    target_elections = load_elections(Path("test_data/extracted_vision/target_aa_elections.json"))

    # Prepare CSV rows
    rows = []
    for mapping in crosswalk['mappings']:
        source = source_elections.get(mapping['source_id'], {})
        target = target_elections.get(mapping['target_id'], {})

        row = {
            'Match Status': 'MATCH' if mapping['is_match'] else 'NO MATCH',
            'Confidence': f"{mapping['confidence_score']:.0%}",
            'Source Question #': mapping['source_question_number'],
            'Source Question': source.get('question_text', '')[:100],
            'Target Question #': mapping['target_question_number'],
            'Target Question': target.get('question_text', '')[:100],
            'Embedding Similarity': f"{mapping['embedding_similarity']:.0%}",
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
    console.print("\n[cyan bold]AA Crosswalk CSV Export[/cyan bold]\n")

    crosswalk_path = Path("test_data/crosswalks/aa_crosswalk.json")
    output_path = Path("test_data/crosswalks/aa_crosswalk.csv")

    export_to_csv(crosswalk_path, output_path)

    console.print("\n[green bold]✓ CSV Export Complete[/green bold]\n")


if __name__ == "__main__":
    main()
