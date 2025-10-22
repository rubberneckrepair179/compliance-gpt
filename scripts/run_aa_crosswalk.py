#!/usr/bin/env python3
"""
Run AA Crosswalk

Performs semantic mapping between source and target AA elections.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mapping.aa_semantic_mapper import AASemanticMapper
from rich.console import Console

console = Console()


def load_elections(path: Path) -> list:
    """Load elections from JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)
    return data['aas']


def save_crosswalk(crosswalk: dict, output_path: Path):
    """Save crosswalk results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(crosswalk, f, indent=2)
    console.print(f"[green]✓ Saved crosswalk to {output_path}[/green]")


def main():
    console.print("\n[cyan bold]AA Crosswalk Generator[/cyan bold]\n")

    # Load source and target elections
    source_path = Path("test_data/extracted_vision/relius_aa_elections.json")
    target_path = Path("test_data/extracted_vision/ascensus_aa_elections.json")

    console.print(f"[dim]Loading source elections from {source_path}...[/dim]")
    source_elections = load_elections(source_path)
    console.print(f"[green]✓ Loaded {len(source_elections)} source elections (Relius)[/green]")

    console.print(f"[dim]Loading target elections from {target_path}...[/dim]")
    target_elections = load_elections(target_path)
    console.print(f"[green]✓ Loaded {len(target_elections)} target elections (Ascensus)[/green]\n")

    # Initialize mapper
    mapper = AASemanticMapper(
        provider='openai',
        top_k=3,
        max_workers=16
    )

    # Run comparison
    start_time = datetime.now()

    crosswalk = mapper.compare_aa_documents(
        source_elections=source_elections,
        target_elections=target_elections,
        source_doc_id="Relius Cycle 3 Adoption Agreement",
        target_doc_id="Ascensus 401(k) Profit Sharing Plan Adoption Agreement"
    )

    elapsed_seconds = (datetime.now() - start_time).total_seconds()
    elapsed_minutes = elapsed_seconds / 60

    # Print results
    console.print("\n[cyan bold]Crosswalk Results[/cyan bold]")
    stats = crosswalk['statistics']
    console.print(f"[dim]Total source elections:[/dim] {stats['total_source_elections']}")
    console.print(f"[dim]Total target elections:[/dim] {stats['total_target_elections']}")
    console.print(f"[green]Matched elections:[/green] {stats['matched_elections']} ({stats['matched_elections']/stats['total_source_elections']*100:.1f}%)")
    console.print(f"[yellow]Unmatched source:[/yellow] {stats['unmatched_source_elections']}")
    console.print(f"[yellow]Unmatched target:[/yellow] {stats['unmatched_target_elections']}")
    console.print(f"\n[cyan]Confidence Distribution:[/cyan]")
    console.print(f"  [green]High (≥90%):[/green] {stats['high_confidence']} ({stats['high_confidence']/stats['total_source_elections']*100:.1f}%)")
    console.print(f"  [yellow]Medium (70-89%):[/yellow] {stats['medium_confidence']} ({stats['medium_confidence']/stats['total_source_elections']*100:.1f}%)")
    console.print(f"  [red]Low (<70%):[/red] {stats['low_confidence']} ({stats['low_confidence']/stats['total_source_elections']*100:.1f}%)")
    console.print(f"\n[dim]Processing time: {elapsed_minutes:.1f} minutes ({elapsed_seconds:.0f} seconds)[/dim]")

    # Save results
    output_path = Path("test_data/crosswalks/aa_crosswalk.json")
    save_crosswalk(crosswalk, output_path)

    console.print("\n[green bold]✓ AA Crosswalk Complete[/green bold]\n")


if __name__ == "__main__":
    main()
