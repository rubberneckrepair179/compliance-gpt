# Next Session Roadmap

**Last Session:** 2025-10-24 - Sprint A Complete (Extraction Quality)
**Status:** ✅ Clean extraction validated, ready for semantic mapping design review

---

## What We Accomplished Today

### ✅ Sprint A: Extraction Quality Improvements
1. **Drafted v4 prompts** - Section heading exclusion + semantic fingerprinting
2. **Re-extracted all documents** - 1,620 items from 328 pages (63.5 min)
3. **Red Team validation** - 10/10 samples substantive (0 headings)
4. **Decision:** ✅ PROCEED - Extraction quality validated

**Key Files:**
- Clean extraction data: `test_data/extracted_vision_v4/*.json`
- Validation results: `test_results/extraction_v4_full_samples.md`
- Sprint summary: `SPRINT_SUMMARY_2025-10-24.md`

---

## Before Running Semantic Crosswalks

**Sergio's Concern (Oct 24):**
> "I am not sure if I want to rerun old semantic crosswalks until we have reviewed and revised their implementation design, if they are using better prompts and such that I think are not yet implemented."

**Translation:** Need to review/improve semantic mapping design BEFORE generating crosswalks with v4 data.

---

## Next Session: Semantic Mapping Design Review

### Step 1: Review Current Semantic Mapping Implementation

**Files to Review:**
1. `prompts/semantic_mapping_v1.txt` - Current LLM prompt for provision comparison
2. `src/mapping/semantic_mapper.py` (or equivalent) - Implementation code
3. `design/reconciliation/semantic_fingerprinting.md` - Design strategy (created Oct 23)
4. `design/data_models/provisional_matching.md` - Matching model (created Oct 23)

**Questions to Answer:**
- ✅ Does semantic_mapping_v1.txt implement semantic fingerprinting?
- ✅ Does it handle provisional matches (template vs election vs instance)?
- ✅ Does it use the variance classification model?
- ✅ Are embeddings generated from clean text (no section numbers)?

---

### Step 2: Identify Gaps Between Design and Implementation

**Design Documents Created (Oct 23):**
- [design/reconciliation/semantic_fingerprinting.md](design/reconciliation/semantic_fingerprinting.md)
- [design/data_models/provisional_matching.md](design/data_models/provisional_matching.md)
- [design/data_models/variance_model.md](design/data_models/variance_model.md)
- [design/llm_strategy/prompt_management.md](design/llm_strategy/prompt_management.md)
- [design/performance_optimization.md](design/performance_optimization.md)

**Likely Gaps:**
1. **Semantic fingerprinting** - Embeddings may include section numbers (need to strip)
2. **Provisional matching** - Mapper may not distinguish template/election/instance levels
3. **Variance classification** - May not use Admin/Design/Regulatory model
4. **Prompt externalization** - semantic_mapping_v1.txt may be hardcoded

---

### Step 3: Draft Improvements

**Potential Deliverables:**
1. **semantic_mapping_v2.txt** - Updated prompt with:
   - Provisional matching awareness
   - Variance classification (Admin/Design/Regulatory)
   - Impact level assessment (High/Medium/Low)
   - Chain-of-thought reasoning

2. **Semantic fingerprinting implementation** - Code to:
   - Strip section numbers before embedding
   - Add section context (heading text only)
   - Preserve regulatory references
   - Cache fingerprints for performance

3. **Updated semantic mapper** - Integrate:
   - Load prompts from external files
   - Apply semantic fingerprinting
   - Return provisional match indicators
   - Classify variances per design model

---

### Step 4: Validate and Approve

**Process:**
1. Review current implementation together
2. Identify specific gaps
3. Draft improvements
4. Sergio reviews and approves
5. Implement changes
6. Generate crosswalks with v4 data + improved mapper

---

## Alternative: Quick Win Option

**If time is limited next session:**

**Option B: Just Review Current Semantic Mapper**
- Don't make changes yet
- Just audit what's there vs design docs
- Document gaps in a "mapper_audit.md" file
- Decide whether to proceed with current mapper or iterate first

**Benefit:** Faster decision on whether current implementation is "good enough" or needs revision before v4 crosswalk generation.

---

## Files Ready for Next Session

### Clean Data (v4 Extraction)
```
test_data/extracted_vision_v4/
├── source_bpd_provisions.json      # 542 provisions (Relius)
├── source_aa_elections.json        # 167 elections (Relius)
├── target_bpd_provisions.json      # 384 provisions (Ascensus)
└── target_aa_elections.json        # 527 elections (Ascensus)
```

### Design Documents (Oct 23)
```
design/
├── reconciliation/semantic_fingerprinting.md
├── data_models/provisional_matching.md
├── data_models/variance_model.md
├── llm_strategy/prompt_management.md
└── performance_optimization.md
```

### Current Implementation (To Review)
```
src/mapping/              # Semantic mapper code
prompts/semantic_mapping_v1.txt  # Current LLM prompt
```

---

## Open Questions for Next Session

1. **Mapper review depth** - Quick audit or full redesign?
2. **Prompt iteration** - Draft v2 or use v1 as-is?
3. **Semantic fingerprinting** - Implement now or defer to post-crosswalk?
4. **Performance** - AsyncIO refactor now or later?

---

## Enhancement Backlog

**Post-MVP Items:**
- Definition formatting: Consider markdown for defined terms (`*term*`)
- Cross-vendor test corpus: Obtain Relius, ftwilliam, DATAIR samples
- Production pilot: Test with real TPA client conversion

---

## Session Start Checklist

When you return:
- [ ] Read this document (NEXT_SESSION.md)
- [ ] Review SPRINT_SUMMARY_2025-10-24.md for context
- [ ] Decide: Full mapper redesign OR quick audit + proceed?
- [ ] If redesign: Start with Step 1 (review current implementation)
- [ ] If proceed: Generate v4 crosswalks with current mapper, then iterate

---

*Document created: 2025-10-24*
*Next session: TBD*
*Status: Ready to resume with semantic mapping design review*
