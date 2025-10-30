# AA v5.1 Fragmentation Consultation
**Date:** 2025-10-30
**Context:** Vision-based extraction of hierarchical legal documents
**Prompt Version:** AA v5.1 (Atomic Field Rule)
**Model:** GPT-5-mini (gpt-5-mini-2025-07-18)

---

## Problem Statement

We are extracting provisions from 100+ page legal documents (Adoption Agreements) using vision-based LLM extraction. Each page is processed **independently and in parallel** for performance (16 workers, ~11 minutes for 104 pages).

**Critical constraint:** Pages cannot see each other during extraction - each page is a separate API call with no shared context.

We've discovered that **all 5 failed extractions (5% failure rate) occur on pages that start mid-hierarchy** - i.e., the page begins with a child provision whose parent is on the previous page.

---

## The Vision Representation Problem

### Document Structure
Legal provisions have hierarchical structure with visual indentation:

```
Page N:
  Section 2: Contribution Elections
    2.a: Pre-Tax Deferrals ☐
    2.b: Roth Deferrals ☐
    2.c: Employer Match ☐
    2.d: Safe Harbor Options
      2.d.1: QNEC ☐ 3% of compensation
[PAGE BREAK]

Page N+1:
      2.d.2: Basic Safe Harbor Match ☐
      2.d.3: Enhanced Safe Harbor Match ☐
    2.e: Profit Sharing ☐
  Section 3: Vesting Schedule
```

### Human Reading Experience
When a human reads page N+1:
1. Sees `2.d.2` is indented (visual cue)
2. Continues reading down the page
3. Encounters `2.d.3` (same indentation), then `2.e` (dedent), then `Section 3` (major dedent)
4. **Retroactively infers** the starting depth: "Oh, I started at H4 level"
5. Understands the full hierarchy by the time they finish the page

### LLM Extraction Challenge
The LLM must produce JSON **immediately** for each provision:
```json
{
  "section_number": "2.d.2",
  "section_title": "Basic Safe Harbor Match",
  "parent_section": "2.d",  ← HOW DOES IT KNOW THIS?
  "local_ordinal": 2,
  ...
}
```

**Problem:** Without seeing page N, the LLM cannot definitively know:
- What is the parent section number? (`2.d` vs `2` vs `1.d` vs something else?)
- What is the correct `local_ordinal`? (Is this the 2nd child of `2.d`, or the 5th?)

---

## Current Extraction Results

### Overall Statistics
- **Relius AA:** 1,216 provisions from 43/45 pages (95.6% success)
- **Ascensus AA:** 2,654 provisions from 99/104 pages (95.2% success)
- **Total:** 3,870 provisions extracted, 12 failed pages (96.9% overall success)

### Failed Page Analysis

All 5 Ascensus AA failures exhibit the same pattern:

| Page | Error | Pattern |
|------|-------|---------|
| 9 | Item 35 missing `form_elements` | Response truncated mid-object (likely token limit) |
| 20 | Item 3 missing `form_elements` | LLM omitted required field |
| 42 | Item 0 missing `form_elements` | LLM omitted required field |
| 82 | Item 3 missing `form_elements` | Inconsistent (some provisions have empty array, one missing) |
| 90 | Item 2 missing `form_elements` | Response truncated mid-provision |

**Key Observation:** User identified that all failed pages start with **fragmented provisions** (H3/H4 depth) whose parents exist on the previous page.

**Hypothesis:** The LLM struggles with hierarchy uncertainty, leading to:
1. Extra token consumption trying to infer relationships → hits `max_completion_tokens=16000` limit (pages 9, 90)
2. Confusion causing schema violations → omits required fields (pages 20, 42, 82)

---

## Current JSON Schema

```json
{
  "pdf_page": 42,
  "section_number": "2.d.2",
  "section_title": "Basic Safe Harbor Match",
  "parent_section": "2.d",           // ← REQUIRED FIELD, but parent on previous page
  "local_ordinal": 2,                // ← Must be accurate for sort order
  "field_label": "Safe Harbor Type",
  "provision_text": "...",
  "provision_type": "operational",
  "status": "unanswered",
  "form_elements": [                 // ← REQUIRED FIELD (array, can be empty)
    {
      "element_type": "checkbox",
      "element_sequence": 1,
      "is_selected": false,
      "text_value": null,
      "confidence": 0.95
    }
  ]
}
```

**Schema Constraints:**
- `parent_section` is **required** (cannot be omitted)
- `form_elements` is **required** (cannot be omitted, but can be `[]`)
- `local_ordinal` must be accurate for deterministic sort order

---

## Solution Options Under Consideration

### Option 1: Accept Fragmentation, Fix in Post-Processing (DEFERRED)
**Approach:**
- Continue page-by-page extraction
- Defragmentation step merges orphans with parents from previous page
- Pattern matching on section numbers (e.g., `2.d.2` is child of `2.d`)
- Re-assign `local_ordinal` based on document-wide sort

**Pros:**
- Preserves parallel processing (fast, cheap)
- Defragmentation is deterministic (no additional LLM calls)
- Already planned in pipeline roadmap

**Cons:**
- 5% page failure rate unresolved
- Still produces malformed JSON (missing required fields)
- Post-processing cannot recover from truncated responses

---

### Option 2: Multi-Page Context Window (OVERLAPPING EXTRACTION)
**Approach:**
- Extract pages N-1 and N together
- LLM sees full context for hierarchy
- Merge results, keeping only page N provisions

**Pros:**
- Eliminates fragmentation at extraction time
- LLM has full parent context
- Should reduce/eliminate page failures

**Cons:**
- 2x API calls (doubled cost)
- 2x processing time (~22 minutes instead of 11)
- Complexity in merging overlapping results

---

### Option 3: Context Header Strategy (HYBRID)
**Approach:**
- Extract last 10 lines of page N-1 as "context header"
- Send context header + full page N to LLM
- Prompt: "Context header is for reference only, extract provisions from page N"

**Pros:**
- Provides parent context without full duplication
- Minimal cost increase (small token overhead)
- Preserves most of parallel processing speed

**Cons:**
- More complex prompt engineering
- Risk of LLM extracting from context header (instruction following)
- Unclear if 10 lines is enough for complex hierarchies

---

### Option 4: Two-Pass Extraction (BOUNDARY DETECTION)
**Approach:**
- **Pass 1:** Page-by-page extraction (current approach)
- **Pass 2:** Identify pages with fragmentation (start with indented provision)
- **Pass 3:** Re-extract only fragmented pages with previous page context

**Pros:**
- Only pays 2x cost for ~10-15% of pages
- Deterministic detection of fragmentation
- Preserves fast parallel processing for majority

**Cons:**
- More complex pipeline orchestration
- Still requires merging strategy

---

### Option 5: JSON Schema Relaxation (ALLOW UNCERTAINTY)
**Approach:**
- Allow `parent_section: "UNKNOWN"` for provisions at page start
- Allow `local_ordinal: null` when uncertain
- Post-processing infers relationships from section numbers

**Pros:**
- LLM can admit uncertainty instead of omitting fields
- Prevents schema violations (missing required fields)
- Fast, cheap extraction

**Cons:**
- Pushes complexity to post-processing
- May not solve token limit truncation issue (pages 9, 90)
- Requires more sophisticated defragmentation logic

---

## Questions for Consultation

### 1. JSON Modeling
- Should `parent_section` be required, optional, or allow sentinel value (`"UNKNOWN"`)?
- Should `local_ordinal` be required at extraction time, or assigned globally in post-processing?
- Should we model "provisional" vs "confirmed" hierarchy (confidence score on parent relationship)?

### 2. Pipeline Architecture
- Is parallel page-by-page extraction fundamentally incompatible with hierarchical documents?
- What is the industry best practice for vision-based extraction of multi-page hierarchical documents?
- Should we optimize for speed (parallel) or accuracy (sequential with context)?

### 3. Cost-Accuracy Tradeoff
- Given 95% success rate with page-by-page extraction:
  - Is 5% failure acceptable if defragmentation can recover most?
  - Or is 100% schema compliance at extraction time critical?
- What is the optimal balance between API cost and post-processing complexity?

### 4. Fragmentation Detection
- Can we deterministically detect "fragmented pages" before extraction?
  - Visual cue: Page starts with indented text?
  - Heuristic: Section number at top has high depth (e.g., `2.d.2.i`)?
- Should fragmentation detection be:
  - Pre-extraction (vision analysis of indentation)?
  - Post-extraction (section number pattern matching)?

### 5. Alternative Architectures
- Should we abandon page-by-page in favor of document-level extraction?
  - Sliding window approach (N lines at a time)?
  - Section-aware chunking (extract by major section, not by page)?
- Is there a hybrid approach we haven't considered?

---

## Current Prompt Characteristics

**AA v5.1 Prompt:**
- ~314 words
- Atomic Field Rule: Each labeled field = separate provision
- Hierarchical: Nested provisions with `parent_section` tracking
- Form elements: Checkboxes, text fields, multi-select
- Expected success: 98-99% (per expert recommendation)

**Extraction Parameters:**
- Model: GPT-5-mini (gpt-5-mini-2025-07-18)
- max_completion_tokens: 16000
- temperature: 0.0 (deterministic)
- Batch size: 1 page per request
- Workers: 16 (parallel)

---

## Success Criteria

**Acceptable solution must:**
1. Achieve ≥98% page success rate (per expert recommendation)
2. Produce valid JSON with all required fields (no schema violations)
3. Maintain hierarchical relationships (correct `parent_section`, `local_ordinal`)
4. Complete 100-page document in ≤20 minutes (reasonable performance)
5. Cost-effective (not >3x current API spend)

**Nice to have:**
- Eliminates need for complex defragmentation post-processing
- Generalizes to other hierarchical document types (BPDs, legal briefs, etc.)
- Simple to understand and maintain

---

## Request for Consultation

Please provide:
1. **Recommended approach** from options 1-5 (or propose alternative)
2. **JSON schema recommendations** (required vs optional fields, sentinel values)
3. **Pipeline architecture guidance** (parallel vs sequential, context strategies)
4. **Trade-off analysis** (cost, speed, accuracy, complexity)
5. **Industry best practices** for vision-based hierarchical document extraction

We are at a decision point: proceed with Option 1 (post-processing defragmentation) as planned, or invest in architectural improvements to achieve 100% extraction success rate.

---

**Thank you for your expertise!**
