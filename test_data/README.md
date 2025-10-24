# Test Data Corpus Documentation

This directory contains test documents and generated crosswalks for POC validation.

**⚠️ PRIVACY NOTICE**: The `/raw` directory contains actual plan documents for testing. These are gitignored and never committed to version control.

---

## Test Corpus: Cross-Vendor Conversion (Relius → Ascensus)

**Scenario:** Cross-vendor conversion (hardest semantic mapping use case)
**Source Vendor:** Relius Cycle 3
**Target Vendor:** Ascensus
**SME Identification:** Lauren Leneis, Oct 21, 2025

⚠️ **Critical Note on Relius Documents**: The Relius source documents contain Ascensus (ASC) markings, footers, and branding text. This is because they were previously ASC documents for this client's prior plan. Despite the ASC text in the PDFs, Lauren Leneis confirmed these are **Relius documents** based on document structure, template language, and section organization.

### Source Documents (Relius Cycle 3)

| Original Filename | Canonical Name | Document Type | Pages | Provisions/Elections | Description |
|-------------------|----------------|---------------|-------|---------------------|-------------|
| `Cycle 3 Basic Plan Document 05-001.pdf` | `source_bpd.pdf` | Basic Plan Document | ~200 | 426 provisions | Relius Cycle 3 BPD (shows ASC branding but is Relius) |
| `Blank Cycle 3 Adoption Agreement.pdf` | `source_aa.pdf` | Adoption Agreement | ~60 | 521 elections | Relius Cycle 3 AA (shows ASC branding but is Relius) |

### Target Documents (Ascensus)

| Original Filename | Canonical Name | Document Type | Pages | Provisions/Elections | Description |
|-------------------|----------------|---------------|-------|---------------------|-------------|
| `Basic Plan Document.pdf` | `target_bpd.pdf` | Basic Plan Document | ~120 | 507 provisions | Ascensus BPD (©2020 Ascensus markings) |
| `401(k) Profit Sharing Plan.pdf` | `target_aa.pdf` | Adoption Agreement | ~90 | 235 elections | Ascensus Profit Sharing AA (©2020 Ascensus markings) |

---

## Generated Artifacts

### Vision Extraction (`/extracted_vision`)

| File | Model | Extraction Type | Items Extracted | Notes |
|------|-------|-----------------|-----------------|-------|
| `source_bpd_01_provisions.json` | GPT-5-nano | BPD provisions | 426 | Section-structured provisions with full text |
| `source_aa_elections.json` | GPT-5-nano | AA election options | 521 | Nested checkbox/fill-in structures |
| `target_bpd_05_provisions.json` | GPT-5-nano | BPD provisions | 507 | Section-structured provisions with full text |
| `target_aa_elections.json` | GPT-5-nano | AA election options | 235 | Nested checkbox/fill-in structures |

**Extraction Performance:**
- Total pages: 328
- Extraction time: 18 minutes (parallel processing with 16 workers)
- Pages per second: ~0.3

### Semantic Crosswalk (`/crosswalk`)

| File | Format | Rows | Description |
|------|--------|------|-------------|
| `bpd_crosswalk.json` | JSON | 425 mappings | Complete crosswalk with metadata, provisions, reasoning |
| `bpd_crosswalk.csv` | CSV | 425 mappings | Human-readable spreadsheet format |
| `aa_crosswalk.json` | JSON | Pending | Election mapping (not yet generated) |

**Crosswalk Performance:**
- Source provisions: 425
- Target provisions: 507
- Total comparisons: 215,475 (425 × 507)
- Embedding candidate filtering: 2,125 comparisons passed to LLM (99% reduction)
- LLM verification time: 11 minutes (parallel processing with 16 workers)

**Crosswalk Results:**
- **Semantic matches:** 82 (19.3%)
- **High confidence (≥90%):** 77 (94% of matches)
- **Medium confidence (70-89%):** 4 (4.9% of matches)
- **Low confidence (<70%):** 1 (1.2% of matches)
- **High-impact variances:** 186
- **Medium-impact variances:** 136
- **Low-impact variances:** 3

---

## What This Test Validates

### ✅ Validates (Proven by POC)

1. **Cross-vendor mapping** - Testing Relius → Ascensus (hardest use case)
2. **Vision extraction works** - Handles complex form structures (checkboxes, nested options)
3. **Parallel processing works** - 16-worker architecture provides 6x speedup
4. **Hybrid architecture works** - Embeddings + LLM provides 99% cost reduction

### ⚠️ Validation In Progress (Red Team Sprint Oct 23, 2025)

1. **Semantic mapping algorithm** - Initial results show quality issues (section headings matched to provisions, embedding pollution)
2. **Confidence scoring calibration** - Need to validate 94% high-confidence claim against SME review
3. **Variance detection accuracy** - Need to validate Administrative/Design/Regulatory classification
4. **Provisional matching for templates** - BPD template matches may not be valid if election structures differ

### ⬜ Not Yet Validated (Requires Fixes or Additional Test Data)

1. **Vendor-specific default detection** - e.g., Relius auto-includes HCEs vs ASC requires checkbox
2. **Multiple vendor document formats** - Different template structures across providers
3. **Real production data** - Actual client conversions with live plan elections
4. **Intra-vendor edition comparison** - Would require obtaining Ascensus BPD 01 → BPD 05 pair

---

## Why Cross-Vendor Testing is Critical

**This corpus tests the hardest use case**: Relius → Ascensus conversion.

**Challenges:**
1. **Different terminology** - "Plan Administrator" (Relius) vs "Employer" (Ascensus)
2. **Different section numbering** - No alignment between document structures
3. **Different election presentation** - Question numbering, option structures vary
4. **Vendor-specific defaults** - Implicit vs explicit elections (e.g., HCE inclusion in safe harbor)
5. **Template language differences** - Same legal concept, completely different wording

**Why this validates the core algorithm:** If semantic matching works for cross-vendor (different words, different structure), it will work even better for intra-vendor edition changes (same vendor, just updated language).

**Current status:** POC has generated crosswalks, but quality issues identified in Red Team Sprint suggest extraction and fingerprinting need revision before validation can proceed.

---

## Additional Test Data Needs (Future)

To expand validation beyond current Relius → Ascensus corpus:

### Priority 1: Other Cross-Vendor Scenarios
- **ftwilliam → Ascensus** - Second most common conversion
- **DATAIR → Ascensus** - Enterprise recordkeeper migrations
- **Ascensus → Relius** - Reverse direction for bidirectional validation

### Priority 2: Intra-Vendor Scenarios
- **Ascensus BPD 01 → BPD 05** - Edition change within same vendor
- **Relius Cycle 2 → Cycle 3** - Regulatory update restatements

### Priority 3: Edge Cases
- **Volume submitter → Prototype** - Different IRS Opinion Letter structure
- **Standardized → Non-standardized AA** - Different election presentation
- **Multiple Employer Plan (MEP) documents** - Participating employer addendums

### Document Requirements
- Matching plan structure (same 401(k) Profit Sharing type)
- Same IRS Cycle (for apples-to-apples comparison)
- Both source and target BPDs + AAs
- Mix of blank and completed AAs for testing election merging

---

## File Structure

```
test_data/
├── README.md                                      # This file - corpus documentation
│
├── raw/                                           # Original PDFs (GITIGNORED)
│   ├── source_bpd.pdf                            # Relius Cycle 3 BPD (canonical)
│   ├── source_aa.pdf                             # Relius Cycle 3 AA (canonical)
│   ├── target_bpd.pdf                            # Ascensus BPD (canonical)
│   ├── target_aa.pdf                             # Ascensus AA (canonical)
│   │
│   ├── Cycle 3 Basic Plan Document 05-001.pdf    # Original filename → source_bpd.pdf
│   ├── Blank Cycle 3 Adoption Agreement.pdf      # Original filename → source_aa.pdf
│   ├── Basic Plan Document.pdf                   # Original filename → target_bpd.pdf
│   └── 401(k) Profit Sharing Plan.pdf            # Original filename → target_aa.pdf
│
├── extracted/                                     # Vision extraction outputs (current)
│   ├── source_bpd_provisions.json                # 426 provisions from Relius BPD
│   ├── source_aa_elections.json                  # 521 elections from Relius AA
│   ├── target_bpd_provisions.json                # 507 provisions from Ascensus BPD
│   └── target_aa_elections.json                  # 235 elections from Ascensus AA
│
├── crosswalks/                                   # Semantic mapping outputs (current)
│   ├── bpd_crosswalk.json                        # 425 Relius→Ascensus BPD mappings (JSON)
│   ├── bpd_crosswalk.csv                         # 425 Relius→Ascensus BPD mappings (CSV)
│   ├── aa_crosswalk.json                         # Relius→Ascensus AA mappings (JSON)
│   └── aa_crosswalk.csv                          # Relius→Ascensus AA mappings (CSV)
│
└── archive/                                      # Historical extractions and experiments
    └── YYYY-MM-DD_description/                   # Timestamped experiment archives
        ├── extracted/
        ├── crosswalks/
        └── notes.md
```

**Naming Convention:**
- **Canonical names** (source_*.pdf, target_*.pdf) are explicit about direction
- **Original filenames** preserved for reference but canonical names used in processing
- **Extracted outputs** match canonical naming (source_bpd_provisions.json, not relius_bpd_provisions.json)
- **Archive folders** use timestamps to preserve experiment history

---

## Data Lineage

```
Raw PDFs (Relius BPD + AA, Ascensus BPD + AA)
   ↓ (GPT-5-nano vision extraction, 18 min, 16 workers)
Vision Extraction JSONs (426 + 521 + 507 + 235 items)
   ↓ (Embeddings + LLM semantic mapping, 11 min, 16 workers)
BPD Crosswalk (425 Relius → 507 Ascensus mappings)
   ↓ (Red Team Sprint validation, in progress Oct 23, 2025)
⚠️ Quality Issues Identified (see Validation Status below)
```

---

## Usage Notes

### For Red Team Sprint Validation
1. Use `crosswalk/bpd_crosswalk.csv` as primary review document
2. Reference `/test_results/red_team_2025-10-20.md` for sample selection
3. Look up provision IDs in `extracted_vision/*.json` for full text
4. Validate semantic equivalence using domain expertise (ERISA/IRC knowledge)

### For Future Cross-Vendor Testing
1. Obtain documents following "Cross-Vendor Test Data Requirements" above
2. Place in `test_data/raw/cross_vendor/[vendor_name]/`
3. Run vision extraction pipeline
4. Generate crosswalk
5. Compare accuracy metrics: intra-vendor vs cross-vendor

### For Production Deployment
1. Test with real client conversion (obtain sponsor approval)
2. Compare AI-generated crosswalk vs manual reconciliation
3. Measure time savings, error detection, confidence calibration
4. Document lessons learned for prompt/architecture refinement

---

## Validation Status

**Current Status**: Red Team Sprint in progress (Oct 23, 2025)

**Quality Issues Identified:**
1. ❌ **Section headings extracted as provisions** - Vision extraction includes TOC entries and headers with no substantive content
2. ❌ **Embedding pollution** - Question numbers and section numbers skew semantic similarity (unrelated provisions show 40-60% similarity)
3. ❌ **Cross-topic false matches** - Template matches valid but provisional (depend on election compatibility)
4. ❌ **AA false positives** - Age eligibility matched to State address at 92% confidence due to question number pollution

**Remediation Plan:**
1. Revise vision extraction prompts to skip section headings
2. Implement semantic fingerprinting (strip structural artifacts before embedding)
3. Add provision type classification (definition, rule, heading)
4. Re-extract corpus with improved prompts
5. Execute Red Team Sprint on extraction quality before attempting semantic mapping

**Next Milestones:**
- ⬜ Complete provisional matching design document
- ⬜ Fix vision extraction and re-run
- ⬜ Validate extraction quality (Red Team Sprint)
- ⬜ Re-generate crosswalks with clean data
- ⬜ Validate semantic mapping accuracy

---

*Last Updated: 2025-10-23*
*Test Corpus Owner: Sergio DuBois*
*Vendor Identity Confirmed: Relius (source) → Ascensus (target) per Lauren Leneis, Oct 21, 2025*
