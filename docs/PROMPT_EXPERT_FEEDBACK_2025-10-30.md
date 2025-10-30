# Prompt Expert Feedback - BPD Extraction Redesign

**Date:** 2025-10-30
**Expert:** External prompt engineering consultant
**Status:** ✅ Received - Ready for implementation

---

## Executive Summary

**Expert's Diagnosis:** Current v4 prompt tries to do **three jobs** (policy, taxonomy, output contract) which causes Nano to "wobble." Parse failures stem from mixed objectives and verbosity.

**Recommended Approach:** Simplify to **one job** - emit valid JSON only. Cut from 1,339 words to ~450 words.

**Expected Impact:**
- Parse rate: 90-98% → **98-99%**
- Metadata completeness: Missing page numbers → **100%**
- Prompt length: 1,339 words → **~450 words**

---

## Root Cause Analysis (Why 10% Parse Failures)

1. **Mixed objectives** - v4 asks for extraction + dual classification + sequencing + embedding hygiene in one pass (too much for nano)
2. **Verbosity → drift** - Long admonitions ("CRITICAL", multi-section examples) increase preamble leakage
3. **Ambiguous heading logic** - Asking model to classify AND filter headings while producing JSON increases failure modes

---

## Recommended Changes

### 1. API Guardrails
- `temperature=0`, `top_p=1`
- **Use JSON-schema/structured-output** if available
- Enable JSON validator + single auto-repair pass

### 2. Page Number Injection (CRITICAL FIX)
- Pass `PDF_PAGE={N}` in the input
- Include **pre-filled field** in JSON skeleton: `"pdf_page": {{PDF_PAGE}}`
- Model copies it → guaranteed presence

### 3. Simplify Classification
- ❌ **Remove:** "heading vs substantive" classification
- ❌ **Remove:** Dual taxonomy
- ✅ **Keep:** Single `provision_type` field with 4 values:
  - `definition` - uses "means"
  - `operational` - SHALL/MUST/MAY/WILL, procedures
  - `regulatory` - cites IRC/Code sections
  - `unknown` - safe fallback

### 4. Empty Page Behavior
- When page has headings only or "continued on next page": return `[]`
- No prose, no explanations
- **This alone eliminates most parse failures**

### 5. Shorten to ~450 Words
**Keep:**
- Minimal schema
- 1 tiny positive example
- 1 empty-page example
- 5 exclusion bullets
- Output rules

**Remove:**
- Global ID talk (handle in post-processing)
- Long taxonomy prose
- Semantic fingerprinting guidance (handle in code)
- Redundant warnings

---

## Recommended Prompt v5 (~450 words)

```text
SYSTEM (concise role)
You extract provisions from a single BPD page and return JSON ONLY. No code fences, no prose.

USER
INPUTS
- PDF_PAGE: {{PDF_PAGE}}   // integer
- IMAGE: (the page image)

TASK
From this page, extract only substantive provisions (actual legal content). Skip headings, TOC lines, headers/footers, section dividers, and pages that say only "(continued on next page)".

OUTPUT
Return a JSON array. Each item must have exactly these keys:

{
  "pdf_page": {{PDF_PAGE}},                 // copy the page number exactly
  "section_number": "string",               // e.g., "1.01" or "" if not shown
  "section_title": "string",                // e.g., "Eligibility" or "" if none
  "provision_text": "string",               // verbatim, complete sentences; preserve paragraph breaks with \n\n
  "provision_type": "definition|operational|regulatory|unknown"
}

RULES
- JSON array only. No preface or trailing text.
- Extract each definition or rule as its own provision.
- A heading with no following sentences is NOT a provision.
- If nothing substantive appears on this page, return [].
- Don't summarize or paraphrase. Copy text verbatim (normalized whitespace is OK).
- If a table conveys a rule, include it as plain text with line breaks.
- Heuristics:
  • Definitions often use "means".
  • Operational language often uses SHALL/MUST/MAY/WILL or prescribes schedules/procedures.
  • Regulatory provisions cite Code/Reg sections (e.g., IRC §401(a)(9)).
  Choose the single best `provision_type`; if uncertain, use "unknown".

TINY EXAMPLES
// If the page has two definitions:
[
  {
    "pdf_page": 7,
    "section_number": "1.01",
    "section_title": "Account",
    "provision_text": "'Account' means the individual account maintained for a Participant...",
    "provision_type": "definition"
  },
  {
    "pdf_page": 7,
    "section_number": "1.02",
    "section_title": "Administrator",
    "provision_text": "'Administrator' means the person or entity designated as Plan Administrator...",
    "provision_type": "definition"
  }
]

// If the page has headings only:
[]
```

---

## Optional: JSON Schema Enforcement

If using structured output API:

```json
{
  "type": "array",
  "items": {
    "type":"object",
    "required":["pdf_page","section_number","section_title","provision_text","provision_type"],
    "properties":{
      "pdf_page":{"type":"integer","const":{{PDF_PAGE}}},
      "section_number":{"type":"string"},
      "section_title":{"type":"string"},
      "provision_text":{"type":"string"},
      "provision_type":{"type":"string","enum":["definition","operational","regulatory","unknown"]}
    },
    "additionalProperties": false
  }
}
```

**Expected result:** Parse rate **≥98-99%** with `temperature=0`

---

## Retry/Repair Pattern (Robustness)

**Pass 1:** Run v5 prompt, validate JSON
**If invalid:** Run 1-line repair:
  - *"Output valid JSON only. Remove any text before/after the array. Do not change content."*
**If still invalid:** Fall back to minimal extractor (~120 words, no examples)

**Sergio's idea:** Retry with GPT-5-mini instead of nano on failures

---

## Why This Hits Success Metrics

| Metric | Current v4 | Proposed v5 | How |
|--------|-----------|-------------|-----|
| Parse Rate | 90-98% | **98-99%** | Fewer moving parts + JSON enforcement + empty-array rule |
| Metadata | Missing page # | **100%** | `pdf_page` pre-filled & copied |
| Accuracy | Mostly good | **Same or better** | Narrow, testable rules; tables retained |
| Consistency | Variable | **High** | Single taxonomy, no dual labels, fewer branches |
| Brevity | 1,339 words | **~450 words** | Ruthless focus on extraction job only |

---

## Implementation Checklist

### Phase 1: Prompt Redesign
- [ ] Create `prompts/provision_extraction_v5.txt` with expert's template
- [ ] Add page number substitution: `{{PDF_PAGE}}` placeholder
- [ ] Test on 5 sample pages manually
- [ ] Verify JSON validity and completeness

### Phase 2: Extractor Updates
- [ ] Modify `src/extraction/parallel_vision_extractor.py`:
  - [ ] Inject page number into prompt (substitute `{{PDF_PAGE}}`)
  - [ ] Add `temperature=0, top_p=1` to API call
  - [ ] Add JSON validation after each response
  - [ ] Implement retry-with-repair on parse failures
  - [ ] Record failed pages in output metadata
- [ ] Add retry-with-mini fallback (Sergio's suggestion)
- [ ] Log all parse failures with page numbers

### Phase 3: Re-Extraction
- [ ] Re-extract Relius BPD (98 pages)
- [ ] Re-extract Ascensus BPD (81 pages)
- [ ] Verify 98%+ parse rate
- [ ] Verify 100% have page numbers
- [ ] Compare provision counts to v4 (sanity check)

### Phase 4: Validation
- [ ] Red Team Sprint on v5 extractions
- [ ] Manual review of 10 random provisions
- [ ] Verify no section headings extracted
- [ ] Verify complete provision text (no truncation)
- [ ] Document results in new sprint summary

---

## Next Steps

**Immediate (Today):**
1. Create v5 prompt file
2. Update extractor to inject page numbers
3. Test on 5 pages

**This Week:**
1. Re-extract all BPD documents
2. Validate quality
3. Update PIPELINE.md with v5 details

**Blocked Until Complete:**
- Section 1.2 (AA Extraction) validation
- Section 2 (Post-processing) validation
- Section 3 (Crosswalks) validation

---

## Expert's Offer

> "If you want, I can also give you the ultra-short fallback prompt and a tiny JSON validator/auto-repair snippet you can drop into the workers."

**Recommendation:** Accept this offer if initial v5 implementation still shows >2% failures.

---

## Questions to Resolve

1. **JSON Schema Support:** Does OpenAI Vision API support structured output/JSON schema mode?
   - If yes: Implement it (biggest reliability gain)
   - If no: Use retry-with-repair pattern

2. **Fallback Strategy:** When to use mini vs repair?
   - Option A: Repair first, then mini if repair fails
   - Option B: Mini immediately on parse failure (more expensive but more reliable)

3. **Empty Pages:** Should we record them or just skip?
   - Current: Skip (no record)
   - Proposed: Record as `{"pdf_page": N, "provisions": []}` for audit trail

---

**Status:** Ready to implement. Awaiting approval to proceed.
