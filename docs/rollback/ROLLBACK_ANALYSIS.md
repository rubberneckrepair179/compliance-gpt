# Selective Rollback Analysis - Oct 30, 2025

## Goal
Separate YOUR work (Sergio + Claude Code collaboration) from CODEX additions in commit e0e9499.

## Files Categorized

### 🟢 KEEP - Your Work (Sergio + Claude)
These files represent legitimate collaboration before Codex:

**Modified in stash (YOUR uncommitted work):**
- `PIPELINE.md` - Updated to v8 with AA crosswalk (YOU said this is important)
- `README.md` - Status updates
- `SESSION_SUMMARY.md` - Session notes
- `design/reconciliation/aa_mapping.md` - AA mapping spec updates
- `prompts/README.md` - Prompt version history
- `prompts/aa_semantic_mapping_v1.txt` - AA mapping prompt v1.1.1
- `scripts/run_aa_crosswalk.py` - AA crosswalk CLI
- `src/mapping/aa_semantic_mapper.py` - AA mapper implementation
- `src/models/aa_mapping.py` - AA data models
- `team/current-sprint.md` - Sprint tracking (if this existed before Codex)
- `tests/test_aa_semantic_mapper.py` - AA mapper tests

**From e0e9499 to potentially keep:**
- `PIPELINE.md` (first version - base for your updates)
- `src/mapping/semantic_mapper.py` (modified Oct 28 - may be yours)
- `test_data/crosswalks/*.csv`, `*.json` (crosswalk results - may be yours)

### 🔴 DELETE - Codex Additions
These files appear to be Codex documentation/experiments:

**Documentation overload:**
- `FRONTIER_CONSULTATION.md` (471 lines - consultation logs)
- `START_HERE_2025-10-29.md` (176 lines - Codex planning)
- `START_HERE_2025-10-29_V3_IMPLEMENTATION.md` (648 lines - unimplemented plans)
- `docs/bpd_crosswalk_manual_workflow.md` (503 lines)
- `docs/fragment_merger_logic.md` (252 lines)
- `docs/prompt_consultation_request_2025-10-28.md` (310 lines)
- `docs/prompt_v2_reaction.md` (461 lines)
- `docs/prompt_v2_review_feedback.md` (188 lines)
- `docs/prompt_v2_review_request.md` (403 lines)
- `docs/prompt_v3_reaction.md` (574 lines)
- `docs/session_end_2025-10-28.md` (61 lines)
- `docs/session_status_2025-10-28.md` (338 lines)

**Unvalidated prompt iterations:**
- `prompts/aa_extraction_v6_2_structure.txt`
- `prompts/aa_extraction_v6_2_values.txt`
- `prompts/aa_extraction_v6_draft.txt`
- `prompts/aa_extraction_v6_unified.txt`
- `prompts/provision_extraction_v4.1.txt`
- `prompts/provision_extraction_v5.txt`
- `prompts/provision_extraction_v6_draft.txt`
- `prompts/semantic_mapping_v2.txt` (superseded by v3)
- `prompts/semantic_mapping_v3.txt` (unimplemented design debt)

**Research logs:**
- `research/prompt_engineering.md`
- `research/the_wizard_responds.md`

**Experimental scripts (60 total, many are tests):**
- `scripts/extract_ascensus_aa_v6.py`
- `scripts/extract_ascensus_bpd_v6.py`
- `scripts/extract_relius_aa_v6.py`
- `scripts/extract_relius_bpd_v5.py`
- `scripts/extract_relius_bpd_v6.py`
- `scripts/extract_sample_pages.py`
- `scripts/forensic_analysis.py`
- `scripts/map_relius_field_ids.py`
- `scripts/organize_test_data.py`
- `scripts/postprocess_*.py` (6 scripts)
- `scripts/red_team_aa_validation.py`
- `scripts/red_team_helper.py`
- `scripts/sanitize_and_assign_ids.py`
- `scripts/show_aa_matches.py`
- `scripts/test_*.py` (11 test scripts)
- `scripts/validate_ground_truth.py`
- `src/extraction/hybrid_aa_extractor.py`

**Extracted data (13MB - may bloat repo):**
- `test_data/extracted_vision_v4.1/`
- `test_data/extracted_vision_v5/`
- `test_data/extracted_vision_v6/` (entire directory - 28 files)
- `test_data/crosswalks/archive_2025-10-27/` (archive files)

**Test results:**
- `test_embedding_fix.py` (root level - should be in tests/)
- `test_results/ascensus_aa_elections_final_validation.json`
- `test_results/bpd_extraction_cross_vendor_v6.md`
- `test_results/bpd_extraction_v4_1_samples.md`
- `test_results/bpd_extraction_v5_vs_v6_comparison.md`
- `test_results/embedding_fix_validation_2025-10-27.md`
- `test_results/red_team_aa_extraction_2025-10-28.md`
- `test_results/red_team_aa_findings_2025-10-28.md`
- `test_results/red_team_programmatic_output.txt`
- `test_results/relius_aa_elections_final_validation.json`

### ⚠️ UNCLEAR - Need Your Input
These could be yours or Codex's:

- `CLAUDE.md` (modified - need to check what changed)
- `README.md` (modified - need to check what changed)
- `.gitignore` (modified - probably safe)
- `src/extraction/parallel_vision_extractor.py` (modified - could be yours)

## Proposed Selective Rollback Strategy

### Option A: Surgical Approach
1. Reset to f9ad942 (Oct 24)
2. Restore YOUR uncommitted work from stash (11 files)
3. Create simple PIPELINE.md v1 for v4 extraction (not overengineered v6)
4. Test that everything still works

### Option B: Cherry-pick Approach
1. Reset to f9ad942 (Oct 24)
2. Cherry-pick only the specific files we want from e0e9499:
   - PIPELINE.md (base version)
   - Any legitimate script changes
3. Apply your uncommitted stash work on top
4. Delete Codex cruft

### Option C: Manual Cleanup (Current State)
1. Stay at e0e9499
2. Delete all Codex files listed above
3. Keep your stashed work
4. Commit cleaned state

## Recommendation

**Option A** - It's cleanest because:
- Oct 24 (f9ad942) was our last verified-good state
- Your stash has 11 files of real work
- We rebuild PIPELINE.md together (15 minutes)
- No confusion about what's production vs experiment

## Next Steps

1. Get your approval on which option
2. Execute the rollback/cleanup
3. Verify tests still pass
4. Continue from clean slate
