"""
AA Input Builder for Semantic Mapping

Assembles the input payload for AA election-to-election semantic mapping.
Transforms extracted elections into the structured format expected by the LLM.
"""

import re
from typing import Any, Dict, List
from pydantic import BaseModel

from src.models.election import (
    Election,
    TextElection,
    SingleSelectElection,
    MultiSelectElection,
    Option,
    FillIn,
)


def build_section_hierarchy(elections: List[Election]) -> Dict[str, str]:
    """
    Build section hierarchy mapping from election list.

    Extracts article/section context from election section_context fields.
    Maps question_number -> section/article heading for contextual hints.

    Args:
        elections: List of elections to analyze

    Returns:
        Dict mapping question_number to section context string
    """
    hierarchy = {}

    for election in elections:
        # Store the section context for this question number
        # section_context already contains the article/section header
        hierarchy[election.question_number] = election.section_context

    return hierarchy


def normalize_option_label(label: str) -> str:
    """
    Normalize option labels for comparison.

    Strips common formatting variations:
    - "a." -> "a"
    - "(a)" -> "a"
    - "a)" -> "a"

    Args:
        label: Raw option label

    Returns:
        Normalized label (lowercase, stripped of punctuation)
    """
    # Remove common punctuation: parentheses, periods, closing parens
    normalized = re.sub(r'[().]', '', label.strip())
    return normalized.lower()


def build_election_fingerprint(election: Election) -> str:
    """
    Build semantic fingerprint for election embedding.

    Includes:
    - Question text
    - Section context
    - Normalized option text (for select types)

    Excludes:
    - Question numbers (structural metadata)
    - Page numbers
    - Option IDs
    - Vendor boilerplate

    Args:
        election: Election to fingerprint

    Returns:
        Text string for embedding
    """
    parts = []

    # Section context provides topic hints
    if election.section_context:
        # Strip any leading question numbers from context
        clean_context = re.sub(r'^\d+\.\s*', '', election.section_context).strip()
        if clean_context:
            parts.append(clean_context)

    # Question text (core semantic content)
    parts.append(election.question_text)

    # Option text for select types (normalized)
    if election.kind in ["single_select", "multi_select"]:
        for option in election.options:
            # Include option text without labels/IDs
            if option.option_text:
                parts.append(option.option_text)

    return " ".join(parts)


def serialize_option(option: Option) -> Dict[str, Any]:
    """
    Serialize an Option to dict format for payload.

    Args:
        option: Option to serialize

    Returns:
        Dict with label, text, selection status, fill-ins
    """
    fill_ins_data = []
    for fill_in in option.fill_ins:
        fill_ins_data.append({
            "id": fill_in.id,
            "question_text": fill_in.question_text,
            "status": fill_in.status,
            "value": fill_in.value,
            "confidence": fill_in.confidence,
        })

    return {
        "label": option.label,
        "text": option.option_text,
        "is_selected": option.is_selected,
        "fill_ins": fill_ins_data,
    }


def build_aa_input(
    source_election: Election,
    target_election: Election,
    *,
    candidate_rank: int,
    run_id: str,
    section_hierarchy: Dict[str, str],
) -> Dict[str, Any]:
    """
    Build the AA semantic mapping prompt input payload.

    Transforms extracted elections into the structured format expected by the LLM.

    Args:
        source_election: Source election to compare
        target_election: Target election to compare
        candidate_rank: Position of target in top-k candidate list (from embeddings)
        run_id: Unique identifier for this comparison run
        section_hierarchy: Mapping of question_number to section/article context

    Returns:
        Dict ready for JSON serialization and LLM input
    """

    def election_to_payload(election: Election, label: str) -> Dict[str, Any]:
        """Convert an Election object to payload format."""
        base_payload = {
            "question_id": election.id,
            "question_number": election.question_number,
            "question_text": election.question_text,
            "section_context": election.section_context,
            "status": election.status,
            "provenance": {
                "page": election.provenance.page,
                "question_number": election.provenance.question_number,
            },
        }

        # Add kind and value based on election type
        if isinstance(election, TextElection):
            base_payload["kind"] = "text"
            base_payload["value"] = election.value
            base_payload["options"] = []

        elif isinstance(election, SingleSelectElection):
            base_payload["kind"] = "single_select"
            base_payload["value"] = {
                "option_id": election.value.option_id,
            }
            base_payload["options"] = [
                serialize_option(opt) for opt in election.options
            ]

        elif isinstance(election, MultiSelectElection):
            base_payload["kind"] = "multi_select"
            base_payload["value"] = {
                "option_ids": election.value.option_ids,
            }
            base_payload["options"] = [
                serialize_option(opt) for opt in election.options
            ]

        return base_payload

    # Assemble the complete input payload
    payload = {
        "run_id": run_id,
        "source": election_to_payload(source_election, "source"),
        "target": election_to_payload(target_election, "target"),
        "context": {
            "section_hierarchy": section_hierarchy,
            "stage1": {
                "candidate_rank": candidate_rank,
                "notes": "top-k from embeddings"
            }
        }
    }

    return payload
