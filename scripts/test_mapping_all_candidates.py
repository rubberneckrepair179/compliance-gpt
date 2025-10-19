"""
Test Semantic Mapping with ALL Candidates

Tests semantic mapping by verifying ALL target provisions for each source (top_k=5).
This ensures we don't miss correct matches due to embedding filtering.
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
    """Test semantic mapping with all candidates (no filtering)."""
    console.print("\n[cyan bold]Testing Semantic Mapping - ALL Candidates (top_k=5)[/cyan bold]")
    console.print("[dim]Hypothesis: Correct matches were filtered out by top-3 embedding selection[/dim]\n")

    # Load operational provisions
    source_path = Path("test_data/processed/pair_a_source_bpd_operational_provisions.json")
    target_path = Path("test_data/processed/pair_a_target_bpd_operational_provisions.json")

    console.print(f"[cyan]Loading provisions...[/cyan]")
    source_provisions = load_provisions(source_path)
    target_provisions = load_provisions(target_path)

    console.print(f"  Source: {len(source_provisions)} operational provisions")
    console.print(f"  Target: {len(target_provisions)} operational provisions\n")

    # Initialize semantic mapper with top_k=5 (all targets)
    mapper = SemanticMapper(
        top_k=5,  # Check ALL 5 target provisions for each source
    )

    # Compare documents
    console.print("[cyan]Running semantic comparison (all candidates)...[/cyan]")
    console.print("[dim]This will verify all 25 possible pairings (5×5)[/dim]\n")

    comparison = mapper.compare_documents(
        source_provisions=source_provisions,
        target_provisions=target_provisions,
        source_doc_id="pair_a_source_bpd",
        target_doc_id="pair_a_target_bpd",
    )

    # Display results
    console.print(f"\n{'='*70}\n")
    console.print("[cyan bold]Semantic Mapping Results (All Candidates)[/cyan bold]\n")

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

    # Compare to previous run
    console.print("[yellow]Previous run (top_k=3): 0% match rate[/yellow]")
    console.print(f"[cyan]Current run (top_k=5): {matched/total_mappings*100:.0f}% match rate[/cyan]\n")

    # Detailed mapping table
    table = Table(title="Provision Mappings (Best Match per Source)", show_header=True, header_style="bold cyan")
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

    # Show matched provisions with reasoning
    if matched > 0:
        console.print("\n[cyan bold]Matched Provisions[/cyan bold]\n")

        for mapping in comparison.mappings:
            if not mapping.is_match:
                continue

            source_prov = next(p for p in source_provisions if p.provision_id == mapping.source_provision_id)
            target_prov = next(p for p in target_provisions if p.provision_id == mapping.target_provision_id)

            console.print(f"[green]✓ Match:[/green] {source_prov.section_reference} → {target_prov.section_reference}")
            console.print(f"[dim]Variance:[/dim] {mapping.variance_type.value} | [dim]Impact:[/dim] {mapping.impact_level.value}")
            console.print(f"[dim]Confidence:[/dim] {mapping.confidence_score:.2%}")
            console.print(f"[dim]Source:[/dim] {source_prov.provision_text[:100]}...")
            console.print(f"[dim]Target:[/dim] {target_prov.provision_text[:100]}...")
            console.print(f"[dim]Reasoning:[/dim] {mapping.reasoning}\n")
    else:
        console.print("\n[red]No matches found even with all candidates verified.[/red]\n")
        console.print("[yellow]This suggests the provisions are genuinely different, not a filtering issue.[/yellow]\n")

    # Save comparison results
    output_path = Path("test_data/processed/pair_a_all_candidates_comparison.json")
    comparison_dict = comparison.model_dump(mode="json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comparison_dict, f, indent=2, default=str)

    # Analysis
    if matched > 0:
        analysis = (
            f"[green]✓ Success! Found {matched} match(es) when checking all candidates.[/green]\n\n"
            f"[cyan]Conclusion:[/cyan] Top-k filtering was too aggressive.\n"
            f"Correct matches had lower embedding similarity than expected.\n\n"
            f"[yellow]Recommendation:[/yellow] Implement provision-type filtering before embeddings."
        )
    else:
        analysis = (
            "[yellow]No matches found, even with exhaustive search.[/yellow]\n\n"
            "[cyan]Possible explanations:[/cyan]\n"
            "1. Documents use very different language (generic vs specific)\n"
            "2. Provisions delegate to Adoption Agreement (semantic gap)\n"
            "3. LLM is being too strict in matching criteria\n\n"
            "[yellow]Recommendation:[/yellow] Manually review a few pairs to validate LLM judgment."
        )

    console.print(Panel(
        f"{analysis}\n\n"
        f"Results saved to:\n"
        f"  • {output_path}",
        title="Analysis",
        border_style="cyan",
    ))


if __name__ == "__main__":
    main()
