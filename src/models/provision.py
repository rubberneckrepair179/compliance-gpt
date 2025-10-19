"""
Provision Data Models

Pydantic models for plan document provisions based on /design/data_models/provision_model.md
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class ProvisionType(str, Enum):
    """Provision taxonomy - maps to common retirement plan provision categories."""

    ELIGIBILITY = "eligibility"
    COMPENSATION_DEFINITION = "compensation_definition"
    EMPLOYER_CONTRIBUTION = "employer_contribution"
    EMPLOYEE_DEFERRAL = "employee_deferral"
    VESTING_SCHEDULE = "vesting_schedule"
    DISTRIBUTION_TRIGGER = "distribution_trigger"
    LOAN_PROVISION = "loan_provision"
    HARDSHIP_WITHDRAWAL = "hardship_withdrawal"
    TOP_HEAVY = "top_heavy"
    COVERAGE_TESTING = "coverage_testing"
    FORFEITURE_USAGE = "forfeiture_usage"
    PLAN_YEAR = "plan_year"
    NORMAL_RETIREMENT_AGE = "normal_retirement_age"
    QACA_EACA = "QACA_EACA"
    OTHER = "other"


class ExtractionMethod(str, Enum):
    """How the provision text was extracted from the source document."""

    TEXT_API = "text_api"  # Standard PDF text extraction
    VISION_FALLBACK = "vision_fallback"  # Vision model (for locked PDFs)


class DocumentType(str, Enum):
    """Type of plan document."""

    BPD = "BPD"  # Basic Plan Document
    ADOPTION_AGREEMENT = "AdoptionAgreement"
    AMENDMENT = "Amendment"
    OPINION_LETTER = "OpinionLetter"
    SPD = "SPD"  # Summary Plan Description


class ExtractedEntities(BaseModel):
    """Structured entities extracted from provision text for faster comparison."""

    ages: List[float] = Field(default_factory=list, description="Age values (e.g., [21, 59.5, 65])")
    service_years: List[float] = Field(
        default_factory=list, description="Service requirements in years (e.g., [1.0, 0.5])"
    )
    percentages: List[float] = Field(
        default_factory=list,
        description="Percentages as decimals (e.g., [0.03, 1.00] for 3% and 100%)",
    )
    dollar_amounts: List[float] = Field(
        default_factory=list, description="Dollar amounts (e.g., [50000.00])"
    )
    dates: List[str] = Field(
        default_factory=list, description="Dates in YYYY-MM-DD format (e.g., ['2024-01-01'])"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Important terms (e.g., ['Safe Harbor', 'Highly Compensated Employee'])",
    )


class ProvisionMetadata(BaseModel):
    """Metadata about the source document and provision context."""

    vendor: Optional[str] = Field(
        None, description="Detected vendor: 'TPA Platform', 'Generic/Unknown', etc."
    )
    document_type: Optional[DocumentType] = Field(None, description="Type of source document")
    effective_date: Optional[str] = Field(None, description="Effective date (YYYY-MM-DD)")
    plan_name: Optional[str] = Field(None, description="Plan name from document")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Extensible key-value pairs"
    )


class Provision(BaseModel):
    """
    A provision is the atomic unit of plan document analysis.

    Represents a specific rule, definition, or election in a plan document
    (e.g., "Employees are eligible at age 21 and 1 year of service").
    """

    # Core identification
    provision_id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    document_id: str = Field(..., description="References source document")

    # Provision content
    provision_type: ProvisionType = Field(..., description="Category from taxonomy")
    section_reference: str = Field(
        ..., description="Section number/letter (e.g., 'Section 2.01', 'Article IV(A)')"
    )
    section_title: Optional[str] = Field(None, description="Section title if present")
    provision_text: str = Field(..., description="Full extracted text of provision")
    normalized_text: Optional[str] = Field(
        None, description="Optional cleaned/standardized version for comparison"
    )

    # Source traceability
    page_number: Optional[int] = Field(None, description="Page in source PDF")
    extraction_method: ExtractionMethod = Field(
        ..., description="How this provision was extracted"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="LLM confidence in extraction (0.0-1.0)"
    )

    # Metadata and entities
    metadata: ProvisionMetadata = Field(default_factory=ProvisionMetadata)
    extracted_entities: ExtractedEntities = Field(default_factory=ExtractedEntities)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence score is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return v

    def is_high_confidence(self, threshold: float = 0.9) -> bool:
        """Check if provision extraction is high confidence."""
        return self.confidence_score >= threshold

    def is_low_confidence(self, threshold: float = 0.7) -> bool:
        """Check if provision extraction is low confidence (requires review)."""
        return self.confidence_score < threshold

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
        use_enum_values = False


class Document(BaseModel):
    """Represents a plan document being analyzed."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Path to source file")
    document_type: Optional[DocumentType] = Field(None, description="Detected document type")
    vendor: Optional[str] = Field(None, description="Detected vendor")
    page_count: int = Field(..., description="Total pages in document")
    is_encrypted: bool = Field(default=False, description="Whether document is locked/encrypted")
    extraction_method: ExtractionMethod = Field(..., description="Extraction method used")

    # Metadata
    plan_name: Optional[str] = None
    effective_date: Optional[str] = None

    # Processing status
    provisions_extracted: int = Field(default=0, description="Number of provisions extracted")
    extraction_complete: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
