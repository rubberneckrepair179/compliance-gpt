# Handoff: Extraction Pipeline Complete + Architecture Decision Needed
**From:** Claude Code
**Date:** 2025-10-30
**Session Duration:** ~3 hours
**Status:** Extraction complete, awaiting v5.2 architecture decision

---

## What Was Accomplished

### 1. Full Extraction Pipeline Complete ✅
All 4 documents successfully extracted:
- **Relius BPD v4.1:** 565 provisions (98% success)
- **Ascensus BPD v4.1:** 466 provisions (100% success)
- **Relius AA v5.1:** 1,216 provisions (95.6% success)
- **Ascensus AA v5.1:** 2,654 provisions (95.2% success)

**Total: 4,901 provisions** across 328 pages, **96.4% overall success rate**

### 2. Critical Discovery: Fragmentation Pattern
User identified that **all 12 failed pages** (5 Ascensus, 7 Relius) share a common pattern:
- Pages start mid-hierarchy (H3/H4 depth provisions)
- Parent sections exist on previous page
- LLM cannot see parent context (parallel page-by-page processing)
- Results in: schema violations (missing `form_elements`) or truncated responses

**Key insight:** This is not random LLM failure - it's a systematic **information availability problem**.

### 3. Architecture Consultation Completed
Created comprehensive consultation document with 5 solution options.

**Consultant Response Received:**
- **Recommended:** Hybrid approach (Option 4 + Option 5 + layout hints)
- Two-stage extraction: fast sweep + selective overlap
- Schema relaxation: explicit uncertainty (`status`, `evidence`, `confidence`)
- Deterministic global reconciliation (rule-based, not LLM)
- Selective re-extract for only ~10-20% fragment pages

**Industry Best Practices Identified:**
1. Two-stage architecture (cheap layout pass + targeted context)
2. Schema with uncertainty (never omit fields, admit uncertainty explicitly)
3. Deterministic global reconciliation (section number pattern matching)
4. Confidence audit trail (status/evidence for QA)
5. Selective overlap (cost control through targeted repair)

**Meta-Lesson:** Stop trying to make LLM perfect. Make the SYSTEM reliable.

---

## Files Created/Modified

### Created:
- **SESSION_SUMMARY.md** - Comprehensive session summary with achievements, learnings, next steps
- **docs/AA_V5.1_FRAGMENTATION_CONSULTATION_2025-10-30.md** - Architecture consultation request + response
- **docs/EXTRACTION_COMPLETE_NEXT_STEPS.md** - 6-phase roadmap with hanging questions
- **team/handoffs/2025-10-30_claude_extraction_complete.md** - This file

### Modified:
- **PIPELINE.md** - Updated with v4.1 BPD + v5.1 AA extraction results

### Extraction Outputs (all in test_data/):
- `extracted_vision_v4.1/relius_bpd_provisions.json`
- `extracted_vision_v4.1/ascensus_bpd_provisions.json`
- `extracted_vision_v5.1/relius_aa_provisions.json`
- `extracted_vision_v5.1/ascensus_aa_provisions.json`

---

## Decision Point: v5.2 Architecture

**Current Status:** Awaiting user decision on consultant-recommended architecture

### Recommended Approach (from consultant):

**AA v5.2 Schema Changes:**
```json
{
  "parent_section": {
    "value": "2.d" | "UNKNOWN",
    "status": "confirmed" | "estimated" | "unknown",
    "evidence": "prefix" | "indent" | "context_header" | "none",
    "confidence": 0.0-1.0
  },
  "local_ordinal": {
    "value": 2 | null,
    "status": "confirmed" | "estimated" | "unknown"
  },
  "fragment_start": true|false,
  "indent_depth_hint": 3,
  "first_section_prefix": "2.d",
  "form_elements": []  // always present, empty when none
}
```

**Pipeline Architecture:**
1. **Pass A:** Fast parallel page-by-page (all pages, admit uncertainty)
2. **Fragment Detection:** Deterministic (indent delta, section depth, heading absence, LLM hint)
3. **Pass B:** Selective re-extract (~10-20% pages) with context header from page N-1
4. **Post-Processing:** Global repair (parent inference, ordinal assignment, confidence upgrade)

**Expected Outcomes:**
- ≥98% page success rate (from 95.3%)
- No schema violations (explicit uncertainty instead of omitted fields)
- ~13 minutes processing (1.2x cost, not 2x)
- Auditable confidence trails

### Open Questions for Next Session:

1. **Schema nesting:** Keep nested through pipeline, or flatten after global repair?
2. **Context header:** Separate fields or visual separator in prompt?
3. **Validation approach:** Test on 5 failing pages first, or full implementation?
4. **JSON Schema Structured Outputs:** Add now (prevents field omission) or defer?
5. **Timeline:** Validate core concept first (1 day), or proceed directly to full implementation (2-3 days)?

---

## Next Session Plan (Proposed)

### Phase 1: Validate Core Concept (Immediate - Day 1)
1. Draft v5.2 schema with nested parent_section/local_ordinal
2. Patch AA v5.1 prompt with 4 consultant clauses:
   - Schema presence rule (never omit fields, admit uncertainty)
   - Fragment flags (fragment_start, indent_depth_hint, first_section_prefix)
   - Hierarchy discipline (use UNKNOWN when parent not on page)
   - Context header usage (for Pass B only)
3. Manually test on 5 failing pages with hand-crafted context headers
4. Verify: No schema violations, correct parent inference

### Phase 2: Build Fragment Detection (Day 2)
1. Implement deterministic fragment detector:
   - Indent delta (z-score from page median)
   - Section depth (≥2 delimiters, no same-page parent)
   - Heading absence (no H1/H2 in first 8 lines)
   - LLM hint (from Pass A)
2. Test on full Ascensus AA (which pages get flagged?)
3. Validate flagging accuracy against manual inspection

### Phase 3: Automate Pass B (Day 2-3)
1. Build context header extractor (last 10-20 lines from previous page)
2. Implement selective re-extract pipeline
3. Run full Ascensus AA with Pass A + Pass B
4. Compare v5.1 (95.2%) vs v5.2 (target ≥98%)

### Phase 4: Global Repair (Day 3)
1. Implement post-processing defragmenter:
   - Canonicalize section numbers (`2.d.2` → `[2, d, 2]`)
   - Infer parents (drop last tier, walk up until found)
   - Assign ordinals (sort by reading order within parent)
   - Upgrade confidence (Pass B confirmations)
2. Flatten schema for downstream consumption (optional)

**Estimated timeline:** 2-3 days for full implementation + validation

---

## Current Blockers

None - extraction pipeline complete, awaiting architectural decision from user.

---

## Key Learnings for Next Agent

### 1. Fragmentation is Systematic, Not Random
All extraction failures share a common root cause: pages starting mid-hierarchy. This is an **information availability problem**, not an LLM quality issue.

### 2. Rigid Schema Causes Cascading Failures
Forcing `parent_section` to be required when the answer isn't on the page leads to:
- Hallucination (LLM invents wrong parent)
- Omission (schema violation, extraction fails)
- Truncation (LLM burns tokens trying to explain uncertainty, hits max_completion_tokens)

**Solution:** Allow explicit uncertainty with status/evidence/confidence.

### 3. Production Systems Use Two-Stage + Uncertainty
Industry best practice is NOT perfect first-pass extraction. It's:
- Fast sweep with explicit uncertainty admission
- Deterministic detection of ambiguity (fragmentation)
- Selective targeted repair (only pages that need context)
- Rule-based global reconciliation (don't use LLM for bookkeeping)

### 4. Cost Control Through Selectivity
Don't double cost for all pages (Option 2 - full overlap).
- Identify the ~10-20% that need context
- Only pay for those (Option 4 - selective overlap)
- Result: 1.2x cost instead of 2x, achieves ≥98% success

### 5. Audit Trails Are Requirements, Not Overhead
For compliance software:
- `status`/`evidence`/`confidence` enable downstream QA filtering
- Regulatory audit defense: "How was parent determined?" → `evidence="prefix", confidence=0.95`
- Threshold-based processing: only use `confidence ≥ 0.9` provisions

---

## Git Status (Ready to Commit)

**Modified:**
- PIPELINE.md (updated with v4.1 + v5.1 results)
- SESSION_SUMMARY.md (created)

**New Files:**
- docs/AA_V5.1_FRAGMENTATION_CONSULTATION_2025-10-30.md
- docs/EXTRACTION_COMPLETE_NEXT_STEPS.md
- team/handoffs/2025-10-30_claude_extraction_complete.md

**New Extractions:**
- test_data/extracted_vision_v4.1/ (BPD outputs)
- test_data/extracted_vision_v5.1/ (AA outputs)

**Commit Message:**
```
Complete extraction pipeline: BPD v4.1 + AA v5.1 (4,901 provisions)

- All 4 documents extracted (96.4% overall success)
- Critical discovery: fragmentation pattern in failed pages
- Architecture consultation: v5.2 two-stage + selective overlap
- Industry best practices: schema with uncertainty, deterministic repair
- Awaiting user decision on v5.2 implementation

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Recommendations for Next Agent

1. **Start with decision:** Ask user to decide on v5.2 architecture approach
2. **Incremental validation:** Test core concept on 5 pages before full implementation
3. **Reference consultant response:** All architectural guidance in fragmentation consultation doc
4. **Trust the industry practices:** Two-stage + selective overlap is proven, not experimental
5. **Focus on system reliability:** Don't over-optimize LLM, build reliable pipeline

---

**Next Steps:** User decision on v5.2 → validation → implementation → Phase 2 (post-processing)
