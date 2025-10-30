# AA Extraction Prompt Engineering Consultation

**Date:** 2025-10-30
**Context:** Adoption Agreement (AA) extraction is currently non-functional despite documented claims
**Goal:** Get expert guidance on redesigning AA extraction prompt for production use

---

## 🔴 CRITICAL ARCHITECTURAL INSIGHT

**The fundamental problem with v4:** We modeled AAs as "election questions" when they're actually **provisions with embedded form elements**.

**What this means:**
- AAs are NOT question-based forms
- AAs ARE hierarchical provisions (like BPDs) with checkboxes/textboxes embedded in the provision text
- Many "questions" are actually commands: "Select one of the following:" (not a question!)
- Form elements (`checkbox_field`, `text_field`) appear at various levels of the provision hierarchy

**Implication for extraction:**
- ❌ Don't extract "questions" as fundamental units (v4's approach)
- ✅ Extract provisions hierarchically (like BPD v5) and note which ones have form elements
- ✅ Use same `section_number` + `parent_section` model as BPD v5
- ✅ Add form element attributes to provisions that have them

**This likely explains why v4 produced 0 elections:**
- Prompt asked for "questions"
- AAs don't contain questions, they contain provisions
- LLM correctly returned empty array because there are no "questions" to extract

---

## Current State Analysis

### What We Claim (PIPELINE.md Section 1.2)
- ❌ Scripts: `extract_relius_aa_v6.py`, `extract_ascensus_aa_v6.py` - **DO NOT EXIST**
- ❌ Prompt: `prompts/aa_extraction_v6_unified.txt` - **DOES NOT EXIST**
- ❌ Output: 1,294 Relius elections, 2,716 Ascensus elections - **DO NOT EXIST**
- ❌ Success rate: 100% - **NEVER HAPPENED**

### What We Actually Have
- ✅ Prompt: `prompts/aa_extraction_v4.txt` - **1,649 words** (Oct 24, 2025)
- ✅ Extractor: `src/extraction/parallel_vision_extractor.py` - Uses **GPT-5-nano** with **mini fallback**
- ✅ Output: `test_data/extracted_vision_v4/source_aa_elections.json` - **0 elections** (extraction ran but produced nothing)
- ✅ Processing time: 13.8 minutes for 45 pages
- ❌ Result: **COMPLETE FAILURE** - 0 elections extracted

### Previous Context (From Earlier Sessions)
During Oct 28 session, we decided to use **GPT-5-mini for AA extraction** after nano showed 50-66% success rate:
> "Strategic Decision: Switched AA extraction from hybrid nano→mini to mini-only"
> "Decision: GPT-5-mini for AA extraction (pragmatic over optimal - shipping > optimizing)"

**However**: The current extractor (`parallel_vision_extractor.py`) still defaults to **GPT-5-nano**, not mini!

---

## Problem Statement

**Primary Issue:** AA extraction with v4 prompt produced 0 elections despite 13.8 minutes of processing

**Root Causes (Suspected):**
1. **Prompt too complex** - 1,649 words (4x longer than BPD v5's ~450 words that works 100%)
2. **Wrong model** - Using nano instead of mini (we decided on mini but never updated the code)
3. **Complex discriminated union model** - Different JSON structures per election "kind"
4. **No page number injection** - BPD v5 success depended on {{PDF_PAGE}} placeholder
5. **Unclear failure mode** - Why did it produce valid JSON with 0 elections instead of parse errors?

---

## Current V4 Prompt Analysis

**File:** `prompts/aa_extraction_v4.txt`
**Word Count:** 1,649 words
**Model Target:** GPT-5-nano (but should be mini based on our decision)

### Prompt Structure
1. **Election Model** (lines 13-31) - Discriminated union by "kind" field
2. **Semantic Fingerprinting Context** (lines 39-63) - Question numbers are provenance only
3. **Election Kinds** (lines 66-318)
   - KIND: "text" - Fill-in fields
   - KIND: "single_select" - Radio buttons
   - KIND: "multi_select" - Checkboxes
4. **Visual Indicators** (lines 321-346) - Blank vs completed vs ambiguous
5. **Page Sequence Tracking** (lines 349-372) - Sequential numbering within page
6. **Confidence Scoring** (lines 375-384)
7. **Important Rules** (lines 387-417) - 7 detailed rules
8. **Output Format** (lines 424-488) - JSON array examples

### Prompt Strengths
- ✅ Comprehensive election model covering all types
- ✅ Clear distinction between blank templates and completed elections
- ✅ Semantic fingerprinting guidance (question numbers as provenance only)
- ✅ Good visual indicator descriptions
- ✅ Page sequence tracking (like BPD v5's page number injection concept)

### Prompt Weaknesses
- ❌ **4x too long** - 1,649 words vs BPD v5's ~450 words
- ❌ **Mixed objectives** - Extraction + status detection + confidence scoring + semantic guidance
- ❌ **Complex data model** - Discriminated unions, nested fill_ins, option-level structures
- ❌ **No page number injection** - Doesn't use {{PDF_PAGE}} placeholder like BPD v5
- ❌ **Verbose examples** - Multiple full JSON examples inflate prompt size
- ❌ **No validation rules** - No guidance on required fields or empty page handling

---

## Comparison to Working BPD v5 Prompt

| Aspect | BPD v5 (WORKS 100%) | AA v4 (FAILS 100%) |
|--------|---------------------|---------------------|
| **Word Count** | ~450 words | 1,649 words |
| **Model** | GPT-5-nano → mini fallback | GPT-5-nano (should be mini) |
| **Page Injection** | ✅ {{PDF_PAGE}} | ❌ No injection |
| **Objectives** | Single: Extract provisions | Multiple: Extract + classify + score |
| **Validation** | ✅ Required fields, empty arrays | ❌ None |
| **Examples** | 2 minimal examples | Multiple verbose examples |
| **Success Rate** | 100% (773 provisions) | 0% (0 elections) |

---

## Specific Questions for Expert

### Question 1: Model Selection
**Context:** We decided on GPT-5-mini for AA extraction (Oct 28) but never updated the code.

**Should we:**
- A) Use GPT-5-mini exclusively for AA (no nano fallback)
- B) Use nano with mini fallback (like BPD v5)
- C) Try nano-first approach with different prompt design

**Considerations:**
- BPD v5 achieves 100% with nano + mini fallback
- AA forms are visually complex (checkboxes, nested options, fill-ins)
- Mini costs more but we need reliability

### Question 2: Prompt Length Reduction
**Context:** Current prompt is 1,649 words. BPD v5 works with ~450 words.

**How to reduce AA prompt to ~500-600 words while preserving:**
- Election kind discrimination (text|single_select|multi_select)
- Blank vs completed distinction
- Nested option structures with fill_ins
- Page sequence tracking

**Specific cuts to consider:**
- Remove semantic fingerprinting section? (130 words - may not be needed in extraction phase)
- Simplify examples? (Current examples are 300+ words)
- Remove visual indicators section? (Rely on model's vision capabilities)
- Consolidate rules? (7 rules could be 3-4)

### Question 3: Page Number Injection
**Context:** BPD v5 success depends on {{PDF_PAGE}} injection.

**For AA extraction, should we:**
- A) Inject page number via {{PDF_PAGE}} in prompt
- B) Include page in provenance field only
- C) Use extractor-level page injection (not in prompt)

**Current AA model has:**
```json
"provenance": {
  "page": 1,
  "question_number": "1.01"
}
```

**Should page number be in main structure like BPD v5?**
```json
{
  "pdf_page": 1,
  "page_sequence": 1,
  "kind": "text",
  ...
}
```

### Question 4: Data Model Simplification
**Context:** AA model has discriminated unions, nested fill_ins, per-option structures.

**Is the complexity necessary, or can we simplify to:**
- Single flat structure for all election types
- Move fill_ins to separate extraction pass
- Treat options as simple array instead of objects with is_selected flags

**Example simplified model:**
```json
{
  "pdf_page": 1,
  "election_sequence": 1,
  "election_type": "text|single|multi",
  "question_number": "1.01",
  "question_text": "Plan Name:",
  "selected_value": "ABC Company 401(k) Plan",  // or array for multi
  "all_options": ["option a text", "option b text"]  // if applicable
}
```

**Trade-off:** Simpler extraction vs need for post-processing to rebuild complex structure

### Question 5: Blank Page Handling
**Context:** BPD v5 returns `[]` for heading-only pages. AA forms may have:
- Blank template pages (all unanswered)
- Partially completed pages
- Instruction pages with no elections

**Should we:**
- A) Return `[]` for pages with no elections (like BPD v5)
- B) Return unanswered elections for blank template pages
- C) Add page classification step (election page vs instruction page)

### Question 6: Hierarchical Structure - CRITICAL ARCHITECTURAL INSIGHT
**Context:** ⚠️ Current v4 model treats "questions" as fundamental units. This is WRONG.

**Critical realization:** AAs are actually **provisions with embedded form elements**, not "election questions."

**What v4 does (WRONG):**
- Treats each "question" as a standalone election object
- Models: `{kind: "text|single_select|multi_select", question_text: "...", value: ...}`
- Assumes question-centric structure

**What AAs actually are (CORRECT):**
- Hierarchical provisions (like BPDs) with form elements embedded at various levels
- Many aren't even questions - they're commands: "Select one of the following:"
- Form elements (`text_field`, `checkbox_field`) appear at different hierarchy levels

**Example AA structure (revised understanding):**
```
Article III - Contributions
  └─ 3.01 "Elective Deferrals" (provision - introductory text)
       ├─ 3.01(a) "The Plan permits pre-tax elective deferrals" (provision text)
       │    └─ [checkbox_field: selected=true]
       ├─ 3.01(b) "The Plan permits Roth elective deferrals" (provision text)
       │    └─ [checkbox_field: selected=false]
       └─ 3.01(c) "Maximum deferral percentage" (provision text)
            └─ [text_field: value="15%"]
  └─ 3.02 "Matching Contributions" (provision)
       ├─ 3.02(a) "Safe harbor matching contribution formula:" (provision)
       │    ├─ "Select one of the following:" (instruction text, NOT a question)
       │    ├─ Option (a): "100% of first 3% plus 50% of next 2%" (provision)
       │    │    └─ [checkbox_field: selected=true]
       │    └─ Option (b): "Other (specify):" (provision)
       │         ├─ [checkbox_field: selected=false]
       │         └─ [text_field: value=null]
       └─ 3.02(b) "Discretionary match permitted" (provision)
            └─ [checkbox_field: selected=true]
```

**Proposed unified model (provisions + form elements):**

**Option A: Provisions with embedded form_elements array**
```json
{
  "pdf_page": 5,
  "section_number": "3.01(a)",
  "section_title": "Pre-tax elective deferrals",
  "parent_section": "3.01",
  "provision_text": "The Plan permits Participants to make pre-tax elective deferrals.",
  "form_elements": [
    {
      "element_type": "checkbox",
      "element_sequence": 1,
      "is_selected": true,
      "confidence": 0.98
    }
  ]
}
```

**Option B: Separate provision and form_element records (flat)**
```json
// Provision record
{
  "pdf_page": 5,
  "section_number": "3.01(a)",
  "section_title": "Pre-tax elective deferrals",
  "parent_section": "3.01",
  "provision_text": "The Plan permits Participants to make pre-tax elective deferrals.",
  "has_form_elements": true
}

// Form element record
{
  "pdf_page": 5,
  "section_number": "3.01(a)",
  "parent_section": "3.01",
  "element_type": "checkbox",
  "element_sequence": 1,
  "is_selected": true,
  "confidence": 0.98
}
```

**Option C: Unified with element_type discriminator**
```json
{
  "pdf_page": 5,
  "section_number": "3.01(a)",
  "parent_section": "3.01",
  "element_type": "provision|checkbox|text_field",
  "section_title": "Pre-tax elective deferrals",
  "provision_text": "The Plan permits...",  // if provision
  "is_selected": true,  // if checkbox
  "text_value": "15%"   // if text_field
}
```

**Key insight:** Just like BPD v5 extracts BOTH parent provisions (1.01) AND children (1.01(a)), AA extraction should extract:
1. **Provision nodes** - The legal text at each section number
2. **Form element nodes** - The checkboxes/textboxes attached to provisions
3. **Hierarchy links** - `parent_section` connects them

**This explains v4's failure:**
- v4 tried to extract "questions" (which don't exist)
- Should extract **provisions** (which do exist, like BPDs)
- Form elements are just attributes of provisions, not separate "questions"

**Critical question for expert:**
Should we use BPD v5's extraction approach but ADD form_element detection?
- Same prompt structure (extract provisions hierarchically)
- Add: "If provision has checkbox, mark is_selected"
- Add: "If provision has text field, capture text_value"
- Result: Unified BPD+AA data model

### Question 7: NDJSON for Election Pages
**Context:** Previous advisor suggested NDJSON (newline-delimited JSON) might help with AA extraction.

**NDJSON approach:**
Instead of returning one big array for the page:
```json
[
  {"pdf_page": 5, "election_sequence": 1, ...},
  {"pdf_page": 5, "election_sequence": 2, ...},
  {"pdf_page": 5, "election_sequence": 3, ...}
]
```

Return one JSON object per line (NDJSON):
```ndjson
{"pdf_page": 5, "election_sequence": 1, ...}
{"pdf_page": 5, "election_sequence": 2, ...}
{"pdf_page": 5, "election_sequence": 3, ...}
```

**Potential benefits:**
- Each election extracted independently (less context needed)
- Partial success possible (some elections succeed even if others fail)
- Simpler for LLM to emit one election at a time vs constructing large array
- Parser can validate per-line instead of waiting for complete array

**BPD v6 exploration note:**
An earlier "wizard" advisor recommended NDJSON optimizations for BPD extraction to push nano from 50% → 80-90% success. We deferred this because mini achieved 100%. However, **AA forms may be different** - visually complex forms might benefit from per-element NDJSON.

**Questions:**
- Should we try NDJSON format for AA extraction?
- Would "one election per line" simplify the prompt?
- Does this align with mini's capabilities or is it nano-specific optimization?

### Question 8: Retry Strategy
**Context:** BPD v5 uses 3-attempt retry (nano → repair → mini).

**For AA extraction, should we:**
- A) Use same pattern (assuming we start with nano)
- B) Skip nano, go straight to mini (no retries needed if mini works)
- C) Use mini with repair-only retry (no model escalation)

**Current failure mode:** v4 produced valid JSON with 0 elections (not parse errors)
- Does this suggest prompt ambiguity rather than model capability issue?
- Would repair retry help, or do we need fundamentally different approach?

---

## Success Criteria

**Must achieve:**
- ✅ 98%+ success rate (like BPD v5's 100%)
- ✅ Extract all elections from page (not 0 like current v4)
- ✅ Handle blank templates correctly (unanswered status)
- ✅ Handle completed elections correctly (answered status with values)
- ✅ Preserve election structure (questions, options, fill-ins)
- ✅ Page number provenance on every election
- ✅ Processing time: <15 minutes for 45 pages

**Nice to have:**
- Confidence scoring on elections
- Ambiguous/conflict status detection
- Semantic fingerprinting guidance

---

## Test Corpus Available

**Relius AA:** `test_data/raw/relius/relius_aa_cycle3.pdf` (45 pages)
**Ascensus AA:** `test_data/raw/ascensus/ascensus_aa_profit_sharing.pdf` (104 pages)

Both available for testing any proposed prompt design.

---

## Requested Deliverables

1. **Recommended model:** nano vs mini vs hybrid approach
2. **Simplified prompt template** (~500-600 words target)
3. **Data model recommendation:** Keep complex structure or simplify?
4. **Page injection strategy:** How to ensure page numbers in output
5. **Retry pattern:** What pattern for AA (if different from BPD)
6. **Expected success rate:** What % should we target with recommended approach?

---

## Additional Context

**Why AA extraction matters:**
- BPD + AA pairs needed for complete document comparison
- AAs contain the actual elected values that populate BPD templates
- Semantic mapping requires matching elections across vendors (Relius Q 3.01 → Ascensus equivalent)
- Current blocker: Can't proceed to crosswalk without AA data

**Timeline pressure:**
- BPD extraction complete and working (v5, 100% success)
- AA extraction is next critical path item
- Post-processing depends on AA extraction completing
- Don't want to over-optimize; need working solution fast

**Philosophy:**
- "Shipping > optimizing" (ship working solution, optimize later)
- Prefer pragmatic mini-only if it works vs optimizing for nano
- Willing to accept slightly higher costs for reliability
- Can iterate on prompt quality after initial success
