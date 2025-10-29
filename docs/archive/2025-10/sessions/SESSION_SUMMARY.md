# Session Summary: Oct 19, 2025 - BPD+AA Architecture Discovery

**Context for Next Session:** This document provides complete context for continuing POC development after discovering the BPD+AA document structure.

---

## Executive Summary

**What We Discovered:**
The POC was based on a false premise. We thought we were comparing a standalone BPD (with specific values like "age 21") to a template BPD (with "as elected in AA" placeholders).

**Reality (validated by GPT-5 Pro):**
- **BOTH BPDs are templates** that defer to Adoption Agreements for actual values
- Our LLM **hallucinated** "age 21" from prompt examples - this text doesn't exist in the source BPD
- The actual source BPD says "as specified in the Adoption Agreement" (same as target)
- We have **4 files representing 2 complete plan sets**, not 2 independent pairs

**Impact:**
- Complete architectural pivot required
- Document merger layer needed (BPD + AA → complete provisions)
- Two analysis modes needed (validation vs prospective)
- CSV output only (NO document generation per user constraint)
- Executive summary report as value-add for customers

---

## Document Structure (Validated by GPT-5)

### What We Have

**Source Plan (Old/Current):**
- `pair_a_source_bpd.pdf` - Ascensus BPD 01 (template, says "specified in AA")
- `pair_b_source_adoption.pdf` - Source Adoption Agreement (actual elections)
- **Together:** Complete source plan specification

**Target Plan (New):**
- `pair_a_target_bpd.pdf` - Ascensus BPD 05 (template, says "as elected in AA")
- `pair_b_target_adoption_locked.pdf` - Target Adoption Agreement (actual elections, password-protected)
- **Together:** Complete target plan specification

### Key Findings from GPT-5 Analysis

**BPD Structure:**
- Both BPDs are **Ascensus templates** (same vendor, different versions)
- BPD 01 uses "Section" numbering (e.g., Section 2.01, Section 4.01)
- BPD 05 uses "Article" numbering (e.g., Article III, Article XIII)
- **BPD 05 distributes provisions** - vesting split across Articles I, III, XIII (not consolidated)

**Critical Section Mappings:**

| Topic | Source BPD 01 | Target BPD 05 | Notes |
|-------|---------------|---------------|-------|
| Eligibility | 2.01 | 3.1, 3.2 | Both defer to AA for age/service |
| Rehire/Breaks | 2.04 | 3.5 | Same logic, both reference AA |
| Always Vested Sources | 4.02 | **1.1(b), 1.1(f), 1.1(g)** | NOT 13.5 (SIMPLE-only) |
| Vesting Schedule | 4.01 | 1.87 + 3.5(f) + AA | Distributed across multiple sections |

**Our Extraction Error:**
- Extracted: "age 21 and completing one Year of Service"
- Actual BPD text: "upon satisfying the age and eligibility service requirements **specified in the Adoption Agreement**"
- Source: Prompt examples (lines 14, 63 in provision_extraction_v2.txt)
- LLM pattern-matched and substituted example values

---

## Architectural Implications

### Old Architecture (Wrong)
```
Extract from Source BPD → Extract from Target BPD → Compare
         ↓                         ↓
  (hallucinated "age 21")    ("as elected in AA")
         ↓                         ↓
    Different text → LLM: "no match" ✓ (correct assessment of wrong data)
```

### New Architecture (Correct)
```
Source Plan:
  SBPD (template) + SAA (elections) → Merger → Complete provisions

Target Plan:
  TBPD (template) + TAA (elections) → Merger → Complete provisions

Complete provisions → Semantic Mapper → CSV Output + Executive Summary
```

### Two Analysis Modes

**Mode 1: Validation (Election-to-Election)**
- Input: SBPD + SAA + TBPD + TAA (all 4 documents, TAA already drafted)
- Output: Variance report comparing actual elections made
- Use case: QC/validation - "Does my completed TAA match the source plan?"

**Mode 2: Prospective (Election-to-Options)**
- Input: SBPD + SAA + TBPD (template only, TAA not yet drafted)
- Output: Recommendations for TAA elections to match source
- Use case: Drafting assistance - "What should I elect in TAA?"

### Key Constraint: No Document Generation

**User requirement:** Our tools should NOT generate legal documents (TPAs have their own doc generators)

**Our output:**
- ✅ CSV with mapping analysis (provision relationships, variances, recommendations)
- ✅ Executive summary in natural language (for sponsor/TPA review)
- ❌ NOT: Filled-in TAA documents, BPD overlays, or any legal paperwork

**Integration point:**
```
Our CSV output → TPA imports → Their doc generator → Legal documents
```

---

## Files Updated This Session

### Core Documentation
- ✅ `CLAUDE.md` - Updated project status, architectural pivot, current tasks
- ✅ `process/control_002_document_reconciliation.md` - Added BPD+AA merger step, new artifacts
- ✅ `GPT5_VALIDATION.md` - Complete GPT-5 findings (45+ pages)
- ✅ `OPUS_VALIDATION.md` - Initial Opus 4.1 findings
- ✅ `POC_FINDINGS.md` - Analysis of 0% match rate
- ✅ `CRITICAL_QUESTION.md` - Document pairing structure question (now resolved)
- ✅ `SESSION_SUMMARY.md` - This file

### POC Implementation
- ✅ `prompts/provision_extraction_v2.txt` - Created (but has hallucination bug)
- ✅ `scripts/extract_operational_provisions.py` - Extracts with v2 prompt (hallucinated results)
- ✅ `scripts/test_operational_mapping.py` - Semantic mapper test (0% matches, correctly)
- ✅ `scripts/analyze_opus_pairs.py` - Embedding analysis (proved embeddings work)
- ✅ `scripts/test_single_pair.py` - LLM verification test (proved LLM works)

### Test Data
- ✅ `test_data/processed/pair_a_source_bpd_operational_provisions.json` - Has hallucinated values
- ✅ `test_data/processed/pair_a_target_bpd_operational_provisions.json` - Has actual template text
- ✅ `test_data/processed/pair_a_operational_comparison.json` - 0% matches (correct for template-to-template)

---

## What Works (Don't Need to Rebuild)

### ✅ Semantic Mapper Algorithm
- Hybrid embeddings + LLM verification works correctly
- Embeddings ranked Opus-identified pairs as #1 (0.814 similarity)
- LLM correctly assessed template vs values as "no match"
- Confidence scoring is accurate (85-100% on clear non-matches)

**Proof:** When given Section 2.01 → Section 3.1 (Opus said these match conceptually):
- Embeddings ranked it #1 of 5 targets (0.814 similarity)
- LLM said "no match" with 85% confidence
- Reasoning: "Source has concrete values, target defers to AA" ✓ CORRECT

### ✅ Provision Models
- Pydantic models are well-designed
- ProvisionType enum covers all cases
- ProvisionMapping captures all needed metadata
- DocumentComparison aggregates results correctly

### ✅ Infrastructure
- PDF extraction works (pdfplumber)
- OpenAI API integration works
- Prompt externalization works
- Rich console output works

---

## What Needs Fixing (Priority Order)

### 🔴 Priority 1: Fix Extraction Hallucination

**File:** `prompts/provision_extraction_v2.txt`

**Problem:** Lines 14 and 63 contain examples with "age 21 and one Year of Service" - LLM uses these as templates and invents values

**Solution:**
```markdown
Examples:
✓ "An Employee shall be eligible upon satisfying the age and service
   requirements specified in the Adoption Agreement."

NOT:
✗ "An Employee shall be eligible upon attaining age 21..." (this is AA text)

CRITICAL: PRESERVE TEMPLATE LANGUAGE EXACTLY
- If provision says "as elected in the Adoption Agreement", keep that phrase
- If provision says "as specified in the Adoption Agreement", keep that phrase
- DO NOT substitute example values or numbers
- Extract ACTUAL text from document, not what you think it should say
```

### 🔴 Priority 2: Re-Extract from BPDs

**Files to regenerate:**
- `test_data/processed/pair_a_source_bpd_operational_provisions.json`
- `test_data/processed/pair_a_target_bpd_operational_provisions.json`

**Expected results:**
```json
// Source Section 2.01 (after fix)
{
  "provision_text": "Each Employee will be eligible upon satisfying the age
                     and eligibility service requirements specified in the
                     Adoption Agreement.",
  "extracted_entities": {
    "ages": [],
    "service_years": [],
    "template_references": ["Adoption Agreement"]
  }
}
```

**Validation:** Both should now have empty ages/service_years arrays and template_references populated

### 🟡 Priority 3: Adoption Agreement Extraction

**New capability needed:**

**Files:**
- `src/extraction/aa_parser.py` - Parse AA checkboxes and fill-ins
- `src/models/aa_election.py` - Data model for elections
- `prompts/aa_extraction_v1.txt` - Prompt for extracting elections

**Key challenge:** AAs have checkboxes, fill-in fields, pick-lists
- Need to detect selected options
- Map to provision types
- Handle locked PDFs (target AA is password-protected)

**Example output:**
```json
{
  "document_id": "pair_b_source_adoption",
  "elections": [
    {
      "provision_type": "eligibility",
      "field_name": "minimum_age",
      "elected_value": "21",
      "section_reference": "AA Section 2.1"
    },
    {
      "provision_type": "eligibility",
      "field_name": "service_requirement",
      "elected_value": "1 year",
      "section_reference": "AA Section 2.1"
    }
  ]
}
```

### 🟡 Priority 4: BPD Crosswalk

**New file:** `design/bpd_crosswalk.json`

**Purpose:** Map BPD 01 sections → BPD 05 sections by topic

**Structure (from GPT-5 findings):**
```json
{
  "topics": [
    {
      "topic": "eligibility",
      "bpd_01_sections": ["2.01", "2.02"],
      "bpd_05_sections": ["3.1", "3.2"],
      "aa_field": "eligibility_requirements"
    },
    {
      "topic": "always_vested_sources",
      "bpd_01_sections": ["4.02"],
      "bpd_05_sections": ["1.1(b)", "1.1(f)", "1.1(g)"],
      "aa_field": null,
      "notes": "Not elected in AA - always true per IRS rules"
    },
    {
      "topic": "vesting_schedule",
      "bpd_01_sections": ["4.01"],
      "bpd_05_sections": ["1.87", "3.5(f)", "AA"],
      "aa_field": "vesting_schedule",
      "notes": "BPD 05 distributes: defs (1.87), breaks (3.5f), schedule (AA)"
    }
  ]
}
```

**Critical mappings from GPT-5:**
- Section 4.02 → **1.1(b), 1.1(f), 1.1(g)** (NOT 13.5, which is SIMPLE-only)
- Section 4.01 → Multiple BPD 05 sections (distributed provision)
- Section 2.03 → 3.2(d) + 3.2(e) (split into subsections)

### 🟡 Priority 5: BPD+AA Merger

**New file:** `src/extraction/provision_merger.py`

**Purpose:** Substitute AA elections into BPD template provisions

**Input:**
- BPD provision: "upon satisfying the age... specified in the Adoption Agreement"
- AA election: "age: 21, service: 1 year"

**Output:**
- Complete provision: "upon satisfying age 21 and 1 Year of Service requirements"

**Edge cases:**
- Optional provisions (if not elected, don't include)
- Custom elections (free-form text fields)
- Distributed provisions (multiple BPD sections + one AA election)

### 🟢 Priority 6: Enhanced Semantic Mapping Prompts

**New prompts needed:**

**`prompts/semantic_mapping_v2_election_to_election.txt`**
- Compare two complete provisions with actual elections
- Focus on substantive differences
- Ignore template language differences

**`prompts/semantic_mapping_v2_election_to_options.txt`**
- Compare source election to target available options
- Recommend best match
- Flag when no exact match exists

**Key addition: Schema-level equivalence**
```markdown
TEMPLATE EQUIVALENCE:

Source: "age 21 and one Year of Service"
Target: "age and service requirements as elected in AA"
→ Classification: SCHEMA-EQUIVALENT (same parameter)
→ Variance: administrative (not substantive)
→ Requires: AA verification to confirm elected values
```

### 🟢 Priority 7: CSV Output & Executive Summary

**New files:**
- `src/output/csv_generator.py` - Generate mapping analysis CSV
- `src/output/summary_generator.py` - Generate NL executive summary

**CSV Schema:**
```csv
source_provision,target_provision,source_election,target_election,match,variance_type,impact,confidence,needs_review,reasoning
"SBPD §2.01 Eligibility","TBPD §3.1 Eligibility","Age 21, 1 YOS","Age 21, 1 YOS",TRUE,none,none,0.95,FALSE,"Identical eligibility"
```

**Executive Summary (natural language):**
```markdown
# Plan Conversion Analysis: BPD 01 → BPD 05

## Summary
Compared 15 provisions across source and target plans.
- 12 matches (80%)
- 2 design variances requiring sponsor approval
- 1 missing provision flagged for review

## Key Findings
### Design Variances (Sponsor Approval Required)
1. **Vesting Schedule Change** (High Impact)
   - Source: 6-year graded (20/40/60/80/100)
   - Target: 3-year cliff (0/0/100)
   - Impact: Accelerates vesting for participants

### Missing Provisions
1. **Forfeiture Application** (Review Required)
   - Source used forfeitures to reduce admin expenses
   - Target options: reduce contributions | pay expenses | reallocate
   - Recommendation: Select "pay plan expenses" (closest match)
```

---

## Immediate Next Steps (For Next Session)

### Session Start Checklist
1. Read `GPT5_VALIDATION.md` (comprehensive findings)
2. Read this file (`SESSION_SUMMARY.md`)
3. Review updated `CLAUDE.md` (architectural context)

### Task 1: Fix Extraction Prompt (30 min)
- Edit `prompts/provision_extraction_v2.txt` → v3
- Remove examples with specific values (lines 14, 63)
- Add PRESERVE TEMPLATE LANGUAGE instruction
- Add negative examples (what NOT to do)

### Task 2: Re-Extract from BPDs (15 min)
- Run extraction script with v3 prompt
- Validate results: check for "as specified in AA" text
- Verify ages/service_years are empty arrays

### Task 3: Validate Template Preservation (15 min)
- Manually check extracted JSON against actual PDF
- Search PDF for extracted text (should exist verbatim)
- Confirm no hallucinated values

### Task 4: Design AA Parser (1-2 hours)
- Review `pair_b_source_adoption.pdf` structure
- Identify checkbox/fill-in patterns
- Design data model for elections
- Draft extraction prompt

---

## Key Insights to Remember

### 1. BPDs are Templates, AAs are Instances
> "Use the BPDs only as dictionaries/guardrails." - GPT-5

Don't treat BPD text as plan specifications. BPDs define what's *possible*, AAs define what's *actual*.

### 2. Section Numbering is NOT Semantic
> "Section numberings are more syntax than semantics in my mind" - User

Section numbers are metadata for traceability, not the primary comparison dimension. Focus on provision PURPOSE.

### 3. LLMs Will Hallucinate from Examples
We gave an example with "age 21" and the LLM pattern-matched, generating fake values. **Never put specific values in extraction examples unless you want the LLM to use them as templates.**

### 4. Our 0% Match Rate Was CORRECT
The algorithm correctly identified that template text ("as elected in AA") doesn't match hallucinated values ("age 21"). This validates our semantic mapper works - we just gave it the wrong inputs.

### 5. Distributed Provisions are Common
BPD 05 splits vesting across:
- Article I (definitions: what's always vested)
- Article III (break-in-service rules)
- Article XIII (SIMPLE-specific rules)
- AA (vesting schedule)

Can't rely on "Section N: Vesting" containing everything.

### 6. Plan Type Matters (SIMPLE vs Regular)
BPD 05 Section 13.5 is **SIMPLE 401(k) only**. We incorrectly mapped general vesting to it. Must detect plan type and scope section usage.

### 7. Two Modes, One Algorithm
Validation (election-to-election) and Prospective (election-to-options) use the **same semantic mapper**, just different prompts and output schemas.

### 8. No Document Generation Constraint
TPAs already have document generators (Relius, ASC, ftwilliam). Our value is the **intelligence layer** (mapping analysis), not document authoring. Output CSV for import into their tools.

---

## Questions Resolved This Session

**Q: Are we comparing the wrong things?**
✅ Yes. We were comparing templates to templates instead of complete provisions.

**Q: Is this a prompt fault or data structure problem?**
✅ Data structure. The prompt worked correctly on wrong inputs.

**Q: Do we have 2 pairs (A and B) or 2 sets (source and target)?**
✅ 2 sets. SBPD+SAA = source plan, TBPD+TAA = target plan.

**Q: Should SAA and TAA be compared independently?**
✅ No. AA option codes are meaningless without BPD definitions. Must compare [BPD+AA] merged units.

**Q: Should we generate TAA documents?**
✅ No. TPAs have their own generators. We output CSV mapping analysis only.

---

## Open Questions for Next Session

1. **How to unlock target AA?** `pair_b_target_adoption_locked.pdf` is password-protected
   - Try common passwords?
   - Use vision model to extract even if locked?
   - Ask user for unlocked copy?

2. **How much AA structure is standardized?** Can we build generic AA parser or need vendor-specific parsers?

3. **What about custom elections?** AAs allow free-form text - how to handle?

4. **Should we implement Mode 1 or Mode 2 first?** Validation or Prospective?

5. **CSV schema - match existing template?** Should output match `process/templates/plan_comparison_workbook.csv`?

---

## Files Ready for Next Session

### Documentation (All Updated)
- ✅ `CLAUDE.md` - Complete project context
- ✅ `GPT5_VALIDATION.md` - Comprehensive findings (reference document)
- ✅ `SESSION_SUMMARY.md` - This handoff document
- ✅ `process/control_002_document_reconciliation.md` - Updated artifacts

### Code (Working, Needs Update)
- ⚠️ `prompts/provision_extraction_v2.txt` - Has hallucination bug (FIX FIRST)
- ✅ `src/extraction/pdf_extractor.py` - Works correctly
- ✅ `src/extraction/provision_parser.py` - Works, loads external prompts
- ✅ `src/mapping/semantic_mapper.py` - Works correctly (proved by tests)
- ✅ `src/models/provision.py` - Data models good
- ✅ `src/models/mapping.py` - Data models good

### Test Data (Some Invalid)
- ⚠️ `test_data/processed/pair_a_source_bpd_operational_provisions.json` - Has hallucinated values (RE-EXTRACT)
- ✅ `test_data/processed/pair_a_target_bpd_operational_provisions.json` - Has actual template text
- ✅ `test_data/raw/` - All 4 PDFs (valid)

---

## Success Metrics for Next Session

**Minimum viable progress:**
1. ✅ Extraction prompt fixed (no hallucination)
2. ✅ Re-extracted BPDs with actual template text
3. ✅ Validated against PDF (text exists verbatim)

**Stretch goals:**
4. ✅ AA parser designed (data model + prompt)
5. ✅ Extracted elections from source AA
6. ✅ BPD crosswalk started (key mappings from GPT-5)

**Long-term goal:**
7. ⬜ First merged provision comparison (expect matches!)

---

*Session ended at ~50% context capacity (96K/200K tokens)*
*Ready to continue with clear architectural understanding and prioritized tasks*

---

## Oct 30, 2025 — AA Crosswalk Pipeline Hardening

**Highlights:**
- ✅ Converted v6 AA provisions to the `Election` schema (`scripts/convert_aa_v6_to_elections.py`, converted JSON artifacts under `test_data/extracted_vision_v6/*_converted.json`).
- ✅ Upgraded AA prompt to v1.1.1 (mirrors BPD v3 discipline, adds cross-field rules, richer few-shots).
- ✅ Added parser guardrails in `AASemanticMapper` to reject incomplete LLM responses (empty rationale, missing abstain reasons, incompatible/impact mismatch) and updated data model to accept structured consistency checks.
- ✅ Expanded unit test suite (`tests/test_aa_semantic_mapper.py`, 8 cases) covering validation fallbacks.
- ✅ Pipeline docs bumped to v8, documenting conversion stage + new prompt requirements.

**Outstanding:**
- Await Claude’s rerun of `scripts/run_aa_crosswalk.py` with the new prompt to confirm abstain reasoning now populates (logs + JSON review still pending).
- Need to update `test_results/crosswalk_runs.md` once new run completes and capture reasoning metrics.

**Next session priorities:**
1. Review rerun outputs (reasoning quality, match distribution) and adjust prompt if we still see unjustified abstains.
2. Backfill sprint board / docs with run metrics and link to new artifacts.
3. Start planning conditional/compatible heuristics once reasoning fields are reliable.
