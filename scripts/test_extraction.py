"""
Test PDF Extraction

Quick test script to validate PDF extraction on sample documents.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.pdf_extractor import PDFExtractor
from rich.console import Console
from rich.panel import Panel

console = Console()


def main() -> None:
    """Test PDF extraction on Pair A documents."""
    console.print("\n[cyan bold]PDF Extraction Test[/cyan bold]\n")

    # Initialize extractor
    extractor = PDFExtractor()

    # Test documents
    test_docs = [
        "test_data/raw/pair_a_source_bpd.pdf",
        "test_data/raw/pair_a_target_bpd.pdf",
    ]

    for doc_path_str in test_docs:
        doc_path = Path(doc_path_str)

        if not doc_path.exists():
            console.print(f"[red]✗ Not found:[/red] {doc_path}")
            continue

        console.print(f"\n{'='*70}")
        console.print(f"[bold]Testing: {doc_path.name}[/bold]")
        console.print(f"{'='*70}\n")

        try:
            # Extract
            extracted_doc = extractor.extract(doc_path)

            # Display results
            console.print(Panel(
                f"""[cyan]Document:[/cyan] {extracted_doc.filename}
[cyan]Total Pages:[/cyan] {extracted_doc.total_pages}
[cyan]Encrypted:[/cyan] {extracted_doc.is_encrypted}
[cyan]Extraction Method:[/cyan] {extracted_doc.extraction_method}
[cyan]Pages Extracted:[/cyan] {len(extracted_doc.pages)}

[cyan]Metadata:[/cyan]
  Creator: {extracted_doc.metadata.get('creator', 'N/A')}
  Producer: {extracted_doc.metadata.get('producer', 'N/A')}
""",
                title="📄 Extraction Results",
                border_style="green"
            ))

            # Show text sample from first page
            first_page_text = extractor.get_page_text(extracted_doc, 1)
            if first_page_text:
                sample = first_page_text[:500]
                console.print(Panel(
                    f"[dim]{sample}...[/dim]",
                    title="📝 First Page Sample (500 chars)",
                    border_style="blue"
                ))

            # Save to processed directory
            output_path = Path("test_data/processed") / f"{doc_path.stem}_extracted.txt"
            extractor.save_extracted_text(extracted_doc, output_path)

            console.print(f"\n[green]✓ Success: {doc_path.name}[/green]")

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            continue

    console.print(f"\n{'='*70}\n")
    console.print("[cyan]Extraction test complete![/cyan]")
    console.print("[dim]Check test_data/processed/ for extracted text files[/dim]\n")


if __name__ == "__main__":
    main()
