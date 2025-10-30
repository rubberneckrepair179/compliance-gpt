# Extraction Pipeline Complete - Hanging Questions & Roadmap

**Date:** 2025-10-30
**Status:** Extraction phase nearly complete, planning merger layer

---

## What We Accomplished Today

### ✅ Completed Extractions

**BPD v4.1 (Production-Grade Prompt from GPT-5 Pro):**
- ✅ Relius BPD: 565 provisions, 98 pages, 100% success
- ✅ Ascensus BPD: 466 provisions, 81 pages, 100% success
- **Features:** Extraction gate, layout rules, provision_classification, page_sequence assigned by post-processing

**AA v5.1 (Atomic Field Rule):**
- ✅ Relius AA: 1,216 provisions, 43/45 pages, 95.6% success (2 failed pages)
- 🔄 Ascensus AA: Running now (104 pages, expected ~2,700+ provisions)
- **Features:** Each labeled field = separate provision, local_ordinal, field_label, nested hierarchy

### Key Insights Discovered

1. **Don't make LLM do bookkeeping** - page_sequence assigned by post-processing (array order), not by LLM
2. **Extraction gate works** - v4.1 correctly filters TOC/headers/footers (0 provisions from pages 1-5, substantive content from pages 6+)
3. **Fragmentation is expected** - Page-by-page extraction creates orphans and page-spanning provisions (to be fixed in post-processing)
4. **Plan Provision is a synthesis** - Not brute concatenation of BPD+AA text, but LLM-generated natural language summary

---

## Hanging Questions

### 1. Post-Processing Pipeline

**Question:** What post-processing steps are needed before merger?

**Known Issues:**
- **Fragmentation:** 2 orphans + 71 page-spanning provisions in Relius AA v5.1
- **Missing parents:** Children reference parent_section that doesn't exist
- **Continued sections:** BPD provision starts on page N, continues on page N+1

**Options:**
- A. Implement defragmentation script (merge based on section_number continuity)
- B. Accept fragmentation, handle in merger layer
- C. Change extraction approach (multi-page context windows)

**Recommendation:** Option A - Create `scripts/postprocess_defragment_bpd.py` and `scripts/postprocess_defragment_aa.py` to merge page-spanning provisions before merger.

---

### 2. BPD ↔ AA Linking Strategy

**Question:** How do we know which AA elections apply to which BPD provisions?

**Example Challenge:**
- BPD Section 2.01 "Eligibility Requirements" says "as elected in AA"
- Which AA question(s) correspond to this? Q5? Q6? Multiple questions?

**Options:**
- A. **Semantic fingerprinting + cosine similarity** (your suggested approach)
  - Create terse semantic fingerprint (exclude structure noise)
  - Find high-similarity BPD-AA pairs
  - Human review/validation of links

- B. **LLM semantic matching**
  - Ask LLM to match BPD provisions to AA elections
  - Expensive but flexible

- C. **Vendor documentation/schema**
  - Check if Relius/Ascensus publish BPD-AA mapping schemas
  - Unlikely to exist, vendor-specific

- D. **Pattern matching in provision_text**
  - Look for "as elected in AA Section X" references
  - Only works when BPD explicitly references AA sections

**Recommendation:** Hybrid approach:
1. Start with pattern matching (D) for explicit references
2. Use semantic fingerprinting (A) for unlinked provisions
3. LLM semantic matching (B) as fallback for low-confidence pairs

---

### 3. Semantic Fingerprint Design

**Question:** What goes into a "semantically clean, terse" fingerprint?

**Include:**
- Core concepts (eligibility, vesting, contributions, distributions)
- Key values when present (age 21, 1 year of service, 1000 hours)
- Provision type indicators (means, shall, must, IRC §)

**Exclude (Structure Noise):**
- Section numbers (1.01, 2.03, Article IV)
- Page numbers, sequence numbers
- Boilerplate ("as elected in AA", "in accordance with")
- Vendor-specific formatting

**Example:**
```
BPD Provision: "Section 2.01 Eligibility Requirements. An Employee shall be eligible to participate upon attaining the age and completing the service requirements as elected in the Adoption Agreement."

Fingerprint: "eligibility requirements employee participate age service"
```

**Question for refinement:** Should we include negations? ("not eligible", "excludes")

---

### 4. Plan Provision Synthesis

**Question:** What instructions/prompt do we give the LLM to synthesize Plan Provisions?

**Goal:** Natural language summary combining BPD template + AA election values

**Example Input:**
```json
{
  "bpd_provision": {
    "section_number": "2.01",
    "provision_text": "An Employee shall be eligible to participate upon attaining the age and completing the service requirements as elected in the Adoption Agreement."
  },
  "aa_elections": [
    {
      "section_number": "5",
      "section_title": "Eligibility Age",
      "form_elements": [{"is_selected": true, "text_value": "21"}]
    },
    {
      "section_number": "6",
      "section_title": "Eligibility Service",
      "form_elements": [{"is_selected": true, "text_value": "1 Year of Service (1,000 hours)"}]
    }
  ]
}
```

**Example Output:**
```
"Employees become eligible to participate upon attaining age 21 and completing 1 Year of Service (defined as 1,000 hours in a 12-month period)."
```

**Open Questions:**
- Should synthesis include section numbers? (Probably not - human-readable)
- Should we preserve legal phrasing or simplify? (Preserve - this is compliance documentation)
- How verbose? (Concise but complete - 1-3 sentences per provision)

---

### 5. Data Model for BPD+AA Molecules

**Question:** What does a "molecule" look like in code?

**Proposed Schema:**
```python
class BPD_AA_Molecule:
    # Source documents
    bpd_provision: Provision           # From BPD extraction
    aa_elections: List[Election]       # Linked AA elections

    # Linking metadata
    link_method: str                   # "explicit_reference" | "semantic_match" | "manual"
    link_confidence: float             # 0.0-1.0 (for semantic matches)

    # Fingerprinting
    semantic_fingerprint: str          # Cleaned text for embedding

    # Synthesis (computed)
    plan_provision_text: str | None    # LLM-generated summary (computed on demand)

    # Provenance
    molecule_id: str                   # Composite key (e.g., "relius:2.01")
```

**Open Question:** Should we cache synthesized plan_provision_text in the molecule, or compute on-demand during crosswalk?

---

### 6. Crosswalk Architecture

**Question:** Do we crosswalk BPDs, crosswalk AAs, then merge? Or merge first, then crosswalk?

**Option 1: Crosswalk First, Merge Later**
```
Relius BPD ←crosswalk→ Ascensus BPD
Relius AA ←crosswalk→ Ascensus AA
   ↓
Merge crosswalks (complex join logic)
```

**Option 2: Merge First, Crosswalk Complete Provisions** (Your Preference)
```
Relius BPD + Relius AA → Merge → Relius Plan Provisions
Ascensus BPD + Ascensus AA → Merge → Ascensus Plan Provisions
   ↓
Crosswalk Plan Provisions (semantic comparison of ACTUAL provisions)
```

**Decision:** Option 2 (confirmed during session)

**Pipeline:**
1. Extract (DONE after Ascensus AA completes)
2. Defragment (merge page-spanning provisions)
3. Link BPD ↔ AA (create molecules)
4. Generate semantic fingerprints
5. Embedding similarity (find candidate pairs: Relius ↔ Ascensus)
6. LLM synthesis (only for high-similarity pairs)
7. Crosswalk report (variance detection on synthesized provisions)

---

### 7. Technical Debt

**Identified During Session:**

1. **JSON Schema for structured outputs** - Replace prompt-based validation with OpenAI JSON Schema for deterministic outputs (deferred, documented in `docs/TECH_DEBT_STRUCTURED_OUTPUTS.md`)

2. **Test vs production file paths** - Test files mixed with production inputs in `test_data/raw/` (should separate to `test_data/test_inputs/`)

3. **Canonical input file documentation** - No single source of truth for which files are production inputs (should create `CANONICAL_INPUTS.md`)

4. **Orphaned background processes** - Multiple old extraction processes still running (need cleanup script)

5. **page_sequence vs pdf_page naming** - BPD v4.1 uses page_sequence (per-page counter), AA v5.1 uses pdf_page (absolute page number) - inconsistent naming

---

## Roadmap Forward

### Phase 1: Complete Extraction ✅ (TODAY)
- [x] BPD v4.1 extraction (Relius + Ascensus)
- [x] AA v5.1 extraction (Relius)
- [🔄] AA v5.1 extraction (Ascensus) - running now

### Phase 2: Post-Processing (NEXT)
**Goal:** Clean data for merger layer

**Tasks:**
1. Create defragmentation scripts
   - `scripts/postprocess_defragment_bpd.py` - Merge page-spanning BPD provisions
   - `scripts/postprocess_defragment_aa.py` - Merge page-spanning AA provisions, resolve orphans
2. Validate defragmented outputs
   - Check orphan count reduced to 0
   - Check page-spanning provisions merged correctly
3. Assign global provision IDs
   - Format: `{vendor}:{doc_type}:{pdf_page}:{section_number}:{sequence}`
   - Example: `relius:bpd:6:1.1:1`

**Deliverable:** Clean, defragmented BPD and AA extractions ready for linking

### Phase 3: BPD ↔ AA Linking (AFTER POST-PROCESSING)
**Goal:** Create BPD+AA molecules

**Tasks:**
1. Implement pattern matching for explicit references
   - Search BPD provision_text for "as elected in AA [Section X]"
   - Create explicit links with 100% confidence
2. Implement semantic fingerprinting
   - Create `src/fingerprinting/semantic_cleaner.py`
   - Strip structure noise (section numbers, boilerplate)
   - Generate terse fingerprints for embedding
3. Compute embeddings and cosine similarity
   - Use OpenAI text-embedding-3-small
   - Find high-similarity pairs (threshold: >0.7?)
4. Manual review interface (optional)
   - Show low-confidence links for human validation
5. Build molecule dataset
   - Save as `test_data/molecules/relius_molecules.json`
   - Save as `test_data/molecules/ascensus_molecules.json`

**Deliverable:** BPD+AA molecules for both vendors ready for synthesis

### Phase 4: Plan Provision Synthesis (AFTER LINKING)
**Goal:** Generate human-readable Plan Provisions

**Tasks:**
1. Design synthesis prompt
   - Input: BPD provision + linked AA elections
   - Output: Natural language summary (1-3 sentences)
   - Preserve legal precision, remove placeholders
2. Implement synthesis pipeline
   - `src/synthesis/plan_provision_synthesizer.py`
   - Use GPT-4.1 for synthesis (higher quality than mini)
   - Cache results in molecule
3. Validate synthesis quality
   - Red Team Sprint: Manual review of 20-30 synthesized provisions
   - Check accuracy, completeness, clarity
4. Generate complete provision sets
   - Relius Plan Provisions (BPD+AA synthesized)
   - Ascensus Plan Provisions (BPD+AA synthesized)

**Deliverable:** Complete, synthesized Plan Provisions ready for crosswalk

### Phase 5: Semantic Crosswalk (AFTER SYNTHESIS)
**Goal:** Compare Relius ↔ Ascensus Plan Provisions

**Tasks:**
1. Reuse semantic mapper from BPD crosswalk
   - Input: Relius Plan Provisions, Ascensus Plan Provisions
   - Embeddings + LLM semantic comparison
2. Generate crosswalk with variance detection
   - Semantic match (equivalent/different)
   - Variance classification (Administrative/Design/Regulatory)
   - Impact level (High/Medium/Low)
3. Export to CSV
   - Match `/process/templates/plan_comparison_workbook.csv` schema
   - Human-readable variance explanations

**Deliverable:** Complete Relius → Ascensus crosswalk report

### Phase 6: Executive Summary & Report (FINAL)
**Goal:** Natural language report for TPA

**Tasks:**
1. Summarize crosswalk findings
   - X% provisions matched exactly
   - Y% have variances (breakdown by type)
   - Z high-impact variances requiring review
2. Generate exception log
   - Auto-populate from high-impact variances
   - Match `/process/templates/exception_log.csv` schema
3. Create executive summary document
   - Natural language overview
   - Key findings
   - Recommended next steps

**Deliverable:** Complete plan conversion analysis report

---

## Open Architecture Questions

### 1. Defragmentation Strategy
**Question:** Should defrag merge provision_text or keep fragments separate with references?

**Option A: Merge Text**
- Combine page N and page N+1 fragments into single provision_text
- Simpler for downstream processing
- Loses page boundary information

**Option B: Keep Fragments with References**
- Store fragments separately, link by fragment_group_id
- Preserves provenance
- More complex to work with

**Lean toward:** Option A (merge text) - simpler, provenance tracked by pdf_page range

### 2. Embedding Model Choice
**Question:** Which embedding model for semantic fingerprinting?

**Options:**
- OpenAI text-embedding-3-small (cheap, fast, good quality)
- OpenAI text-embedding-3-large (expensive, slower, best quality)
- Custom fine-tuned model (ERISA/retirement plan domain)

**Lean toward:** text-embedding-3-small for POC, evaluate quality before considering upgrade

### 3. Synthesis Caching
**Question:** Where to cache synthesized Plan Provisions?

**Options:**
- A. In molecule JSON (simple, self-contained)
- B. Separate synthesis cache (SQLite? JSON?)
- C. Don't cache, regenerate on demand (expensive)

**Lean toward:** Option A (in molecule) for POC, Option B (SQLite) for production scale

---

## Success Criteria

**Extraction Phase (Current):**
- ✅ All 4 documents extracted with 95%+ success rate
- ✅ BPD v4.1 extraction gate working (filters TOC/headers)
- ✅ AA v5.1 Atomic Field Rule working (each field = separate provision)

**Post-Processing Phase (Next):**
- ⬜ Orphan count reduced to <1% (was 2/1216 = 0.16%)
- ⬜ Page-spanning provisions merged successfully
- ⬜ Global provision IDs assigned deterministically

**Linking Phase:**
- ⬜ 80%+ of BPD provisions linked to AA elections (explicit or semantic)
- ⬜ High-confidence links (>0.9) reviewed and validated

**Synthesis Phase:**
- ⬜ 95%+ of molecules synthesized successfully
- ⬜ Red Team validation: 90%+ of synthesized provisions accurate

**Crosswalk Phase:**
- ⬜ Relius ↔ Ascensus crosswalk complete
- ⬜ Variance detection working (Administrative/Design/Regulatory classification)
- ⬜ CSV export matches process template schema

---

## Files to Create (Immediate Next Steps)

1. **CANONICAL_INPUTS.md** - Document production input files
2. **scripts/postprocess_defragment_bpd.py** - Defragment BPD provisions
3. **scripts/postprocess_defragment_aa.py** - Defragment AA provisions
4. **src/fingerprinting/semantic_cleaner.py** - Generate semantic fingerprints
5. **src/linking/bpd_aa_linker.py** - Link BPD ↔ AA (pattern + semantic)
6. **src/models/molecule.py** - BPD+AA molecule data model
7. **src/synthesis/plan_provision_synthesizer.py** - LLM-powered synthesis

---

**Last Updated:** 2025-10-30
**Next Review:** After Ascensus AA extraction completes
