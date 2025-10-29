"""
Unit tests for AASemanticMapper.

These tests stub out embeddings and LLM interactions so we can validate the
parser and document comparison logic deterministically.
"""

import json

import pytest

from src.mapping.aa_semantic_mapper import AASemanticMapper
from src.models.aa_mapping import (
    AAElectionMapping,
    Classification,
    ElectionAnchor,
    ElectionDependency,
    MatchType,
    QuestionAlignment,
    StructureAnalysis,
    ValueAlignment,
)
from src.models.election import Provenance, TextElection
from src.models.mapping import ConfidenceLevel, ImpactLevel


def _make_text_election(election_id: str, question_number: str, text: str, section: str) -> TextElection:
    """Create a minimal text election for testing."""
    return TextElection(
        id=election_id,
        question_number=question_number,
        question_text=text,
        section_context=section,
        status="answered",
        confidence=1.0,
        provenance=Provenance(page=1, question_number=question_number),
        value=f"value-{election_id}",
    )


def test_parse_mapping_converts_payload_to_model():
    """Ensure JSON payloads from the LLM are parsed into domain models."""
    mapper = AASemanticMapper(provider="openai")

    source = _make_text_election("src-1", "1.01", "Employer Name", "Part A - Employer")
    target = _make_text_election("tgt-1", "1.02", "Name of Employer", "Part A - Employer")

    payload = {
        "schema_version": "aa-v1",
        "run_id": "run-123",
        "source_anchor": {"question_id": "src-1", "section_context": "Part A", "page": 2},
        "target_anchor": {"question_id": "tgt-1", "section_context": "Part A", "page": 3},
        "structure_analysis": {
            "question_alignment": {"value": True, "reasons": ["same employer detail"]},
            "requires_definition": ["Employer"],
            "election_dependency": {"status": "none", "evidence": []},
        },
        "option_mappings": [],
        "value_alignment": {
            "source_selected": ["Example Co."],
            "target_selected": ["Example Co."],
            "compatible": True,
            "justification": "Identical employer name",
        },
        "classification": {
            "match_type": "exact",
            "impact": "none",
            "confidence_level": "High",
            "confidence_rationale": "Clear textual match",
            "abstain_reasons": [],
        },
        "consistency_checks": {
            "exact_requires_none_impact": "passed",
            "incompatible_requires_non_none_impact": "passed",
            "abstain_requires_alignment_false_or_insufficient_context": "passed",
            "violations": []
        },
    }

    response = json.dumps(payload)
    mapping = mapper._parse_mapping(
        response,
        source=source,
        target=target,
        embedding_similarity=0.92,
        fallback_run_id="fallback-run",
    )

    assert mapping.schema_version == "aa-v1"
    assert mapping.embedding_similarity == pytest.approx(0.92)
    assert mapping.source_anchor.question_id == "src-1"
    assert mapping.target_anchor.page == 3
    assert mapping.structure_analysis.question_alignment.value is True
    assert mapping.value_alignment.compatible is True
    assert mapping.classification.match_type == MatchType.EXACT
    assert mapping.classification.confidence_level == ConfidenceLevel.HIGH
    assert mapping.classification.impact == ImpactLevel.NONE
    assert mapping.classification.confidence_rationale == "Clear textual match"
    assert mapping.consistency_checks.exact_requires_none_impact == "passed"
    assert mapping.consistency_checks.violations == []


def test_compare_documents_selects_highest_confidence_match(monkeypatch):
    """Comparator should pick the highest-confidence candidate per source election."""
    mapper = AASemanticMapper(provider="openai", top_k=2, max_workers=2)

    source = [_make_text_election("src-1", "1.01", "Eligibility age", "Part B - Eligibility")]
    target = [
        _make_text_election("tgt-1", "2.01", "Eligibility service", "Part B - Eligibility"),
        _make_text_election("tgt-2", "2.02", "Eligibility age", "Part B - Eligibility"),
    ]

    def fake_generate_embeddings(self, elections):
        return {str(e.id): [1.0] for e in elections}

    def fake_similarity_matrix(self, source_elections, target_elections, *_args, **_kwargs):
        return {
            str(source_elections[0].id): [
                (target_elections[0], 0.71),
                (target_elections[1], 0.94),
            ]
        }

    calls = []

    def fake_verify(
        self,
        source_election,
        target_election,
        *,
        embedding_similarity,
        candidate_rank,
        section_hierarchy,
        run_id,
    ):
        calls.append((source_election.id, target_election.id, candidate_rank, embedding_similarity, section_hierarchy))

        confidence = ConfidenceLevel.HIGH if target_election.id == "tgt-2" else ConfidenceLevel.MEDIUM
        classification = Classification(
            match_type=MatchType.EXACT,
            impact=ImpactLevel.NONE,
            confidence_level=confidence,
            confidence_rationale=f"rank-{candidate_rank}",
            abstain_reasons=[],
        )

        return AAElectionMapping(
            schema_version="aa-v1",
            run_id=run_id,
            source_election_id=source_election.id,
            target_election_id=target_election.id,
            source_anchor=ElectionAnchor(
                question_id=source_election.id,
                section_context=source_election.section_context,
                page=source_election.provenance.page,
            ),
            target_anchor=ElectionAnchor(
                question_id=target_election.id,
                section_context=target_election.section_context,
                page=target_election.provenance.page,
            ),
            structure_analysis=StructureAnalysis(
                question_alignment=QuestionAlignment(value=True, reasons=["topic alignment"]),
                requires_definition=[],
                election_dependency=ElectionDependency(status="none", evidence=[]),
            ),
            option_mappings=[],
                value_alignment=ValueAlignment(
                    source_selected=["value"],
                    target_selected=["value"],
                    compatible=True,
                    justification=None,
                ),
                classification=classification,
                embedding_similarity=embedding_similarity,
            )

    monkeypatch.setattr(AASemanticMapper, "_generate_embeddings", fake_generate_embeddings, raising=True)
    monkeypatch.setattr(AASemanticMapper, "_compute_similarity_matrix", fake_similarity_matrix, raising=True)
    monkeypatch.setattr(AASemanticMapper, "_verify_mapping", fake_verify, raising=True)

    comparison = mapper.compare_documents(
        source_elections=source,
        target_elections=target,
        source_doc_id="Source AA",
        target_doc_id="Target AA",
    )

    assert len(calls) == 2
    # Highest-confidence candidate (tgt-2) should be selected
    assert comparison.matched_elections == 1
    assert comparison.unmatched_source_elections == 0
    assert comparison.unmatched_target_elections == 1
    assert comparison.mappings[0].target_election_id == "tgt-2"
    assert comparison.mappings[0].classification.confidence_level == ConfidenceLevel.HIGH
    assert comparison.mappings[0].classification.confidence_rationale == "rank-2"


def test_compare_documents_uses_fallback_on_failure(monkeypatch):
    """If verification fails, the mapper should emit a fallback abstain mapping."""
    mapper = AASemanticMapper(provider="openai", top_k=1, max_workers=1)

    source = [_make_text_election("src-1", "1.01", "Employer Name", "Part A - Employer")]
    target = [_make_text_election("tgt-1", "1.02", "Plan Sponsor", "Part A - Employer")]

    def fake_generate_embeddings(self, elections):
        return {str(e.id): [1.0] for e in elections}

    def fake_similarity_matrix(self, source_elections, target_elections, *_args, **_kwargs):
        return {str(source_elections[0].id): [(target_elections[0], 0.85)]}

    def broken_verify(*_args, **_kwargs):
        raise RuntimeError("LLM offline")

    monkeypatch.setattr(AASemanticMapper, "_generate_embeddings", fake_generate_embeddings, raising=True)
    monkeypatch.setattr(AASemanticMapper, "_compute_similarity_matrix", fake_similarity_matrix, raising=True)
    monkeypatch.setattr(AASemanticMapper, "_verify_mapping", broken_verify, raising=True)

    comparison = mapper.compare_documents(
        source_elections=source,
        target_elections=target,
        source_doc_id="Source AA",
        target_doc_id="Target AA",
    )

    assert comparison.matched_elections == 0
    assert comparison.unmatched_source_elections == 1
    assert comparison.unmatched_target_elections == 1
    fallback_mapping = comparison.mappings[0]
    assert fallback_mapping.classification.match_type == MatchType.ABSTAIN
    assert fallback_mapping.classification.confidence_level == ConfidenceLevel.LOW
    assert fallback_mapping.classification.abstain_reasons == ["llm_failure"]
    assert "LLM offline" in fallback_mapping.classification.confidence_rationale
    assert fallback_mapping.embedding_similarity == pytest.approx(0.0)

# =============================================================================
# Parser Guardrail Tests (v1.1.1)
# =============================================================================

def test_validation_rejects_empty_confidence_rationale():
    """Parser should reject LLM response with empty confidence_rationale."""
    mapper = AASemanticMapper(provider="openai")

    source = _make_text_election("src-1", "1.01", "Employer Name", "Part A")
    target = _make_text_election("tgt-1", "1.02", "Sponsor Name", "Part A")

    payload = {
        "schema_version": "aa-v1",
        "run_id": "test-run",
        "source_anchor": {"question_id": "src-1", "section_context": "Part A", "page": 1},
        "target_anchor": {"question_id": "tgt-1", "section_context": "Part A", "page": 1},
        "structure_analysis": {
            "question_alignment": {"value": True, "reasons": []},
            "requires_definition": [],
            "election_dependency": {"status": "none", "evidence": []}
        },
        "option_mappings": [],
        "value_alignment": {
            "source_selected": [],
            "target_selected": [],
            "compatible": True,
            "justification": None
        },
        "classification": {
            "match_type": "exact",
            "impact": "none",
            "confidence_level": "High",
            "confidence_rationale": "",  # INVALID: empty
            "abstain_reasons": []
        },
        "consistency_checks": {
            "exact_requires_none_impact": "passed",
            "incompatible_requires_non_none_impact": "passed",
            "abstain_requires_alignment_false_or_insufficient_context": "passed",
            "violations": []
        }
    }

    response = json.dumps(payload)
    mapping = mapper._parse_mapping(
        response,
        source=source,
        target=target,
        embedding_similarity=0.95,
        fallback_run_id="fallback-run"
    )

    # Should trigger fallback due to validation failure
    assert mapping.classification.match_type == MatchType.ABSTAIN
    assert mapping.classification.abstain_reasons == ["llm_failure"]
    assert "confidence_rationale is empty" in mapping.classification.confidence_rationale


def test_validation_rejects_abstain_without_reasons():
    """Parser should reject abstain with empty abstain_reasons array."""
    mapper = AASemanticMapper(provider="openai")

    source = _make_text_election("src-1", "1.01", "Entity Type", "Part A")
    target = _make_text_election("tgt-1", "2.01", "Eligibility Hours", "Part B")

    payload = {
        "schema_version": "aa-v1",
        "run_id": "test-run",
        "source_anchor": {"question_id": "src-1", "section_context": "Part A", "page": 1},
        "target_anchor": {"question_id": "tgt-1", "section_context": "Part B", "page": 2},
        "structure_analysis": {
            "question_alignment": {"value": False, "reasons": ["topic mismatch"]},
            "requires_definition": [],
            "election_dependency": {"status": "none", "evidence": []}
        },
        "option_mappings": [],
        "value_alignment": {
            "source_selected": [],
            "target_selected": [],
            "compatible": False,
            "justification": "Different topics"
        },
        "classification": {
            "match_type": "abstain",
            "impact": "low",
            "confidence_level": "Low",
            "confidence_rationale": "Topics do not align",
            "abstain_reasons": []  # INVALID: empty when match_type=abstain
        },
        "consistency_checks": {
            "exact_requires_none_impact": "passed",
            "incompatible_requires_non_none_impact": "passed",
            "abstain_requires_alignment_false_or_insufficient_context": "failed",
            "violations": []
        }
    }

    response = json.dumps(payload)
    mapping = mapper._parse_mapping(
        response,
        source=source,
        target=target,
        embedding_similarity=0.42,
        fallback_run_id="fallback-run"
    )

    # Should trigger fallback due to validation failure
    assert mapping.classification.match_type == MatchType.ABSTAIN
    assert mapping.classification.abstain_reasons == ["llm_failure"]
    assert "abstain_reasons is empty when match_type=abstain" in mapping.classification.confidence_rationale


def test_validation_rejects_alignment_false_without_reasons():
    """Parser should reject question_alignment=false with empty reasons."""
    mapper = AASemanticMapper(provider="openai")

    source = _make_text_election("src-1", "1.01", "Contact Email", "Part A")
    target = _make_text_election("tgt-1", "3.01", "Service Requirement", "Part C")

    payload = {
        "schema_version": "aa-v1",
        "run_id": "test-run",
        "source_anchor": {"question_id": "src-1", "section_context": "Part A", "page": 1},
        "target_anchor": {"question_id": "tgt-1", "section_context": "Part C", "page": 3},
        "structure_analysis": {
            "question_alignment": {"value": False, "reasons": []},  # INVALID: no reasons when false
            "requires_definition": [],
            "election_dependency": {"status": "none", "evidence": []}
        },
        "option_mappings": [],
        "value_alignment": {
            "source_selected": [],
            "target_selected": [],
            "compatible": False,
            "justification": None
        },
        "classification": {
            "match_type": "abstain",
            "impact": "low",
            "confidence_level": "Low",
            "confidence_rationale": "Administrative vs design provision",
            "abstain_reasons": ["topic_mismatch"]
        },
        "consistency_checks": {
            "exact_requires_none_impact": "passed",
            "incompatible_requires_non_none_impact": "passed",
            "abstain_requires_alignment_false_or_insufficient_context": "failed",
            "violations": []
        }
    }

    response = json.dumps(payload)
    mapping = mapper._parse_mapping(
        response,
        source=source,
        target=target,
        embedding_similarity=0.31,
        fallback_run_id="fallback-run"
    )

    # Should trigger fallback due to validation failure
    assert mapping.classification.match_type == MatchType.ABSTAIN
    assert mapping.classification.abstain_reasons == ["llm_failure"]
    assert "question_alignment.reasons is empty when alignment is false" in mapping.classification.confidence_rationale


def test_validation_rejects_exact_match_with_incompatible_relationship():
    """Parser should reject exact match that includes incompatible relationships."""
    mapper = AASemanticMapper(provider="openai")

    source = _make_text_election("src-1", "2.01", "Vesting Schedule", "Part B")
    target = _make_text_election("tgt-1", "2.02", "Vesting Options", "Part B")

    payload = {
        "schema_version": "aa-v1",
        "run_id": "test-run",
        "source_anchor": {"question_id": "src-1", "section_context": "Part B", "page": 2},
        "target_anchor": {"question_id": "tgt-1", "section_context": "Part B", "page": 2},
        "structure_analysis": {
            "question_alignment": {"value": True, "reasons": []},
            "requires_definition": [],
            "election_dependency": {"status": "none", "evidence": []}
        },
        "option_mappings": [
            {
                "source_option": {"label": "a", "text": "Immediate", "is_selected": True, "fill_ins": []},
                "target_option": {"label": "1", "text": "Cliff 3-year", "is_selected": False, "fill_ins": []},
                "relationship": "incompatible",  # INVALID: exact match can't have incompatible
                "notes": "Different vesting schedules"
            }
        ],
        "value_alignment": {
            "source_selected": ["a"],
            "target_selected": [],
            "compatible": True,
            "justification": None
        },
        "classification": {
            "match_type": "exact",  # INVALID: claims exact but has incompatible option
            "impact": "none",
            "confidence_level": "High",
            "confidence_rationale": "Perfect alignment",
            "abstain_reasons": []
        },
        "consistency_checks": {
            "exact_requires_none_impact": "failed",
            "incompatible_requires_non_none_impact": "failed",
            "abstain_requires_alignment_false_or_insufficient_context": "passed",
            "violations": ["exact declared but option relationships conflict"]
        }
    }

    response = json.dumps(payload)
    mapping = mapper._parse_mapping(
        response,
        source=source,
        target=target,
        embedding_similarity=0.88,
        fallback_run_id="fallback-run"
    )

    # Should trigger fallback due to validation failure
    assert mapping.classification.match_type == MatchType.ABSTAIN
    assert mapping.classification.abstain_reasons == ["llm_failure"]
    assert "exact match has incompatible relationship" in mapping.classification.confidence_rationale


def test_validation_rejects_incompatible_with_impact_none():
    """Parser should reject incompatible relationship with impact=none."""
    mapper = AASemanticMapper(provider="openai")

    source = _make_text_election("src-1", "4.01", "Distribution Rules", "Part D")
    target = _make_text_election("tgt-1", "4.01", "Distribution Options", "Part D")

    payload = {
        "schema_version": "aa-v1",
        "run_id": "test-run",
        "source_anchor": {"question_id": "src-1", "section_context": "Part D", "page": 4},
        "target_anchor": {"question_id": "tgt-1", "section_context": "Part D", "page": 4},
        "structure_analysis": {
            "question_alignment": {"value": True, "reasons": []},
            "requires_definition": [],
            "election_dependency": {"status": "none", "evidence": []}
        },
        "option_mappings": [
            {
                "source_option": {"label": "a", "text": "Hardship only", "is_selected": True, "fill_ins": []},
                "target_option": {"label": "1", "text": "Unrestricted", "is_selected": False, "fill_ins": []},
                "relationship": "incompatible",  # Incompatible present
                "notes": "Source restricts, target allows unrestricted"
            }
        ],
        "value_alignment": {
            "source_selected": ["a"],
            "target_selected": [],
            "compatible": False,
            "justification": "Incompatible distribution rules"
        },
        "classification": {
            "match_type": "compatible",
            "impact": "none",  # INVALID: incompatible relationship but impact=none
            "confidence_level": "Medium",
            "confidence_rationale": "Options differ substantively",
            "abstain_reasons": []
        },
        "consistency_checks": {
            "exact_requires_none_impact": "passed",
            "incompatible_requires_non_none_impact": "failed",
            "abstain_requires_alignment_false_or_insufficient_context": "passed",
            "violations": ["impact should not be none when incompatible options exist"]
        }
    }

    response = json.dumps(payload)
    mapping = mapper._parse_mapping(
        response,
        source=source,
        target=target,
        embedding_similarity=0.79,
        fallback_run_id="fallback-run"
    )

    # Should trigger fallback due to validation failure
    assert mapping.classification.match_type == MatchType.ABSTAIN
    assert mapping.classification.abstain_reasons == ["llm_failure"]
    assert "incompatible relationship present but impact=none" in mapping.classification.confidence_rationale
