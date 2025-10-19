"""
Test Semantic Mapping

Tests the hybrid embedding + LLM semantic mapper on Pair A provisions.
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


def load_provisions(json_path: Path) -> list[Provision]:
    """Load provisions from JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provisions = []
    for prov_dict in data:
        prov = Provision(**prov_dict)
        provisions.append(prov)

    return provisions


def display_comparison_summary(comparison):
    """Display comparison results in a formatted table."""
    console.print(f"\n[cyan bold]Document Comparison Results[/cyan bold]\n")

    # Summary stats
    table = Table(title="Comparison Statistics", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Source Provisions", str(comparison.total_source_provisions))
    table.add_row("Target Provisions", str(comparison.total_target_provisions))
    table.add_row("Matched Provisions", str(comparison.matched_provisions))
    table.add_row("Unmatched Source", str(comparison.unmatched_source_provisions))
    table.add_row("Unmatched Target", str(comparison.unmatched_target_provisions))
    table.add_row("Completion Rate", f"{comparison.completion_rate():.1%}")
    table.add_row("---", "---")
    table.add_row("High Impact Variances", str(comparison.high_impact_variances))
    table.add_row("Medium Impact Variances", str(comparison.medium_impact_variances))
    table.add_row("Low Impact Variances", str(comparison.low_impact_variances))
    table.add_row("Requires Review", str(comparison.requires_review_count()))

    console.print(table)
    console.print()

    # Detailed mappings
    console.print("[cyan bold]Provision Mappings:[/cyan bold]\n")

    for idx, mapping in enumerate(comparison.mappings, 1):
        match_indicator = "✓" if mapping.is_match else "✗"
        confidence_color = (
            "green"
            if mapping.is_high_confidence()
            else "yellow"
            if not mapping.is_low_confidence()
            else "red"
        )

        console.print(Panel(
            f"[{confidence_color}]{match_indicator} Match: {mapping.is_match}[/{confidence_color}]\n"
            f"[cyan]Embedding Similarity:[/cyan] {mapping.embedding_similarity:.1%}\n"
            f"[cyan]LLM Similarity:[/cyan] {mapping.llm_similarity:.1%}\n"
            f"[cyan]Variance Type:[/cyan] {mapping.variance_type.value}\n"
            f"[cyan]Impact Level:[/cyan] {mapping.impact_level.value}\n"
            f"[cyan]Confidence:[/cyan] {mapping.confidence_score:.1%}\n"
            f"[cyan]Requires Review:[/cyan] {mapping.requires_review()}\n\n"
            f"[cyan]Reasoning:[/cyan]\n[dim]{mapping.reasoning}[/dim]",
            title=f"Mapping #{idx}",
            border_style=confidence_color,
        ))


def main() -> None:
    """Test semantic mapping on Pair A provisions."""
    console.print("\n[cyan bold]Semantic Mapping Test[/cyan bold]")
    console.print("[dim]POC: Hybrid embedding + LLM approach[/dim]\n")

    # Load provisions
    source_path = Path("test_data/processed/pair_a_source_bpd_provisions.json")
    target_path = Path("test_data/processed/pair_a_target_bpd_provisions.json")

    if not source_path.exists() or not target_path.exists():
        console.print("[red]Provision files not found. Run extract_both_documents.py first.[/red]")
        sys.exit(1)

    console.print(f"[cyan]Loading provisions...[/cyan]")
    source_provisions = load_provisions(source_path)
    target_provisions = load_provisions(target_path)

    console.print(f"[green]✓ Loaded {len(source_provisions)} source provisions[/green]")
    console.print(f"[green]✓ Loaded {len(target_provisions)} target provisions[/green]\n")

    # Initialize mapper
    mapper = SemanticMapper(top_k=3)

    # Run comparison
    try:
        comparison = mapper.compare_documents(
            source_provisions=source_provisions,
            target_provisions=target_provisions,
            source_doc_id="pair_a_source_bpd",
            target_doc_id="pair_a_target_bpd",
        )

        # Display results
        display_comparison_summary(comparison)

        # Save results
        output_path = Path("test_data/processed/pair_a_comparison.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(comparison.model_dump(mode="json"), f, indent=2, default=str)

        console.print(f"\n[green]✓ Saved comparison results to:[/green] {output_path}\n")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
