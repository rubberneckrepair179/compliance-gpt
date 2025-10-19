"""
Extract provisions from both Pair A documents

Extracts provisions from both source and target documents for comparison.
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

console = Console()


def extract_from_document(pdf_path: Path, document_id: str) -> list:
    """Extract provisions from a single document."""
    console.print(f"\n{'='*70}")
    console.print(f"[bold]Processing: {pdf_path.name}[/bold]")
    console.print(f"{'='*70}\n")

    # Step 1: Extract PDF text
    console.print("[cyan]Step 1: Extracting PDF text...[/cyan]")
    extractor = PDFExtractor()
    extracted_doc = extractor.extract(pdf_path)
    console.print(f"[green]✓ Extracted {extracted_doc.total_pages} pages[/green]\n")

    # Step 2: Parse provisions
    console.print("[cyan]Step 2: Parsing provisions...[/cyan]")
    parser = ProvisionParser()

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

    # Save to JSON
    output_path = Path("test_data/processed") / f"{document_id}_provisions.json"
    parser.save_provisions(provisions, output_path)

    console.print(f"[green]✓ Success: Extracted {len(provisions)} provisions[/green]\n")

    return provisions


def main() -> None:
    """Extract provisions from both Pair A documents."""
    console.print("\n[cyan bold]Extracting Provisions from Pair A Documents[/cyan bold]")
    console.print("[dim]This will extract 5 provisions from each document for comparison[/dim]\n")

    documents = [
        ("test_data/raw/pair_a_source_bpd.pdf", "pair_a_source_bpd"),
        ("test_data/raw/pair_a_target_bpd.pdf", "pair_a_target_bpd"),
    ]

    all_provisions = {}

    for pdf_path_str, doc_id in documents:
        pdf_path = Path(pdf_path_str)

        if not pdf_path.exists():
            console.print(f"[red]✗ Not found:[/red] {pdf_path}")
            continue

        try:
            provisions = extract_from_document(pdf_path, doc_id)
            all_provisions[doc_id] = provisions
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            continue

    # Summary
    console.print(f"\n{'='*70}\n")
    console.print("[cyan bold]Extraction Complete![/cyan bold]\n")

    for doc_id, provisions in all_provisions.items():
        console.print(f"[green]✓ {doc_id}:[/green] {len(provisions)} provisions")

    console.print()
    console.print(Panel(
        f"[green]Successfully extracted provisions from {len(all_provisions)} documents![/green]\n\n"
        "Files created:\n"
        "  • test_data/processed/pair_a_source_bpd_provisions.json\n"
        "  • test_data/processed/pair_a_target_bpd_provisions.json\n\n"
        "[cyan]Next step:[/cyan] Build semantic mapper to compare provisions",
        title="Success",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
