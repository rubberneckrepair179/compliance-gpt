# GPT-5 Pro Validation Results

**Date:** 2025-10-19
**Validator:** OpenAI GPT-5 Pro (with actual PDF documents)
**Status:** 🔴 CRITICAL - Invalidates previous POC approach, defines new architecture

---

## Executive Summary

**TL;DR:** Our entire POC was based on a false premise. We thought we were comparing standalone BPD vs template BPD. In reality, **BOTH are templates** that defer to Adoption Agreements, and **our LLM hallucinated the specific values** from prompt examples.

**The Real Problem:**
- We're not comparing BPD → BPD
- We're automating **plan conversion**, which means writing a **target Adoption Agreement**
- This requires **AA → AA mapping** (Mode A) or **BPD inference → AA** (Mode B)

---

## Critical Findings

### 1. Both BPDs Are Templates (Not Standalone)

**What we thought:**
- Source BPD (Doc 1) = Standalone with specific values ("age 21 and one Year of Service")
- Target BPD (Doc 2) = Template with AA references ("as elected in the Adoption Agreement")

**What GPT-5 proved:**
- Source BPD (Doc 1) = Ascensus **BPD 01** template, Section 2.01 says "**specified in the Adoption Agreement**"
- Target BPD (Doc 2) = Ascensus **BPD 05** template, Article 3.1 says "**as elected in the Adoption Agreement**"
- **BOTH defer to AAs for actual values**

**Evidence from actual PDF:**
```
Page 25, Section 2.01 (Source BPD):
"Each Employee... will be eligible to participate in this Plan upon satisfying
the age and eligibility service requirements SPECIFIED IN THE ADOPTION AGREEMENT."
```

We extracted: "age 21 and completing one Year of Service"
Actual text: "specified in the Adoption Agreement"

### 2. Our LLM Hallucinated Values from Prompt Examples

**The smoking gun:**

Our prompt ([prompts/provision_extraction_v2.txt](prompts/provision_extraction_v2.txt:14)) contained:
```
Examples:
✓ "An Employee shall be eligible to participate upon attaining age 21 and
   completing one Year of Service."
```

And the JSON example (line 63):
```json
"provision_text": "An Employee shall be eligible... age 21 and completing
                   one Year of Service..."
```

**What happened:**
1. LLM read: "upon satisfying the age and eligibility service requirements specified in the Adoption Agreement"
2. LLM pattern-matched to our example
3. LLM **substituted example values** ("age 21 and one Year of Service")
4. LLM returned hallucinated text as if it came from the document

**Verification:** Searched entire source BPD PDF - the phrase "age 21 and completing one Year of Service" **does not appear anywhere**.

### 3. Document Structure: 2 Plan Sets, Not 2 Pairs

**Correct interpretation:**

Our 4 files represent **2 complete plans** (old vs new):

**Source/Old Plan (complete):**
- `pair_a_source_bpd.pdf` - Ascensus BPD 01 (template)
- `pair_b_source_adoption.pdf` - Source Adoption Agreement (elected values)
- **Together:** Complete plan specification

**Target/New Plan (complete):**
- `pair_a_target_bpd.pdf` - Ascensus BPD 05 (template)
- `pair_b_target_adoption_locked.pdf` - Target Adoption Agreement (elected values)
- **Together:** Complete plan specification

**Not 2 independent pairs (A and B), but 2 sets (source and target).**

### 4. The Real Use Case: Writing Target Adoption Agreements

**What plan conversion actually means:**

When a TPA converts a plan from one vendor to another (or updates to new BPD version), they're not comparing BPDs - they're **writing a new Adoption Agreement** that mirrors the old plan's elections under the new BPD structure.

**Two modes of operation:**

**Mode A (preferred): AA → AA**
- Read **source Adoption Agreement** for elected values (age, service, vesting schedule, etc.)
- Map to **target Adoption Agreement** elections allowed under target BPD
- Use BPDs as "dictionaries/guardrails" for what's allowed

**Mode B (fallback): BPD inference → AA**
- When source AA is missing/lost
- Infer elections from source BPD operational text (if any exist)
- Or from SPD/"plan as operated" evidence
- Map to target AA
- Flag "needs human choice" for ambiguous items

**Our POC was attempting neither mode** - we were comparing template to template.

---

## Detailed GPT-5 Findings

### Document Identification

**Question:** Same vendor or different vendors?

**Answer:** Same vendor family (**Ascensus**), but different BPD templates:
- Doc 1: "Basic Plan Document 01, #3000 (Rev. 6/2020)"
- Doc 2: "Defined Contribution Pre-Approved Plan – Basic Plan Document 05"

Different article/section numbering systems, but both Ascensus pre-approved library.

### Section-by-Section Mapping Corrections

**Our wrong mappings:**

| Source | Target | Issue |
|--------|--------|-------|
| Section 4.02 (100% vesting) | Section 13.5 (VESTING REQUIREMENTS) | ❌ 13.5 is **SIMPLE 401(k) only**, not general vesting |

**Correct mappings:**

| Source (BPD 01) | Target (BPD 05) | Explanation |
|-----------------|-----------------|-------------|
| 2.01 Eligibility to Participate | 3.1 Conditions of Eligibility + 3.2 Effective Date | Same function, values in AA |
| 2.04 Break in Service/Rehire | 3.5 Rehired Employees and 1-Year Breaks | Same rehire/break logic |
| 2.03 Transfer to Ineligible Class | 3.2(d) + 3.2(e) | Doc 2 splits class changes into subsections |
| 4.01 Determining Vested Portion | 1.87 "Vested" definition + 3.5(f) break rules + AA schedule | BPD 05 distributes vesting across multiple sections |
| 4.02 100% Vesting (always vested) | **1.1(b) Elective Deferral** + **1.1(f) QMAC** + **1.1(g) QNEC** | These define "nonforfeitable when made" |

**Key insight:** Target BPD **distributes** vesting provisions:
- "Always vested" sources → Article I account definitions (1.1)
- Break-in-service effects → Article III (3.5(f))
- Vesting schedule → **Adoption Agreement** (not in BPD text)
- SIMPLE-specific vesting → Article XIII (13.5) **only for SIMPLE plans**

### Extraction Validation Issues

**GPT-5 identified our mistakes:**

1. ❌ **Used Section 13.5 for general vesting** - This is SIMPLE 401(k) only
   - Should use: 1.1(b), 1.1(f), 1.1(g) for always-vested sources

2. ❌ **Attributed specific values to BPD sections** - Values come from AA
   - Doc 1 Section 2.01 doesn't say "age 21" - it says "specified in AA"
   - LLM hallucinated from prompt examples

3. ❌ **Compared template text directly** - Missing the elected values
   - Need to extract from AAs first, then merge

### Why We Got 0% Match Rate

**Root causes (per GPT-5):**

1. **Template vs filled-value mismatch**
   - We compared hallucinated values ("age 21") to template text ("as elected in AA")
   - LLM correctly identified these as non-equivalent

2. **Sectioning drift**
   - BPD 01 has "Section Four: Vesting"
   - BPD 05 distributes vesting across Articles I, III, XIII
   - Cosine similarity struggled with reorganization

3. **Wrong target sections**
   - Matched to SIMPLE-only provisions (13.5)
   - Missed distributed provisions (1.1(b), 1.1(f), 1.1(g))

4. **No metadata in embeddings**
   - Only embedded provision_text (no section numbers, titles, types)
   - Lost strong anchors like "Article III — Eligibility"

5. **Verifier too strict**
   - Treated "as elected in AA" as substantively different from specific values
   - Should treat as "schema-level match" (same parameterized rule)

---

## Architectural Implications

### What We Built (Wrong Approach)

```
Extract from Source BPD → Extract from Target BPD → Compare
         ↓                         ↓
  (hallucinated values)      (template text)
         ↓                         ↓
    "age 21"          vs    "as elected in AA"
         ↓                         ↓
             LLM: "no match" ✓ (correct assessment)
```

### What We Should Build (Correct Approach)

**Mode A: AA → AA (Preferred)**
```
Extract from Source AA → Extract from Target AA → Map elections
         ↓                         ↓
   Elected values            Available options
   (age: 21)                (age: [18, 21, other])
         ↓                         ↓
             Mapping: "age 21" → "age 21" ✓
```

**Mode B: BPD → AA (Fallback)**
```
Extract from Source BPD → Infer elections → Map to Target AA
         ↓                      ↓                    ↓
   Template + samples    Best guess values    Available options
   "as specified in AA"   (age 21 inferred)   (age: [18, 21, other])
   + SPD evidence              ↓                    ↓
                         Mapping + human review flags
```

### Required Components

**New capabilities needed:**

1. **Adoption Agreement Parser**
   - Extract elected values from AA checkboxes/fill-ins
   - Handle locked PDFs (vision fallback)
   - Map AA fields to BPD provision types

2. **BPD Topic Crosswalk**
   - Pre-built map: BPD 01 sections → BPD 05 sections
   - Topic-based routing (Eligibility, Vesting, Entry, Contributions, etc.)
   - Handle distributed provisions (vesting across Articles I, III, XIII)

3. **Template + Election Merger**
   - Substitute elected values into BPD template provisions
   - Generate "complete" provisions for comparison
   - Handle optional provisions (if elected in AA, include; else skip)

4. **Two-Stage Matching**
   - Stage 1: Route by topic (Eligibility → Eligibility)
   - Stage 2: Semantic similarity within topic bucket
   - Prevents cross-topic false matches (eligibility vs vesting)

5. **Schema-Level Equivalence**
   - Recognize "age 21" ≈ "age as elected in AA" (same parameter)
   - Classify as "schema-equivalent; values differ/pulled from AA"
   - Don't treat as substantive difference

---

## Specific Fixes Required

### 1. Fix Extraction Prompt (URGENT)

**Problem:** Lines 14 and 63 of [prompts/provision_extraction_v2.txt](prompts/provision_extraction_v2.txt) contain examples with specific values that LLM uses as templates.

**Solution:**
```markdown
Examples:
✓ "An Employee shall be eligible to participate upon satisfying the age and
   service requirements specified in the Adoption Agreement."
✓ "The vesting schedule shall be as elected in the Adoption Agreement."

NOT:
✗ "An Employee shall be eligible upon attaining age 21..." (this is AA text, not BPD)
```

**Critical instruction to add:**
```
PRESERVE TEMPLATE LANGUAGE:
- If the provision says "as elected in the Adoption Agreement", preserve that exact phrase
- If the provision says "as specified in the Adoption Agreement", preserve that exact phrase
- DO NOT substitute example values or numbers
- Extract the ACTUAL text from the document, not what you think it should say
```

### 2. Re-Extract from Both BPDs

**Expected results after fix:**

**Source BPD Section 2.01:**
```json
{
  "provision_text": "Each Employee will be eligible to participate upon
                     satisfying the age and eligibility service requirements
                     specified in the Adoption Agreement.",
  "extracted_entities": {
    "ages": [],
    "service_years": [],
    "template_references": ["Adoption Agreement"]
  }
}
```

**Target BPD Section 3.1:**
```json
{
  "provision_text": "An Employee shall be eligible to participate upon
                     satisfying the age and service requirements, if any,
                     as elected in the Adoption Agreement.",
  "extracted_entities": {
    "ages": [],
    "service_years": [],
    "template_references": ["Adoption Agreement"]
  }
}
```

Now these will be recognized as **schema-equivalent**.

### 3. Extract from Adoption Agreements

**Source AA** (`pair_b_source_adoption.pdf`):
- Extract elected values:
  - Eligibility age: ?
  - Eligibility service: ?
  - Vesting schedule: ?
  - Entry dates: ?
  - etc.

**Target AA** (`pair_b_target_adoption_locked.pdf`):
- **Unlock first** (password-protected)
- Extract available options/elections
- Map source elections to target options

### 4. Build BPD Crosswalk

**Structure:**
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
      "notes": "BPD 05 distributes: definitions (1.87), breaks (3.5f), schedule (AA)"
    }
  ]
}
```

### 5. Enhance Embedding Strategy

**GPT-5 recommendations:**

1. **Include metadata in embedding text:**
   ```python
   # Bad (current)
   embedding_text = provision.provision_text

   # Good (recommended)
   embedding_text = f"{provision.section_reference} {provision.section_title}: {provision.provision_text}"
   ```

2. **Add domain labels:**
   ```python
   keywords = ["eligibility", "rehire", "break-in-service", "always vested", "QNEC", "QMAC"]
   embedding_text = f"{section} {title} [{', '.join(keywords)}]: {text}"
   ```

3. **Two-stage matching:**
   - Filter by provision_type first (eligibility → eligibility only)
   - Then compute embeddings within type
   - Prevents cross-type false matches

### 6. Update Semantic Mapping Prompt

**Add schema-level equivalence recognition:**

```markdown
TEMPLATE LANGUAGE EQUIVALENCE:

When comparing provisions, recognize these patterns as SCHEMA-EQUIVALENT:

Source: "age 21 and one Year of Service"
Target: "age and service requirements as elected in the Adoption Agreement"
→ Classification: SCHEMA-EQUIVALENT (same parameter, value deferred to AA)
→ Variance: administrative (structural difference, not substantive)
→ Requires: AA verification to confirm elected values match

Source: "0% for years 1-2, 20% year 3, 40% year 4..."
Target: "according to the vesting schedule specified in the Adoption Agreement"
→ Classification: SCHEMA-EQUIVALENT
→ Variance: administrative
→ Requires: AA verification

DO NOT classify template references as substantive differences unless the
Adoption Agreement elections are known to differ.
```

---

## Updated POC Success Criteria

### Original (Invalidated)
- ❌ Extract operational provisions from PDFs (achieved, but hallucinated values)
- ❌ 70-90% semantic match rate (0% because wrong approach)
- ✅ Confidence scoring and reasoning (working correctly)
- ✅ Variance classification (working correctly)

### Revised (Post-GPT-5)

**Phase 1: Fix Extraction**
- [ ] Extraction preserves template language (no hallucination)
- [ ] Re-extract from both BPDs with corrected prompt
- [ ] Validate against actual PDF text

**Phase 2: AA Integration**
- [ ] Extract elections from source Adoption Agreement
- [ ] Unlock target Adoption Agreement (or work with unlocked copy)
- [ ] Extract target AA options/elections

**Phase 3: BPD Crosswalk**
- [ ] Build topic-based crosswalk (BPD 01 → BPD 05)
- [ ] Handle distributed provisions (vesting across multiple BPD 05 sections)
- [ ] Validate mappings against GPT-5 findings

**Phase 4: Merger & Comparison**
- [ ] Merge AA elections into BPD templates
- [ ] Generate complete provisions
- [ ] Re-run semantic mapper
- [ ] Expect 70-90% match rate

---

## Market Research Validation

**This finding validates the core pain point:**

From [research/market_research.pdf](research/market_research.pdf):
> "True document-to-document reconciliation remains largely manual. It relies on
> the expertise of compliance professionals to interpret and compare provisions."

**Why it's manual:** Compliance professionals:
1. Know that BPDs are templates
2. Read the Adoption Agreement for actual elections
3. Mentally map "age 21" in source AA → "age as elected" in target BPD
4. Verify the target AA elections match source plan intent
5. Handle cross-vendor structural differences (BPD 01 vs BPD 05)

**Our contribution:** Automate steps 3-5.

---

## Next Steps (Prioritized)

### Immediate (Today)
1. ✅ Document GPT-5 findings (this file)
2. [ ] Fix extraction prompt (remove value examples, add template preservation)
3. [ ] Re-extract from both BPDs
4. [ ] Validate extraction against actual PDF text

### Short-term (This Week)
5. [ ] Unlock target AA or obtain unlocked copy
6. [ ] Design AA extraction approach (checkbox/fill-in detection)
7. [ ] Extract from source AA (elections)
8. [ ] Extract from target AA (available options)

### Medium-term (POC Completion)
9. [ ] Build BPD 01 → BPD 05 crosswalk (topic-based)
10. [ ] Implement template + election merger
11. [ ] Re-run comparison with complete provisions
12. [ ] Measure match rate improvement

### Long-term (MVP)
13. [ ] Generalize to other BPD versions (not just 01 → 05)
14. [ ] Handle cross-vendor conversions (Ascensus → different vendor)
15. [ ] Build "Mode B" (BPD inference → AA when source AA missing)

---

## Critical Insights from GPT-5

### 1. On SIMPLE 401(k) Trap
> "Doc 2 §13.5 lives under SIMPLE 401(k) and says salary reduction + matching
> are fully vested in a SIMPLE design — a special case, not the general rule."

**Lesson:** Must detect plan type and scope section usage. Don't match general provisions to plan-type-specific provisions.

### 2. On BPD as Dictionary
> "Use the BPDs only as dictionaries/guardrails."

**Lesson:** BPDs define what's *possible*. AAs define what's *actual*. Don't treat BPD text as plan specifications.

### 3. On Distributed Provisions
> "In BPD 05, 'Vesting Requirements' for general plans aren't in a single 'Vesting'
> article; they're distributed (definitions + break rules + AA)."

**Lesson:** Can't rely on section numbering alone. Need topic-based routing that handles provisions split across multiple sections.

### 4. On Two Modes
> "Mode A (preferred): AA → AA. Read the source Adoption Agreement for the actual
> elections, then populate the target Adoption Agreement."

**Lesson:** When source AA is available, use it. Only fall back to BPD inference when AA is missing/lost.

---

## Files to Update

**Immediate:**
- [ ] `prompts/provision_extraction_v2.txt` → v3 (fix hallucination)
- [ ] `CLAUDE.md` - Update project status, architecture understanding
- [ ] `POC_FINDINGS.md` - Append GPT-5 validation results
- [ ] `CRITICAL_QUESTION.md` - Mark as RESOLVED

**New files needed:**
- [ ] `design/bpd_crosswalk.json` - BPD 01 → BPD 05 topic mapping
- [ ] `design/aa_extraction_strategy.md` - How to extract from AAs
- [ ] `design/template_merger.md` - How to substitute AA values into BPD

---

*Validated by: OpenAI GPT-5 Pro with actual PDF documents*
*Key revelation: "Your 'age 21' likely came from an AA (or sample overlay), not from the BPD core."*
