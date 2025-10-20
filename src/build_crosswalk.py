#!/usr/bin/env python3
"""
BPD Crosswalk Builder

Uses semantic mapping to create BPD 01 ↔ BPD 05 crosswalk specification.

Architecture:
1. Load extracted provisions from JSON
2. Convert to Provision objects
3. Use SemanticMapper (embeddings + LLM) to find matches
4. Generate crosswalk CSV + JSON output
"""

import json
from pathlib import Path
from typing import List
from datetime import datetime

from src.models.provision import Provision, ProvisionType, ExtractionMethod
from src.mapping.semantic_mapper import SemanticMapper
from rich.console import Console
from uuid import uuid4

console = Console()


def load_provisions_from_json(json_path: Path, doc_id: str) -> List[Provision]:
    """Load provisions from BPD extraction JSON and convert to Provision objects"""

    with open(json_path, "r") as f:
        data = json.load(f)

    provisions = []

    for i, prov_data in enumerate(data["provisions"]):
        # Create Provision object
        provision = Provision(
            provision_id=uuid4(),  # Generate UUID
            document_id=doc_id,
            provision_type=ProvisionType.OTHER,  # Generic type for all BPD provisions
            section_reference=prov_data.get("section_number", "UNKNOWN"),
            section_title=prov_data.get("section_title", ""),
            provision_text=prov_data.get("provision_text", ""),
            page_number=prov_data.get("page_number"),
            extraction_method=ExtractionMethod.TEXT_API,  # Simple PDF extraction
            confidence_score=1.0,  # Mark as high confidence for now
        )

        # Add topic to metadata custom_fields
        provision.metadata.custom_fields["topic"] = prov_data.get("topic", "Other")

        provisions.append(provision)

    return provisions


def generate_crosswalk_csv(comparison, output_path: Path):
    """Generate CSV crosswalk from comparison results"""

    import csv

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "mapping_id",
                "source_section",
                "source_title",
                "source_text_preview",
                "target_section",
                "target_title",
                "target_text_preview",
                "mapping_type",
                "confidence",
                "embedding_similarity",
                "llm_similarity",
                "variance_type",
                "impact_level",
                "reasoning",
            ]
        )

        # Data rows
        for i, mapping in enumerate(comparison.mappings):
            # Determine mapping type
            if mapping.is_match and mapping.confidence_score >= 0.9:
                mapping_type = "1:1"
            elif mapping.is_match and mapping.confidence_score >= 0.7:
                mapping_type = "with_constraints"
            elif mapping.is_match:
                mapping_type = "with_exceptions"
            else:
                mapping_type = "no_mapping"

            writer.writerow(
                [
                    f"MAP-{i+1:03d}",
                    mapping.source_provision_id,
                    "",  # Will need to look up title from source provisions
                    "",  # Text preview
                    mapping.target_provision_id if mapping.is_match else "",
                    "",  # Target title
                    "",  # Target text preview
                    mapping_type,
                    f"{mapping.confidence_score:.2f}",
                    f"{mapping.embedding_similarity:.3f}",
                    f"{mapping.llm_similarity:.2f}",
                    mapping.variance_type.value,
                    mapping.impact_level.value,
                    mapping.reasoning,
                ]
            )

    console.print(f"[green]✓ Crosswalk CSV saved to {output_path}[/green]")


def generate_crosswalk_json(comparison, source_provisions, target_provisions, output_path: Path):
    """Generate detailed JSON crosswalk with full provision data"""

    # Build lookup maps
    source_map = {p.provision_id: p for p in source_provisions}
    target_map = {p.provision_id: p for p in target_provisions}

    crosswalk = {
        "crosswalk_metadata": {
            "created_date": datetime.utcnow().isoformat(),
            "source_document": comparison.source_document_id,
            "target_document": comparison.target_document_id,
            "total_mappings": len(comparison.mappings),
            "mapping_summary": {
                "matched": comparison.matched_provisions,
                "unmatched_source": comparison.unmatched_source_provisions,
                "unmatched_target": comparison.unmatched_target_provisions,
            },
            "confidence_distribution": {
                "high (90-100)": sum(1 for m in comparison.mappings if m.confidence_score >= 0.9),
                "medium (70-89)": sum(
                    1
                    for m in comparison.mappings
                    if 0.7 <= m.confidence_score < 0.9
                ),
                "low (<70)": sum(1 for m in comparison.mappings if m.confidence_score < 0.7),
            },
        },
        "mappings": [],
    }

    for i, mapping in enumerate(comparison.mappings):
        source_prov = source_map.get(mapping.source_provision_id)
        target_prov = target_map.get(mapping.target_provision_id)

        # Determine mapping type
        if mapping.is_match and mapping.confidence_score >= 0.9:
            mapping_type = "1:1"
        elif mapping.is_match and mapping.confidence_score >= 0.7:
            mapping_type = "with_constraints"
        elif mapping.is_match:
            mapping_type = "with_exceptions"
        else:
            mapping_type = "no_mapping"

        crosswalk_entry = {
            "mapping_id": f"MAP-{i+1:03d}",
            "source": {
                "provision_id": str(mapping.source_provision_id),
                "section_number": source_prov.section_reference if source_prov else "",
                "section_title": source_prov.section_title if source_prov else "",
                "provision_text": source_prov.provision_text[:500] + "..." if source_prov else "",
                "topic": source_prov.metadata.custom_fields.get("topic", "") if source_prov else "",
                "page": source_prov.page_number if source_prov else None,
            },
            "target": {
                "provision_id": str(mapping.target_provision_id) if mapping.is_match else None,
                "section_number": target_prov.section_reference if target_prov else "",
                "section_title": target_prov.section_title if target_prov else "",
                "provision_text": target_prov.provision_text[:500] + "..." if target_prov else "",
                "topic": target_prov.metadata.custom_fields.get("topic", "") if target_prov else "",
                "page": target_prov.page_number if target_prov else None,
            },
            "mapping_metadata": {
                "mapping_type": mapping_type,
                "confidence_score": round(mapping.confidence_score, 3),
                "embedding_similarity": round(mapping.embedding_similarity, 3),
                "llm_similarity": round(mapping.llm_similarity, 3),
                "variance_type": mapping.variance_type.value,
                "impact_level": mapping.impact_level.value,
                "reasoning": mapping.reasoning,
                "requires_manual_review": mapping.confidence_score < 0.7,
            },
        }

        crosswalk["mappings"].append(crosswalk_entry)

    with open(output_path, "w") as f:
        json.dump(crosswalk, f, indent=2)

    console.print(f"[green]✓ Crosswalk JSON saved to {output_path}[/green]")


def main():
    """Build BPD crosswalk specification"""

    console.print("\n[cyan bold]═══ BPD Crosswalk Builder ═══[/cyan bold]\n")

    # Paths
    source_json = Path("test_data/extracted/source_bpd_01_provisions.json")
    target_json = Path("test_data/extracted/target_bpd_05_provisions.json")
    output_dir = Path("test_data/crosswalk")
    output_dir.mkdir(exist_ok=True)

    # Load provisions
    console.print("[cyan]Loading extracted provisions...[/cyan]")
    source_provisions = load_provisions_from_json(source_json, "BPD_01")
    target_provisions = load_provisions_from_json(target_json, "BPD_05")

    console.print(f"[green]✓ Loaded {len(source_provisions)} source provisions[/green]")
    console.print(f"[green]✓ Loaded {len(target_provisions)} target provisions[/green]\n")

    # Initialize mapper
    console.print("[cyan]Initializing semantic mapper...[/cyan]")
    mapper = SemanticMapper(provider="openai", top_k=5)  # Check top 5 candidates per source
    console.print("[green]✓ Mapper initialized[/green]\n")

    # Run comparison
    comparison = mapper.compare_documents(
        source_provisions=source_provisions,
        target_provisions=target_provisions,
        source_doc_id="BPD_01",
        target_doc_id="BPD_05",
    )

    # Generate outputs
    console.print("\n[cyan bold]Generating Crosswalk Outputs[/cyan bold]\n")

    csv_path = output_dir / "bpd_crosswalk.csv"
    json_path = output_dir / "bpd_crosswalk.json"

    generate_crosswalk_csv(comparison, csv_path)
    generate_crosswalk_json(comparison, source_provisions, target_provisions, json_path)

    # Summary
    console.print("\n[cyan bold]═══ Crosswalk Summary ═══[/cyan bold]\n")
    console.print(f"Total source provisions: {comparison.total_source_provisions}")
    console.print(f"Total target provisions: {comparison.total_target_provisions}")
    console.print(f"Matched provisions: {comparison.matched_provisions}")
    console.print(f"Unmatched source: {comparison.unmatched_source_provisions}")
    console.print(f"Unmatched target: {comparison.unmatched_target_provisions}")
    console.print(f"\n[yellow]High impact variances: {comparison.high_impact_variances}[/yellow]")
    console.print(f"[yellow]Medium impact variances: {comparison.medium_impact_variances}[/yellow]")
    console.print(f"[dim]Low impact variances: {comparison.low_impact_variances}[/dim]")

    console.print(f"\n[green bold]✓ Crosswalk complete![/green bold]")
    console.print(f"[dim]CSV: {csv_path}[/dim]")
    console.print(f"[dim]JSON: {json_path}[/dim]\n")


if __name__ == "__main__":
    main()
