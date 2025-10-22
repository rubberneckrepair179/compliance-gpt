# AA Crosswalk Validation Test Set

**Created:** 2025-10-21T20:19:47.717659
**Source:** Relius Cycle 3 Adoption Agreement (182 elections)
**Target:** Ascensus 401(k) Profit Sharing Plan Adoption Agreement (550 elections)

## Sample Composition

- **Matches:** 22 examples
- **Non-matches (high conf ≥90%):** 5 examples
- **Non-matches (medium conf 70-89%):** 5 examples
- **Non-matches (low conf <70%):** 5 examples

## Validation Instructions

For each example in `validation_test_set.csv`, please fill in:

1. **Human Says Match?** - Your expert judgment: YES/NO/PARTIAL
2. **Correct Tier** - What tier would you assign?
   - EXACT: Same election, minor wording only
   - PARTIAL: Same election, options changed (actionable deltas)
   - POSSIBLE: Related but uncertain
   - NONE: Different elections entirely

3. **Deltas** (for PARTIAL matches):
   - Options Added: List new options in target
   - Options Removed: List removed options from source
   - Options Reworded: Note wording changes
   - Logic Changed: Note default changes, dependencies, etc.

4. **Recommended Action** - What should compliance officer do?
5. **Notes** - Any other observations

## Goals

- Validate AI match quality (do our 22 matches agree with your judgment?)
- Calibrate confidence thresholds (are 90%+ scores actually reliable?)
- Identify useful 'near misses' (non-matches with actionable deltas)
- Define what deltas matter in practice
- Design better output format for compliance workflow
