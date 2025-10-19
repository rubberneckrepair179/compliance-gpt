"""
Test a single provision pair that Opus says should match.

Manually verify Section 2.01 → Section 3.1 to see what LLM says.
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.provision import Provision
from src.mapping.semantic_mapper import SemanticMapper
from rich.console import Console
from rich.panel import Panel

console = Console()


def main():
    """Test Section 2.01 → Section 3.1 specifically."""

    console.print("\n[cyan bold]Testing Opus-Identified Match: Section 2.01 → Section 3.1[/cyan bold]\n")

    # Load provisions
    with open("test_data/processed/pair_a_source_bpd_operational_provisions.json") as f:
        source_data = json.load(f)

    with open("test_data/processed/pair_a_target_bpd_operational_provisions.json") as f:
        target_data = json.load(f)

    # Find the specific provisions
    source_prov_data = next(p for p in source_data if p['section_reference'] == 'Section 2.01')
    target_prov_data = next(p for p in target_data if p['section_reference'] == 'Section 3.1')

    source_prov = Provision(**source_prov_data)
    target_prov = Provision(**target_prov_data)

    # Display provisions
    console.print("[yellow]Source Provision:[/yellow]")
    console.print(f"  Section: {source_prov.section_reference}")
    console.print(f"  Title: {source_prov.section_title}")
    console.print(f"  Type: {source_prov.provision_type.value}")
    console.print(f"  Text: {source_prov.provision_text[:200]}...")
    console.print()

    console.print("[yellow]Target Provision:[/yellow]")
    console.print(f"  Section: {target_prov.section_reference}")
    console.print(f"  Title: {target_prov.section_title}")
    console.print(f"  Type: {target_prov.provision_type.value}")
    console.print(f"  Text: {target_prov.provision_text[:200]}...")
    console.print()

    # Verify with LLM
    console.print("[cyan]Asking LLM to verify semantic equivalence...[/cyan]\n")

    mapper = SemanticMapper()
    mapping = mapper.verify_mapping(source_prov, target_prov, embedding_score=0.814)

    # Display results
    console.print("[cyan bold]LLM Assessment:[/cyan bold]\n")
    console.print(f"  Is Match: {mapping.is_match}")
    console.print(f"  LLM Similarity: {mapping.llm_similarity:.2f}")
    console.print(f"  Variance Type: {mapping.variance_type.value}")
    console.print(f"  Impact Level: {mapping.impact_level.value}")
    console.print(f"  Confidence: {mapping.confidence_score:.0%}")
    console.print(f"\n  Reasoning:\n  {mapping.reasoning}\n")

    # Analysis
    if mapping.is_match:
        result = "[green]✓ LLM agrees with Opus - these match![/green]"
    else:
        result = "[red]✗ LLM disagrees with Opus - says no match[/red]"

    console.print(Panel(
        f"{result}\n\n"
        f"[cyan]Opus says:[/cyan] These are conceptually equivalent (same purpose)\n"
        f"[cyan]LLM says:[/cyan] is_match={mapping.is_match}, confidence={mapping.confidence_score:.0%}\n\n"
        f"[yellow]Why the disconnect?[/yellow]\n"
        f"Source has specific values ('age 21 and one Year of Service')\n"
        f"Target has placeholders ('as elected in the Adoption Agreement')\n\n"
        f"LLM current prompt treats this as a substantive difference.\n"
        f"Need v2 prompt that recognizes template equivalence.",
        title="Analysis",
        border_style="cyan"
    ))


if __name__ == "__main__":
    main()
