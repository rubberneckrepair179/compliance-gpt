#!/usr/bin/env python3
"""
Vision-Based Crosswalk Builder

Builds crosswalks from vision-extracted JSONs:
1. BPD Crosswalk: source_bpd_01 provisions → target_bpd_05 provisions
2. AA Crosswalk: source_aa elections → target_aa elections

Uses semantic mapping (embeddings + LLM) to find matches.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from typing import List, Dict
from datetime import datetime
from uuid import uuid4

from src.models.provision import Provision, ProvisionType, ExtractionMethod
from src.mapping.semantic_mapper import SemanticMapper
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def load_bpd_provisions(json_path: Path, doc_id: str) -> List[Provision]:
    """Load BPD provisions from vision extraction JSON"""

    with open(json_path, "r") as f:
        data = json.load(f)

    provisions = []
    skipped = 0

    for i, bpd_data in enumerate(data.get("bpds", [])):
        provision_text = bpd_data.get("provision_text", "").strip()

        # Skip provisions with empty text (embeddings API rejects empty strings)
        if not provision_text:
            skipped += 1
            continue

        provision = Provision(
            provision_id=uuid4(),
            document_id=doc_id,
            provision_type=ProvisionType.OTHER,  # Could map from provision_type field
            section_reference=bpd_data.get("section_number", "UNKNOWN"),
            section_title=bpd_data.get("section_title", ""),
            provision_text=provision_text,
            page_number=None,  # Vision extraction doesn't track page per provision
            extraction_method=ExtractionMethod.VISION_FALLBACK,
            confidence_score=1.0,
        )

        # Store original provision_type in metadata
        provision.metadata.custom_fields["vision_provision_type"] = bpd_data.get("provision_type", "other")

        provisions.append(provision)

    if skipped > 0:
        console.print(f"[yellow]  Skipped {skipped} provisions with empty text[/yellow]")

    return provisions


def load_aa_elections(json_path: Path, doc_id: str) -> List[Dict]:
    """Load AA elections from vision extraction JSON (returns raw dicts, not Provision objects)"""

    with open(json_path, "r") as f:
        data = json.load(f)

    elections = []

    for election_data in data.get("aas", []):
        # Add document ID for tracking
        election_data["document_id"] = doc_id
        election_data["election_id"] = str(uuid4())
        elections.append(election_data)

    return elections


def build_bpd_crosswalk(
    source_provisions: List[Provision],
    target_provisions: List[Provision],
    output_dir: Path
):
    """Build BPD crosswalk using semantic mapper"""

    console.print(f"\n[bold cyan]Building BPD Crosswalk[/bold cyan]")
    console.print(f"Source provisions: {len(source_provisions)}")
    console.print(f"Target provisions: {len(target_provisions)}")

    # Initialize semantic mapper with parallelization
    # top_k=5 means we'll verify top 5 candidates per source provision
    # max_workers=16 for parallel LLM verification (16x speedup)
    mapper = SemanticMapper(
        provider="openai",  # Using OpenAI (GPT-5-Mini for semantic matching)
        top_k=5,
        max_workers=16
    )

    # Run semantic mapping
    console.print("\n[yellow]Running semantic mapping (embeddings + LLM)...[/yellow]")
    console.print(f"[dim]Stage 1: Generate embeddings for {len(source_provisions) + len(target_provisions)} provisions[/dim]")
    console.print(f"[dim]Stage 2: Cosine similarity to find top 5 candidates per source provision[/dim]")
    console.print(f"[dim]Stage 3: LLM verification for {len(source_provisions) * 5} candidate pairs[/dim]")
    console.print(f"[dim]Model: gpt-5-mini (semantic reasoning)[/dim]\n")

    comparison = mapper.compare_documents(
        source_provisions=source_provisions,
        target_provisions=target_provisions,
        source_doc_id="source_bpd_01",
        target_doc_id="target_bpd_05"
    )

    # Generate JSON output
    json_path = output_dir / "bpd_crosswalk.json"
    with open(json_path, 'w') as f:
        json.dump({
            "crosswalk_type": "BPD",
            "source_document": "source_bpd_01",
            "target_document": "target_bpd_05",
            "generated_at": datetime.now().isoformat(),
            "total_mappings": len(comparison.mappings),
            "total_source_provisions": comparison.total_source_provisions,
            "total_target_provisions": comparison.total_target_provisions,
            "matched_provisions": comparison.matched_provisions,
            "unmatched_source": comparison.unmatched_source_provisions,
            "unmatched_target": comparison.unmatched_target_provisions,
            "high_impact_variances": comparison.high_impact_variances,
            "medium_impact_variances": comparison.medium_impact_variances,
            "low_impact_variances": comparison.low_impact_variances,
            "mappings": [m.model_dump(mode='json') for m in comparison.mappings]
        }, f, indent=2, default=str)  # default=str handles UUID and other non-serializable types

    console.print(f"\n[green]✓ BPD Crosswalk saved:[/green]")
    console.print(f"  JSON: {json_path}")
    console.print(f"  Total mappings: {len(comparison.mappings)}")

    # Summary stats
    high_conf = sum(1 for m in comparison.mappings if m.confidence_score >= 0.90)
    medium_conf = sum(1 for m in comparison.mappings if 0.70 <= m.confidence_score < 0.90)
    no_match = sum(1 for m in comparison.mappings if not m.is_match)

    console.print(f"\n[bold]Match Quality:[/bold]")
    console.print(f"  High confidence (≥90%): {high_conf}")
    console.print(f"  Medium confidence (70-89%): {medium_conf}")
    console.print(f"  No match found: {no_match}")


def build_aa_crosswalk_simple(
    source_elections: List[Dict],
    target_elections: List[Dict],
    output_dir: Path
):
    """Build AA crosswalk (simplified version - just saves to JSON for now)"""

    console.print(f"\n[bold cyan]Building AA Crosswalk[/bold cyan]")
    console.print(f"Source elections: {len(source_elections)}")
    console.print(f"Target elections: {len(target_elections)}")

    console.print("\n[yellow]Note: AA crosswalk using simple export for now[/yellow]")
    console.print("[yellow]Future: Will use semantic matching for election options[/yellow]")

    # For now, just save the elections to structured JSON
    json_path = output_dir / "aa_crosswalk.json"

    with open(json_path, 'w') as f:
        json.dump({
            "crosswalk_type": "AA",
            "source_document": "source_aa",
            "target_document": "target_aa",
            "generated_at": datetime.now().isoformat(),
            "source_elections": source_elections,
            "target_elections": target_elections,
            "note": "AA semantic matching to be implemented"
        }, f, indent=2)

    console.print(f"\n[green]✓ AA data saved:[/green]")
    console.print(f"  JSON: {json_path}")


def main():
    """Build both BPD and AA crosswalks"""

    console.print("[bold magenta]VISION-BASED CROSSWALK BUILDER[/bold magenta]")
    console.print("="*80)

    # Paths
    extracted_dir = Path("test_data/extracted_vision")
    output_dir = Path("test_data/crosswalk")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load BPD provisions
    console.print("\n[cyan]Loading BPD provisions...[/cyan]")
    source_bpd = load_bpd_provisions(
        extracted_dir / "source_bpd_01_provisions.json",
        "source_bpd_01"
    )
    target_bpd = load_bpd_provisions(
        extracted_dir / "target_bpd_05_provisions.json",
        "target_bpd_05"
    )

    # Load AA elections
    console.print("\n[cyan]Loading AA elections...[/cyan]")
    source_aa = load_aa_elections(
        extracted_dir / "source_aa_elections.json",
        "source_aa"
    )
    target_aa = load_aa_elections(
        extracted_dir / "target_aa_elections.json",
        "target_aa"
    )

    # Build BPD crosswalk
    build_bpd_crosswalk(source_bpd, target_bpd, output_dir)

    # Build AA crosswalk (simple version for now)
    build_aa_crosswalk_simple(source_aa, target_aa, output_dir)

    console.print(f"\n[bold green]✓ CROSSWALK GENERATION COMPLETE[/bold green]")
    console.print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
