"""
Analyze the specific pairs Opus identified as conceptual matches.

Check embedding similarities and whether they were in top-5 candidates.
"""

import sys
from pathlib import Path
import json
import numpy as np
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from rich.console import Console
from rich.table import Table

console = Console()


def main():
    """Analyze Opus-identified conceptual matches."""

    console.print("\n[cyan bold]Analyzing Opus-Identified Conceptual Matches[/cyan bold]\n")

    # Load provisions
    with open("test_data/processed/pair_a_source_bpd_operational_provisions.json") as f:
        source_provs = json.load(f)

    with open("test_data/processed/pair_a_target_bpd_operational_provisions.json") as f:
        target_provs = json.load(f)

    # Create lookup by section reference
    source_by_section = {p['section_reference']: p for p in source_provs}
    target_by_section = {p['section_reference']: p for p in target_provs}

    # Opus-identified pairs
    opus_pairs = [
        ("Section 2.01", "Section 3.1", "Eligibility to Participate → CONDITIONS OF ELIGIBILITY"),
        ("Section 2.04", "Section 3.5", "Break in Service → REHIRED EMPLOYEES"),
        ("Section 4.01", "Section 13.5", "Vesting Schedule → VESTING REQUIREMENTS"),
        ("Section 4.02", "Section 13.5", "100% Vesting → VESTING REQUIREMENTS"),
    ]

    console.print("[yellow]Opus said these provisions are conceptually equivalent:[/yellow]\n")

    # Generate embeddings for all provisions
    client = OpenAI(api_key=settings.openai_api_key)

    all_texts = [p['provision_text'] for p in source_provs + target_provs]
    response = client.embeddings.create(model=settings.embedding_model, input=all_texts)

    embeddings = {}
    for i, p in enumerate(source_provs + target_provs):
        embeddings[p['provision_id']] = np.array(response.data[i].embedding)

    # Analyze each pair
    table = Table(title="Opus-Identified Pairs - Embedding Analysis", show_header=True)
    table.add_column("Source", width=15)
    table.add_column("Target", width=15)
    table.add_column("Description", width=35)
    table.add_column("Embed Sim", justify="center", width=10)
    table.add_column("Rank", justify="center", width=8)

    for source_sec, target_sec, description in opus_pairs:
        if source_sec not in source_by_section:
            console.print(f"[red]Source section not found: {source_sec}[/red]")
            continue

        if target_sec not in target_by_section:
            console.print(f"[red]Target section not found: {target_sec}[/red]")
            continue

        source_prov = source_by_section[source_sec]
        target_prov = target_by_section[target_sec]

        # Compute embedding similarity
        source_vec = embeddings[source_prov['provision_id']]
        target_vec = embeddings[target_prov['provision_id']]

        similarity = float(
            np.dot(source_vec, target_vec) /
            (np.linalg.norm(source_vec) * np.linalg.norm(target_vec))
        )

        # Compute rank - where does this target rank among all targets for this source?
        all_target_sims = []
        for t in target_provs:
            t_vec = embeddings[t['provision_id']]
            sim = float(
                np.dot(source_vec, t_vec) /
                (np.linalg.norm(source_vec) * np.linalg.norm(t_vec))
            )
            all_target_sims.append((t['section_reference'], sim))

        all_target_sims.sort(key=lambda x: x[1], reverse=True)
        rank = next(i+1 for i, (sec, _) in enumerate(all_target_sims) if sec == target_sec)

        # Color code by rank
        if rank <= 3:
            rank_str = f"[green]{rank}/5[/green]"
        else:
            rank_str = f"[red]{rank}/5[/red]"

        table.add_row(
            source_sec,
            target_sec,
            description,
            f"{similarity:.3f}",
            rank_str
        )

    console.print(table)
    console.print()

    # Show full ranking for one example
    console.print("[cyan]Example: Full ranking for Section 2.01 (Basic Eligibility)[/cyan]\n")

    source_prov = source_by_section["Section 2.01"]
    source_vec = embeddings[source_prov['provision_id']]

    rankings = []
    for t in target_provs:
        t_vec = embeddings[t['provision_id']]
        sim = float(
            np.dot(source_vec, t_vec) /
            (np.linalg.norm(source_vec) * np.linalg.norm(t_vec))
        )
        rankings.append({
            'section': t['section_reference'],
            'title': t['section_title'],
            'type': t['provision_type'],
            'similarity': sim
        })

    rankings.sort(key=lambda x: x['similarity'], reverse=True)

    rank_table = Table(show_header=True)
    rank_table.add_column("Rank", justify="center", width=6)
    rank_table.add_column("Target Section", width=18)
    rank_table.add_column("Type", width=18)
    rank_table.add_column("Similarity", justify="center", width=10)
    rank_table.add_column("Notes", width=30)

    for i, r in enumerate(rankings, 1):
        if r['section'] == "Section 3.1":
            notes = "← Opus said this matches!"
            style = "green"
        elif i <= 3:
            notes = "In top-3 (was verified)"
            style = "yellow"
        else:
            notes = "Not in top-3 (skipped)"
            style = "dim"

        rank_table.add_row(
            str(i),
            r['section'],
            r['type'],
            f"{r['similarity']:.3f}",
            notes,
            style=style
        )

    console.print(rank_table)
    console.print()

    # Analysis
    console.print("[cyan bold]Key Findings:[/cyan bold]\n")
    console.print("1. If Opus pairs are ranked 4th or 5th, they were SKIPPED with top_k=3")
    console.print("2. If they're in top-3 but weren't selected, another had higher LLM confidence")
    console.print("3. Embedding similarity doesn't capture 'template equivalence'\n")


if __name__ == "__main__":
    main()
