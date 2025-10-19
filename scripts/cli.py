"""
compliance-gpt CLI

Entry point for the compliance-gpt POC tool.
"""

import click
from rich.console import Console
from pathlib import Path

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """
    compliance-gpt: AI-assisted plan document compliance tool

    Automates provision-by-provision reconciliation for retirement plan conversions.
    """
    pass


@main.command()
@click.argument("pdf_path", type=click.Path(exists=True, path_type=Path))
def extract(pdf_path: Path) -> None:
    """Extract provisions from a plan document."""
    console.print(f"[cyan]Extracting provisions from:[/cyan] {pdf_path}")
    console.print("[yellow]Not implemented yet - POC in progress[/yellow]")


@main.command()
@click.argument("source_pdf", type=click.Path(exists=True, path_type=Path))
@click.argument("target_pdf", type=click.Path(exists=True, path_type=Path))
def compare(source_pdf: Path, target_pdf: Path) -> None:
    """Compare two plan documents and generate variance report."""
    console.print(f"[cyan]Comparing documents:[/cyan]")
    console.print(f"  Source: {source_pdf}")
    console.print(f"  Target: {target_pdf}")
    console.print("[yellow]Not implemented yet - POC in progress[/yellow]")


@main.command()
def inspect() -> None:
    """Inspect plan documents in test_data/raw/ to understand their characteristics."""
    import sys
    from pathlib import Path

    # Add parent directory to path to import inspect_documents
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from scripts.inspect_documents import main as inspect_main
    inspect_main()


@main.command()
def verify_keys() -> None:
    """Verify API keys are configured and working."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.verify_api_keys import main as verify_main
    verify_main()


@main.command()
def test_setup() -> None:
    """Test that dependencies are properly installed."""
    console.print("[cyan]Testing dependency installation...[/cyan]\n")

    dependencies = {
        "PyPDF": "pypdf",
        "pdfplumber": "pdfplumber",
        "Anthropic SDK": "anthropic",
        "OpenAI SDK": "openai",
        "Pydantic": "pydantic",
        "SQLAlchemy": "sqlalchemy",
        "Rich": "rich",
        "Click": "click",
    }

    success = True
    for name, module in dependencies.items():
        try:
            __import__(module)
            console.print(f"✓ {name:20s} [green]OK[/green]")
        except ImportError:
            console.print(f"✗ {name:20s} [red]MISSING[/red]")
            success = False

    console.print()
    if success:
        console.print("[green]All dependencies installed successfully![/green]")
    else:
        console.print("[red]Some dependencies are missing. Run: pip install -e '.[dev]'[/red]")


if __name__ == "__main__":
    main()
