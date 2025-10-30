# PIPELINE.md Audit - Oct 30, 2025

## Executive Summary

**CRITICAL FINDING:** PIPELINE.md describes a **v6/v7/v8 pipeline that does NOT exist**. The actual project state is **v4** (Oct 24, 2025 baseline).

**Status:** 🔴 PIPELINE.md is **INCORRECT and MISLEADING**

## Discrepancies Found

### 1. Extraction Scripts (Phase 1)

**PIPELINE.md Claims:**
- `scripts/extract_relius_bpd_v6.py`
- `scripts/extract_ascensus_bpd_v6.py`
- `scripts/extract_relius_aa_v6.py`
- `scripts/extract_ascensus_aa_v6.py`

**Reality:**
```bash
$ ls scripts/extract_*.py
scripts/extract_aa_pairs.py
scripts/extract_both_documents.py
scripts/extract_bpd_pairs.py
scripts/extract_bpd_pairs_v3.py
scripts/extract_operational_provisions.py
```

❌ **None of the v6 scripts exist**

### 2. Post-Processing Scripts (Phase 2)

**PIPELINE.md Claims:**
- `scripts/postprocess_sanitize.py`
- `scripts/postprocess_sanitize_aa.py`
- `scripts/postprocess_defragment.py`
- `scripts/postprocess_defragment_aa.py`
- `scripts/postprocess_assign_ids.py`
- `scripts/postprocess_assign_ids_aa.py`

**Reality:**
```bash
$ ls scripts/postprocess_*.py
ls: scripts/postprocess_*.py: No such file or directory
```

❌ **Zero post-processing scripts exist**

### 3. Conversion Script (Phase 2.4)

**PIPELINE.md Claims:**
- `scripts/convert_aa_v6_to_elections.py` (marked as "Pending implementation")

**Reality:**
```bash
$ ls scripts/convert_*.py
ls: scripts/convert_*.py: No such file or directory
```

❌ **Does not exist** (correctly marked as pending, but...)

### 4. Extraction Data (Test Data)

**PIPELINE.md Claims:**
- `test_data/extracted_vision_v6/` with:
  - `relius_bpd_provisions_raw.json` (489 provisions)
  - `ascensus_bpd_provisions_raw.json` (218 provisions)
  - `relius_aa_elections_raw.json` (1,294 elections)
  - `ascensus_aa_elections_raw.json` (2,708 elections)
  - Plus sanitized, defragmented, and final versions

**Reality:**
```bash
$ ls test_data/extracted_vision*/
test_data/extracted_vision_v4/:
source_aa_elections.json (167 elections)
source_bpd_provisions.json (542 provisions)
target_aa_elections.json (527 elections)
target_bpd_provisions.json (384 provisions)
```

❌ **v6 data does NOT exist** (was removed during rollback)
✅ **v4 data exists** from Oct 24

### 5. Prompts

**PIPELINE.md Claims:**
- `prompts/provision_extraction_v6_draft.txt`
- `prompts/aa_extraction_v6_unified.txt`
- `prompts/semantic_mapping_v3.txt`

**Reality:**
```bash
$ ls prompts/*extraction*.txt
prompts/aa_extraction_v1.txt
prompts/aa_extraction_v2.txt
prompts/aa_extraction_v3.txt
prompts/aa_extraction_v4.txt  ✅
prompts/provision_extraction_v1.txt
prompts/provision_extraction_v2.txt
prompts/provision_extraction_v3.txt
prompts/provision_extraction_v4.txt  ✅
```

❌ **No v6 prompts**
✅ **v4 prompts exist**

**Semantic mapping:**
```bash
$ ls prompts/semantic_mapping*.txt
prompts/aa_semantic_mapping_v1.txt  ✅
prompts/semantic_mapping_v1.txt  ✅
```

❌ **No v3 semantic mapping prompt**
✅ **v1 prompts exist**

### 6. Crosswalk Scripts

**PIPELINE.md Claims:**
- `scripts/run_bpd_crosswalk.py` (generates v3 output)
- `scripts/run_aa_crosswalk.py` (generates v1 output)

**Reality:**
```bash
$ ls scripts/run_*.py
scripts/run_aa_crosswalk.py  ✅
scripts/run_bpd_crosswalk.py  ✅
```

✅ **Scripts exist**

❓ **But do they work? Need to test**

### 7. Crosswalk Data

**PIPELINE.md Claims:**
- `test_data/crosswalks/bpd_crosswalk_v3.json`
- `test_data/crosswalks/bpd_crosswalk_v3.csv`
- `test_data/crosswalks/aa_crosswalk_v1.json`
- `test_data/crosswalks/aa_crosswalk_v1.csv`

**Reality:**
```bash
$ ls test_data/crosswalks/
aa_crosswalk.csv
aa_crosswalk.json
bpd_crosswalk.csv
bpd_crosswalk.json
```

❓ **Crosswalk files exist but no version suffix**
❓ **Are these v1 or v3? Unknown**

### 8. Tests

**PIPELINE.md Claims:**
- `tests/test_v3_input_builder.py`
- `tests/test_v3_semantic_mapper.py`
- `tests/test_aa_semantic_mapper.py`

**Reality:**
```bash
$ ls tests/test*.py
tests/test_aa_conversion.py
tests/test_aa_input_builder.py  ✅
tests/test_aa_semantic_mapper.py  ✅
```

❌ **No v3 tests**
✅ **AA tests exist**

## What Actually Works (Oct 24 Baseline)

Based on our rollback to f9ad942:

### ✅ Working Components

1. **Extraction v4:**
   - Scripts: `scripts/extract_bpd_pairs.py`, `scripts/extract_aa_pairs.py` (likely)
   - Prompts: `prompts/provision_extraction_v4.txt`, `prompts/aa_extraction_v4.txt`
   - Data: `test_data/extracted_vision_v4/` (542 source BPD, 384 target BPD, 167 source AA, 527 target AA)

2. **Semantic Mapping v1:**
   - Scripts: `scripts/run_bpd_crosswalk.py`, `scripts/run_aa_crosswalk.py`
   - Prompts: `prompts/semantic_mapping_v1.txt`, `prompts/aa_semantic_mapping_v1.txt`
   - Data: `test_data/crosswalks/*.json` (unknown version)

3. **Tests:**
   - `tests/test_aa_input_builder.py` (11 tests passing)
   - `tests/test_aa_semantic_mapper.py` (8 tests passing)
   - `tests/test_aa_conversion.py` (20 tests passing)

### ❌ Missing Components

1. **v6 extraction** - Does not exist
2. **Post-processing pipeline** - Does not exist
3. **v3 semantic mapping** - Does not exist
4. **v6 data** - Was removed during rollback

## Root Cause

**PIPELINE.md was written by Codex** describing the v6/v7/v8 pipeline that Codex was *planning* to implement, not what actually existed.

During the rollback, we:
- ✅ Removed Codex's v6 scripts and data
- ✅ Restored to Oct 24 (f9ad942) baseline
- ❌ **Forgot to revert PIPELINE.md** - It came from the stash with YOUR uncommitted work

PIPELINE.md is a **Codex artifact** describing a **non-existent future state**.

## Correct Baseline State (Oct 24)

### What We Have:
- **Extraction:** v4 pipeline (validated Red Team Sprint A)
- **Data:** 1,620 provisions/elections in `test_data/extracted_vision_v4/`
- **Semantic Mapping:** v1 (BPD and AA)
- **Tests:** 39 passing

### What We Don't Have:
- v6 extraction
- Post-processing (sanitize, defragment, assign IDs)
- v3 semantic mapping
- Conversion scripts

## Recommended Actions

### Priority 1: Fix PIPELINE.md
Replace with accurate v4 pipeline documentation matching Oct 24 baseline.

### Priority 2: Test Current Pipeline
Verify that `scripts/run_bpd_crosswalk.py` and `scripts/run_aa_crosswalk.py` actually work with v4 data.

### Priority 3: Update CLAUDE.md
Correct project status to reflect v4 baseline, not v6/v7/v8.

### Priority 4: Document Known Issues
From NEXT_SESSION.md (Oct 24), we were about to:
1. Review semantic mapper implementation
2. Identify gaps (fingerprinting, provisional matching, variance model)
3. Decide whether to improve mapper or proceed

## Impact Assessment

**Severity:** 🔴 **CRITICAL**

**Impact:**
- PIPELINE.md cannot be used as operational guide
- Confusion about what actually works
- Risk of attempting to run non-existent scripts
- Misaligned expectations about project state

**Mitigation:**
- Rewrite PIPELINE.md to match v4 reality
- Test current crosswalk scripts
- Update CLAUDE.md with accurate status

## Next Steps

1. Create accurate PIPELINE_V4.md from scratch
2. Test `scripts/run_bpd_crosswalk.py` and `scripts/run_aa_crosswalk.py`
3. Audit CLAUDE.md for accuracy
4. Document true project capabilities
