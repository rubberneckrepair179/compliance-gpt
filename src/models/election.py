"""
Election data models using discriminated unions.

Implements the advisor's election model with kind-based discrimination.
Supports: text, single_select, multi_select election types.
"""

from typing import Literal, Optional, List, Union
from pydantic import BaseModel, Field


# ============================================================================
# PROVENANCE
# ============================================================================

class Provenance(BaseModel):
    """Source document location for auditability"""
    page: int = Field(..., description="Page number in source PDF")
    question_number: str = Field(..., description="Question number as appears in document")


# ============================================================================
# FILL-IN (Nested Elections within Options)
# ============================================================================

class FillIn(BaseModel):
    """
    Sub-election within an option (e.g., "Other (specify): _____")

    Currently simplified to text-only for POC.
    """
    id: str = Field(..., description="Unique identifier for fill-in")
    kind: Literal["text"] = Field(default="text", description="Fill-ins are always text for POC")
    question_text: str = Field(..., description="Label for the fill-in field")
    status: Literal["unanswered", "answered", "ambiguous", "conflict"] = Field(
        ..., description="Whether fill-in has a value"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    value: Optional[str] = Field(None, description="Text entered in fill-in, null if blank")


# ============================================================================
# OPTION (For single_select and multi_select)
# ============================================================================

class Option(BaseModel):
    """
    A selectable option within single_select or multi_select elections
    """
    option_id: str = Field(..., description="Unique identifier for this option")
    label: str = Field(..., description="Option label (a, b, c, etc.)")
    option_text: str = Field(..., description="Full text of the option")
    is_selected: bool = Field(..., description="Whether this option is marked/selected")
    fill_ins: List[FillIn] = Field(
        default_factory=list,
        description="Sub-fields within this option (e.g., 'Other: ____')"
    )


# ============================================================================
# ELECTION VALUE STRUCTURES (Discriminated by kind)
# ============================================================================

class TextValue(BaseModel):
    """Value structure for text elections"""
    value: Optional[str] = Field(None, description="Text entered, null if blank")


class SingleSelectValue(BaseModel):
    """Value structure for single_select elections"""
    option_id: Optional[str] = Field(None, description="ID of selected option, null if none")


class MultiSelectValue(BaseModel):
    """Value structure for multi_select elections"""
    option_ids: List[str] = Field(
        default_factory=list,
        description="Array of selected option IDs, empty if none"
    )


# ============================================================================
# BASE ELECTION
# ============================================================================

class BaseElection(BaseModel):
    """Common fields for all election types"""
    id: str = Field(..., description="Unique identifier (e.g., q2_03)")
    question_number: str = Field(..., description="Question number as in document (e.g., 2.03)")
    question_text: str = Field(..., description="Full question text")
    section_context: str = Field(..., description="Article/section header for context")
    status: Literal["unanswered", "answered", "ambiguous", "conflict"] = Field(
        ..., description="Election completion status"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    provenance: Provenance = Field(..., description="Source document location")


# ============================================================================
# DISCRIMINATED ELECTION TYPES
# ============================================================================

class TextElection(BaseElection):
    """Fill-in-the-blank, text entry, numeric entry without dropdowns"""
    kind: Literal["text"] = "text"
    value: Optional[str] = Field(None, description="Text entered, null if blank")


class SingleSelectElection(BaseElection):
    """Radio buttons, single-choice checkboxes"""
    kind: Literal["single_select"] = "single_select"
    value: SingleSelectValue = Field(..., description="Selected option")
    options: List[Option] = Field(..., description="Available options")


class MultiSelectElection(BaseElection):
    """Multiple checkboxes, check-all-that-apply"""
    kind: Literal["multi_select"] = "multi_select"
    value: MultiSelectValue = Field(..., description="Selected options")
    options: List[Option] = Field(..., description="Available options")


# ============================================================================
# UNION TYPE
# ============================================================================

Election = Union[TextElection, SingleSelectElection, MultiSelectElection]

# Pydantic v2: use Field discriminator
# This enables proper parsing based on "kind" field
Election = Union[
    TextElection,
    SingleSelectElection,
    MultiSelectElection
]


# ============================================================================
# CONTAINER
# ============================================================================

class ElectionPage(BaseModel):
    """
    Container for elections extracted from a single AA page
    """
    elections: List[Election] = Field(..., description="Elections on this page")

    class Config:
        # Enable discriminated union parsing in Pydantic v2
        # The "kind" field determines which Election subtype to use
        use_enum_values = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_text_election(
    id: str,
    question_number: str,
    question_text: str,
    section_context: str,
    status: Literal["unanswered", "answered", "ambiguous", "conflict"],
    confidence: float,
    page: int,
    value: Optional[str] = None
) -> TextElection:
    """Factory function for text elections"""
    return TextElection(
        id=id,
        kind="text",
        question_number=question_number,
        question_text=question_text,
        section_context=section_context,
        status=status,
        confidence=confidence,
        provenance=Provenance(page=page, question_number=question_number),
        value=value
    )


def create_single_select_election(
    id: str,
    question_number: str,
    question_text: str,
    section_context: str,
    status: Literal["unanswered", "answered", "ambiguous", "conflict"],
    confidence: float,
    page: int,
    options: List[Option],
    selected_option_id: Optional[str] = None
) -> SingleSelectElection:
    """Factory function for single_select elections"""
    return SingleSelectElection(
        id=id,
        kind="single_select",
        question_number=question_number,
        question_text=question_text,
        section_context=section_context,
        status=status,
        confidence=confidence,
        provenance=Provenance(page=page, question_number=question_number),
        value=SingleSelectValue(option_id=selected_option_id),
        options=options
    )


def create_multi_select_election(
    id: str,
    question_number: str,
    question_text: str,
    section_context: str,
    status: Literal["unanswered", "answered", "ambiguous", "conflict"],
    confidence: float,
    page: int,
    options: List[Option],
    selected_option_ids: Optional[List[str]] = None
) -> MultiSelectElection:
    """Factory function for multi_select elections"""
    return MultiSelectElection(
        id=id,
        kind="multi_select",
        question_number=question_number,
        question_text=question_text,
        section_context=section_context,
        status=status,
        confidence=confidence,
        provenance=Provenance(page=page, question_number=question_number),
        value=MultiSelectValue(option_ids=selected_option_ids or []),
        options=options
    )
