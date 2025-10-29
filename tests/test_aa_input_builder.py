"""
Unit tests for AA Input Builder

Tests the AA election semantic mapping input payload assembly.
"""

import json
import pytest
from uuid import uuid4

from src.mapping.aa_input_builder import (
    build_aa_input,
    build_section_hierarchy,
    normalize_option_label,
    build_election_fingerprint,
    serialize_option,
)
from src.models.election import (
    TextElection,
    SingleSelectElection,
    MultiSelectElection,
    Option,
    FillIn,
    Provenance,
    SingleSelectValue,
    MultiSelectValue,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_text_election():
    """Sample text election for testing."""
    return TextElection(
        id="q1_01",
        question_number="1.01",
        question_text="Enter plan name",
        section_context="Part A - Plan Information",
        status="answered",
        confidence=1.0,
        provenance=Provenance(page=1, question_number="1.01"),
        value="ABC Company 401(k) Plan",
    )


@pytest.fixture
def sample_single_select_election():
    """Sample single-select election for testing."""
    return SingleSelectElection(
        id="q2_03",
        question_number="2.03",
        question_text="Entry date timing",
        section_context="Part B - Eligibility",
        status="answered",
        confidence=0.98,
        provenance=Provenance(page=3, question_number="2.03"),
        value=SingleSelectValue(option_id="opt_a"),
        options=[
            Option(
                option_id="opt_a",
                label="a",
                option_text="Immediate (first of month after satisfaction)",
                is_selected=True,
                fill_ins=[],
            ),
            Option(
                option_id="opt_b",
                label="b",
                option_text="Quarterly (Jan 1, Apr 1, Jul 1, Oct 1)",
                is_selected=False,
                fill_ins=[],
            ),
        ],
    )


@pytest.fixture
def sample_multi_select_election():
    """Sample multi-select election with fill-ins for testing."""
    return MultiSelectElection(
        id="q3_05",
        question_number="3.05",
        question_text="Excluded employee classes (check all that apply)",
        section_context="Part C - Coverage",
        status="answered",
        confidence=0.95,
        provenance=Provenance(page=5, question_number="3.05"),
        value=MultiSelectValue(option_ids=["opt_a", "opt_c"]),
        options=[
            Option(
                option_id="opt_a",
                label="a",
                option_text="Union employees",
                is_selected=True,
                fill_ins=[],
            ),
            Option(
                option_id="opt_b",
                label="b",
                option_text="Leased employees",
                is_selected=False,
                fill_ins=[],
            ),
            Option(
                option_id="opt_c",
                label="c",
                option_text="Other (specify)",
                is_selected=True,
                fill_ins=[
                    FillIn(
                        id="fill_c1",
                        kind="text",
                        question_text="Specify excluded class",
                        status="answered",
                        confidence=0.90,
                        value="Seasonal employees",
                    )
                ],
            ),
        ],
    )


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

def test_build_section_hierarchy():
    """Test section hierarchy builder."""
    elections = [
        TextElection(
            id="q1_01",
            question_number="1.01",
            question_text="Plan name",
            section_context="Part A - Plan Information",
            status="answered",
            confidence=1.0,
            provenance=Provenance(page=1, question_number="1.01"),
            value="Test Plan",
        ),
        TextElection(
            id="q2_01",
            question_number="2.01",
            question_text="Eligibility age",
            section_context="Part B - Eligibility",
            status="answered",
            confidence=1.0,
            provenance=Provenance(page=3, question_number="2.01"),
            value="21",
        ),
    ]

    hierarchy = build_section_hierarchy(elections)

    assert len(hierarchy) == 2
    assert hierarchy["1.01"] == "Part A - Plan Information"
    assert hierarchy["2.01"] == "Part B - Eligibility"


def test_normalize_option_label():
    """Test option label normalization."""
    assert normalize_option_label("a.") == "a"
    assert normalize_option_label("(a)") == "a"
    assert normalize_option_label("a)") == "a"
    assert normalize_option_label("A") == "a"
    assert normalize_option_label("  b.  ") == "b"
    assert normalize_option_label("(1)") == "1"


def test_build_election_fingerprint_text(sample_text_election):
    """Test fingerprint generation for text election."""
    fingerprint = build_election_fingerprint(sample_text_election)

    assert "Part A - Plan Information" in fingerprint
    assert "Enter plan name" in fingerprint
    # Should not include question numbers, page numbers, or values
    assert "1.01" not in fingerprint
    assert "ABC Company" not in fingerprint


def test_build_election_fingerprint_single_select(sample_single_select_election):
    """Test fingerprint generation for single-select election."""
    fingerprint = build_election_fingerprint(sample_single_select_election)

    assert "Part B - Eligibility" in fingerprint
    assert "Entry date timing" in fingerprint
    assert "Immediate" in fingerprint
    assert "Quarterly" in fingerprint
    # Should not include labels or IDs
    assert "opt_a" not in fingerprint


def test_build_election_fingerprint_multi_select(sample_multi_select_election):
    """Test fingerprint generation for multi-select election."""
    fingerprint = build_election_fingerprint(sample_multi_select_election)

    assert "Part C - Coverage" in fingerprint
    assert "Excluded employee classes" in fingerprint
    assert "Union employees" in fingerprint
    assert "Other (specify)" in fingerprint


def test_serialize_option():
    """Test option serialization."""
    option = Option(
        option_id="opt_a",
        label="a",
        option_text="Test option",
        is_selected=True,
        fill_ins=[
            FillIn(
                id="fill_1",
                kind="text",
                question_text="Specify",
                status="answered",
                confidence=0.95,
                value="Test value",
            )
        ],
    )

    serialized = serialize_option(option)

    assert serialized["label"] == "a"
    assert serialized["text"] == "Test option"
    assert serialized["is_selected"] is True
    assert len(serialized["fill_ins"]) == 1
    assert serialized["fill_ins"][0]["id"] == "fill_1"
    assert serialized["fill_ins"][0]["value"] == "Test value"


# ============================================================================
# FULL PAYLOAD TESTS
# ============================================================================

def test_build_aa_input_text_election(sample_text_election):
    """Test payload assembly for text elections."""
    run_id = str(uuid4())
    hierarchy = {"1.01": "Part A - Plan Information"}

    payload = build_aa_input(
        source_election=sample_text_election,
        target_election=sample_text_election,
        candidate_rank=1,
        run_id=run_id,
        section_hierarchy=hierarchy,
    )

    # Verify structure
    assert payload["run_id"] == run_id
    assert "source" in payload
    assert "target" in payload
    assert "context" in payload

    # Verify source election data
    source = payload["source"]
    assert source["question_id"] == "q1_01"
    assert source["question_number"] == "1.01"
    assert source["question_text"] == "Enter plan name"
    assert source["section_context"] == "Part A - Plan Information"
    assert source["status"] == "answered"
    assert source["kind"] == "text"
    assert source["value"] == "ABC Company 401(k) Plan"
    assert source["options"] == []

    # Verify provenance
    assert source["provenance"]["page"] == 1
    assert source["provenance"]["question_number"] == "1.01"

    # Verify context
    context = payload["context"]
    assert context["section_hierarchy"] == hierarchy
    assert context["stage1"]["candidate_rank"] == 1
    assert context["stage1"]["notes"] == "top-k from embeddings"


def test_build_aa_input_single_select(sample_single_select_election):
    """Test payload assembly for single-select elections."""
    run_id = str(uuid4())
    hierarchy = {"2.03": "Part B - Eligibility"}

    payload = build_aa_input(
        source_election=sample_single_select_election,
        target_election=sample_single_select_election,
        candidate_rank=2,
        run_id=run_id,
        section_hierarchy=hierarchy,
    )

    source = payload["source"]
    assert source["kind"] == "single_select"
    assert source["value"]["option_id"] == "opt_a"
    assert len(source["options"]) == 2

    # Verify option structure
    opt_a = source["options"][0]
    assert opt_a["label"] == "a"
    assert opt_a["text"] == "Immediate (first of month after satisfaction)"
    assert opt_a["is_selected"] is True
    assert opt_a["fill_ins"] == []


def test_build_aa_input_multi_select(sample_multi_select_election):
    """Test payload assembly for multi-select elections with fill-ins."""
    run_id = str(uuid4())
    hierarchy = {"3.05": "Part C - Coverage"}

    payload = build_aa_input(
        source_election=sample_multi_select_election,
        target_election=sample_multi_select_election,
        candidate_rank=3,
        run_id=run_id,
        section_hierarchy=hierarchy,
    )

    source = payload["source"]
    assert source["kind"] == "multi_select"
    assert set(source["value"]["option_ids"]) == {"opt_a", "opt_c"}
    assert len(source["options"]) == 3

    # Verify option with fill-in
    opt_c = source["options"][2]
    assert opt_c["label"] == "c"
    assert opt_c["is_selected"] is True
    assert len(opt_c["fill_ins"]) == 1

    fill_in = opt_c["fill_ins"][0]
    assert fill_in["id"] == "fill_c1"
    assert fill_in["question_text"] == "Specify excluded class"
    assert fill_in["status"] == "answered"
    assert fill_in["value"] == "Seasonal employees"


def test_json_serialization(sample_single_select_election):
    """Test that payload is JSON-serializable."""
    run_id = str(uuid4())
    hierarchy = {"2.03": "Part B - Eligibility"}

    payload = build_aa_input(
        source_election=sample_single_select_election,
        target_election=sample_single_select_election,
        candidate_rank=1,
        run_id=run_id,
        section_hierarchy=hierarchy,
    )

    # Should not raise an exception
    json_str = json.dumps(payload, indent=2)
    assert json_str is not None

    # Should be able to parse back
    parsed = json.loads(json_str)
    assert parsed["run_id"] == run_id
    assert parsed["source"]["kind"] == "single_select"


def test_different_source_target_elections(sample_text_election, sample_single_select_election):
    """Test payload with different source and target elections."""
    run_id = str(uuid4())
    hierarchy = {
        "1.01": "Part A - Plan Information",
        "2.03": "Part B - Eligibility",
    }

    payload = build_aa_input(
        source_election=sample_text_election,
        target_election=sample_single_select_election,
        candidate_rank=2,
        run_id=run_id,
        section_hierarchy=hierarchy,
    )

    # Verify different types
    assert payload["source"]["kind"] == "text"
    assert payload["target"]["kind"] == "single_select"

    # Verify different question numbers
    assert payload["source"]["question_number"] == "1.01"
    assert payload["target"]["question_number"] == "2.03"
