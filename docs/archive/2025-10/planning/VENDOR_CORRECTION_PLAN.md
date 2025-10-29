# Vendor Misconception Correction Plan

**Date:** 2025-10-20
**Issue:** Project documentation incorrectly labels test data as "Relius → ASC" cross-vendor mapping
**Reality:** Test data is "Ascensus BPD 01 → Ascensus BPD 05" intra-vendor Cycle 3 restatement
**Impact:** Medium - Misleading claims about test data, but POC still validates algorithm

---

## Ground Truth

| File | Actual Vendor | Actual Document Type | Actual Version |
|------|---------------|---------------------|----------------|
| `Basic Plan Document.pdf` | Ascensus | Basic Plan Document | BPD 01 (Cycle 3) |
| `Cycle 3 Basic Plan Document 05-001.pdf` | Ascensus | Basic Plan Document | BPD 05 (Cycle 3) |
| `401(k) Profit Sharing Plan.pdf` | Ascensus | Adoption Agreement (completed) | For BPD 01 |
| `Blank Cycle 3 Adoption Agreement.pdf` | Ascensus | Adoption Agreement (template) | For BPD 05 |

**Conclusion:** All test documents are **Ascensus**. No Relius documents exist in test corpus.

---

## Correction Strategy

### Principle 1: Distinguish "Capability" from "Test Data"
- **Capability claim (KEEP):** "System can handle cross-vendor comparisons (Relius, ASC, ftwilliam)"
- **Test data claim (FIX):** "POC tested with Ascensus BPD 01 → BPD 05 (intra-vendor)"

### Principle 2: Preserve Real-World Pain Examples
- **KEEP:** Market research quote about Relius→ASC HCE safe harbor error (p.3)
- **LABEL CORRECTLY:** "This is a real-world example; our POC tests a different scenario"

### Principle 3: Future-Proof for Actual Cross-Vendor Testing
- **KEEP:** Requirements for cross-vendor capability
- **ADD:** Note that cross-vendor validation requires obtaining Relius/ftwilliam samples

---

## Files Requiring Updates (17 total)

### Critical (User-Facing Documentation)
1. ✅ **README.md** - Project description, MVP claims
2. ✅ **CLAUDE.md** - Test data labeling, project status, examples

### Design Documents (6 files)
3. ✅ **design/README.md**
4. ✅ **design/architecture/system_architecture.md**
5. ✅ **design/data_models/mapping_model.md**
6. ✅ **design/data_models/provision_model.md**
7. ✅ **design/llm_strategy/README.md**
8. ✅ **design/llm_strategy/llm_research_report.md**

### Requirements (2 files)
9. ✅ **requirements/README.md**
10. ✅ **requirements/functional_requirements.md**

### Supporting Documents (6 files)
11. ⚠️ **SESSION_SUMMARY.md** - Historical session log (may archive instead of edit)
12. ⚠️ **CRITICAL_QUESTION.md** - Historical design discussion (may archive)
13. ⚠️ **OPUS_VALIDATION.md** - Historical validation (may archive)
14. ⚠️ **GPT5_VALIDATION.md** - Recent validation (update or integrate)
15. ✅ **prompts/README.md**
16. ✅ **scripts/inspect_documents.py**
17. ✅ **design/llm_strategy/model_selection.md**
18. ✅ **design/llm_strategy/decision_matrix.md**

### Test Data (NEW - to create)
19. ✅ **test_data/README.md** - Document actual vendor/version of test corpus

---

## Replacement Patterns

### Pattern 1: Test Data Examples
**BEFORE:**
```
Example: Relius BPD → ASC prototype
```

**AFTER:**
```
Example: Cross-vendor mapping (e.g., Relius → ASC, ftwilliam → DATAIR)
POC tested with: Ascensus BPD 01 → BPD 05 (Cycle 3 restatement)
```

### Pattern 2: Current POC Status
**BEFORE:**
```
BPD crosswalk complete - 425 source → 507 target provisions mapped
```

**AFTER:**
```
BPD crosswalk complete - Ascensus BPD 01 → BPD 05
425 source provisions → 507 target provisions (Cycle 3 restatement)
```

### Pattern 3: Requirements Statements
**BEFORE:**
```
System SHALL handle cross-vendor comparisons (e.g., Relius BPD → ASC prototype)
```

**AFTER:**
```
System SHALL handle cross-vendor comparisons (e.g., Relius → ASC, ftwilliam → DATAIR)
Note: POC validation performed with intra-vendor test data (Ascensus BPD 01 → BPD 05)
```

### Pattern 4: Real-World Examples (PRESERVE with context)
**BEFORE:**
```
Market research example: Relius→ASC conversion error...
```

**AFTER:**
```
Market research example (real-world case): Relius→ASC conversion error...
Note: This illustrates cross-vendor risk; POC tested intra-vendor scenario.
```

---

## Historical Documents Decision

**Options:**
1. **Archive** - Move to `/archive/historical/` with timestamp
2. **Update** - Apply corrections inline
3. **Annotate** - Add header noting "Historical document - reflects earlier understanding"

**Recommendation:**
- **Archive:** SESSION_SUMMARY.md, CRITICAL_QUESTION.md, OPUS_VALIDATION.md
- **Update:** GPT5_VALIDATION.md (recent and valuable)
- **Keep as reference:** Market research PDF (external source, correct as-is)

---

## File Renaming (Optional but Recommended)

**Current naming suggests cross-vendor:**
- `source_bpd_01` / `target_bpd_05` → Neutral, but ambiguous

**Clearer naming:**
- `asc_bpd_01_cycle3` / `asc_bpd_05_cycle3` → Explicit vendor + version

**Decision:** ⬜ Keep current naming (vendor-neutral) OR ✅ Rename for clarity?

---

## Crosswalk CSV Column Updates

**Current:** Columns are correct (no vendor-specific naming)

**Metadata to add (optional):**
- Add `source_vendor` and `target_vendor` columns for future multi-vendor corpus
- Current files would populate both as "Ascensus"

**Decision:** Defer until multi-vendor test data acquired

---

## Testing/Validation Impact

**Red Team Sprint:** No changes needed
- Sample selection algorithm is vendor-agnostic
- Validation methodology applies to both intra-vendor and cross-vendor

**Accuracy claims:** No changes needed
- 19% match rate makes sense for BPD edition comparison
- Confidence scoring calibration is vendor-agnostic

---

## Documentation Hierarchy (Update Order)

1. **README.md** - Correct project description FIRST (most visible)
2. **CLAUDE.md** - Update AI assistant context (most referenced)
3. **test_data/README.md** - Create definitive test corpus documentation
4. **Requirements** - Distinguish capability from current validation
5. **Design docs** - Update examples and use cases
6. **Supporting docs** - Archive or annotate historical materials

---

## Success Criteria

✅ No documentation claims POC tested cross-vendor scenario
✅ Clear distinction between "system capability" and "current test data"
✅ Real-world cross-vendor examples preserved (labeled as such)
✅ Future cross-vendor testing plans acknowledged
✅ Test data corpus clearly documented (vendor, version, document type)

---

*Plan created: 2025-10-20*
*Estimated effort: 2-3 hours for comprehensive update*
*Priority: High (affects user-facing claims and technical accuracy)*
