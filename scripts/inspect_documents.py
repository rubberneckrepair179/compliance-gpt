"""
Document Inspection Tool

Analyzes plan documents to understand their structure, format, and characteristics.
This is the first step before categorizing and pairing documents for testing.
"""

from pathlib import Path
from typing import Dict, Any, List
import pypdf
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()


def inspect_pdf_metadata(pdf_path: Path) -> Dict[str, Any]:
    """Extract basic PDF metadata and characteristics."""
    try:
        reader = pypdf.PdfReader(pdf_path)

        metadata = {
            "filename": pdf_path.name,
            "size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 2),
            "page_count": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
            "metadata": {},
        }

        # Try to get PDF metadata
        if reader.metadata:
            metadata["metadata"] = {
                "title": reader.metadata.get("/Title", "N/A"),
                "author": reader.metadata.get("/Author", "N/A"),
                "creator": reader.metadata.get("/Creator", "N/A"),
                "producer": reader.metadata.get("/Producer", "N/A"),
            }

        # Try to extract first page text (to test extraction capability)
        if not reader.is_encrypted:
            try:
                first_page = reader.pages[0]
                text_sample = first_page.extract_text()[:500]  # First 500 chars
                metadata["extraction_works"] = len(text_sample.strip()) > 0
                metadata["text_sample"] = text_sample.strip()[:200]  # Store smaller sample
            except Exception as e:
                metadata["extraction_works"] = False
                metadata["extraction_error"] = str(e)
        else:
            metadata["extraction_works"] = None
            metadata["note"] = "Document is encrypted - will need vision fallback"

        return metadata

    except Exception as e:
        return {
            "filename": pdf_path.name,
            "error": str(e),
            "inspection_failed": True
        }


def analyze_document_type(text_sample: str, metadata: Dict[str, Any]) -> str:
    """
    Attempt to identify document type from text and metadata.
    Returns: "basic_plan_document", "adoption_agreement", "amendment", "unknown"
    """
    text_lower = text_sample.lower() if text_sample else ""
    title_lower = str(metadata.get("metadata", {}).get("title", "")).lower()

    # Look for common indicators
    if "adoption agreement" in text_lower or "adoption agreement" in title_lower:
        return "adoption_agreement"
    elif "amendment" in text_lower or "amendment" in title_lower:
        return "amendment"
    elif "basic plan document" in text_lower or "bpd" in text_lower:
        return "basic_plan_document"
    elif "prototype" in text_lower or "prototype" in title_lower:
        return "prototype"
    elif "volume submitter" in text_lower:
        return "volume_submitter"
    else:
        return "unknown"


def identify_vendor(metadata: Dict[str, Any]) -> str:
    """Attempt to identify document vendor from metadata."""
    creator = str(metadata.get("metadata", {}).get("creator", "")).lower()
    producer = str(metadata.get("metadata", {}).get("producer", "")).lower()
    text_sample = metadata.get("text_sample", "").lower()

    # Generic vendor detection (avoid exposing specific vendor names in docs)
    # Check for common TPA platform indicators
    if any(indicator in creator or indicator in producer or indicator in text_sample
           for indicator in ["relius", "asc", "ascensus", "ftwilliam", "datair"]):
        return "TPA Platform"
    else:
        return "Generic/Unknown"


def main() -> None:
    """Inspect all documents in test_data/raw/"""
    console.print("\n[cyan bold]Document Inspection Tool[/cyan bold]\n")

    raw_dir = Path("test_data/raw")
    if not raw_dir.exists():
        console.print(f"[red]Error: {raw_dir} does not exist[/red]")
        return

    pdf_files = list(raw_dir.glob("*.pdf"))

    if not pdf_files:
        console.print(f"[yellow]No PDF files found in {raw_dir}[/yellow]")
        console.print("[dim]Place your plan documents in test_data/raw/ and run again[/dim]")
        return

    console.print(f"[green]Found {len(pdf_files)} PDF document(s)[/green]\n")

    # Inspect each document
    results: List[Dict[str, Any]] = []

    for pdf_path in sorted(pdf_files):
        console.print(f"[cyan]Inspecting:[/cyan] {pdf_path.name}")
        metadata = inspect_pdf_metadata(pdf_path)

        if not metadata.get("inspection_failed"):
            vendor = identify_vendor(metadata)
            doc_type = analyze_document_type(
                metadata.get("text_sample", ""),
                metadata
            )
            metadata["vendor"] = vendor
            metadata["doc_type"] = doc_type

        results.append(metadata)
        console.print()

    # Display summary table
    table = Table(title="Document Summary", show_header=True, header_style="bold magenta")
    table.add_column("Filename", style="cyan", width=30)
    table.add_column("Pages", justify="right")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Vendor", style="yellow")
    table.add_column("Type", style="green")
    table.add_column("Locked", justify="center")
    table.add_column("Extractable", justify="center")

    for result in results:
        if result.get("inspection_failed"):
            table.add_row(
                result["filename"],
                "[red]ERROR[/red]",
                "",
                "",
                "",
                "",
                ""
            )
        else:
            table.add_row(
                result["filename"],
                str(result.get("page_count", "?")),
                str(result.get("size_mb", "?")),
                result.get("vendor", "Unknown"),
                result.get("doc_type", "unknown"),
                "🔒" if result.get("is_encrypted") else "✓",
                "✓" if result.get("extraction_works") else "⚠️"
            )

    console.print(table)
    console.print()

    # Display detailed findings
    for result in results:
        if result.get("inspection_failed"):
            console.print(Panel(
                f"[red]Failed to inspect: {result.get('error')}[/red]",
                title=result["filename"],
                border_style="red"
            ))
        else:
            details = f"""[cyan]Vendor:[/cyan] {result.get('vendor', 'Unknown')}
[cyan]Document Type:[/cyan] {result.get('doc_type', 'unknown')}
[cyan]Pages:[/cyan] {result.get('page_count')}
[cyan]Size:[/cyan] {result.get('size_mb')} MB
[cyan]Encrypted:[/cyan] {result.get('is_encrypted')}
[cyan]Text Extraction:[/cyan] {'✓ Works' if result.get('extraction_works') else '⚠️ May need vision fallback'}

[cyan]PDF Metadata:[/cyan]
  Creator: {result.get('metadata', {}).get('creator', 'N/A')}
  Producer: {result.get('metadata', {}).get('producer', 'N/A')}
"""

            if result.get("text_sample"):
                details += f"\n[cyan]Text Sample (first 200 chars):[/cyan]\n[dim]{result['text_sample']}[/dim]"

            console.print(Panel(
                details,
                title=f"📄 {result['filename']}",
                border_style="green" if result.get("extraction_works") else "yellow"
            ))
            console.print()

    # Analysis recommendations
    console.print("[bold]Next Steps:[/bold]")

    locked_count = sum(1 for r in results if r.get("is_encrypted"))
    if locked_count > 0:
        console.print(f"⚠️  {locked_count} document(s) are encrypted - vision fallback will be needed")

    extraction_issues = sum(1 for r in results if not r.get("extraction_works"))
    if extraction_issues > 0:
        console.print(f"⚠️  {extraction_issues} document(s) have text extraction issues")

    console.print("\n[dim]Review the document types and vendors to determine comparison pairs[/dim]")


if __name__ == "__main__":
    main()
