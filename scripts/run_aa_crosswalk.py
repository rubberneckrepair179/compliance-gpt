#!/usr/bin/env python3
"""
Run AA Crosswalk

Performs semantic mapping between source and target Adoption Agreement elections.
Sprint 2 scaffold - mapper implementation pending S2-T4.
"""

import json
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.election import Election
from src.mapping.aa_input_builder import build_section_hierarchy
from src.mapping.aa_semantic_mapper import AASemanticMapper
from src.models.aa_mapping import AAComparison, MatchType
from src.models.mapping import ConfidenceLevel
from rich.console import Console

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aa_crosswalk.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_elections(path: Path) -> List[Election]:
    """
    Load elections from JSON file and convert to Election objects.

    Args:
        path: Path to JSON file containing elections

    Returns:
        List of Election objects
    """
    with open(path, 'r') as f:
        data = json.load(f)

    elections = []

    # Handle different JSON structures (wrapped or direct list)
    if isinstance(data, dict) and 'elections' in data:
        elections_data = data['elections']
    elif isinstance(data, list):
        elections_data = data
    else:
        raise ValueError(f"Unexpected JSON structure in {path}")

    # Parse each election using Pydantic discriminated union
    for election_dict in elections_data:
        # Pydantic will automatically discriminate based on "kind" field
        kind = election_dict.get('kind')

        if kind == 'text':
            from src.models.election import TextElection
            election = TextElection(**election_dict)
        elif kind == 'single_select':
            from src.models.election import SingleSelectElection
            election = SingleSelectElection(**election_dict)
        elif kind == 'multi_select':
            from src.models.election import MultiSelectElection
            election = MultiSelectElection(**election_dict)
        else:
            logger.warning(f"Unknown election kind: {kind}, skipping")
            continue

        elections.append(election)

    return elections


def save_crosswalk(comparison: AAComparison, output_path: Path, run_id: str):
    """Save crosswalk results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = comparison.model_dump(mode='json')
    payload['run_id'] = run_id
    payload['completed_at'] = datetime.utcnow().isoformat()

    with open(output_path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)

    logger.info(f"Saved JSON crosswalk to {output_path}")
    console.print(f"[green]✓ Saved crosswalk to {output_path}[/green]")


def save_crosswalk_csv(comparison: AAComparison, output_path: Path, run_id: str):
    """Save crosswalk results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        writer.writerow([
            'run_id',
            'source_question',
            'target_question',
            'match_type',
            'confidence_level',
            'impact',
            'abstain',
            'source_selected',
            'target_selected',
            'compatible',
            'option_summary',
            'notes',
        ])
        for mapping in comparison.mappings:
            classification = mapping.classification
            writer.writerow([
                run_id,
                mapping.source_anchor.question_id,
                mapping.target_anchor.question_id,
                classification.match_type.value,
                classification.confidence_level.value,
                classification.impact.value,
                classification.match_type == MatchType.ABSTAIN,
                '; '.join(map(str, mapping.value_alignment.source_selected)),
                '; '.join(map(str, mapping.value_alignment.target_selected)),
                mapping.value_alignment.compatible,
                '; '.join(
                    f"{opt.relationship.value}:{opt.source.label}->{opt.target.label if opt.target else 'None'}"
                    for opt in mapping.option_mappings
                ),
                classification.confidence_rationale[:200],
            ])

    logger.info(f"Saved CSV crosswalk to {output_path}")
    console.print(f"[green]✓ Saved CSV to {output_path}[/green]")


def main():
    """Run AA crosswalk generation."""
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    console.print("\n[cyan bold]AA Crosswalk Generator (Sprint 2 Scaffold)[/cyan bold]\n")

    # Generate run ID for this comparison
    run_id = str(uuid4())
    logger.info(f"Starting AA crosswalk run: {run_id}")
    console.print(f"[dim]Run ID: {run_id}[/dim]\n")

    # Load source and target elections
    source_path = Path("test_data/extracted_vision_v6/relius_aa_elections_converted.json")
    target_path = Path("test_data/extracted_vision_v6/ascensus_aa_elections_converted.json")

    console.print(f"[dim]Loading source elections from {source_path}...[/dim]")
    try:
        source_elections = load_elections(source_path)
        console.print(f"[green]✓ Loaded {len(source_elections)} source elections (Relius)[/green]")
        logger.info(f"Loaded {len(source_elections)} source elections")
    except FileNotFoundError:
        console.print(f"[red]✗ File not found: {source_path}[/red]")
        logger.error(f"Source file not found: {source_path}")
        return
    except Exception as e:
        console.print(f"[red]✗ Error loading source: {e}[/red]")
        logger.error(f"Error loading source elections: {e}")
        return

    console.print(f"[dim]Loading target elections from {target_path}...[/dim]")
    try:
        target_elections = load_elections(target_path)
        console.print(f"[green]✓ Loaded {len(target_elections)} target elections (Ascensus)[/green]\n")
        logger.info(f"Loaded {len(target_elections)} target elections")
    except FileNotFoundError:
        console.print(f"[red]✗ File not found: {target_path}[/red]")
        logger.error(f"Target file not found: {target_path}")
        return
    except Exception as e:
        console.print(f"[red]✗ Error loading target: {e}[/red]")
        logger.error(f"Error loading target elections: {e}")
        return

    # Build section hierarchy (once for entire run)
    console.print("[dim]Building section hierarchy...[/dim]")
    all_elections = source_elections + target_elections
    section_hierarchy = build_section_hierarchy(all_elections)
    console.print(f"[green]✓ Built section hierarchy with {len(section_hierarchy)} entries[/green]\n")
    logger.info(f"Built section hierarchy with {len(section_hierarchy)} entries")

    mapper = AASemanticMapper(provider='openai', top_k=3, max_workers=16)

    start_time = datetime.now()
    console.print("[dim]Running semantic mapping...[/dim]")

    comparison = mapper.compare_documents(
        source_elections=source_elections,
        target_elections=target_elections,
        source_doc_id="Relius Adoption Agreement",
        target_doc_id="Ascensus Adoption Agreement",
    )

    elapsed_seconds = (datetime.now() - start_time).total_seconds()

    high_conf = sum(
        1
        for m in comparison.mappings
        if m.classification.confidence_level == ConfidenceLevel.HIGH
    )
    medium_conf = sum(
        1
        for m in comparison.mappings
        if m.classification.confidence_level == ConfidenceLevel.MEDIUM
    )
    low_conf = sum(
        1
        for m in comparison.mappings
        if m.classification.confidence_level == ConfidenceLevel.LOW
    )

    console.print("\n[cyan bold]Crosswalk Results[/cyan bold]")
    console.print(f"[dim]Total source elections:[/dim] {comparison.total_source_elections}")
    console.print(f"[dim]Total target elections:[/dim] {comparison.total_target_elections}")
    console.print(f"[green]Matched elections:[/green] {comparison.matched_elections}")
    console.print(f"[yellow]Unmatched source:[/yellow] {comparison.unmatched_source_elections}")
    console.print(f"[yellow]Unmatched target:[/yellow] {comparison.unmatched_target_elections}")

    total_mappings = max(len(comparison.mappings), 1)
    console.print("\n[cyan]Confidence Distribution:[/cyan]")
    console.print(f"  [green]High:[/green] {high_conf} ({high_conf/total_mappings*100:.1f}%)")
    console.print(f"  [yellow]Medium:[/yellow] {medium_conf} ({medium_conf/total_mappings*100:.1f}%)")
    console.print(f"  [red]Low:[/red] {low_conf} ({low_conf/total_mappings*100:.1f}%)")

    console.print(f"\n[dim]Processing time: {elapsed_seconds:.1f} seconds[/dim]")

    json_path = Path("test_data/crosswalks/aa_crosswalk_v1.json")
    csv_path = Path("test_data/crosswalks/aa_crosswalk_v1.csv")

    save_crosswalk(comparison, json_path, run_id)
    save_crosswalk_csv(comparison, csv_path, run_id)

    console.print("\n[green bold]✓ AA Crosswalk Complete[/green bold]\n")
    logger.info(f"Run {run_id} completed")


if __name__ == "__main__":
    main()
