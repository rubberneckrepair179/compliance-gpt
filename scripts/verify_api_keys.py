"""
API Key Verification Script

Tests that API keys are properly configured and working.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def verify_anthropic_key() -> bool:
    """Verify Anthropic API key is configured and working."""
    console.print("\n[cyan]Testing Anthropic API key...[/cyan]")

    if not settings.anthropic_api_key or settings.anthropic_api_key == "your_api_key_here":
        console.print("[red]✗ Anthropic API key not configured[/red]")
        console.print("[yellow]Please add your API key to .env file:[/yellow]")
        console.print("[dim]ANTHROPIC_API_KEY=sk-ant-...[/dim]\n")
        return False

    # Test the key with a simple API call
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=settings.anthropic_api_key)

        # Make a minimal test call
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Use stable model for test
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )

        console.print("[green]✓ Anthropic API key is valid and working[/green]")
        console.print(f"[dim]Model: {response.model}[/dim]")
        console.print(f"[dim]Response: {response.content[0].text}[/dim]\n")
        return True

    except Exception as e:
        console.print(f"[red]✗ Anthropic API key test failed: {e}[/red]\n")
        return False


def verify_openai_key() -> bool:
    """Verify OpenAI API key (optional for embeddings)."""
    console.print("[cyan]Testing OpenAI API key (optional)...[/cyan]")

    if not settings.openai_api_key or settings.openai_api_key == "your_api_key_here":
        console.print("[yellow]⚠ OpenAI API key not configured (optional)[/yellow]")
        console.print("[dim]Only needed if using OpenAI embeddings[/dim]\n")
        return True  # Not required, so return True

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        # Test with a simple embedding call
        response = client.embeddings.create(
            model="text-embedding-3-small", input="test"
        )

        console.print("[green]✓ OpenAI API key is valid and working[/green]")
        console.print(f"[dim]Embedding dimensions: {len(response.data[0].embedding)}[/dim]\n")
        return True

    except Exception as e:
        console.print(f"[yellow]⚠ OpenAI API key test failed: {e}[/yellow]")
        console.print("[dim]This is optional - you can proceed without it[/dim]\n")
        return True  # Optional, so don't block


def display_configuration() -> None:
    """Display current configuration settings."""
    console.print("[cyan bold]Current Configuration:[/cyan bold]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("LLM Model", settings.llm_model)
    table.add_row("Embedding Model", settings.embedding_model)
    table.add_row("Confidence High Threshold", f"{settings.confidence_high:.1%}")
    table.add_row("Confidence Medium Threshold", f"{settings.confidence_medium:.1%}")
    table.add_row("Max Retries", str(settings.max_retries))
    table.add_row("Database Path", str(settings.database_path))
    table.add_row("Log Level", settings.log_level)

    console.print(table)
    console.print()


def main() -> None:
    """Run all verification checks."""
    console.print("\n" + "=" * 70)
    console.print("[bold]API Key Verification Tool[/bold]")
    console.print("=" * 70 + "\n")

    # Display configuration
    display_configuration()

    # Test API keys
    anthropic_ok = verify_anthropic_key()
    openai_ok = verify_openai_key()

    # Summary
    console.print("=" * 70)
    console.print("[bold]Verification Summary:[/bold]\n")

    if anthropic_ok:
        console.print("[green]✓ Anthropic API: Ready for provision extraction[/green]")
    else:
        console.print("[red]✗ Anthropic API: Not configured (REQUIRED)[/red]")

    if not settings.openai_api_key or settings.openai_api_key == "your_api_key_here":
        console.print("[dim]  OpenAI API: Not configured (optional)[/dim]")
    else:
        console.print("[green]✓ OpenAI API: Configured[/green]")

    console.print()

    if anthropic_ok:
        console.print(Panel(
            "[green]✓ You're ready to run provision extraction![/green]\n\n"
            "Next step:\n"
            "[cyan]python scripts/test_provision_parsing.py[/cyan]",
            title="Ready to Proceed",
            border_style="green",
        ))
    else:
        console.print(Panel(
            "[yellow]Please configure your Anthropic API key:[/yellow]\n\n"
            "1. Get your API key from: https://console.anthropic.com/\n"
            "2. Edit .env file and replace:\n"
            "   [dim]ANTHROPIC_API_KEY=your_api_key_here[/dim]\n"
            "   with your actual key:\n"
            "   [dim]ANTHROPIC_API_KEY=sk-ant-...[/dim]\n"
            "3. Run this script again to verify",
            title="Action Required",
            border_style="yellow",
        ))

    console.print()
    sys.exit(0 if anthropic_ok else 1)


if __name__ == "__main__":
    main()
