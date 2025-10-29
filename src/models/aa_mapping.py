"""AA Election Mapping Data Models.

Defines structured outputs for Adoption Agreement election semantic mapping
as specified in design/reconciliation/aa_mapping.md.
"""

from datetime import datetime
from enum import Enum
from typing import Any, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.mapping import ConfidenceLevel, ImpactLevel


class OptionRelationship(str, Enum):
    """Relationship between source and target election options."""

    EXACT = "exact"
    COMPATIBLE = "compatible"
    PARTIAL = "partial"
    MISSING = "missing"
    INCOMPATIBLE = "incompatible"


class MatchType(str, Enum):
    """Overall classification for an election pair."""

    EXACT = "exact"
    COMPATIBLE = "compatible"
    CONDITIONAL = "conditional"
    NO_MATCH = "no_match"
    ABSTAIN = "abstain"


class QuestionAlignment(BaseModel):
    """Topic alignment assessment."""

    value: bool
    reasons: List[str] = Field(default_factory=list)


class ElectionDependency(BaseModel):
    """Election dependency metadata."""

    status: str = Field(default="none", description="none|source_only|target_only|both")
    evidence: List[str] = Field(default_factory=list)


class StructureAnalysis(BaseModel):
    """Analysis of question structure before option comparison."""

    question_alignment: QuestionAlignment
    requires_definition: List[str] = Field(default_factory=list)
    election_dependency: ElectionDependency = Field(default_factory=ElectionDependency)


class OptionDescriptor(BaseModel):
    """Normalized representation of an election option for reporting."""

    label: Optional[str] = None
    text: str
    is_selected: Optional[bool] = None
    fill_ins: List[Any] = Field(default_factory=list)


class OptionMapping(BaseModel):
    """Mapping between a source option and target counterpart."""

    source: OptionDescriptor
    target: Optional[OptionDescriptor] = None
    relationship: OptionRelationship
    notes: Optional[str] = None


class ValueAlignment(BaseModel):
    """Comparison of selected values for the election."""

    source_selected: List[Any] = Field(default_factory=list)
    target_selected: List[Any] = Field(default_factory=list)
    compatible: bool = False
    justification: Optional[str] = None


class Classification(BaseModel):
    """Final classification and confidence metadata."""

    match_type: MatchType
    impact: ImpactLevel = ImpactLevel.NONE
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    confidence_rationale: str
    abstain_reasons: List[str] = Field(default_factory=list)


class ElectionAnchor(BaseModel):
    """Anchor metadata for locating an election within a document."""

    question_id: str
    section_context: Optional[str] = None
    page: Optional[int] = None


class ConsistencyChecks(BaseModel):
    """Structured consistency check outcomes returned by the LLM."""

    exact_requires_none_impact: Literal["passed", "failed"] = "passed"
    incompatible_requires_non_none_impact: Literal["passed", "failed"] = "passed"
    abstain_requires_alignment_false_or_insufficient_context: Literal["passed", "failed"] = "passed"
    violations: List[str] = Field(default_factory=list)


class AAElectionMapping(BaseModel):
    """Semantic mapping between Adoption Agreement elections."""

    mapping_id: UUID = Field(default_factory=uuid4)
    schema_version: str = Field(default="aa-v1")
    run_id: Optional[str] = None

    source_election_id: str
    target_election_id: str
    source_anchor: ElectionAnchor
    target_anchor: ElectionAnchor

    structure_analysis: StructureAnalysis
    option_mappings: List[OptionMapping] = Field(default_factory=list)
    value_alignment: ValueAlignment = Field(default_factory=ValueAlignment)
    classification: Classification
    consistency_checks: ConsistencyChecks = Field(default_factory=ConsistencyChecks)

    embedding_similarity: float = Field(ge=0.0, le=1.0)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    def match_decision(self) -> bool:
        """Determine whether this mapping counts as a match."""

        if self.classification.match_type in (MatchType.EXACT, MatchType.COMPATIBLE, MatchType.CONDITIONAL):
            return True
        return False


class AAComparison(BaseModel):
    """Aggregate comparison result for a pair of AA documents."""

    comparison_id: UUID = Field(default_factory=uuid4)
    source_document_id: str
    target_document_id: str
    mappings: List[AAElectionMapping] = Field(default_factory=list)

    total_source_elections: int = 0
    total_target_elections: int = 0
    matched_elections: int = 0
    unmatched_source_elections: int = 0
    unmatched_target_elections: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def match_rate(self) -> float:
        if self.total_source_elections == 0:
            return 0.0
        return self.matched_elections / self.total_source_elections
