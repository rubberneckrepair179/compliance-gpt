# Critical Question: Document Pairing Structure

**Date:** 2025-10-19
**Status:** 🔴 BLOCKING - Need to resolve before proceeding with POC

---

## The Question

**Are we comparing the wrong things?**

We've been treating this as 2 independent pairs:
- Pair A: `source_bpd.pdf` ↔ `target_bpd.pdf`
- Pair B: `source_adoption.pdf` ↔ `target_adoption.pdf`

But the evidence suggests it might actually be 2 plan sets:
- **Source/Old Plan**: `source_bpd.pdf` + `source_adoption.pdf` (combined)
- **Target/New Plan**: `target_bpd.pdf` + `target_adoption.pdf` (combined)

---

## Evidence

### 1. Opus Validation Findings

Opus confirmed:
- Document 1 (source_bpd): **Standalone BPD** with specific values embedded
- Document 2 (target_bpd): **Prototype/Template BPD** that references Adoption Agreement

Key quote:
> "Should Document 1 and Document 2 be compared directly, or do they require companion Adoption Agreements to be meaningful?"

### 2. Our Test Results

Section 2.01 (source) vs Section 3.1 (target):
- **Source**: "age 21 and completing one Year of Service" (specific)
- **Target**: "as elected in the Adoption Agreement" (placeholder)
- **LLM verdict**: No match (85% confidence)
- **LLM reasoning**: "defers eligibility requirements to the Adoption Agreement, allowing for variability"

The LLM is **correctly** identifying that the target provision is incomplete without the AA.

### 3. File Naming Pattern

```
pair_a_source_bpd.pdf        ← BPD (complete, specific values)
pair_b_source_adoption.pdf   ← Adoption Agreement for source plan?

pair_a_target_bpd.pdf        ← BPD (template, references AA)
pair_b_target_adoption_locked.pdf  ← Adoption Agreement for target plan?
```

The "pair_a/pair_b" naming suggests pairs, but "source/target" suggests old vs new.

**Question:** Do we have:
- 2 pairs (A and B)?
- OR 2 sets (source and target)?

---

## What This Means

### If we have 2 independent pairs:
- Compare source_bpd ↔ target_bpd (both standalone, both complete)
- Compare source_adoption ↔ target_adoption (both specify elections)
- **Expected:** High match rate within each pair
- **Actual:** 0% match rate between BPDs

**Conclusion:** This scenario is unlikely given our results.

### If we have 2 plan sets (source vs target):
- Source plan = source_bpd (standalone, already merged with AA values)
- Target plan = target_bpd + target_adoption (template + elections)
- **To compare fairly:** Need to merge target_bpd + target_adoption first
- **Expected:** Can't get matches until we extract AA values and substitute

**Conclusion:** This scenario matches our observations.

---

## What We Need to Know

### Questions for GPT-5 Pro (with actual PDFs):

1. **Document Relationship:**
   - Which Adoption Agreement corresponds to which BPD?
   - Is `source_adoption.pdf` the companion to `source_bpd.pdf`?
   - Is `target_adoption_locked.pdf` the companion to `target_bpd.pdf`?

2. **Source BPD Structure:**
   - Does `source_bpd.pdf` contain merged AA elections, or is it truly standalone?
   - Does it reference an Adoption Agreement anywhere?
   - If it references an AA, where is that AA?

3. **Comparison Strategy:**
   - To compare these plans, should we:
     a) Compare source_bpd alone to target_bpd alone? (current approach)
     b) Compare source_bpd to (target_bpd + target_adoption merged)?
     c) Compare (source_bpd + source_adoption) to (target_bpd + target_adoption)?

4. **Adoption Agreement Content:**
   - What is elected in `source_adoption.pdf` (if it goes with source_bpd)?
   - What is elected in `target_adoption_locked.pdf` (if we can unlock it)?
   - Do the elections match the specific values in source_bpd?
     - Example: Does target_adoption elect "age 21, 1 year service"?

---

## Impact on POC

### If we're comparing wrong structure:

**Current approach:**
```
source_bpd (complete)  →  target_bpd (incomplete/template)
    ↓                          ↓
"age 21"               →  "as elected in AA"
    ↓                          ↓
  LLM says: "no match" ← CORRECT assessment of incomplete data
```

**Correct approach:**
```
source_bpd (complete)  →  target_bpd + target_adoption (complete)
    ↓                          ↓
"age 21"               →  "age 21" (from AA)
    ↓                          ↓
  LLM says: "match" ← Can now compare apples to apples
```

### This changes our architecture

**Current:**
1. Extract from source_bpd
2. Extract from target_bpd
3. Compare

**Required:**
1. Extract from source_bpd
2. Extract from target_bpd (template provisions)
3. **Extract from target_adoption (elected values)**
4. **Merge template + elections** (new capability)
5. Compare complete provisions

---

## Next Steps (Pending GPT-5 Analysis)

### If GPT-5 confirms 2 plan sets:

1. **Immediate:**
   - [ ] Unlock or extract from target_adoption_locked.pdf
   - [ ] Extract provisions from both Adoption Agreements
   - [ ] Identify which AA values correspond to which BPD provisions

2. **Short-term (POC):**
   - [ ] Implement simple merge: substitute AA values into template
   - [ ] Re-run comparison with complete target provisions
   - [ ] Expect much higher match rate

3. **Medium-term (MVP):**
   - [ ] Build robust AA parsing (handle all provision types)
   - [ ] Detect template patterns automatically
   - [ ] Validate substitution correctness

### If GPT-5 says independent pairs:

1. **Reconsider:**
   - Why do both BPDs appear to be from different vendors?
   - Why does target_bpd use template language if it's standalone?
   - What explains 0% match rate if they're meant to be compared directly?

2. **Alternative explanation:**
   - Maybe source_bpd is from Vendor A (old system, merged format)
   - Maybe target_bpd is from Vendor B (new system, modular format)
   - This is the "cross-vendor conversion" problem from market research

---

## Why This Matters

From market research:
> "someone re-enters it or maps it field by field"

If we're doing cross-vendor conversions (Relius → ASC), we MUST handle:
- Different document architectures (standalone vs modular)
- Template language vs specific values
- Adoption Agreement integration

**This is the CORE use case.** We can't skip it just because it's complex.

---

## Current Status

**Waiting for:** GPT-5 Pro analysis with actual PDF documents

**Blocking questions:**
1. Document pairing structure
2. Which AA goes with which BPD
3. Correct comparison approach

**Cannot proceed with POC until resolved.**

---

*Sergio is running GPT-5 Pro analysis now - standby for results*
