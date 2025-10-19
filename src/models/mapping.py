"""
Provision Mapping Data Models

Models for semantic provision matching and variance detection.
Based on /design/data_models/mapping_model.md
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class VarianceType(str, Enum):
    """Classification of provision variance."""

    NONE = "none"  # Semantically identical
    ADMINISTRATIVE = "administrative"  # Wording/formatting only
    DESIGN = "design"  # Substantive change
    REGULATORY = "regulatory"  # Required by law


class ImpactLevel(str, Enum):
    """Impact level of detected variance."""

    NONE = "none"  # No impact
    LOW = "low"  # Minor, informational
    MEDIUM = "medium"  # Review recommended
    HIGH = "high"  # Critical, requires attention


class ProvisionMapping(BaseModel):
    """
    Represents a semantic mapping between source and target provisions.

    Links provisions across documents based on semantic similarity.
    """

    # Identification
    mapping_id: UUID = Field(default_factory=uuid4)
    source_provision_id: UUID = Field(..., description="Source provision UUID")
    target_provision_id: UUID = Field(..., description="Target provision UUID")

    # Matching scores
    embedding_similarity: float = Field(
        ..., ge=0.0, le=1.0, description="Cosine similarity of embeddings (0.0-1.0)"
    )
    llm_similarity: float = Field(
        ..., ge=0.0, le=1.0, description="LLM-assessed semantic similarity (0.0-1.0)"
    )
    is_match: bool = Field(..., description="LLM determination: are these the same provision?")

    # Variance analysis
    variance_type: VarianceType = Field(...)
    impact_level: ImpactLevel = Field(...)
    reasoning: str = Field(..., description="LLM explanation of similarity/variance")

    # Confidence
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="LLM confidence in mapping (0.0-1.0)"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_high_confidence(self, threshold: float = 0.9) -> bool:
        """Check if mapping is high confidence."""
        return self.confidence_score >= threshold

    def is_low_confidence(self, threshold: float = 0.7) -> bool:
        """Check if mapping is low confidence (requires review)."""
        return self.confidence_score < threshold

    def requires_review(self) -> bool:
        """Determine if this mapping requires human review."""
        return (
            self.is_low_confidence()
            or self.impact_level in [ImpactLevel.MEDIUM, ImpactLevel.HIGH]
            or self.variance_type in [VarianceType.DESIGN, VarianceType.REGULATORY]
        )

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
        use_enum_values = False


class MappingCandidate(BaseModel):
    """
    Candidate provision for semantic matching.

    Represents a potential match before LLM verification.
    """

    target_provision_id: UUID
    embedding_similarity: float = Field(ge=0.0, le=1.0)

    class Config:
        """Pydantic configuration."""

        json_encoders = {UUID: lambda v: str(v)}


class DocumentComparison(BaseModel):
    """
    Complete comparison result between two documents.

    Aggregates all provision mappings for a document pair.
    """

    comparison_id: UUID = Field(default_factory=uuid4)
    source_document_id: str
    target_document_id: str

    # Mappings
    mappings: List[ProvisionMapping] = Field(default_factory=list)

    # Statistics
    total_source_provisions: int
    total_target_provisions: int
    matched_provisions: int
    unmatched_source_provisions: int
    unmatched_target_provisions: int

    # Summary
    high_impact_variances: int = 0
    medium_impact_variances: int = 0
    low_impact_variances: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def completion_rate(self) -> float:
        """Calculate % of source provisions matched."""
        if self.total_source_provisions == 0:
            return 0.0
        return self.matched_provisions / self.total_source_provisions

    def requires_review_count(self) -> int:
        """Count mappings requiring human review."""
        return sum(1 for m in self.mappings if m.requires_review())

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
