# AA Election Crosswalk Specification (Sprint 2 Scope)

**Status:** Implemented (Sprint 2)  
**Date:** 2025-10-29  
**Author:** Codex  
**Scope:** Define the architecture, data structures, and test strategy for Adoption Agreement (AA) election-to-election semantic mapping. Targets Sprint 2 backlog.

---

## 0. Objectives

1. Produce a deterministic crosswalk between source and target AA election questions.
2. Support option-level alignment (single-select, multi-select, fill-ins) and highlight incompatibilities.
3. Generate artifacts consumable by BPD provisional matches (Level 2 of the provisional matching model).
4. Maintain parity with the v3 BPD mapping patterns (structured output, categorical confidence).

Deliverables (Sprint 2) — **Status: Complete**

- ✅ AA mapping prompt & builder (mirrors BPD v3 approach)  
- ✅ `src/mapping/aa_semantic_mapper.py` upgraded for structured output  
- ✅ CLI runner (`scripts/run_aa_crosswalk.py`) producing JSON/CSV  
- ✅ Unit tests validating parsing, candidate ranking, and fallback logic (`tests/test_aa_semantic_mapper.py`)  
- ✅ Documentation & pipeline updates

---

## 1. Input & Context Assembly

### 1.1 Election Data Sources

- **Source:** `test_data/extracted_vision_v6/relius_aa_elections_final.json`
- **Target:** `test_data/extracted_vision_v6/ascensus_aa_elections_final.json`
- **Model:** `Election` discriminated unions defined in `src/models/election.py`

### 1.2 Election Fingerprints (Stage 1)

Purpose: produce embeddings for fast candidate filtering (top-k).

```
def build_election_fingerprint(election: Election) -> str:
    # Include question text, section context, normalized option text (omit IDs)
    # Exclude question numbers, page numbers, vendor boilerplate
```

### 1.3 v3-style Input Payload

Borrow from BPD builder but adapt to election semantics:

```python
def build_aa_input(
    source_election: Election,
    target_election: Election,
    *,
    candidate_rank: int,
    run_id: str,
    section_hierarchy: Dict[str, str],  # map question_number -> article/section
) -> Dict[str, Any]:
    """
    Required fields:
      - question metadata (number, section context, page)
      - option sets (normalized labels, fill-ins)
      - election status/value (answered/unanswered/ambiguous)
      - stage1 info (candidate rank, notes)
    """
```

Additional context:
- `section_hierarchy`: derived from AA structure to supply topical hints (e.g., “Part A – Employer Information”).
- Known elections (from future merger) not required Sprint 2.

### 1.4 Election Schema Contract

The AA mapper consumes the discriminated-union models defined in `src/models/election.py`. Every election record provided to `AASemanticMapper.compare_documents()` MUST satisfy the following:

- `id`: Stable identifier (`{vendor}_{doc_type}_p{page}_{section_hint}`) used for join keys throughout the mapper.
- `kind`: Literal `"text"`, `"single_select"`, or `"multi_select"` – drives union parsing.
- `question_number`: Human-readable anchor from the AA (e.g., `2.03`, `Entry Date`).
- `question_text`: Full prompt text presented to the sponsor.
- `section_context`: Heading or article title for semantic fingerprinting.
- `status`: One of `unanswered | answered | ambiguous | conflict`; informs default compatibility logic.
- `confidence`: Float 0.0–1.0 (default 1.0 when inferred deterministically).
- `provenance`: `{page, question_number}` for audit links back to the PDF.
- Value payload:
  - `text` → `value: str | None`
  - `single_select` → `value: {"option_id": str | None}`
  - `multi_select` → `value: {"option_ids": list[str]}`
- Options (`single_select`/`multi_select` only):
  - Deterministic `option_id` (`{election_id}_opt_{label}`).
  - Raw `label` (a, b, c, …) and `option_text`.
  - `is_selected`: Mirrors selection status.
  - Optional `fill_ins`: Each entry conforms to `FillIn` model (`id`, `question_text`, `status`, `confidence`, `value`).

Reference test coverage: `tests/test_aa_input_builder.py::test_build_aa_input_*` exercises the required shapes for each election kind.

---

## 2. LLM Prompt & Output Schema

### 2.1 Prompt Goals

1. Determine if two election questions capture the same plan design decision.
2. Align option sets, including nested fill-ins.
3. Identify design incompatibilities (missing option, divergent semantics).
4. Provide actionable classification (match, needs manual mapping, no match).

### 2.2 Output Schema (v1)

```json
{
  "schema_version": "aa-v1",
  "run_id": "...",
  "source_anchor": {"question_id": "...", "page": 5, "section_context": "..."},
  "target_anchor": {"question_id": "...", "page": 7, "section_context": "..."},

  "structure_analysis": {
    "question_alignment": {"value": true, "reasons": ["both employer eligibility"]},
    "requires_definition": ["Highly Compensated Employee"],
    "election_dependency": {"status": "none|source_only|target_only|both", "evidence": []}
  },

  "option_mappings": [
    {
      "source_option": {"label": "a", "text": "...", "requires_fill": false},
      "target_option": {"label": "1", "text": "..."},
      "relationship": "exact|compatible|partial|missing",
      "notes": "Explain any nuance"
    }
  ],

  "value_alignment": {
    "source_selected": ["a"],
    "target_selected": ["1"],
    "compatible": true,
    "justification": "Both elect immediate eligibility."
  },

  "classification": {
    "match_type": "exact|compatible|conditional|no_match|abstain",
    "impact": "none|low|medium|high",
    "confidence": "High|Medium|Low",
    "confidence_rationale": "Short explanation",
    "abstain_reasons": []
  },

  "consistency_checks": [
    "If match_type='exact' then impact must be 'none'"
  ]
}
```

### 2.3 Prompt Content (Ready for implementation)

**System message**

```
You are an ERISA compliance specialist evaluating Adoption Agreement elections. Compare the source and target questions and return ONLY a JSON object that strictly matches the provided schema. Do not add commentary, markdown, or extra keys.
```

**User message template**

```
Please analyse the following Adoption Agreement elections and populate the JSON schema exactly as specified.

<PAYLOAD_JSON>

Instructions:
1. Confirm the questions address the same plan design topic.
2. Align available options; mark relationship as:
   - "exact": same meaning (label text differences allowed)
   - "compatible": different phrasing but meaning equivalent
   - "partial": overlaps but one side contains extra substantive options
   - "missing": source option lacks counterpart in target
   - "incompatible": meanings conflict
3. Assess selected values (if answered) and whether they are compatible.
4. Classify match_type:
   - "exact": structure and values align
   - "compatible": differences exist but sponsor intent preserved with notes
   - "conditional": match depends on additional elections or definitions
   - "no_match": different topics or incompatible structures
   - "abstain": insufficient information (e.g., election dependency unresolved)
5. Set impact:
   - "none": administrative only
   - "low": minor review needed (e.g., missing optional choice)
   - "medium": operational significance (affects processes, not core rights)
   - "high": impacts participant rights, compliance, or funding
6. Use confidence levels {High, Medium, Low}. Prefer "Low" when abstaining.
7. Keep evidence spans ≤12 words and quote verbatim.

Return only the JSON object. Omit comments and trailing commas.

---

## 3. Prompt v1.1 Enhancements (Planned)

The baseline AA crosswalk run (`5d5c98de-595c-4b0e-a5bd-1a6cd1586d01`) exposed that the v1 prompt allows abstentions without meaningful reasoning. The v1.1 revision MUST add the following constraints:

### 3.1 Mandatory reasoning output
- When `match_type="abstain"`, the model MUST supply a non-empty `confidence_rationale`.
- `abstain_reasons` must contain ≥1 item, drawn from an enumerated set (`topic_mismatch`, `missing_option`, `insufficient_context`, `structural_conflict`, `llm_failure`, etc.).
- When `question_alignment.value=false`, the `reasons` array must list ≤3 concise bullets explaining the divergence.

### 3.2 Topic alignment guidance
- Clarify that administrative fields (e.g., contact information) should abstain when compared to design provisions, while regulatory equivalents (e.g., “QACA vesting” vs “QACA ACP vesting”) should be evaluated for compatibility.
- Encourage classification as `compatible` or `conditional` when the design intent can be preserved with explanatory notes.

### 3.3 Option mapping expectations
- Require `option_mappings` to highlight missing or incompatible options even in abstain scenarios and cover every substantive option (single- and multi-select).
- Provide inline schema comments showing how to flag missing target options and partial overlaps.

### 3.4 Few-shot coverage
- Add examples illustrating:
  1. Cross-vendor exact match with differing option labels.
  2. Cross-vendor compatible match that needs reviewer notes.
  3. Legitimate abstain, with populated reasoning fields and option commentary.
  4. Conditional match driven by an unresolved election dependency.
  5. Multi-select overlap where additional selections do not break compatibility.
  6. Topic-aligned but value-conflicting pair that should result in `match_type="no_match"`.

### 3.5 Output schema reminders
- Embed inline comments to reinforce non-empty constraints (e.g., `// REQUIRED: non-empty string`).
- Remind the model that `confidence_level="Low"` is acceptable only when the rationale documents the uncertainty.
- Add cross-field rules (e.g., alignment false ⇒ abstain; incompatible ⇒ non-none impact; exact ⇒ no partial/missing/incompatible).
- Consistency checks now return a structured object:
  ```json
  {
    "exact_requires_none_impact": "passed|failed",
    "incompatible_requires_non_none_impact": "passed|failed",
    "abstain_requires_alignment_false_or_insufficient_context": "passed|failed",
    "violations": []
  }
  ```
  Downstream schema must accept this shape (`ConsistencyChecks` model).

Implementation of these prompt changes is assigned to Claude once spec finalization is complete.

---

## 6. Data Conversion (v6 Extraction → Election Schema)

The production extractions in `test_data/extracted_vision_v6/*_aa_elections_final.json` preserve page-level provision metadata. Before the AA mapper can operate, these records must be transformed into the `Election` schema described in §1.4. The conversion pipeline should implement the following stages:

1. **Identify question anchors**
   - Treat any node with a `selection_field.kind` (`"single_select"` or `"multi_select"`) or a `text_field` and no `parent_section` as a top-level election.
   - Ignore structural headings with neither field; they serve purely as section context.

2. **Assemble election metadata**
   - `id`: reuse the existing `id` (already deterministic).
   - `question_number`: prefer `section_number`; fall back to `id` if blank.
   - `question_text`: use `provision_text`; if empty, fall back to `section_title`.
   - `section_context`: locate the nearest ancestor node with a non-empty `section_title`; if none, synthesize from the parent `section_number`.
   - `status`: derive from field payloads — `answered` when a selection/text value is present, `unanswered` when empty, `ambiguous` or `conflict` reserved for future manual overrides.
   - `confidence`: propagate from `text_field.confidence` when available; default to `1.0`.
   - `provenance`: `{page: node.page, question_number: question_number}`.

3. **Build option lists**
   - Gather immediate children where `parent_section == question.section_number`.
   - For each child with `selection_field.label`, create an `Option`:
     - `option_id = f\"{question_id}_opt_{label}\"`
     - `label` and `option_text` from the child node.
     - `is_selected` from `selection_field.is_selected`.
     - If the child carries a `text_field`, translate to a `FillIn` entry (`status`, `confidence`, `value`).

4. **Derive election values**
   - `single_select`: `option_id` comes from `selection_field.selected_label` mapped through the option list.
   - `multi_select`: `option_ids` are constructed from `selection_field.selected_labels`.
   - `text`: carry over `text_field.value`.

5. **Output payload**
   - Emit a document-level wrapper: `{"document": ..., "schema_version": "aa-election-v1", "elections": [...]}`.
   - Preserve original metadata (model, prompt version) for auditability.

6. **Validation**
   - Unit tests should cover at least: plain text fields, radio groups, checkbox groups with multiple selections, options containing fill-ins, and nodes without parents to ensure they are excluded or correctly contextualised.

---

## 7. Parser Validation Enhancements (Planned)

To complement the prompt update, the AA mapper parser will enforce stricter validation before accepting an LLM response:

1. Ensure `classification.confidence_rationale.strip()` is non-empty. Empty rationales should raise validation errors and force the fallback mapping with `abstain_reasons=["llm_response_invalid"]`.
2. When `classification.match_type == MatchType.ABSTAIN`, require `classification.abstain_reasons` to contain at least one entry.
3. When `structure_analysis.question_alignment.value` is `False`, require `structure_analysis.question_alignment.reasons` to be a non-empty list.
4. Enforce option-level rules: if any option mapping has `relationship` in `{partial, missing, incompatible}` ensure `classification.match_type` is not `"exact"`; if any mapping is `incompatible`, enforce `impact` ∈ {`medium`,`high`}.
5. Log validation failures (mapping ID, offending field) for diagnostics.
6. Extend `tests/test_aa_semantic_mapper.py` to cover invalid responses that trigger the fallback path (e.g., empty rationale, missing abstain reasons, missing alignment reasons, incompatible impact mismatch).

Claude will implement these parser updates alongside prompt v1.1 to guarantee the pipeline remains auditable.
```

**Few-shot examples**

Provide the model with 4–5 reference exchanges. Suggested coverage:

1. **Exact Match** — Source “Immediate entry (no waiting period)” vs target “Participants enter immediately”. Expected: `match_type="exact"`, `impact="none"`, option relationships all `exact`.
2. **Compatible with extra option** — Source offers choices (Immediate, 1 month, 3 months); target introduces “6 months”. Classify missing option with `relationship="missing"`, mark `match_type="compatible"`, `impact="medium"` if sponsor intent uncertain. Confidence `Medium`.
3. **Different Questions** — Source asks “Plan Type” (entity classification), target asks “Eligibility class exclusions”. Set `question_alignment.value=false`, `match_type="no_match"`, `impact="none"`, `abstain=false`.
4. **Election dependent** — Source references AA question for match formula details; target lacks election context. Set `election_dependency.status="source_only"`, `match_type="abstain"`, `abstain_reasons=["election"]`, `confidence="Low"`.
5. **Conditional compatibility** — Source allows “Exclude HCEs unless safe harbor elected”; target provides explicit safe harbor toggle. Use `match_type="conditional"`, `impact="medium"`, note dependency on safe harbor selections, `confidence="Medium"`.

Include the schema reminder at the end of each example to reinforce strict adherence.

---

## 3. Mapper Architecture

### 3.1 Module Structure

```
src/mapping/
  ├── aa_semantic_mapper.py   # new/refactored
  ├── v3_input_builder.py     # reuse patterns for building payloads
  └── semantic_mapper.py      # BPD mapper (existing)
```

### 3.2 `AASemanticMapper` Responsibilities

1. Build embeddings using election fingerprints.
2. Compute similarity matrix (top-k candidates).
3. For each candidate pair:
   - Build v1 AA payload.
   - Call LLM, parse output into new `AAElectionMapping` model.
   - Apply lint rules similar to BPD (consistency checks).
4. Produce `AAComparison` object for summary/export.

### 3.3 Data Models (new file `src/models/aa_mapping.py`)

```python
class OptionMapping(BaseModel):
    source_label: str
    target_label: Optional[str]
    relationship: OptionRelationship
    notes: Optional[str]

class AAElectionMapping(BaseModel):
    mapping_id: UUID
    source_election_id: UUID
    target_election_id: UUID
    structure_analysis: StructureAnalysis
    option_mappings: List[OptionMapping]
    value_alignment: ValueAlignment
    classification: Classification
    confidence_level: ConfidenceLevel
    confidence_rationale: str
    abstain_reasons: List[str]
    embedding_similarity: float
    created_at: datetime
```

Enums:
- `OptionRelationship`: `exact`, `compatible`, `partial`, `missing`, `incompatible`.
- `MatchType`: `exact`, `compatible`, `conditional`, `no_match`, `abstain`.
- `ImpactLevel`: reuse from `mapping.py`.
- `ConfidenceLevel`: reuse existing enum.

### 3.4 Output Aggregation

`AAComparison` should mirror `DocumentComparison` structure:
- Total elections, matched, unmatched.
- Count by match type and confidence level.
- Provide hook for downstream merged provision validation.

---

## 4. CLI Runner & Exports

- Script: `scripts/run_aa_crosswalk.py`
  - Similar logging structure as BPD runner.
  - Outputs `test_data/crosswalks/aa_crosswalk_v1.json` and `.csv`.
  - Saves metadata: run ID, counts, confidence distribution.

- CSV Columns (proposed):
  - `run_id`, `source_question`, `target_question`, `match_type`, `confidence_level`, `impact`, `abstain`.
  - `source_selected`, `target_selected`, `compatible`.
  - `option_summary` (serialized mapping), `notes`.

---

## 5. Test Strategy

### 5.1 Unit Tests

- **Builder Tests** (`tests/test_aa_input_builder.py`)
  - Verify payload includes required fields, option sets, fill-ins.
  - Confirm election dependency detection (if reused from BPD).

- **Parser Tests** (`tests/test_aa_semantic_mapper.py`)
  - Feed sample JSON output; assert mapping fields align with enums and convenience accessors.

### 5.2 Smoke Test

- Monkeypatch embeddings, similarity matrix, and LLM call to return deterministic payload.
- Validate `AASemanticMapper.compare_documents()` returns expected counts.
- Ensure CLI runner logs and outputs files without hitting real APIs.

### 5.3 Integration (Optional / Later)

- Pair actual small subset (3–5 elections) with real API once prompt is ready.
- Compare manual mapping vs. tool output; capture metrics in `/test_results/`.

---

## 6. Sprint 2 Backlog Mapping

| Task ID | Description | Owner (default) | Dependencies |
|---------|-------------|-----------------|--------------|
| S2-T1 | Finalize AA prompt schema & examples | Codex | Spec doc |
| S2-T2 | Implement AA input builder + helpers | Claude | S2-T1 |
| S2-T3 | Add AA mapping data models (`aa_mapping.py`) | Codex | S2-T1 |
| S2-T4 | Implement `AASemanticMapper` (embeddings + parser) | Codex | S2-T2, S2-T3 |
| S2-T5 | Build CLI runner (`run_aa_crosswalk.py`) | Claude | S2-T4 |
| S2-T6 | Tests (unit + smoke) | Codex | S2-T2, S2-T4 |
| S2-T7 | Docs & pipeline updates | Codex | S2 deliverables |

Stretch: integrate with provisional matching Level 3 once S2 core stable.

---

## 7. Open Questions / Follow-Ups

1. **Option normalization:** Should we pre-normalize enumerated options (e.g., “a.” vs. “(a)”) before sending to LLM?
2. **Multi-select semantics:** How to represent partial overlaps (e.g., target missing one optional checkbox)? Proposed classification: `partial` with High/Medium/Low impact based on severity.
3. **Fill-in numeric normalization:** Consider pre-extracting numeric values (percentages, dollar amounts) for optional post-processing.
4. **Performance:** Expect ~3,000 elections per document; confirm top-k (3?) to balance accuracy vs. cost.
5. **Calibration:** Deferred to Sprint 4, but capture raw option mapping stats for later analysis.

---

This document will evolve as Sprint 2 progresses; log updates in the “Update Log” section below.

### Update Log

| Date | Author | Summary |
|------|--------|---------|
| 2025-10-29 | Codex | Initial draft for AA crosswalk architecture and backlog |
| 2025-10-29 | Codex | Completed prompt instructions & few-shot guidance for implementation |
