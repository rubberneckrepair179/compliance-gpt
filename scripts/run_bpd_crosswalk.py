#!/usr/bin/env python3
"""
Run BPD Crosswalk

Performs semantic mapping between source and target BPD provisions.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.provision import Provision
from src.mapping.semantic_mapper import SemanticMapper
from rich.console import Console

console = Console()


def load_provisions(path: Path) -> list:
    """Load provisions from JSON file and convert to Provision objects."""
    with open(path, 'r') as f:
        data = json.load(f)

    # Convert dicts to Provision objects
    provisions = []
    for prov_dict in data['bpds']:
        # Only include provisions with actual text
        prov_text = prov_dict.get('provision_text', '') or ''
        if len(prov_text) > 10:
            # Create simple Provision-like object
            import uuid
            from src.models.provision import ProvisionType

            # Map simple types to ProvisionType enum
            prov_type_map = {
                'definition': ProvisionType.OTHER,
                'operational': ProvisionType.OTHER,
                'regulatory': ProvisionType.OTHER,
            }
            prov_type = prov_type_map.get(prov_dict.get('provision_type', 'definition'), ProvisionType.OTHER)

            prov = Provision(
                provision_id=str(uuid.uuid4()),
                document_id=str(uuid.uuid4()),
                section_reference=prov_dict.get('section_number', '') or '',
                section_title=prov_dict.get('section_title', '') or '',
                provision_text=prov_text,
                provision_type=prov_type,
                extraction_method='vision_fallback',
                confidence_score=1.0
            )
            # Store original ID for mapping back
            prov._original_id = prov_dict['id']
            provisions.append(prov)

    return provisions


def save_crosswalk(comparison, output_path: Path):
    """Save crosswalk results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict
    result = {
        'source_document_id': comparison.source_document_id,
        'target_document_id': comparison.target_document_id,
        'total_source_provisions': comparison.total_source_provisions,
        'total_target_provisions': comparison.total_target_provisions,
        'matched_provisions': comparison.matched_provisions,
        'unmatched_source_provisions': comparison.unmatched_source_provisions,
        'unmatched_target_provisions': comparison.unmatched_target_provisions,
        'high_impact_variances': comparison.high_impact_variances,
        'medium_impact_variances': comparison.medium_impact_variances,
        'low_impact_variances': comparison.low_impact_variances,
        'completed_at': comparison.completed_at.isoformat(),
        'mappings': [
            {
                'source_provision_id': str(m.source_provision_id),
                'target_provision_id': str(m.target_provision_id),
                'embedding_similarity': m.embedding_similarity,
                'llm_similarity': m.llm_similarity,
                'is_match': m.is_match,
                'variance_type': m.variance_type.value,
                'impact_level': m.impact_level.value,
                'reasoning': m.reasoning,
                'confidence_score': m.confidence_score,
            }
            for m in comparison.mappings
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    console.print(f"[green]✓ Saved crosswalk to {output_path}[/green]")


def main():
    console.print("\n[cyan bold]BPD Crosswalk Generator[/cyan bold]\n")

    # Load source and target provisions
    source_path = Path("test_data/extracted/relius_bpd_provisions.json")
    target_path = Path("test_data/extracted/ascensus_bpd_provisions.json")

    console.print(f"[dim]Loading source provisions from {source_path}...[/dim]")
    source_provisions = load_provisions(source_path)
    console.print(f"[green]✓ Loaded {len(source_provisions)} source provisions (Relius)[/green]")

    console.print(f"[dim]Loading target provisions from {target_path}...[/dim]")
    target_provisions = load_provisions(target_path)
    console.print(f"[green]✓ Loaded {len(target_provisions)} target provisions (Ascensus)[/green]\n")

    # Initialize mapper
    mapper = SemanticMapper(
        provider='openai',
        top_k=5,  # Check top 5 candidates for BPD (more complex than AA)
        max_workers=16
    )

    # Run comparison
    start_time = datetime.now()

    comparison = mapper.compare_documents(
        source_provisions=source_provisions,
        target_provisions=target_provisions,
        source_doc_id="Relius Cycle 3 Basic Plan Document",
        target_doc_id="Ascensus Basic Plan Document"
    )

    elapsed_seconds = (datetime.now() - start_time).total_seconds()
    elapsed_minutes = elapsed_seconds / 60

    # Print results
    console.print("\n[cyan bold]Crosswalk Results[/cyan bold]")
    console.print(f"[dim]Total source provisions:[/dim] {comparison.total_source_provisions}")
    console.print(f"[dim]Total target provisions:[/dim] {comparison.total_target_provisions}")
    console.print(f"[green]Matched provisions:[/green] {comparison.matched_provisions} ({comparison.matched_provisions/comparison.total_source_provisions*100:.1f}%)")
    console.print(f"[yellow]Unmatched source:[/yellow] {comparison.unmatched_source_provisions}")
    console.print(f"[yellow]Unmatched target:[/yellow] {comparison.unmatched_target_provisions}")

    # High confidence count
    high_conf_matches = sum(1 for m in comparison.mappings if m.is_match and m.confidence_score >= 0.9)
    console.print(f"\n[cyan]Confidence Distribution:[/cyan]")
    console.print(f"  [green]High (≥90%):[/green] {high_conf_matches} ({high_conf_matches/comparison.matched_provisions*100:.1f}% of matches)")

    console.print(f"\n[cyan]Impact Variances:[/cyan]")
    console.print(f"  [red]High Impact:[/red] {comparison.high_impact_variances}")
    console.print(f"  [yellow]Medium Impact:[/yellow] {comparison.medium_impact_variances}")
    console.print(f"  [dim]Low Impact:[/dim] {comparison.low_impact_variances}")

    console.print(f"\n[dim]Processing time: {elapsed_minutes:.1f} minutes ({elapsed_seconds:.0f} seconds)[/dim]")

    # Save results
    output_path = Path("test_data/crosswalks/bpd_crosswalk.json")
    save_crosswalk(comparison, output_path)

    console.print("\n[green bold]✓ BPD Crosswalk Complete[/green bold]\n")


if __name__ == "__main__":
    main()
