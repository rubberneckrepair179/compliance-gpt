"""
Extract Operational Provisions from Pair A Documents

Uses v2 prompt with operational vs definitional distinction.
Scans full documents (no page limit) for narrow provision types.
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
    """Extract operational provisions from a single document."""
    console.print(f"\n{'='*70}")
    console.print(f"[bold]Processing: {pdf_path.name}[/bold]")
    console.print(f"{'='*70}\n")

    # Step 1: Extract PDF text
    console.print("[cyan]Step 1: Extracting PDF text (full document)...[/cyan]")
    extractor = PDFExtractor()
    extracted_doc = extractor.extract(pdf_path)
    console.print(f"[green]✓ Extracted {extracted_doc.total_pages} pages[/green]\n")

    # Step 2: Parse provisions using v2 prompt
    console.print("[cyan]Step 2: Parsing OPERATIONAL provisions (v2 prompt)...[/cyan]")
    parser = ProvisionParser(prompt_version="v2")

    provisions = parser.parse_provisions(
        extracted_doc=extracted_doc,
        document_id=document_id,
        provision_types=[
            ProvisionType.ELIGIBILITY,
            ProvisionType.VESTING_SCHEDULE,
        ],
        max_provisions=5,  # POC limit
    )

    # Save to JSON
    output_path = Path("test_data/processed") / f"{document_id}_operational_provisions.json"
    parser.save_provisions(provisions, output_path)

    console.print(f"[green]✓ Success: Extracted {len(provisions)} operational provisions[/green]\n")

    return provisions


def main() -> None:
    """Extract operational provisions from both Pair A documents."""
    console.print("\n[cyan bold]Extracting OPERATIONAL Provisions from Pair A Documents[/cyan bold]")
    console.print("[dim]Using v2 prompt: Operational vs Definitional distinction[/dim]")
    console.print("[dim]Scanning full documents for ELIGIBILITY and VESTING_SCHEDULE[/dim]\n")

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
        console.print(f"[green]✓ {doc_id}:[/green] {len(provisions)} operational provisions")

    console.print()
    console.print(Panel(
        f"[green]Successfully extracted operational provisions from {len(all_provisions)} documents![/green]\n\n"
        "Files created:\n"
        "  • test_data/processed/pair_a_source_bpd_operational_provisions.json\n"
        "  • test_data/processed/pair_a_target_bpd_operational_provisions.json\n\n"
        "[cyan]Next step:[/cyan] Run semantic mapper to compare operational provisions",
        title="Success",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
