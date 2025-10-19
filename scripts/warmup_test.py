"""
API Warmup Test

Makes small test requests to warm up a new Anthropic API account.
New accounts have gradual scaling - need to start with smaller requests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from anthropic import Anthropic
from src.config import settings
from rich.console import Console
from rich.panel import Panel

console = Console()


def main() -> None:
    """Run progressively larger test requests to warm up the API account."""
    console.print("\n[cyan bold]API Warmup Test[/cyan bold]")
    console.print("[dim]New Anthropic accounts require gradual scaling[/dim]\n")

    client = Anthropic(api_key=settings.anthropic_api_key)

    # Test 1: Tiny request
    console.print("[cyan]Test 1: Tiny request (100 tokens)...[/cyan]")
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": "Say hello in 5 words."}],
        )
        console.print(f"[green]✓ Success:[/green] {response.content[0].text}\n")
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]\n")
        return

    # Test 2: Small request
    console.print("[cyan]Test 2: Small request (500 tokens)...[/cyan]")
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": "Explain what a 401(k) plan is in 2-3 sentences."
            }],
        )
        console.print(f"[green]✓ Success:[/green] {response.content[0].text[:200]}...\n")
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]\n")
        return

    # Test 3: Medium request with sample text
    console.print("[cyan]Test 3: Medium request (1000 tokens)...[/cyan]")
    sample_text = """
    Section 2.01 Eligibility to Participate

    An Employee shall be eligible to participate in the Plan upon attaining age 21
    and completing one Year of Service. A Year of Service means a 12-consecutive-month
    period during which the Employee completes at least 1,000 Hours of Service.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"Extract the eligibility requirements from this text:\n\n{sample_text}"
            }],
        )
        console.print(f"[green]✓ Success:[/green] {response.content[0].text[:200]}...\n")
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]\n")
        return

    console.print(Panel(
        "[green]✓ Warmup complete![/green]\n\n"
        "Your API account is warmed up. You should now be able to:\n"
        "1. Make larger requests\n"
        "2. Run the provision extraction test\n\n"
        "Wait 5-10 minutes, then try:\n"
        "[cyan]python scripts/test_provision_parsing.py[/cyan]",
        title="Success",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
