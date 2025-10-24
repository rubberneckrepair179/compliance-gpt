# Provisional Matching Model for Election-Dependent Provisions

## Overview

**The Problem:** Plan document provisions exist in three manifestations with different semantic completeness:

1. **BPD Template Provisions** - Legal structure with election placeholders (e.g., "as elected in AA")
2. **AA Election Specifications** - Available parameter choices for templates
3. **Merged Provisions** - Complete legal provisions with elections substituted

**The Insight** (per Sergio's observation, Oct 23, 2025):
> "We have matching at definition levels and rule levels, but to the extent that those provisions are election dependent, then they are provisional measures of rule 'template similarity', and (apologies to Magritte) **the template is not the instance.**"

This document defines a semantic matching model that recognizes template matches as **provisional** until election compatibility is validated.

---

## Requirements Addressed

- **REQ-021:** Semantic provision mapping (extended to handle provisional matches)
- **REQ-022:** Variance detection (must account for template vs instance differences)
- **REQ-024:** Confidence scoring (provisional matches scored differently than confirmed matches)

---

## Core Concept: Provisional Matching

### Definition

A **provisional match** is a semantic equivalence claim between two BPD template provisions that:
1. Have equivalent legal structure and framework
2. Reference elections for parameter values
3. **Cannot be confirmed without validating election compatibility**

### Example

**Source BPD (Relius):**
```
Section 3.01: An Employee shall be eligible to participate
after completing [as elected in Adoption Agreement Question 3.01]
of service.
```

**Target BPD (Ascensus):**
```
Section 1.7: Eligibility commences upon completion of the service
requirement specified in Adoption Agreement Section 4.02.
```

**Analysis:**
- ✅ **Template semantics match**: Both define eligibility based on service requirement
- ⚠️ **Match is provisional**: Depends on whether AA Q 3.01 options are compatible with AA Section 4.02 options
- ❓ **Confirmation required**: If AA crosswalk shows Q 3.01 ↔ Section 4.02 are compatible, template match is confirmed

---

## Three Levels of Semantic Matching

### Level 1: Template Matching (BPD ↔ BPD)

**What we compare:** Legal structure, rule definitions, with placeholders intact

**Match types:**
- **Standalone provision**: No election dependencies, can match definitively
  - Example: Definition of "Code" as "Internal Revenue Code of 1986"
- **Election-dependent provision**: Contains placeholders, match is **provisional**
  - Example: Eligibility rule referencing "as elected in AA"

**Output:**
```json
{
  "match_type": "PROVISIONAL_TEMPLATE_MATCH",
  "confidence": 0.92,
  "source_provision_id": "uuid-source",
  "target_provision_id": "uuid-target",
  "dependencies": {
    "source_election_refs": ["Q 3.01", "Q 3.02"],
    "target_election_refs": ["Section 4.02", "Section 4.03"]
  },
  "validation_status": "PENDING_ELECTION_RECONCILIATION",
  "reasoning": "Both provisions define eligibility based on service and age requirements, but actual values depend on elections."
}
```

### Level 2: Election Structure Matching (AA ↔ AA)

**What we compare:** Election question + available option sets (structure, not values)

**Match criteria:**
- Question semantic equivalence (both ask about same plan design concept)
- Option set compatibility (source options can map to target options)
- Preserves sponsor intent (elected value in source has equivalent in target)

**Output:**
```json
{
  "match_type": "ELECTION_STRUCTURE_MATCH",
  "confidence": 0.95,
  "source_election_id": "Q-3.01",
  "target_election_id": "Section-4.02",
  "option_mapping": [
    {"source": "a. 1 year", "target": "a. 12 months", "semantic_equivalence": 1.0},
    {"source": "b. 2 years", "target": "b. 24 months", "semantic_equivalence": 1.0},
    {"source": "c. Immediate", "target": "c. No requirement", "semantic_equivalence": 0.98}
  ],
  "validation_status": "CONFIRMED",
  "reasoning": "Election structures are compatible - all source options have semantic equivalents in target."
}
```

### Level 3: Instance Matching (Merged ↔ Merged)

**What we compare:** Complete provisions with elected values substituted

**Match criteria:**
- Legal effect equivalence
- Participant rights preservation
- Operational procedure alignment

**Output:**
```json
{
  "match_type": "CONFIRMED_INSTANCE_MATCH",
  "confidence": 0.98,
  "source_provision_id": "uuid-source-merged",
  "target_provision_id": "uuid-target-merged",
  "template_match_id": "uuid-template-match",
  "election_match_id": "uuid-election-match",
  "validation_status": "CONFIRMED",
  "reasoning": "Both provisions require 1 year of service for eligibility. Template match confirmed by election compatibility."
}
```

---

## Unified Provision Schema

Extends existing `provision_model.md` to support all three manifestations:

```json
{
  "id": "uuid",
  "provision_text": "Full text of provision",
  "section_context": "ARTICLE III - ELIGIBILITY (no section number)",
  "provision_type": "eligibility_rule | contribution_formula | definition | vesting_schedule | ...",

  "manifestation": {
    "type": "BPD_TEMPLATE | AA_ELECTION | MERGED_INSTANCE",

    "bpd_template": {
      "has_election_dependencies": true,
      "election_references": [
        {
          "placeholder_text": "as elected in Adoption Agreement Question 3.01",
          "referenced_section": "Q 3.01",
          "parameter_type": "service_requirement"
        }
      ],
      "standalone_semantic_completeness": 0.6
    },

    "aa_election": {
      "question_number": "3.01",
      "question_text": "Eligibility service requirement",
      "election_options": [
        {"id": "a", "description": "1 year of service", "value": "1 year"},
        {"id": "b", "description": "2 years of service", "value": "2 years"},
        {"id": "c", "description": "Immediate (no requirement)", "value": "0 years"}
      ],
      "elected_value": "a",
      "is_filled": true
    },

    "merged_instance": {
      "template_provision_id": "uuid-bpd-template",
      "election_values": [
        {
          "election_id": "Q-3.01",
          "elected_option": "a",
          "substituted_value": "1 year of service"
        }
      ],
      "merged_text": "An Employee shall be eligible to participate after completing 1 year of service.",
      "merge_timestamp": "2025-10-23T10:30:00Z"
    }
  },

  "semantic_fingerprint": {
    "clean_text": "eligibility participate employee service requirement plan entry",
    "provision_type_tags": ["eligibility", "service_based"],
    "regulatory_refs": ["IRC §410(a)", "Code §410(a)(1)(A)"],
    "structural_artifacts_removed": ["section_numbers", "question_numbers", "page_refs"]
  },

  "extraction_metadata": {
    "extraction_method": "vision | text_api",
    "model": "gpt-5-nano",
    "confidence": 0.95,
    "page_number": 42,
    "document_id": "uuid-source-bpd"
  }
}
```

---

## Semantic Fingerprinting Rules

### What to Include (Semantic Content)

1. **Legal concepts**: eligibility, vesting, contribution, distribution
2. **Regulatory references**: IRC sections, Code sections, ERISA sections
3. **Plan design terms**: safe harbor, QACA, EACA, top-heavy
4. **Section context** (heading text, not numbers): "ELIGIBILITY", "VESTING SCHEDULE"

### What to Exclude (Structural Artifacts)

1. **Section numbers**: "3.01", "Article IV", "Section 1.7"
2. **Question numbers**: "Q 3.01", "Question 4.02"
3. **Page references**: "See page 42", "as described in Section X"
4. **Vendor branding**: "©2020 Ascensus", "Relius"
5. **Formatting markers**: Headers, footers, "SAMPLE" watermarks

### Implementation

```python
def create_semantic_fingerprint(provision):
    """
    Strip structural artifacts, preserve semantic content.

    Implements "the template is not the instance" principle:
    - For BPD templates: Include placeholder TYPE ("service requirement")
      not placeholder TEXT ("as elected in AA Q 3.01")
    - For AA elections: Include question semantics ("service requirement")
      not question NUMBER ("3.01")
    - For merged instances: Include actual VALUES ("1 year")
    """
    text = provision.provision_text

    # Remove section/question numbers
    text = re.sub(r'\b(?:Section|Article|Question|Q\.?)\s+[\d.]+\b', '', text)

    # Remove page references
    text = re.sub(r'\b(?:page|pg\.?)\s+\d+\b', '', text, flags=re.IGNORECASE)

    # Remove vendor branding
    text = re.sub(r'©\s*\d{4}\s+\w+', '', text)

    # Keep section context (heading without number)
    if provision.section_context:
        # Strip "ARTICLE III -" but keep "ELIGIBILITY"
        context_semantic = re.sub(r'^(?:ARTICLE|SECTION)\s+[IVX\d.]+\s*[-–]\s*', '',
                                  provision.section_context)
        text = f"{context_semantic}: {text}"

    # For BPD templates: Replace election placeholders with parameter TYPE
    if provision.manifestation.type == "BPD_TEMPLATE":
        for ref in provision.manifestation.bpd_template.election_references:
            text = text.replace(ref.placeholder_text, f"[{ref.parameter_type}]")

    # Lowercase, dedupe whitespace
    text = ' '.join(text.lower().split())

    return text
```

---

## Match Validation Workflow

```
Step 1: BPD Template Crosswalk
├─ Extract all BPD provisions
├─ Generate semantic fingerprints (with parameter TYPES, not refs)
├─ Embedding-based candidate generation (≥70% similarity)
├─ LLM semantic verification
└─ Output: Provisional matches with election dependencies tracked

Step 2: AA Election Structure Crosswalk
├─ Extract all AA elections
├─ Generate semantic fingerprints (question semantics, not numbers)
├─ Embedding-based candidate generation
├─ LLM option compatibility verification
└─ Output: Election structure matches

Step 3: Confirm Provisional Matches
├─ For each provisional BPD match:
│   ├─ Check if all referenced elections have compatible mappings
│   ├─ If yes → CONFIRMED
│   ├─ If no → BLOCKED (flag for manual review)
│   └─ If partial → CONDITIONAL (some elections compatible, some not)
└─ Output: Confirmed template matches

Step 4: Generate Merged Instance Crosswalk (Optional - Post-MVP)
├─ Substitute elected values into BPD templates
├─ Compare merged provisions (full legal text)
├─ Validate legal equivalence
└─ Output: Instance-level variance report
```

---

## Confidence Scoring for Provisional Matches

### BPD Template Match Confidence

```python
def calculate_template_match_confidence(bpd_match):
    """
    Template match confidence is provisional until elections validated.
    """
    base_confidence = bpd_match.llm_similarity_score  # 0.0-1.0

    # Penalty for unresolved election dependencies
    election_dependency_penalty = 0.0
    if bpd_match.has_election_dependencies:
        if bpd_match.validation_status == "PENDING_ELECTION_RECONCILIATION":
            election_dependency_penalty = 0.15  # -15% for unconfirmed
        elif bpd_match.validation_status == "BLOCKED":
            election_dependency_penalty = 0.40  # -40% for incompatible elections

    provisional_confidence = base_confidence - election_dependency_penalty

    return {
        "confidence": provisional_confidence,
        "confidence_label": get_confidence_label(provisional_confidence),
        "is_provisional": bpd_match.has_election_dependencies,
        "validation_required": bpd_match.validation_status != "CONFIRMED"
    }
```

### Confidence Labels

- **90-100%**: High confidence (but may still be provisional)
- **70-89%**: Medium confidence
- **<70%**: Low confidence (abstain from match claim)
- **Provisional flag**: Shown alongside confidence if election validation pending

### CSV Output Format

```csv
Match Type,Confidence,Provisional,Source ID,Target ID,Validation Status,Reasoning
TEMPLATE_MATCH,92%,YES,uuid-src,uuid-tgt,PENDING_ELECTION,"Eligibility rules match structurally, pending AA Q3.01↔Sec4.02 validation"
TEMPLATE_MATCH,88%,NO,uuid-src2,uuid-tgt2,CONFIRMED,"Definition of 'Code' - standalone provision, no elections"
ELECTION_MATCH,95%,NO,Q-3.01,Sec-4.02,CONFIRMED,"Service requirement options are compatible (1yr↔12mo, 2yr↔24mo, immed↔none)"
INSTANCE_MATCH,98%,NO,uuid-mrg-src,uuid-mrg-tgt,CONFIRMED,"Both provisions require 1 year service. Template+election validated."
```

---

## Design Rationale

### Why Three Levels?

1. **Template matching** identifies corresponding legal frameworks across vendors
2. **Election matching** validates parameter compatibility
3. **Instance matching** confirms actual plan operation equivalence

Each level serves a purpose:
- **Template level**: Useful for understanding vendor document structure mapping
- **Election level**: Critical for cross-vendor conversions (different option presentations)
- **Instance level**: Final validation for client-specific plan comparison

### Why "Provisional" Terminology?

Alternative terms considered:
- "Partial match" - implies incompleteness, not dependency
- "Conditional match" - accurate but jargon-heavy
- "Template match" - doesn't convey the dependency concept
- **"Provisional match"** - ✅ Conveys temporary/pending status until validation

Sergio's phrasing: "provisional measures of rule template similarity" directly inspired this.

### Why Separate Semantic Fingerprints?

**Problem**: Including question numbers in embeddings causes false positives
- "Q 3.01: Age requirement" embedding ≈ "Q 3.01: State address" (due to "3.01" overlap)

**Solution**: Strip all structural identifiers, keep only semantic content
- "age requirement eligibility plan participation"
- "state mailing address employer location"
- Now embeddings correctly show low similarity

---

## Open Questions / Future Decisions

1. **Should we expose provisional matches to users in MVP?**
   - Pro: Transparency about validation status
   - Con: Adds complexity to UI/workflow
   - **Decision pending**: User testing needed

2. **What confidence threshold for provisional matches?**
   - Current: -15% penalty for provisional, -40% for blocked
   - **Decision pending**: Red Team Sprint validation

3. **Should we auto-generate merged instances, or require user to provide elected values?**
   - Auto-generate: Requires parsing AA elections correctly
   - User-provided: More accurate but manual effort
   - **Decision pending**: Post-MVP feature scope

4. **How to handle partially-compatible election sets?**
   - Example: Source has options {A, B, C}, Target has {A, B, D}
   - If elected value is A or B → confirmed
   - If elected value is C → blocked
   - **Decision**: Mark as CONDITIONAL, require manual review for option C

---

## Integration with Existing Design

### Updates Required to `provision_model.md`

- Add `manifestation` object (BPD_TEMPLATE | AA_ELECTION | MERGED_INSTANCE)
- Add `semantic_fingerprint` object
- Add `election_references` array for BPD templates

### Updates Required to `mapping_model.md`

- Add `match_type` enum (TEMPLATE | ELECTION | INSTANCE)
- Add `validation_status` enum (PENDING | CONFIRMED | BLOCKED | CONDITIONAL)
- Add `is_provisional` boolean flag
- Add `dependencies` object tracking election refs

### New Prompts Required

1. **BPD template extraction** - Must identify election placeholders and parameter types
2. **AA election extraction** - Must capture question semantics and option structure
3. **Election compatibility verification** - LLM prompt to compare option sets
4. **Provisional match confirmation** - Logic to check election crosswalk results

---

## Success Criteria

**For Red Team Sprint Validation:**

1. ✅ Semantic fingerprints exclude all structural artifacts (section/question numbers)
2. ✅ Unrelated provisions show <30% embedding similarity
3. ✅ Template matches correctly flagged as provisional when election-dependent
4. ✅ Standalone provisions (definitions, no elections) match with high confidence
5. ✅ Election structure matches validate option compatibility

**For MVP Deployment:**

1. ✅ Users understand distinction between provisional and confirmed matches
2. ✅ Confidence scores correlate with SME validation (90%+ scores = 90%+ accuracy)
3. ✅ Workflow supports: BPD crosswalk → AA crosswalk → confirmation step
4. ✅ CSV output clearly indicates validation status

---

## References

- `/design/data_models/provision_model.md` - Base provision schema
- `/design/data_models/mapping_model.md` - Semantic mapping model
- `/requirements/functional_requirements.md` - REQ-021, REQ-022, REQ-024
- Sergio's insight (Oct 23, 2025): "The template is not the instance"
- Market research example (p.3): Relius→ASC HCE safe harbor election missed

---

*Document Created: 2025-10-23*
*Author: Claude (with Sergio DuBois)*
*Status: Draft - pending Sergio's review and approval*
*Next Review: After Red Team Sprint extraction validation*
