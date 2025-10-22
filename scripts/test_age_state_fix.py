#!/usr/bin/env python3
"""
Test Age→State False Positive Fix

Validates that the embedding and prompt improvements prevent the false positive
where "Age" eligibility election matched to "State" address field (both Q 1.04).
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mapping.aa_semantic_mapper import AASemanticMapper
from rich.console import Console

console = Console()


def load_elections(path: Path) -> dict:
    """Load elections and build lookup dict."""
    with open(path, 'r') as f:
        data = json.load(f)
    return {e['id']: e for e in data['aas']}


def main():
    console.print("\n[cyan bold]Testing Age→State False Positive Fix[/cyan bold]\n")

    # Load elections
    source_elections = load_elections(Path("test_data/extracted/relius_aa_elections.json"))
    target_elections = load_elections(Path("test_data/extracted/ascensus_aa_elections.json"))

    # Find the problematic elections from validation Row 1
    # Source: Question 1.04 "g. Age ____ (may not exceed 21)" [Section: Eligibility Conditions]
    # Target: Question 1.04 "State" [Section: Part A - Adopting Employer]

    source_election = None
    target_election = None

    # Search for source election (Age)
    for e in source_elections.values():
        if e['question_number'] == '1.04' and 'Age' in e['question_text']:
            source_election = e
            break

    # Search for target election (State)
    for e in target_elections.values():
        if e['question_number'] == '1.04' and e['question_text'].strip() == 'State':
            target_election = e
            break

    if not source_election or not target_election:
        console.print("[red]Could not find test elections in extracted data[/red]")
        return

    console.print("[dim]Source Election:[/dim]")
    console.print(f"  Q {source_election['question_number']}: {source_election['question_text']}")
    console.print(f"  Section: {source_election.get('section_context', 'N/A')}")
    console.print(f"  Kind: {source_election.get('kind', 'N/A')}\n")

    console.print("[dim]Target Election:[/dim]")
    console.print(f"  Q {target_election['question_number']}: {target_election['question_text']}")
    console.print(f"  Section: {target_election.get('section_context', 'N/A')}")
    console.print(f"  Kind: {target_election.get('kind', 'N/A')}\n")

    # Initialize mapper
    mapper = AASemanticMapper(provider='openai', top_k=1, max_workers=1)

    # Test 1: Check embedding text representation
    console.print("[cyan]Test 1: Embedding Text Representation[/cyan]")
    source_text = mapper._election_to_text(source_election)
    target_text = mapper._election_to_text(target_election)

    console.print("[dim]Source embedding text:[/dim]")
    console.print(f"{source_text}\n")
    console.print("[dim]Target embedding text:[/dim]")
    console.print(f"{target_text}\n")

    # Verify question numbers are stripped
    if "Question 1.04" in source_text or "Question 1.04" in target_text:
        console.print("[red]❌ FAIL: Question numbers still present in embedding text[/red]")
    else:
        console.print("[green]✓ PASS: Question numbers stripped from embedding text[/green]")

    # Verify section context is included
    if "Section:" in source_text and "Section:" in target_text:
        console.print("[green]✓ PASS: Section context included in embedding text[/green]")
    else:
        console.print("[red]❌ FAIL: Section context missing from embedding text[/red]")

    # Test 2: Check embedding similarity
    console.print("\n[cyan]Test 2: Embedding Similarity[/cyan]")
    embeddings = mapper.generate_embeddings([source_election, target_election])

    import numpy as np
    source_vec = embeddings[source_election['id']]
    target_vec = embeddings[target_election['id']]
    similarity = float(
        np.dot(source_vec, target_vec) / (np.linalg.norm(source_vec) * np.linalg.norm(target_vec))
    )

    console.print(f"Embedding similarity: {similarity:.4f}")

    if similarity < 0.7:
        console.print("[green]✓ PASS: Low embedding similarity (< 0.7)[/green]")
    else:
        console.print(f"[yellow]⚠️  WARNING: High embedding similarity ({similarity:.0%}) - may still be flagged as candidate[/yellow]")

    # Test 3: LLM verification
    console.print("\n[cyan]Test 3: LLM Verification[/cyan]")
    mapping = mapper.verify_mapping(source_election, target_election, similarity)

    console.print(f"Is Match: {mapping['is_match']}")
    console.print(f"Confidence: {mapping['confidence_score']:.0%}")
    console.print(f"Reasoning: {mapping['reasoning'][:200]}...")

    if not mapping['is_match']:
        console.print("[green]✓ PASS: LLM correctly identifies NO MATCH[/green]")
    else:
        console.print(f"[red]❌ FAIL: LLM incorrectly matched Age→State ({mapping['confidence_score']:.0%} confidence)[/red]")
        console.print(f"[dim]Full reasoning: {mapping['reasoning']}[/dim]")

    # Summary
    console.print("\n[cyan bold]Summary[/cyan bold]")
    if not mapping['is_match'] and similarity < 0.9:
        console.print("[green bold]✓ FALSE POSITIVE FIXED[/green bold]")
        console.print("Both embedding and LLM stages correctly reject Age→State match")
    elif not mapping['is_match']:
        console.print("[yellow bold]⚠️  PARTIALLY FIXED[/yellow bold]")
        console.print("LLM catches the error, but embeddings still show high similarity")
    else:
        console.print("[red bold]❌ FIX FAILED[/red bold]")
        console.print("False positive persists - requires further investigation")

    console.print()


if __name__ == "__main__":
    main()
