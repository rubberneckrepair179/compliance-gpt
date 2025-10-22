#!/usr/bin/env python3
"""
Create Validation Test Set

Extracts representative mappings from AA crosswalk for manual validation.
Includes diverse examples across confidence levels and match types.
"""

import json
import csv
from pathlib import Path
from rich.console import Console

console = Console()


def load_elections(path: Path) -> dict:
    """Load elections and build lookup dict."""
    with open(path, 'r') as f:
        data = json.load(f)
    return {e['id']: e for e in data['aas']}


def format_options(options: list) -> str:
    """Format election options for display."""
    if not options:
        return "(text field)"
    return "\n".join([f"{opt['label']}. {opt['option_text']}" for opt in options])


def create_validation_set():
    """Create validation test set with diverse examples."""

    # Load crosswalk
    crosswalk_path = Path("test_data/crosswalks/aa_crosswalk.json")
    with open(crosswalk_path, 'r') as f:
        crosswalk = json.load(f)

    # Load source and target elections
    source_elections = load_elections(Path("test_data/extracted/relius_aa_elections.json"))
    target_elections = load_elections(Path("test_data/extracted/ascensus_aa_elections.json"))

    # Categorize mappings
    matches = [m for m in crosswalk['mappings'] if m['is_match']]
    non_matches_high_conf = [m for m in crosswalk['mappings']
                              if not m['is_match'] and m['confidence_score'] >= 0.9]
    non_matches_medium_conf = [m for m in crosswalk['mappings']
                                if not m['is_match'] and 0.7 <= m['confidence_score'] < 0.9]
    non_matches_low_conf = [m for m in crosswalk['mappings']
                             if not m['is_match'] and m['confidence_score'] < 0.7]

    console.print(f"[cyan]Categorizing mappings:[/cyan]")
    console.print(f"  Matches: {len(matches)}")
    console.print(f"  Non-matches (high conf): {len(non_matches_high_conf)}")
    console.print(f"  Non-matches (medium conf): {len(non_matches_medium_conf)}")
    console.print(f"  Non-matches (low conf): {len(non_matches_low_conf)}")

    # Sample strategy: Get diverse examples
    # - All 22 matches (since there are so few)
    # - 5 high-conf non-matches (interesting edge cases)
    # - 5 medium-conf non-matches
    # - 5 low-conf non-matches

    sample = []

    # All matches
    sample.extend(matches)

    # Sample non-matches
    import random
    random.seed(42)  # Reproducible sampling
    sample.extend(random.sample(non_matches_high_conf, min(5, len(non_matches_high_conf))))
    sample.extend(random.sample(non_matches_medium_conf, min(5, len(non_matches_medium_conf))))
    sample.extend(random.sample(non_matches_low_conf, min(5, len(non_matches_low_conf))))

    console.print(f"\n[green]Selected {len(sample)} examples for validation[/green]\n")

    # Create detailed CSV
    rows = []
    for idx, mapping in enumerate(sample, 1):
        source = source_elections.get(mapping['source_id'], {})
        target = target_elections.get(mapping['target_id'], {})

        row = {
            'ID': idx,
            'Source Q#': mapping['source_question_number'],
            'Source Page': source.get('provenance', {}).get('page', ''),
            'Source Section': source.get('section_context', ''),
            'Source Question': source.get('question_text', ''),
            'Source Kind': source.get('kind', ''),
            'Source Options': format_options(source.get('options', [])),

            'Target Q#': mapping['target_question_number'],
            'Target Page': target.get('provenance', {}).get('page', ''),
            'Target Section': target.get('section_context', ''),
            'Target Question': target.get('question_text', ''),
            'Target Kind': target.get('kind', ''),
            'Target Options': format_options(target.get('options', [])),

            'Embedding Similarity': f"{mapping['embedding_similarity']:.0%}",
            'AI Says Match?': 'YES' if mapping['is_match'] else 'NO',
            'AI Confidence': f"{mapping['confidence_score']:.0%}",
            'AI Reasoning': mapping['reasoning'],

            # Validation columns (empty for Lauren to fill)
            'Human Says Match?': '',
            'Correct Tier': '',
            'Options Added': '',
            'Options Removed': '',
            'Options Reworded': '',
            'Logic Changed': '',
            'Recommended Action': '',
            'Notes': '',
        }
        rows.append(row)

    # Write to CSV
    output_path = Path("test_data/validation_test_set.csv")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    console.print(f"[green]✓ Created validation test set: {output_path}[/green]")
    console.print(f"[dim]  {len(sample)} examples ready for manual review[/dim]")

    # Also create a summary
    summary_path = Path("test_data/validation_test_set_summary.md")
    with open(summary_path, 'w') as f:
        f.write("# AA Crosswalk Validation Test Set\n\n")
        f.write(f"**Created:** {crosswalk['completed_at'] if 'completed_at' in crosswalk else 'N/A'}\n")
        f.write(f"**Source:** Relius Cycle 3 Adoption Agreement (182 elections)\n")
        f.write(f"**Target:** Ascensus 401(k) Profit Sharing Plan Adoption Agreement (550 elections)\n\n")

        f.write("## Sample Composition\n\n")
        f.write(f"- **Matches:** {len([m for m in sample if m['is_match']])} examples\n")
        f.write(f"- **Non-matches (high conf ≥90%):** {len([m for m in sample if not m['is_match'] and m['confidence_score'] >= 0.9])} examples\n")
        f.write(f"- **Non-matches (medium conf 70-89%):** {len([m for m in sample if not m['is_match'] and 0.7 <= m['confidence_score'] < 0.9])} examples\n")
        f.write(f"- **Non-matches (low conf <70%):** {len([m for m in sample if not m['is_match'] and m['confidence_score'] < 0.7])} examples\n\n")

        f.write("## Validation Instructions\n\n")
        f.write("For each example in `validation_test_set.csv`, please fill in:\n\n")
        f.write("1. **Human Says Match?** - Your expert judgment: YES/NO/PARTIAL\n")
        f.write("2. **Correct Tier** - What tier would you assign?\n")
        f.write("   - EXACT: Same election, minor wording only\n")
        f.write("   - PARTIAL: Same election, options changed (actionable deltas)\n")
        f.write("   - POSSIBLE: Related but uncertain\n")
        f.write("   - NONE: Different elections entirely\n\n")
        f.write("3. **Deltas** (for PARTIAL matches):\n")
        f.write("   - Options Added: List new options in target\n")
        f.write("   - Options Removed: List removed options from source\n")
        f.write("   - Options Reworded: Note wording changes\n")
        f.write("   - Logic Changed: Note default changes, dependencies, etc.\n\n")
        f.write("4. **Recommended Action** - What should compliance officer do?\n")
        f.write("5. **Notes** - Any other observations\n\n")

        f.write("## Goals\n\n")
        f.write("- Validate AI match quality (do our 22 matches agree with your judgment?)\n")
        f.write("- Calibrate confidence thresholds (are 90%+ scores actually reliable?)\n")
        f.write("- Identify useful 'near misses' (non-matches with actionable deltas)\n")
        f.write("- Define what deltas matter in practice\n")
        f.write("- Design better output format for compliance workflow\n")

    console.print(f"[green]✓ Created instructions: {summary_path}[/green]")


if __name__ == "__main__":
    create_validation_set()
