# Phase 2: Value Substitution Implementation Plan

**Status:** Ready to Begin
**Prerequisites:** ✅ Phase 1 Complete, ✅ Phase 1.5 Complete
**Duration Estimate:** 4-6 days
**Goal:** Automate substitution of AA election VALUES into BPD template provisions

---

## Overview

Phase 2 takes the **template-level Plan Provisions** from Phase 1 and adds **value substitution** capability. When filled AA forms are available, we'll automatically substitute the selected values into BPD template text to create **complete, value-resolved provisions**.

**Input:**
- BPD Provision (template with "as elected in AA" references)
- AA Election (with SELECTED values from filled form)

**Output:**
- Complete Provision (BPD text with values substituted)
- Full provenance (BPD sections + AA fields + merge rule applied)

---

## What Phase 1 + 1.5 Gave Us

### Phase 1 Deliverables
✅ Plan Provision data model (BPD + linked AA elections)
✅ Linking algorithm (keyword-based, 100% success on test cases)
✅ Template-level structure (reusable for values)

### Phase 1.5 Validation
✅ Quantitative proof: +6.2% embedding improvement
✅ Larger gains (+11%) for election-dependent provisions
✅ Two-phase crosswalk architecture validated

### What's Missing for Production
❌ **Value substitution** - Can't merge without filled AA forms
❌ **Merge rule automation** - Currently manual/conceptual only
❌ **Provenance tracking** - Need to log which rules applied to which provisions
❌ **Failure handling** - What happens when anchor is ambiguous or election missing?

---

## Phase 2 Goals

### Primary Goal
**Implement automated value substitution for the 3 most common merge patterns**

### Success Criteria (from ADR-001)
- ✅ **Auto-merge coverage:** ≥80% of high-impact provisions successfully merged
- ✅ **Merge speed:** Median <50ms per provision
- ✅ **Provenance completeness:** 100% of merged provisions track BPD sections + AA fields + merge rule ID
- ✅ **Failure transparency:** All "needs review" cases include specific reasons

### Out of Scope (Phase 2)
- ❌ Complex multi-provision dependencies
- ❌ Regulatory compliance validation
- ❌ Amendment detection
- ❌ All 10 merge patterns (only top 3)

---

## The 3 Merge Patterns (Priority Order)

### Pattern-01: Direct Substitution (Highest Priority)
**Use case:** Age, service, compensation amounts, dates

**Example:**
```
BPD: "Employee eligible upon attainment of age [___] and completion of [___] of Service"
AA:  age = 21, service = "1 Year"
→ "Employee eligible upon attainment of age 21 and completion of 1 Year of Service"
```

**Complexity:** Low
**Coverage:** ~30-40% of election-dependent provisions
**Implementation:**
- Regex pattern matching for placeholders (`[___]`, `[insert]`, `_____`)
- Direct field value substitution
- Normalize units (e.g., "1 Year" vs "12 months")

---

### Pattern-02: Checkbox Enumeration (High Priority)
**Use case:** Vesting schedules, entry date frequencies, plan type elections

**Example:**
```
BPD: "Vesting schedule:
      (a) 3-year cliff
      (b) 6-year graded: 0%/20%/40%/60%/80%/100%
      (c) Immediate 100%
      as elected in AA"

AA:  option_selected = "b"

→ "Vesting schedule: 6-year graded with the following percentages:
   Years 1-2: 0%
   Years 3: 20%
   Years 4: 40%
   Years 5: 60%
   Years 6: 80%
   Years 7+: 100%"
```

**Complexity:** Medium
**Coverage:** ~20-30% of election-dependent provisions
**Implementation:**
- Detect enumerated options (a/b/c/d, 1/2/3/4, checkboxes)
- Extract selected option from AA
- Drop unselected options
- Expand selected option text (extract embedded details like percentages)

---

### Pattern-03: Numeric Parameter Injection (Medium Priority)
**Use case:** Match formulas, contribution percentages, dollar limits

**Example:**
```
BPD: "Employer matching contribution equals [___]% of the first [___]% of Compensation deferred"
AA:  match_percentage = 100, compensation_limit = 3
→ "Employer matching contribution equals 100% of the first 3% of Compensation deferred"
```

**Complexity:** Low-Medium
**Coverage:** ~10-20% of election-dependent provisions
**Implementation:**
- Identify numeric placeholders
- Inject values from AA
- Standardize format (e.g., "3%" not "three percent" or "0.03")
- Validate ranges (e.g., percentages 0-100, ages 18-21)

---

## Implementation Roadmap

### Week 1: Pattern-01 (Direct Substitution)

**Day 1-2: Detection & Extraction**
```python
# Pseudo-code
def detect_placeholders(bpd_text):
    """Find all placeholders in BPD text."""
    patterns = [
        r'\[___+\]',           # [___]
        r'\[insert\]',         # [insert]
        r'_____+',             # _____
        r'<fill in>',          # <fill in>
    ]
    return find_all_matches(bpd_text, patterns)

def extract_expected_type(context):
    """Infer what type of value expected from surrounding text."""
    # "age [___]" → numeric, range 18-21
    # "completion of [___] of Service" → duration ("1 Year", "6 months")
    # "effective [___]" → date
    pass
```

**Day 3-4: Value Matching & Substitution**
```python
def find_matching_aa_field(bpd_provision, placeholder, aa_elections):
    """Find AA field that corresponds to this placeholder."""
    # Use existing linkage from Phase 1 (BPD → AA elections)
    # Within linked AA elections, find field matching expected type
    # Match by:
    #   1. Explicit reference (best)
    #   2. Keyword proximity (good)
    #   3. Type inference (fallback)
    pass

def substitute_value(bpd_text, placeholder, aa_value):
    """Replace placeholder with actual value."""
    # Normalize value format
    # Replace in text
    # Preserve grammatical context ("a" vs "an", singular vs plural)
    return merged_text
```

**Day 5: Testing & Validation**
- Test on eligibility provisions (age + service)
- Test on compensation provisions (dollar limits)
- Validate provenance tracking
- Error handling for missing values

**Deliverable:** Pattern-01 working for 5 test provisions

---

### Week 2: Pattern-02 (Checkbox Enumeration)

**Day 6-7: Option Detection**
```python
def detect_enumerated_options(bpd_text):
    """Find enumerated option structures."""
    # Look for:
    #   (a) ... (b) ... (c) ...
    #   □ option 1  □ option 2  □ option 3
    #   1. ... 2. ... 3. ...
    # Extract option labels and associated text
    pass

def parse_option_structure(options):
    """Parse nested options and sub-options."""
    # Handle:
    #   Option d with sub-options d.1, d.2, d.3
    #   Conditional text ("if this option, then...")
    # Build option tree
    pass
```

**Day 8-9: Option Selection & Expansion**
```python
def select_option(options, aa_selection):
    """Identify which option was selected in AA."""
    # Match AA checkbox/radio button to BPD option
    # Handle multiple selections (if allowed)
    # Extract selected option's full text
    pass

def expand_selected_option(option):
    """Expand selected option with embedded details."""
    # Example: "6-year graded: 0%/20%/40%/60%/80%/100%"
    # → Full vesting schedule table
    # Extract percentages, years, format as table
    pass

def remove_unselected_options(bpd_text, selected_option, all_options):
    """Drop unselected options from BPD text."""
    # Remove option labels (a), (b), (c)
    # Remove conditional phrases ("if elected under option a")
    # Clean up formatting (extra line breaks, "or"/"and" connectors)
    return clean_text
```

**Day 10: Testing & Validation**
- Test on vesting schedule provisions
- Test on entry date frequency provisions
- Test on plan type conditionals ("in the case of a 401(k) Plan")
- Validate option nesting (d.1, d.2, d.3)

**Deliverable:** Pattern-02 working for 3 test provisions (vesting, entry dates, plan type)

---

### Week 3: Pattern-03 & Integration

**Day 11: Numeric Parameter Injection**
```python
def detect_numeric_placeholders(bpd_text):
    """Find numeric placeholders."""
    # [___]% → percentage
    # $[___] → dollar amount
    # [___] years → duration
    pass

def inject_numeric_value(bpd_text, placeholder, aa_numeric_value):
    """Inject numeric value with proper formatting."""
    # Format percentage: 3% (not 0.03 or "three percent")
    # Format currency: $1,000 (not 1000.00)
    # Validate ranges (age 18-21, percentage 0-100)
    return formatted_text
```

**Day 12-13: Integration & End-to-End Pipeline**
```python
def merge_provision(bpd_provision, aa_elections):
    """Main merge function - applies all patterns."""

    # Step 1: Apply Pattern-01 (direct substitution)
    merged_text, pattern_01_applied = apply_pattern_01(bpd_provision, aa_elections)

    # Step 2: Apply Pattern-02 (checkbox enumeration)
    merged_text, pattern_02_applied = apply_pattern_02(merged_text, aa_elections)

    # Step 3: Apply Pattern-03 (numeric injection)
    merged_text, pattern_03_applied = apply_pattern_03(merged_text, aa_elections)

    # Step 4: Validate result
    merge_status = validate_merge(merged_text, bpd_provision)

    # Step 5: Build provenance
    provenance = {
        'bpd_sections': [bpd_provision.section_number],
        'aa_fields': extract_aa_field_ids(aa_elections),
        'merge_rules': [pattern_01_applied, pattern_02_applied, pattern_03_applied],
        'timestamp': now(),
        'confidence': calculate_confidence(merge_status)
    }

    return MergedProvision(
        merged_text=merged_text,
        provenance=provenance,
        merge_status=merge_status  # 'ok' | 'needs_review' | 'failed'
    )
```

**Day 14: Testing & Coverage Analysis**
- Run on 20-provision golden set (5 types × 2 vendors × 2 provisions)
- Measure auto-merge coverage (target: ≥80%)
- Identify failure patterns
- Document "needs review" cases

**Deliverable:** End-to-end merger working on golden set

---

## Data Structures

### MergedProvision (with Values)

```json
{
  "merged_provision_id": "prov_relius_eligibility_001_merged",
  "canonical_key": "eligibility.conditions",
  "provision_category": "eligibility",
  "source_vendor": "Relius",
  "completeness": "filled",

  "bpd_component": {
    "section_number": "3.1",
    "section_title": "CONDITIONS OF ELIGIBILITY",
    "provision_text_template": "Employee eligible upon attainment of age [___] and [___] of Service",
    "pdf_page": 15
  },

  "aa_components": [
    {
      "question_id": "AA.Q1.04",
      "field_label": "age_requirement",
      "selected_value": "21",
      "confidence": 0.95
    },
    {
      "question_id": "AA.Q1.04",
      "field_label": "service_requirement",
      "selected_value": "1 Year",
      "confidence": 0.95
    }
  ],

  "merged_text": "Employee eligible upon attainment of age 21 and 1 Year of Service",

  "merge_operations": [
    {
      "rule_id": "pattern_01_direct_substitution",
      "placeholder": "[___]",
      "substituted_value": "21",
      "aa_field": "AA.Q1.04.age_requirement"
    },
    {
      "rule_id": "pattern_01_direct_substitution",
      "placeholder": "[___]",
      "substituted_value": "1 Year",
      "aa_field": "AA.Q1.04.service_requirement"
    }
  ],

  "merge_status": "ok",
  "confidence": 0.95,
  "merge_timestamp": "2025-10-30T16:00:00Z",
  "hash": "sha256:def456..."
}
```

---

## Testing Strategy

### Unit Tests (Per Pattern)
- Pattern-01: 10 test cases (age, service, dates, amounts)
- Pattern-02: 8 test cases (2-4 options, nested options, plan type conditionals)
- Pattern-03: 6 test cases (percentages, dollar amounts, counts)

### Integration Tests
- End-to-end merge on 20-provision golden set
- Measure coverage (% successfully merged)
- Measure speed (<50ms median)
- Validate provenance completeness

### Failure Mode Tests
- Missing AA value → "needs_review" with reason
- Ambiguous anchor → "needs_review" with reason
- Multiple possible values → "needs_review" with reason
- Type mismatch → "needs_review" with reason

---

## Success Metrics

### Coverage (Target: ≥80%)
```
Auto-merged provisions / Total election-dependent provisions ≥ 0.80
```

**Measured on:**
- Eligibility provisions
- Compensation provisions
- Contribution provisions (match, profit sharing)
- Vesting provisions
- Distribution provisions

### Speed (Target: <50ms median)
```
Median merge time across all provisions < 50ms
```

**Includes:**
- Placeholder detection
- AA field matching
- Value substitution
- Provenance construction

### Provenance (Target: 100%)
```
All merged provisions have:
- bpd_sections[]
- aa_fields[]
- merge_rules[]
- timestamp
```

### Transparency (Target: 100%)
```
All "needs_review" cases include:
- merge_status reason
- which step failed
- what information is missing
```

---

## Failure Handling Strategy

### Graceful Degradation

**Level 1: Full Success**
- All placeholders resolved
- All AA values found
- High confidence (≥90%)
- Status: `ok`

**Level 2: Partial Success**
- Some placeholders resolved
- Some AA values missing
- Medium confidence (70-89%)
- Status: `needs_review`
- Reason: "Unable to resolve placeholders: [___] (no matching AA field found)"

**Level 3: Failure**
- No placeholders resolved OR
- Critical AA value missing OR
- Type mismatch detected
- Low confidence (<70%)
- Status: `failed`
- Reason: Specific error message

### "Needs Review" Examples

```json
{
  "merge_status": "needs_review",
  "merge_issues": [
    {
      "issue_type": "missing_aa_value",
      "placeholder": "[___]",
      "expected_field": "AA.Q1.04.age_requirement",
      "reason": "AA field found but no value selected"
    },
    {
      "issue_type": "ambiguous_anchor",
      "bpd_text": "as elected in the Adoption Agreement",
      "candidate_aa_fields": ["AA.Q1.04", "AA.Q1.05"],
      "reason": "Multiple AA fields match, cannot determine which is correct"
    }
  ]
}
```

---

## Phase 2 Exit Criteria

### Must Have (Blocking)
- ✅ Pattern-01 implemented and tested (direct substitution)
- ✅ Pattern-02 implemented and tested (checkbox enumeration)
- ✅ Pattern-03 implemented and tested (numeric injection)
- ✅ Coverage ≥80% on golden set
- ✅ Median merge speed <50ms
- ✅ Provenance tracking 100% complete
- ✅ Failure modes documented with reasons

### Should Have (Non-Blocking)
- ⚠️ Edge case handling (nested options, conditionals)
- ⚠️ Vendor-specific lexicon (normalize "Nonelective" vs "Employer Contribution")
- ⚠️ Grammatical cleanup ("a" vs "an", plural agreements)

### Nice to Have (Future)
- ❌ Patterns 04-10 (deferred to Phase 3)
- ❌ Multi-provision dependencies
- ❌ Regulatory validation
- ❌ Amendment detection

---

## Deliverables

### Code
- `src/merging/pattern_01_direct_substitution.py`
- `src/merging/pattern_02_checkbox_enumeration.py`
- `src/merging/pattern_03_numeric_injection.py`
- `src/merging/merger.py` (main orchestrator)
- `tests/test_pattern_01.py`
- `tests/test_pattern_02.py`
- `tests/test_pattern_03.py`
- `tests/test_merger_integration.py`

### Data
- `test_data/golden_set/phase2_merger/` (20 test provisions with filled AA values)
- `test_data/golden_set/phase2_merger/merged_results.json` (output)

### Documentation
- `design/data_models/merged_provision_v2.md` (updated with values)
- `design/architecture/merge_rules_catalogue.md` (detailed rule specs)
- `test_results/phase2_merger_validation.md` (coverage, speed, accuracy results)

---

## Risk Mitigation

### Risk: Filled AA Forms Not Available
**Mitigation:** Simulate filled forms for golden set
- Use realistic values (age 21, 1 year service, 6-year graded vesting)
- Create both Relius and Ascensus filled examples
- Document which values are synthetic vs real

### Risk: 80% Coverage Target Too Aggressive
**Mitigation:** Prioritize provision types
- Focus on high-impact types (eligibility, vesting, match, contributions)
- Defer low-frequency types (loans, hardships, QDROs)
- Measure coverage per type, not overall

### Risk: Vendor Idiosyncrasies Break Patterns
**Mitigation:** Vendor-specific rule sets
- Start with Relius + Ascensus (known vendors)
- Document vendor-specific patterns
- Build extensible rule system (add vendor adaptors later)

### Risk: Performance Bottleneck
**Mitigation:** Profile and optimize
- Cache compiled regex patterns
- Parallelize merge operations
- Benchmark on large provision sets (100+)

---

## Dependencies

### Data Prerequisites
- ✅ BPD extractions (Relius, Ascensus) - **Have from Phase 1**
- ✅ AA extractions (Relius, Ascensus) - **Have from Phase 1**
- ❌ Filled AA forms - **Need to simulate or obtain**

### Code Prerequisites
- ✅ Plan Provision data model - **Have from Phase 1**
- ✅ BPD→AA linking algorithm - **Have from Phase 1**
- ✅ Provenance schema - **Have from ADR-001**

### Infrastructure Prerequisites
- ✅ OpenAI API access - **Have**
- ✅ Python environment - **Have**
- ✅ Test framework - **Have**

---

## Next Actions (When Ready to Start Phase 2)

1. **Create golden set with filled AA values** (1 day)
   - Select 20 provisions (5 types × 2 vendors × 2 provisions)
   - Simulate realistic AA elections for each
   - Document which values are synthetic vs real

2. **Implement Pattern-01** (2-3 days)
   - Placeholder detection
   - AA field matching
   - Value substitution
   - Unit tests

3. **Implement Pattern-02** (2-3 days)
   - Option enumeration detection
   - Option selection
   - Unselected option removal
   - Unit tests

4. **Implement Pattern-03** (1-2 days)
   - Numeric placeholder detection
   - Value injection
   - Format validation
   - Unit tests

5. **Integration & validation** (1-2 days)
   - End-to-end pipeline
   - Coverage measurement
   - Speed benchmarking
   - Failure mode testing

---

## Questions to Resolve Before Starting

### 1. Filled AA Forms
**Question:** Do we have ANY real filled AA forms, or all synthetic?
**Impact:** Determines realism of Phase 2 testing
**Options:**
- A) Use fully synthetic values (age 21, 1 yr service, etc.)
- B) Obtain 1-2 real filled forms from TPA contacts
- C) Hybrid (real for 1-2 plans, synthetic for rest)

### 2. Coverage Target
**Question:** Is 80% realistic, or should we target 60-70% for Phase 2?
**Impact:** Scope and timeline
**Options:**
- A) Keep 80%, focus on top provision types only
- B) Reduce to 60%, broader provision type coverage
- C) Measure per-type, no overall target

### 3. Vendor Scope
**Question:** Relius + Ascensus only, or add ftwilliam/DATAIR?
**Impact:** Complexity and timeline
**Options:**
- A) Relius + Ascensus only (proven test data)
- B) Add ftwilliam (requires new extractions)
- C) Add DATAIR (requires new extractions)

---

**Status:** ✅ Phase 2 Plan Complete - Ready to Execute When You Are

**Author:** Sergio DuBois (with AI assistance from Claude)
**Date:** 2025-10-30
**Related:**
- [ADR-001: Merge Strategy](adr_001_merge_strategy.md)
- [Phase 1 POC Report](../../test_results/phase1_plan_provisions_poc_2025-10-30.md)
- [Phase 1.5 Quantitative Validation](../../test_results/phase1.5_embedding_quality_2025-10-30.md)
- [Plan Provision Data Model](../data_models/plan_provision_model.md)
