# AA Extraction v2 Implementation Summary

**Date:** 2025-10-20
**Status:** Implemented, pending validation test
**Purpose:** Fix false positive bug in AA extraction using advisor's discriminated union model

---

## Problem Statement

### Critical Bug Discovered (2025-10-20)

**Issue:** AA extraction v1 claimed 63 elections had values in `source_aa.pdf`, but manual inspection revealed the document is a blank SAMPLE template with ZERO elections made.

**Root Cause:**
```python
# aa_extraction_v1.txt (DEPRECATED)
{
  "value": null|"checked"|"text",  # Ambiguous: WHEN to use each?
}
```

The prompt had no clear rules for distinguishing:
- Field **existence** (checkbox/fill-in structure present)
- Field **completion** (actual selection/text entered)

Vision model interpreted structure existence as having values → 100% false positives on blank templates.

---

## Solution: Discriminated Union Model

### Advisor's Model Architecture

**Key Innovation:** Different election **kinds** require different value structures.

1. **text** elections: `value: string | null`
2. **single_select** elections: `value: { option_id: string | null }`
3. **multi_select** elections: `value: { option_ids: string[] }`

Each election has:
- **kind** field: Determines structure (type discrimination)
- **status** field: `unanswered | answered | ambiguous | conflict`
- **confidence** field: Extraction quality (0.0 to 1.0)
- **provenance** field: Auditability (page, question_number)

---

## Implementation

### Files Created/Modified

#### 1. `/prompts/aa_extraction_v2.txt` (NEW)
Comprehensive 300-line prompt with:

**Election Kinds:**
- `text` - Fill-in-the-blank fields
- `single_select` - Radio buttons (one choice)
- `multi_select` - Checkboxes (multiple choices allowed)

**Status Rules:**
- `unanswered`: No selection/text (blank template indicators: ☐, ____, SAMPLE watermark)
- `answered`: Clear selection/text (☑, ✓, [X], typed/handwritten text)
- `ambiguous`: Unclear marks (faint, partial, smudged)
- `conflict`: Contradictory selections (multiple radios checked, crossed-out text)

**Visual Indicators:**
- Blank templates: ☐ [ ] (empty), ____ (underscores), "SAMPLE" watermark
- Completed elections: ☑ ✓ ✗ [X] (marked), handwritten/typed text

**Nested Structures:**
- Options can have `fill_ins` array (e.g., "Other (specify): _____")
- Each fill-in is a mini text election with own status/value

**ID Generation:**
- Elections: `q{question_number}` (e.g., `q2_03`)
- Options: `{election_id}_opt_{label}` (e.g., `q2_03_opt_b`)
- Fill-ins: `{option_id}_fill{index}` (e.g., `q2_03_opt_c_fill1`)

**Examples:**
- Blank text field (unanswered)
- Completed text field (answered with "ABC Company 401(k) Plan")
- Blank single_select (all options is_selected: false)
- Completed single_select (one option is_selected: true)
- Blank multi_select (option_ids: [])
- Completed multi_select (option_ids: ["q3_02_opt_a", "q3_02_opt_c"])
- Option with fill-in sub-field

#### 2. `/src/models/election.py` (NEW)
Pydantic v2 models matching JSON Schema:

**Models:**
```python
class Provenance(BaseModel):
    page: int
    question_number: str

class FillIn(BaseModel):
    id: str
    kind: Literal["text"]  # Simplified for POC
    question_text: str
    status: Literal["unanswered", "answered", "ambiguous", "conflict"]
    confidence: float
    value: Optional[str]

class Option(BaseModel):
    option_id: str
    label: str
    option_text: str
    is_selected: bool
    fill_ins: List[FillIn]

class BaseElection(BaseModel):
    id: str
    question_number: str
    question_text: str
    section_context: str
    status: Literal["unanswered", "answered", "ambiguous", "conflict"]
    confidence: float
    provenance: Provenance

class TextElection(BaseElection):
    kind: Literal["text"] = "text"
    value: Optional[str]

class SingleSelectElection(BaseElection):
    kind: Literal["single_select"] = "single_select"
    value: SingleSelectValue  # { option_id: string | null }
    options: List[Option]

class MultiSelectElection(BaseElection):
    kind: Literal["multi_select"] = "multi_select"
    value: MultiSelectValue  # { option_ids: string[] }
    options: List[Option]

Election = Union[TextElection, SingleSelectElection, MultiSelectElection]
```

**Factory Functions:**
- `create_text_election(...)`
- `create_single_select_election(...)`
- `create_multi_select_election(...)`

Simplifies construction with defaults and validation.

#### 3. `/src/extraction/parallel_vision_extractor.py` (MODIFIED)
Updated to load new prompt:

```python
AA_PROMPT = load_prompt("aa_extraction_v2.txt")  # Updated from v1
```

#### 4. `/scripts/test_aa_extraction_v2.py` (NEW)
Test script to validate:
- Prompt generates valid JSON
- JSON matches Pydantic schema
- Elections parsed correctly by kind
- Status field reflects blank vs completed
- Confidence scoring makes sense

**Test Approach:**
1. Extract single AA page
2. Parse JSON response
3. Validate with Pydantic models (discriminated union)
4. Count by kind and status
5. Display detailed analysis
6. Save output for manual review

#### 5. `/prompts/README.md` (UPDATED)
Documented:
- `aa_extraction_v1.txt` as DEPRECATED (false positive bug)
- `aa_extraction_v2.txt` as pending validation
- Modification history with rationale

---

## Simplifications for POC

Per recommendation, deferred these advisor model features:

1. **Election kinds:** Implemented `text`, `single_select`, `multi_select` only
   - Deferred: `date`, `number`, `composite` (until basic validation works)

2. **Provenance:** Simplified to `page` and `question_number` only
   - Deferred: `bbox` (bounding box coordinates) - complex to extract

3. **Nested elections:** Supported `fill_ins` within options only
   - Deferred: `children` (nested sub-questions) - rare in test corpus

4. **Validation:** Focus on JSON parsing and schema compliance
   - Deferred: Advanced validation rules (e.g., conflicting election detection logic)

---

## Testing Plan

### Phase 1: Single Page Test (NEXT)
```bash
python scripts/test_aa_extraction_v2.py
```

**Expected Outcome (source_aa.pdf page 1):**
- All elections should have `status: "unanswered"`
- All text elections should have `value: null`
- All single_select should have `option_id: null`, all options `is_selected: false`
- All multi_select should have `option_ids: []`, all options `is_selected: false`
- **Confidence should be high (0.95-1.0)** - blank template is unambiguous

**Success Criteria:**
✅ Zero false positives (no elections marked as "answered")
✅ JSON parses correctly
✅ Pydantic validation passes
✅ Visual inspection of test output confirms structure correctness

### Phase 2: Full Document Re-Extraction (IF Phase 1 passes)
```bash
# Modify parallel_vision_extractor.py to use aa_extraction_v2.txt
python src/extraction/parallel_vision_extractor.py
```

**Expected Outcome:**
- `source_aa_elections.json` should show 0 answered elections (SAMPLE doc)
- `target_aa_elections.json` should show 0 answered elections (blank template)
- Election counts may differ from v1 (more accurate question detection)

### Phase 3: Completed AA Test (Future - requires obtaining completed AA)
- Test on actual client AA with filled elections
- Validate `status: "answered"` detection works
- Verify option selections and fill-in text captured correctly

---

## Key Design Decisions

### 1. Why Discriminated Union?

**Problem:** Single JSON structure can't handle different value types cleanly.

**Bad approach (v1):**
```json
{
  "value": "checked"  // What does this mean? Which option? How many?
}
```

**Good approach (v2):**
```json
// text election
{ "kind": "text", "value": "ABC Company 401(k) Plan" }

// single_select election
{ "kind": "single_select", "value": { "option_id": "q2_03_opt_b" } }

// multi_select election
{ "kind": "multi_select", "value": { "option_ids": ["opt_a", "opt_c"] } }
```

Type-safe, unambiguous, extensible.

### 2. Why Status Field?

**Context:** Blank templates are the common case, not the exception.

**Status triage:**
- `unanswered` - **DEFAULT** for blank templates (explicit, not implicit)
- `answered` - Clear visual evidence of completion
- `ambiguous` - LLM uncertain (requires human review)
- `conflict` - Contradictory marks (e.g., multiple radios checked)

**Benefits:**
- Prevents false positives (v1 bug)
- Enables quality tracking (% ambiguous/conflict = extraction difficulty)
- Supports downstream workflows (only process "answered" elections)

### 3. Why Separate `is_selected` and `value`?

**For choice-based elections (single_select, multi_select):**
- `is_selected` at option level - visual state (☑ or ☐)
- `option_id` / `option_ids` in value - which option(s) selected

**For text elections:**
- No `is_selected` (doesn't make sense)
- `value: string | null` directly - what was typed

**This separation:**
- Mirrors document structure (options array is the spec, value is the observation)
- Enables validation (value.option_id must exist in options array)
- Supports provenance (can track which visual mark led to is_selected: true)

### 4. Why Nested `fill_ins`?

**Common pattern in AAs:**
```
Entry date (select one):
  ☐ a. First day of month
  ☐ b. Immediate
  ☐ c. Other (specify): _____
```

Option c has TWO pieces of data:
1. **Selection:** Is option c checked?
2. **Fill-in:** What text is in the blank?

**Model:**
```json
{
  "option_id": "q2_03_opt_c",
  "is_selected": true,
  "fill_ins": [
    {
      "id": "q2_03_opt_c_fill1",
      "kind": "text",
      "status": "answered",
      "value": "First day of quarter"
    }
  ]
}
```

Preserves hierarchical relationship while keeping each piece typed.

---

## Expected Impact

### Before (v1):
- ❌ 63 false positives on blank template
- ❌ Ambiguous value structure
- ❌ No status field (implicit assumption all have values)
- ❌ Mixed field semantics (text vs option text vs filled value)

### After (v2):
- ✅ Zero false positives (status: "unanswered" for blank templates)
- ✅ Type-safe discriminated unions
- ✅ Explicit status triage (unanswered/answered/ambiguous/conflict)
- ✅ Clean separation: spec (options) vs observation (value)
- ✅ Provenance tracking (auditability)
- ✅ Confidence scoring (quality metrics)

---

## Next Steps

1. **Run Phase 1 test** - Validate single page extraction
2. **Manual review** - Sergio inspects output JSON structure
3. **If successful:** Run full re-extraction on all 4 AAs
4. **If issues found:** Iterate on prompt based on specific failures
5. **Document findings** - Update CLAUDE.md with v2 validation results

---

## Files Summary

| File | Status | Purpose |
|------|--------|---------|
| `prompts/aa_extraction_v2.txt` | ✅ Created | Comprehensive prompt with discriminated union model |
| `src/models/election.py` | ✅ Created | Pydantic models for type-safe parsing |
| `src/extraction/parallel_vision_extractor.py` | ✅ Updated | Load v2 prompt |
| `scripts/test_aa_extraction_v2.py` | ✅ Created | Single-page validation test |
| `prompts/README.md` | ✅ Updated | Documentation and versioning |
| `AA_EXTRACTION_V2_IMPLEMENTATION.md` | ✅ This file | Implementation summary |

---

*Implementation Date: 2025-10-20*
*Advisor Model: Discriminated union with kind-based value structures*
*POC Simplifications: text/single_select/multi_select only, deferred date/number/composite*
*Next: Run test_aa_extraction_v2.py to validate*
