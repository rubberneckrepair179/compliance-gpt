# PIPELINE.md - Production Pipeline Manifest

**Last Updated:** 2025-10-30
**Pipeline Version:** v8 (AA semantic mapping v1 integrated)

---

## Overview

This document defines the **production-ready components** of the compliance-gpt extraction and crosswalk pipeline. Scripts NOT listed here are either tests, prototypes, or deprecated iterations.

**Purpose:**
- Document canonical production scripts
- Define execution order and dependencies
- Track input/output artifacts
- Distinguish production from test/prototype code

**See also:** [CLAUDE.md](CLAUDE.md) for project context and design rationale.

---

## Production Pipeline Components

### Phase 1: Extraction

#### 1.1 BPD Extraction (Templates)

**Production Scripts:**
- `scripts/extract_relius_bpd_v6.py` - Extract Relius BPD provisions
- `scripts/extract_ascensus_bpd_v6.py` - Extract Ascensus BPD provisions

**Configuration:**
- **Prompt:** `prompts/provision_extraction_v6_draft.txt`
- **Model:** GPT-5-nano (gpt-5-nano)
- **Workers:** 16 parallel
- **Batch size:** 1 page/request (required for page number substitution)

**Inputs:**
- `test_data/raw/relius/relius_bpd_cycle3.pdf` (100 pages)
- `test_data/raw/ascensus/ascensus_bpd.pdf` (81 pages)

**Outputs:**
- `test_data/extracted_vision_v6/relius_bpd_provisions_raw.json` (489 provisions)
- `test_data/extracted_vision_v6/ascensus_bpd_provisions_raw.json` (218 provisions)

**Success Rate:** 96% (Relius), 96% (Ascensus)
**Processing Time:** ~6-8 minutes per document

---

#### 1.2 AA Extraction (Elections)

**Production Scripts:**
- `scripts/extract_relius_aa_v6.py` - Extract Relius AA elections
- `scripts/extract_ascensus_aa_v6.py` - Extract Ascensus AA elections

**Configuration:**
- **Prompt:** `prompts/aa_extraction_v6_unified.txt`
- **Model:** GPT-5-mini (gpt-5-mini) - 100% success rate validated
- **Workers:** 16 parallel
- **Batch size:** 1 page/request (required for page number substitution)

**Inputs:**
- `test_data/raw/relius/relius_aa_cycle3.pdf` (45 pages)
- `test_data/raw/ascensus/ascensus_aa_profit_sharing.pdf` (104 pages)

**Outputs:**
- `test_data/extracted_vision_v6/relius_aa_elections_raw.json` (1,294 elections)
- `test_data/extracted_vision_v6/ascensus_aa_elections_raw.json` (2,716 elections)

**Success Rate:** 100% (both documents)
**Processing Time:** 7m 11s (Relius), 11m 13s (Ascensus)

---

### Phase 2: Post-Processing

#### 2.1 Sanitize (Step 1)

**Purpose:** Clean control characters and formatting artifacts (deterministic, no LLM)

**Production Scripts:**
- `scripts/postprocess_sanitize.py` - Sanitize BPD provisions
- `scripts/postprocess_sanitize_aa.py` - Sanitize AA elections

**Inputs:**
- `test_data/extracted_vision_v6/*_raw.json`

**Outputs:**
- `test_data/extracted_vision_v6/*_sanitized.json`

**Processing:** Removes control characters, zero-width spaces, normalizes whitespace

---

#### 2.2 Defragment (Step 2)

**Purpose:** Merge multi-page provisions/elections split during extraction (deterministic, no LLM)

**Production Scripts:**
- `scripts/postprocess_defragment.py` - Defragment BPD provisions
- `scripts/postprocess_defragment_aa.py` - Defragment AA elections

**Inputs:**
- `test_data/extracted_vision_v6/*_sanitized.json`

**Outputs:**
- `test_data/extracted_vision_v6/*_defragmented.json`

**Logic:** Uses `fragment_position` field (start/continue/end/complete) to merge fragments

---

#### 2.3 Assign IDs (Step 3)

**Purpose:** Generate unique, deterministic identifiers (deterministic, no LLM)

**Production Scripts:**
- `scripts/postprocess_assign_ids.py` - Assign IDs to BPD provisions
- `scripts/postprocess_assign_ids_aa.py` - Assign IDs to AA elections

**Inputs:**
- `test_data/extracted_vision_v6/*_defragmented.json`

**Outputs:**
- `test_data/extracted_vision_v6/*_final.json`

**ID Format:** `{vendor}_{doc_type}_p{page}_{section_number}`
- Examples: `relius_bpd_p7_1.1`, `ascensus_aa_p11_Q1.04`

---

#### 2.4 Election Schema Conversion (AA only)

**Purpose:** Transform provision-style AA extractions (v6) into the `Election` schema consumed by the semantic mapper.

**Production Script:** _Pending implementation_ (`scripts/convert_aa_v6_to_elections.py`)

**Inputs:**
- `test_data/extracted_vision_v6/relius_aa_elections_final.json`
- `test_data/extracted_vision_v6/ascensus_aa_elections_final.json`

**Outputs:**
- `test_data/extracted_vision_v6/relius_aa_elections_converted.json`
- `test_data/extracted_vision_v6/ascensus_aa_elections_converted.json`

**Transformation highlights:**
- Detect election anchors via `selection_field.kind` / `text_field`.
- Assemble options and fill-ins as defined in `src/models/election.py`.
- Derive status/value/section context per spec (§6 in `design/reconciliation/aa_mapping.md`).

**Status:** Design complete; implementation assigned to Claude (Sprint 2 follow-up).

---

### Phase 3: Crosswalk (Semantic Mapping)

#### 3.1 BPD Crosswalk (Semantic Mapping v3)

**Production Script:**
- `scripts/run_bpd_crosswalk.py` — Generates v3-compliant provision mappings (JSON + CSV)

**Configuration:**
- **Model:** GPT-5-mini (semantic reasoning) via v3 prompt (`prompts/semantic_mapping_v3.txt`)
- **Strategy:** Hybrid embeddings + LLM verification with Step 0–5 structured output
- **Parallelism:** 16 workers (configurable), top-k candidate verification default 5

**Inputs:**
- `test_data/extracted_vision_v6/relius_bpd_provisions_final.json` (489 provisions)
- `test_data/extracted_vision_v6/ascensus_bpd_provisions_final.json` (218 provisions)

**Outputs:**
- `test_data/crosswalks/bpd_crosswalk_v3.json` — Structured mappings (topic alignment, element deltas, categorical confidence)
- `test_data/crosswalks/bpd_crosswalk_v3.csv` — Reviewer-friendly export including legacy columns for backward compatibility

**Notes:**
- Logging emitted to `logs/bpd_crosswalk.log` (run ID, confidence/impact distributions).
- Legacy v1/v2 crosswalk exports remain available in `/test_data/crosswalks/` for reference.

---

#### 3.2 AA Crosswalk (Semantic Mapping v1)

**Production Script:**
- `scripts/run_aa_crosswalk.py` — Generates v1 election mappings (JSON + CSV)

**Configuration:**
- **Model:** GPT-5-mini via AA prompt (`prompts/aa_semantic_mapping_v1.txt`)
- **Strategy:** Hybrid embeddings (fingerprints from `build_election_fingerprint`) + LLM verification with structured AA schema
- **Parallelism:** 16 workers (configurable), top-k candidate verification default 3

**Inputs:**
- `test_data/extracted_vision_v6/relius_aa_elections_converted.json` (1,294 elections)
- `test_data/extracted_vision_v6/ascensus_aa_elections_converted.json` (2,708 elections)

**Outputs:**
- `test_data/crosswalks/aa_crosswalk_v1.json` — Structured election mappings (question alignment, option relationships, variance classification)
- `test_data/crosswalks/aa_crosswalk_v1.csv` — Reviewer export with option summaries and confidence columns

**Notes:**
- Logging emitted to `logs/aa_crosswalk.log` (run ID, confidence distribution, timing).
- CLI depends on configured OpenAI/Anthropic API keys; see `src/config/settings.py` for environment variables.
- Mapper implementation: `src/mapping/aa_semantic_mapper.py`; deterministic unit tests in `tests/test_aa_semantic_mapper.py`.

---

## Final Production Artifacts

### Quality-Controlled Extractions

**BPD Provisions (Templates):**
- `test_data/extracted_vision_v6/relius_bpd_provisions_final.json` - 489 provisions
- `test_data/extracted_vision_v6/ascensus_bpd_provisions_final.json` - 218 provisions

**AA Elections:**
- `test_data/extracted_vision_v6/relius_aa_elections_final.json` - 1,294 elections
  - Text fields: 335 (26%), Selection fields: 1,011 (78%), Headers: 95 (7%)
- `test_data/extracted_vision_v6/ascensus_aa_elections_final.json` - 2,708 elections
  - Text fields: 581 (21%), Selection fields: 1,916 (71%), Headers: 266 (10%)

### Crosswalks

**BPD Crosswalk (v3):**
- `test_data/crosswalks/bpd_crosswalk_v3.json`
- `test_data/crosswalks/bpd_crosswalk_v3.csv`

**AA Crosswalk (v1):**
- `test_data/crosswalks/aa_crosswalk_v1.json`
- `test_data/crosswalks/aa_crosswalk_v1.csv`

---

## Quick Start: Running the Full Pipeline

### 1. Extract BPDs

```bash
python3 scripts/extract_relius_bpd_v6.py
python3 scripts/extract_ascensus_bpd_v6.py
```

### 2. Extract AAs

```bash
python3 scripts/extract_relius_aa_v6.py
python3 scripts/extract_ascensus_aa_v6.py
```

### 3. Post-Process All Extractions

```bash
# BPD post-processing
python3 scripts/postprocess_sanitize.py
python3 scripts/postprocess_defragment.py
python3 scripts/postprocess_assign_ids.py

# AA post-processing
python3 scripts/postprocess_sanitize_aa.py
python3 scripts/postprocess_defragment_aa.py
python3 scripts/postprocess_assign_ids_aa.py
```

### 4. Convert AA Extractions to Election Schema

```bash
python3 scripts/convert_aa_v6_to_elections.py
```

Generates `*_aa_elections_converted.json` files expected by the AA crosswalk.

### 5. Generate BPD Crosswalk (v3)

```bash
python3 scripts/run_bpd_crosswalk.py
```

Outputs (`test_data/crosswalks/bpd_crosswalk_v3.*`) and logs (`logs/bpd_crosswalk.log`) will be produced automatically. Expect ~25–30 minutes for the full pipeline (extraction + post-processing + semantic mapping) on reference hardware.

### 6. Generate AA Crosswalk (v1)

```bash
python3 scripts/run_aa_crosswalk.py
```

Outputs (`test_data/crosswalks/aa_crosswalk_v1.*`) and logs (`logs/aa_crosswalk.log`) will be produced automatically. Expected runtime ≈20 minutes with embeddings + top-k LLM verification.

---

## Test & Prototype Scripts (Non-Production)

These scripts are for validation, prototyping, or iteration - **not part of production pipeline:**

### Extraction Tests
- `scripts/test_aa_extraction_v2.py` - Early AA extraction prototype
- `scripts/test_aa_v6_unified_pages_1_5.py` - AA v6 prompt validation (5 pages)
- `scripts/test_aa_v6_2_pages_2_3.py` - AA v6.2 iteration testing
- `scripts/test_aa_v6_pages_1_5.py` - AA v6 pages 1-5 validation
- `scripts/test_hybrid_aa_pages_1_5.py` - Hybrid nano→mini approach test
- `scripts/test_bpd_extraction_v4_1.py` - BPD v4.1 testing
- `scripts/test_v6_pages_*.py` - Various v6 validation tests

### Analysis & Utility Scripts
- `scripts/show_aa_matches.py` - Display AA crosswalk matches
- `scripts/extract_sample_pages.py` - Extract specific pages for testing
- `scripts/forensic_analysis.py` - Debug extraction issues
- `scripts/validate_ground_truth.py` - Manual validation helper
- `scripts/test_semantic_matching.py` - Test semantic matching algorithms

### Experimental Scripts
- `scripts/test_hierarchical_extraction.py` - Hierarchical extraction experiments
- `scripts/test_mini_escalation_page_3.py` - Mini escalation testing

---

## Deprecated Components

### Deprecated Scripts (v5 and earlier)
- `scripts/extract_relius_bpd_v5.py` - Replaced by v6
- `scripts/extract_relius_bpd_v6.py` uses v6 prompt (76% word reduction)

### Deprecated Prompts
- `prompts/provision_extraction_v5.txt` - Replaced by v6_draft
- `prompts/aa_extraction_v1.txt` through `v4.txt` - Replaced by v6_unified
- `prompts/aa_extraction_v6_draft.txt` - Intermediate iteration (v6_unified is final)
- `prompts/aa_extraction_v6_2_*.txt` - Experimental split approach (not adopted)

### Deprecated Data
- `test_data/extracted_vision_v4/` - Old extraction format
- `test_data/extracted_vision_v5/` - Previous iteration
- `test_data/crosswalks/archive_2025-10-27/` - Archived crosswalks (pre-correction)

---

## Validation & Quality Checks

### Expected Output Counts (for validation)

**BPD Extraction:**
- Relius: ~489 provisions (96% page success rate)
- Ascensus: ~218 provisions (96% page success rate)

**AA Extraction:**
- Relius: ~1,294 elections (100% page success rate)
- Ascensus: ~2,708 elections (100% page success rate)

**BPD Crosswalk (v3 runner):**
- Metrics recomputed per run; inspect `bpd_crosswalk_v3.json` for aggregate stats and `logs/bpd_crosswalk.log` for confidence/impact distribution.

### Quality Checks

1. **Extraction completeness:** All pages extracted (100% success rate for AA, 96% for BPD)
2. **ID uniqueness:** <1% duplicate IDs (handled with `_dup` suffix)
3. **Fragment merging:** Multi-page provisions properly merged
4. **Confidence calibration:** 90%+ confidence scores should be 90%+ accurate (validated)

---

## Automated Tests

- `pytest tests/test_v3_input_builder.py`
  - Verifies definition glossary extraction, election dependency heuristics, and v3 payload contract.
- `pytest tests/test_v3_semantic_mapper.py`
  - Confirms parser hydration of Step 0–5 structures and exercises a smoke comparison with monkeypatched dependencies.
- `pytest tests/test_aa_semantic_mapper.py`
  - Validates AA mapper parsing, confidence-based ranking, and failure fallback using deterministic stubs (run via `python - <<'PY' ... pytest.main(...)` in sandboxed environments).

Run both after modifying semantic mapping logic before executing the full pipeline script.

---

## Model Selection Rationale

### GPT-5-nano for BPD
- **Why:** 96% success rate, cost-efficient for large template documents
- **Trade-off:** Occasional fragment issues (acceptable with post-processing)

### GPT-5-mini for AA
- **Why:** 100% success rate, handles form-based extraction better than nano
- **Trade-off:** ~2x cost vs nano, but justified by quality improvement
- **Validation:** 5-page test showed 100% success (vs 50-66% for nano on AA)

### GPT-5-mini for Semantic Mapping (v3)
- **Why:** Delivers structured Step 0–5 reasoning with categorical confidence and lower latency than GPT-4.x
- **Alternative:** Claude Sonnet 4.5 remains an option for redundancy (accuracy trade-offs pending evaluation)
- **Cost optimization:** Hybrid embeddings + top-k LLM verification (≈95% reduction vs naive pairwise comparison)

---

## Pipeline Versioning

- **v7** (Current) - Semantic mapping v3 integrated (builder, mapper, CLI, tests)
- **v6** (Legacy) - BPD + AA extraction complete, BPD crosswalk v1
- **v5** (Deprecated) - BPD-only extraction, heavier prompts
- **v4** (Deprecated) - Early prototypes

**Breaking changes trigger new version number.** Prompt iterations within same version use suffixes (e.g., v6_draft, v6_unified).

---

## Future Production Components (Planned)

1. **BPD+AA Merger** - Substitute elected values into BPD template provisions
2. **Executive Summary Generator** - Natural language report from crosswalks
3. **Cross-Vendor Validation** - Requires obtaining ftwilliam, DATAIR samples
4. **Confidence Calibration** - Align LLM categorical confidence to empirical probabilities

---

## Known Issues & Backlog

### Semantic Matching Improvements

**Issue:** Section titles excluded from embeddings (under-utilizing semantic signal)

**Current State:**
- Only `provision_text` is embedded for semantic matching
- `section_title` contains valuable semantic content (e.g., "Forfeitures", "Vesting Schedule")
- Missing title signal may reduce cosine similarity for semantically equivalent provisions

**Example:**
```
Relius: section_title="Forfeiture Application", provision_text="Such amounts shall reduce obligations"
Ascensus: section_title="Use of Forfeitures", provision_text="Forfeitures may offset requirements"
```
Both titles contain "Forfeiture/Forfeitures" but neither provision_text does → low cosine similarity

**Proposed Solution (Option A):**
```python
def prepare_text_for_embedding(prov: Provision) -> str:
    """Prepare provision text for embedding with semantic content only."""
    # Clean title: strip numbering but keep semantic terms
    clean_title = re.sub(r'^\d+\.?\d*\.?\s*', '', prov.section_title or '')

    # Concatenate if title exists and isn't already in text
    if clean_title and not prov.provision_text.startswith(f'"{clean_title}"'):
        return f"{clean_title}. {prov.provision_text}"

    return prov.provision_text
```

**Principle:** Include semantic content (titles), exclude structural metadata (section numbers)

**Priority:** Medium - No evidence of false negatives yet, but logical improvement

**Status:** Backlogged pending Red Team validation of current crosswalk accuracy

---

### Cover Page Filtering (AA Extraction)

**Issue:** Cover page metadata extracted as text_fields (semantically valid but noisy)

**Example:** Plan Name and Plan Type on Ascensus AA cover page

**Priority:** Low - Extraction is technically correct, just includes non-election data

**Status:** Backlogged

---

## Notes

- All production scripts use externalized prompts (loaded from `prompts/` directory)
- Post-processing is 100% deterministic (no LLM inference)
- Extraction uses parallel workers (16) for performance
- All outputs are version-controlled JSON (human-readable with indent=2)
- ID format ensures uniqueness and traceability to source documents

---

**For project context, design rationale, and regulatory background, see:** [CLAUDE.md](CLAUDE.md)
**For user-facing documentation and project overview, see:** [README.md](README.md)
