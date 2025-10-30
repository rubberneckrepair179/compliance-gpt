# Prompt Engineering Expert Consultation Request

**Date:** 2025-10-30
**Project:** compliance-gpt - Retirement Plan Document Extraction
**Task:** BPD (Basic Plan Document) Provision Extraction via GPT-5-nano Vision API

---

## Problem Statement

We need expert guidance on redesigning a vision-based extraction prompt that is currently **failing to extract ~10% of pages** (parse errors) and producing **incomplete metadata** (missing page numbers).

---

## What We're Trying to Extract

**Input:** PDF pages from retirement plan legal documents (Basic Plan Documents)
- 80-100 pages per document
- Dense legal text with nested structure
- Mix of definitions, operational provisions, and regulatory language

**Example Page Content:**
```
ARTICLE I - DEFINITIONS

1.01 Account
The individual account maintained for a Participant...

1.02 Administrator
The person or entity designated as Plan Administrator...

1.03 Compensation
For purposes of determining contributions, Compensation means
wages as defined in Code Section 3401(a)...
```

**Desired Output:** JSON array of provisions with:
1. **Page number** (PDF page where provision appears)
2. **Section number** (e.g., "1.01")
3. **Section title** (e.g., "Account")
4. **Provision text** (complete legal language)
5. **Provision type** (definition, operational, regulatory)

---

## Current Problems

### Problem 1: Parse Failures (10% failure rate)
- **Symptom:** 2 out of 98 pages (Relius), 8 out of 81 pages (Ascensus) return non-JSON responses
- **Impact:** Missing provisions, no record of which pages failed
- **Hypothesis:** Prompt too long/complex causes LLM to output explanatory text instead of JSON

### Problem 2: Missing Page Numbers
- **Symptom:** Output contains `page_sequence` (provision number within page) but NOT the actual PDF page number
- **Impact:** Cannot map provisions back to source PDF for validation
- **Root Cause:** Prompt doesn't ask for it, extractor doesn't provide it

### Problem 3: Prompt Length
- **Current:** 1,339 words
- **Target:** ~500 words (based on prior success with shorter prompts)
- **Concern:** Verbose instructions may confuse LLM or cause attention issues

### Problem 4: Unclear Classification Requirements
- **Current:** Asks LLM to classify provisions as "heading" vs "substantive" AND categorize as "definition|operational|regulatory"
- **Concern:** Dual classification may be causing confusion/errors

---

## Current Prompt Structure

The prompt includes:
1. JSON schema definition with field explanations
2. Classification instructions ("heading" vs "substantive")
3. Examples of what NOT to extract (section headings, TOC entries)
4. Provision type taxonomy (3 types)
5. Semantic fingerprinting guidance
6. Multiple warnings about ID generation
7. Numerous edge case examples

**Total:** 1,339 words, ~10,700 characters

---

## Technical Constraints

### Model
- **GPT-5-nano** (gpt-5-nano via OpenAI Vision API)
- Vision model processing PNG images of PDF pages
- `max_completion_tokens=16000`
- Batch size: 1 page per request (batching increased failures)

### Processing Pattern
- 16 parallel workers
- Each page sent individually with same prompt
- No context sharing between pages
- LLM has NO knowledge of PDF page number (we need to inject it)

### Success Criteria
- **Parse rate:** 95%+ (currently 90-98%)
- **Completeness:** Page number, section number, title, full text
- **Accuracy:** No section headings, all substantive provisions captured
- **Consistency:** Same prompt works across 80-100 pages

---

## Questions for Expert

### 1. Prompt Length & Structure
- Is 1,339 words too long for vision models?
- What's the optimal prompt length for consistent JSON output?
- Should we separate instructions (system) from schema (user)?

### 2. JSON Reliability
- Best practices for ensuring LLM returns ONLY JSON (no preamble/postamble)?
- Should we use structured output APIs or rely on prompt instructions?
- How to handle classification tasks (heading vs substantive) without breaking JSON?

### 3. Page Number Injection
- How should we provide the PDF page number to the LLM?
- Options considered:
  - Add to prompt: "You are processing page {N} of the PDF"
  - Include in schema: `"pdf_page": {N}` (pre-filled)
  - Inject via vision metadata
- Which approach is most reliable?

### 4. Classification Simplification
- Current: "heading|substantive" + "definition|operational|regulatory"
- Is dual classification causing errors?
- Should we:
  - Drop "heading" filter (handle in post-processing)?
  - Simplify to single type field?
  - Use structured hints instead of classifications?

### 5. Error Reduction
- What causes 10% parse failures?
- Is it prompt complexity, page complexity, or model limitations?
- How to make prompt more robust to edge cases?

### 6. Conciseness Strategy
- If we need to cut from 1,339 words to ~500 words, what stays?
  - JSON schema (required)
  - Classification rules (?)
  - Examples (how many?)
  - Edge case warnings (?)
  - Semantic guidance (?)

---

## Success Metrics for Redesigned Prompt

1. **Parse Rate:** 98%+ pages return valid JSON
2. **Metadata Completeness:** 100% of provisions have page number
3. **Accuracy:** 0 section headings extracted (substantive content only)
4. **Consistency:** Same quality across all 80-100 pages
5. **Brevity:** ≤600 words (prefer ~500)

---

## Example Desired Output

```json
[
  {
    "pdf_page": 7,
    "section_number": "1.01",
    "section_title": "Account",
    "provision_text": "The individual account maintained for a Participant which reflects the Participant's Elective Deferrals, Matching Contributions, and earnings thereon.",
    "provision_type": "definition"
  },
  {
    "pdf_page": 7,
    "section_number": "1.02",
    "section_title": "Administrator",
    "provision_text": "The Plan Administrator as defined in Section 8.01.",
    "provision_type": "definition"
  }
]
```

---

## Current Prompt Performance

**Strengths:**
- Successfully extracts provisions (when it works)
- Captures full text (no truncation)
- Identifies section structure correctly
- Filters out most section headings

**Weaknesses:**
- 10% parse failure rate (returns non-JSON)
- Missing page numbers (critical metadata)
- Too verbose (may confuse model)
- Dual classification adds complexity

---

## Expert Guidance Requested

Please review our current prompt (attached separately) and provide:

1. **Diagnosis:** What's likely causing the 10% parse failures?
2. **Page Number Strategy:** Best way to inject and capture PDF page number?
3. **Simplification Plan:** How to cut from 1,339 to ~500 words without losing accuracy?
4. **JSON Reliability:** Techniques to guarantee JSON-only output?
5. **Revised Structure:** Recommended prompt template/structure?
6. **Specific Edits:** If possible, suggest concrete changes to our prompt

**Deliverable:** Written analysis + recommended prompt revision strategy

---

## Additional Context

**Document Characteristics:**
- Retirement plan legal documents (IRS pre-approved templates)
- Highly structured (numbered sections, hierarchical)
- Legal precision required (can't paraphrase or truncate)
- Standard format across vendors (Relius, Ascensus, ftwilliam)

**Use Case:**
- Extracted provisions feed semantic mapping (provision-to-provision comparison)
- Page numbers essential for audit trail and user validation
- Parse failures block entire pipeline (missing pages = incomplete comparison)

**Team Constraints:**
- Need to re-extract 179 pages (98 + 81) after prompt improvements
- Cost-sensitive (GPT-5-nano chosen for cost vs GPT-5-mini)
- Time-sensitive (blocking pipeline validation)

---

## Appendix: Current Prompt Text

*[Prompt will be provided separately - see `prompts/provision_extraction_v4.txt`]*

---

**Thank you for your expertise!**

We're open to radical redesigns if needed - accuracy and reliability are more important than preserving our current approach.
