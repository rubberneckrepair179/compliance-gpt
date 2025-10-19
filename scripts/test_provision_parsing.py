"""
Test Provision Parsing

Tests end-to-end provision extraction from PDFs using Claude.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.pdf_extractor import PDFExtractor
from src.extraction.provision_parser import ProvisionParser
from src.models.provision import ProvisionType
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_provision_extraction(pdf_path: Path) -> None:
    """
    Test full provision extraction pipeline on a document.

    Args:
        pdf_path: Path to PDF document
    """
    console.print(f"\n{'='*70}")
    console.print(f"[bold]Testing: {pdf_path.name}[/bold]")
    console.print(f"{'='*70}\n")

    # Step 1: Extract PDF text
    console.print("[cyan]Step 1: Extracting PDF text...[/cyan]")
    extractor = PDFExtractor()

    try:
        extracted_doc = extractor.extract(pdf_path)
        console.print(f"[green]✓ Extracted {extracted_doc.total_pages} pages[/green]\n")
    except Exception as e:
        console.print(f"[red]✗ PDF extraction failed: {e}[/red]")
        return

    # Step 2: Parse provisions with Claude
    console.print("[cyan]Step 2: Parsing provisions with Claude...[/cyan]")
    parser = ProvisionParser()

    # Generate document ID
    document_id = pdf_path.stem

    try:
        provisions = parser.parse_provisions(
            extracted_doc=extracted_doc,
            document_id=document_id,
            provision_types=[
                ProvisionType.ELIGIBILITY,
                ProvisionType.VESTING_SCHEDULE,
                ProvisionType.EMPLOYER_CONTRIBUTION,
            ],
            max_provisions=5,  # POC limit
        )

        if not provisions:
            console.print("[yellow]⚠ No provisions extracted[/yellow]\n")
            return

        # Step 3: Display results
        console.print(f"[green]✓ Extracted {len(provisions)} provisions[/green]\n")
        display_provisions(provisions)

        # Step 4: Save to JSON
        output_path = Path("test_data/processed") / f"{document_id}_provisions.json"
        parser.save_provisions(provisions, output_path)

    except Exception as e:
        console.print(f"[red]✗ Provision parsing failed: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return


def display_provisions(provisions) -> None:
    """Display extracted provisions in a formatted table."""
    # Summary table
    table = Table(title="Extracted Provisions Summary", show_header=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Type", style="yellow")
    table.add_column("Section", style="green")
    table.add_column("Title", style="blue", max_width=30)
    table.add_column("Confidence", justify="right")

    for idx, prov in enumerate(provisions, 1):
        confidence_str = f"{prov.confidence_score:.1%}"
        confidence_color = (
            "green" if prov.is_high_confidence()
            else "yellow" if not prov.is_low_confidence()
            else "red"
        )

        table.add_row(
            str(idx),
            prov.provision_type.value,
            prov.section_reference,
            prov.section_title or "[dim]N/A[/dim]",
            f"[{confidence_color}]{confidence_str}[/{confidence_color}]",
        )

    console.print(table)
    console.print()

    # Detailed view of each provision
    for idx, prov in enumerate(provisions, 1):
        entities_str = ""
        if prov.extracted_entities.ages:
            entities_str += f"\n  Ages: {prov.extracted_entities.ages}"
        if prov.extracted_entities.service_years:
            entities_str += f"\n  Service Years: {prov.extracted_entities.service_years}"
        if prov.extracted_entities.percentages:
            pct_display = [f"{p:.1%}" for p in prov.extracted_entities.percentages]
            entities_str += f"\n  Percentages: {pct_display}"
        if prov.extracted_entities.keywords:
            entities_str += f"\n  Keywords: {', '.join(prov.extracted_entities.keywords[:5])}"

        text_preview = prov.provision_text[:300] + "..." if len(prov.provision_text) > 300 else prov.provision_text

        console.print(Panel(
            f"[cyan]Type:[/cyan] {prov.provision_type.value}\n"
            f"[cyan]Section:[/cyan] {prov.section_reference}\n"
            f"[cyan]Title:[/cyan] {prov.section_title or 'N/A'}\n"
            f"[cyan]Confidence:[/cyan] {prov.confidence_score:.1%}\n"
            f"[cyan]Entities:[/cyan]{entities_str}\n\n"
            f"[cyan]Text Preview:[/cyan]\n[dim]{text_preview}[/dim]",
            title=f"Provision #{idx}",
            border_style="green" if prov.is_high_confidence() else "yellow",
        ))


def main() -> None:
    """Test provision extraction on sample documents."""
    console.print("\n[cyan bold]Provision Parsing Test[/cyan bold]")
    console.print("[dim]POC Version: Extracts 5 key provisions for testing[/dim]\n")

    # Test on pair_a_source_bpd.pdf first (smaller document)
    test_doc = Path("test_data/raw/pair_a_source_bpd.pdf")

    if not test_doc.exists():
        console.print(f"[red]✗ Test document not found:[/red] {test_doc}")
        console.print("[yellow]Please ensure sample documents are in test_data/raw/[/yellow]")
        sys.exit(1)

    # Run test
    test_provision_extraction(test_doc)

    # Summary
    console.print(f"\n{'='*70}\n")
    console.print("[cyan]Test complete![/cyan]")
    console.print("[dim]Check test_data/processed/ for JSON output[/dim]\n")

    console.print(Panel(
        "[green]Next Steps:[/green]\n\n"
        "1. Review the extracted provisions above\n"
        "2. Check the JSON file for full structured data\n"
        "3. Validate provision types are correct\n"
        "4. Test on second document (pair_a_target_bpd.pdf)\n"
        "5. Build semantic mapping between provision pairs",
        title="POC Progress",
        border_style="cyan",
    ))
    console.print()


if __name__ == "__main__":
    main()
