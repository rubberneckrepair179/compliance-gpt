"""
Test Semantic Mapping on Operational Provisions

Compares operational provisions extracted with v2 prompt.
"""

import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.provision import Provision
from src.mapping.semantic_mapper import SemanticMapper
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def load_provisions(filepath: Path) -> list[Provision]:
    """Load provisions from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Provision(**prov) for prov in data]


def main() -> None:
    """Test semantic mapping on operational provisions."""
    console.print("\n[cyan bold]Testing Semantic Mapping on Operational Provisions[/cyan bold]")
    console.print("[dim]Using hybrid embeddings + LLM verification approach[/dim]\n")

    # Load operational provisions
    source_path = Path("test_data/processed/pair_a_source_bpd_operational_provisions.json")
    target_path = Path("test_data/processed/pair_a_target_bpd_operational_provisions.json")

    console.print(f"[cyan]Loading provisions...[/cyan]")
    source_provisions = load_provisions(source_path)
    target_provisions = load_provisions(target_path)

    console.print(f"  Source: {len(source_provisions)} operational provisions")
    console.print(f"  Target: {len(target_provisions)} operational provisions\n")

    # Initialize semantic mapper
    mapper = SemanticMapper(
        top_k=3,  # Check top 3 candidates per source provision
    )

    # Compare documents
    console.print("[cyan]Running semantic comparison...[/cyan]")
    console.print("[dim]Step 1: Generating embeddings...[/dim]")
    console.print("[dim]Step 2: Computing similarity matrix...[/dim]")
    console.print("[dim]Step 3: LLM verification of top candidates...[/dim]\n")

    comparison = mapper.compare_documents(
        source_provisions=source_provisions,
        target_provisions=target_provisions,
        source_doc_id="pair_a_source_bpd",
        target_doc_id="pair_a_target_bpd",
    )

    # Display results
    console.print(f"\n{'='*70}\n")
    console.print("[cyan bold]Semantic Mapping Results[/cyan bold]\n")

    # Summary statistics
    total_mappings = len(comparison.mappings)
    matched = sum(1 for m in comparison.mappings if m.is_match)
    high_conf = sum(1 for m in comparison.mappings if m.confidence_score >= 0.9)
    med_conf = sum(1 for m in comparison.mappings if 0.7 <= m.confidence_score < 0.9)
    low_conf = sum(1 for m in comparison.mappings if m.confidence_score < 0.7)

    console.print(f"[green]Total Source Provisions:[/green] {len(source_provisions)}")
    console.print(f"[green]Total Target Provisions:[/green] {len(target_provisions)}")
    console.print(f"[green]Mappings Created:[/green] {total_mappings}")
    console.print(f"[green]Matched:[/green] {matched} ({matched/total_mappings*100:.0f}%)")
    console.print(f"[green]High Confidence (≥90%):[/green] {high_conf}")
    console.print(f"[green]Medium Confidence (70-89%):[/green] {med_conf}")
    console.print(f"[green]Low Confidence (<70%):[/green] {low_conf}\n")

    # Detailed mapping table
    table = Table(title="Provision Mappings", show_header=True, header_style="bold cyan")
    table.add_column("Source", style="dim", width=20)
    table.add_column("Target", style="dim", width=20)
    table.add_column("Embed", justify="center", width=7)
    table.add_column("LLM", justify="center", width=7)
    table.add_column("Match", justify="center", width=7)
    table.add_column("Variance", width=12)
    table.add_column("Impact", width=8)
    table.add_column("Conf", justify="center", width=6)

    for mapping in comparison.mappings:
        # Find source and target provisions
        source_prov = next(p for p in source_provisions if p.provision_id == mapping.source_provision_id)
        target_prov = next(p for p in target_provisions if p.provision_id == mapping.target_provision_id)

        # Color code based on match and confidence
        if mapping.is_match:
            match_str = "[green]✓[/green]"
        else:
            match_str = "[red]✗[/red]"

        if mapping.confidence_score >= 0.9:
            conf_str = f"[green]{mapping.confidence_score:.2f}[/green]"
        elif mapping.confidence_score >= 0.7:
            conf_str = f"[yellow]{mapping.confidence_score:.2f}[/yellow]"
        else:
            conf_str = f"[red]{mapping.confidence_score:.2f}[/red]"

        table.add_row(
            source_prov.section_reference,
            target_prov.section_reference,
            f"{mapping.embedding_similarity:.2f}",
            f"{mapping.llm_similarity:.2f}",
            match_str,
            mapping.variance_type.value,
            mapping.impact_level.value,
            conf_str,
        )

    console.print(table)
    console.print()

    # Show reasoning for each mapping
    console.print("\n[cyan bold]Mapping Details & Reasoning[/cyan bold]\n")

    for i, mapping in enumerate(comparison.mappings, 1):
        source_prov = next(p for p in source_provisions if p.provision_id == mapping.source_provision_id)
        target_prov = next(p for p in target_provisions if p.provision_id == mapping.target_provision_id)

        console.print(f"[bold]Mapping {i}:[/bold] {source_prov.section_reference} → {target_prov.section_reference}")
        console.print(f"[dim]Match:[/dim] {mapping.is_match}")
        console.print(f"[dim]Variance:[/dim] {mapping.variance_type.value} | [dim]Impact:[/dim] {mapping.impact_level.value}")
        console.print(f"[dim]Confidence:[/dim] {mapping.confidence_score:.2%}")
        console.print(f"[dim]Reasoning:[/dim] {mapping.reasoning}\n")

    # Save comparison results
    output_path = Path("test_data/processed/pair_a_operational_comparison.json")
    comparison_dict = comparison.model_dump(mode="json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comparison_dict, f, indent=2, default=str)

    console.print(Panel(
        f"[green]✓ Semantic mapping complete![/green]\n\n"
        f"Match rate: {matched}/{total_mappings} ({matched/total_mappings*100:.0f}%)\n"
        f"High confidence mappings: {high_conf}\n\n"
        f"Results saved to:\n"
        f"  • {output_path}\n\n"
        "[cyan]Analysis:[/cyan] Compare to previous 0% match rate with definitional provisions.",
        title="Success",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
