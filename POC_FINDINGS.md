# POC Findings: Operational vs Definitional Provisions

**Date:** 2025-10-19
**Test:** Pair A document comparison using v2 prompt (operational provisions only)

---

## Executive Summary

Successfully extracted operational provisions from both documents using v2 prompt with "operational vs definitional" distinction. However, semantic mapping still yielded 0% match rate due to candidate selection algorithm limitations, NOT extraction quality.

**Key Insight:** The LLM correctly identified non-matches with high confidence (95-100%), but the embedding-based candidate filtering prevented it from seeing the correct matches.

---

## Extraction Results

### ✅ Success: v2 Prompt Worked Correctly

**Source Document (81 pages):**
- 3 eligibility provisions (Sections 2.01, 2.04, 2.03)
- 2 vesting provisions (Sections 4.01, 4.02)
- All operational (using SHALL, WILL, establishing rules)
- No definitions extracted

**Target Document (98 pages):**
- 3 eligibility provisions (Sections 3.1, 3.2, 3.5)
- 2 vesting provisions (Sections 13.5, 1.37(a))
- All operational
- No definitions extracted

**Comparison to v1 results:**
- v1 (first 20 pages): Extracted definitions from target ("'Eligible Employee' means...")
- v2 (full document): Extracted operational provisions ("An Employee shall be eligible...")

**Conclusion:** The v2 prompt successfully distinguished operational from definitional provisions.

---

## Mapping Algorithm Issue

### Problem: Top-K Candidate Filtering Too Aggressive

**Current Algorithm:**
1. Generate embeddings for all provisions (cheap)
2. Compute cosine similarity matrix (5×5 = 25 pairs)
3. Select top-3 candidates per source provision based on embedding similarity
4. LLM verifies only those 3 candidates (expensive)
5. Select highest-confidence mapping from verified candidates

**What Happened:**
- Source Section 2.01 (basic eligibility) → Top 3 candidates did NOT include correct match (Target Section 3.1)
- Algorithm verified wrong candidates, LLM correctly said "no match" with high confidence
- Same issue across all provisions

**Example:**
```
Source: Section 2.01 "Eligibility to Participate"
  "An Employee shall be eligible... upon attaining age 21 and completing one Year of Service"

Correct Target: Section 3.1 "CONDITIONS OF ELIGIBILITY"
  "An Employee shall be eligible... upon satisfying the age and service requirements"

Actual Match: Section 3.5 "REHIRED EMPLOYEES" (embedding similarity 0.62)
  "If a Former Employee is reemployed..."

Result: LLM said "NOT a match" (95% confidence) ✓ Correct assessment of wrong pairing
```

---

## Root Cause Analysis

### Why Embeddings Missed Correct Matches

**Hypothesis 1: Generic vs Specific Language**
- Source uses specific values ("age 21", "one Year of Service")
- Target uses generic references ("as elected in the Adoption Agreement")
- Embeddings may favor lexical similarity over semantic equivalence

**Hypothesis 2: Document Structure Differences**
- Source: Self-contained provisions with concrete values
- Target: Provisions that delegate to Adoption Agreement
- Different writing styles → different embedding vectors

**Hypothesis 3: Top-K Too Small**
- With only 5 target provisions, top-3 means we're discarding 40% of candidates
- Correct match might be #4 or #5 in similarity ranking

---

## LLM Performance

### ✅ LLM Verification Worked Correctly

When given the WRONG pairings, the LLM:
- Correctly identified they were NOT matches
- Provided detailed, accurate reasoning
- Assigned appropriate confidence scores (95-100% for clear non-matches)
- Classified variance types and impact levels correctly

**Example reasoning (Section 4.01 vesting → Section 3.5 rehired employees):**
> "The source provision describes a graded vesting schedule for employer contributions... The target provision addresses eligibility for plan participation and service crediting rules for rehired employees... These provisions address fundamentally different plan concepts... There is no semantic equivalence, and the difference is substantive, affecting both participant rights and plan operations."

**Confidence:** 100% ✓

**Conclusion:** The LLM is highly capable of semantic comparison when given the correct candidates.

---

## Proposed Solutions

### Option 1: Increase Top-K (Simplest for POC)

**Change:** `top_k=3` → `top_k=5` (verify ALL target provisions)

**Pros:**
- Simple one-line change
- Guarantees we check all possible matches
- Only 25 LLM calls for 5×5 (acceptable for POC)

**Cons:**
- Doesn't scale to larger documents (50×50 = 2,500 LLM calls)
- Loses cost optimization benefit of embeddings

**POC Verdict:** ✅ Acceptable - We're testing with 5-10 provisions, not 50+

---

### Option 2: Hybrid Approach with Fallback (Post-POC)

**Change:**
1. Try top-3 candidates first
2. If no high-confidence match found, expand to top-5 or all candidates
3. Track which provisions required fallback for analysis

**Pros:**
- Maintains cost optimization for clear matches
- Provides safety net for ambiguous cases
- Generates data on when embeddings work vs don't

**Cons:**
- More complex implementation
- Variable cost (unpredictable)

**POC Verdict:** 🟡 Defer - Good idea, but adds complexity

---

### Option 3: Provision-Type Filtering (Recommended for MVP)

**Change:**
1. Filter candidates by provision_type FIRST (eligibility → eligibility only)
2. Then apply embedding similarity within same type
3. Then LLM verification

**Example:**
- Source Section 2.01 (eligibility) → Only check against Target Sections 3.1, 3.2, 3.5 (eligibility)
- Ignore Target Sections 13.5, 1.37(a) (vesting)

**Pros:**
- Dramatically reduces candidate space (3×3 instead of 5×5 for this test)
- Makes semantic sense (don't compare eligibility to vesting)
- Scales better (50 provisions split into 5 types = 10×10 per type max)

**Cons:**
- Assumes provision_type extraction is accurate
- Might miss edge cases where provision type was miscategorized

**POC Verdict:** ✅ Implement this - aligns with REQ-021 requirement

---

### Option 4: Two-Pass Approach (Future Enhancement)

**Pass 1: Structural alignment**
- Match by provision_type
- Match by extracted_entities similarity (ages, service_years, percentages)
- Generate high-confidence matches for provisions with identical structure

**Pass 2: Semantic verification**
- LLM verifies remaining ambiguous cases
- Focuses LLM effort where it's needed most

**POC Verdict:** 🔵 Document for future - too complex for POC

---

## Immediate Next Steps

**For this POC session:**

1. **Quick Win: Test with top_k=5** (verify all candidates)
   - Change one parameter, re-run test
   - See if we get matches with correct pairings
   - Measure improvement

2. **If matches found: Analyze results**
   - Which provisions matched?
   - What were the confidence scores?
   - Does variance classification make sense?

3. **If still no matches: Deeper investigation**
   - Manually inspect embedding similarity matrix
   - Identify why correct pairs have low embedding similarity
   - Consider provision-type filtering

---

## Cost Analysis

**Current approach (top-k=3):**
- Embeddings: 10 provisions × $0.00002 = $0.0002
- LLM calls: 15 verifications × $0.01 = $0.15
- **Total: ~$0.15 per document pair**

**Proposed approach (top-k=5):**
- Embeddings: 10 provisions × $0.00002 = $0.0002
- LLM calls: 25 verifications × $0.01 = $0.25
- **Total: ~$0.25 per document pair**

**With provision-type filtering (3 types, avg 2×2 per type):**
- Embeddings: Same
- LLM calls: ~12 verifications × $0.01 = $0.12
- **Total: ~$0.12 per document pair** (20% savings vs current)

**Conclusion:** Even checking all candidates is affordable for POC scale.

---

## Technical Debt / Future Considerations

1. **Embedding model selection** - Text-embedding-3-small might not be optimal for regulatory language
2. **Prompt engineering for comparison** - Could we improve semantic_mapping_v1.txt?
3. **Confidence calibration** - Need more test data to validate 70/90% thresholds
4. **Alternative match suggestions** - Should we show user top 3 candidates when confident match not found?
5. **Missing provision detection** - How to handle provisions with no good match?

---

## Files Modified/Created This Session

**New Scripts:**
- `scripts/extract_operational_provisions.py` - Uses v2 prompt, scans full documents
- `scripts/test_operational_mapping.py` - Tests semantic mapping with operational provisions

**New Prompt:**
- `prompts/provision_extraction_v2.txt` - Operational vs definitional distinction

**New Data:**
- `test_data/processed/pair_a_source_bpd_operational_provisions.json` (5 provisions)
- `test_data/processed/pair_a_target_bpd_operational_provisions.json` (5 provisions)
- `test_data/processed/pair_a_operational_comparison.json` (mapping results)

---

*End of POC Findings Document*
