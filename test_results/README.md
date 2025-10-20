# Red Team Sprint Test Results

This directory contains Red Team Sprint findings and quality validation reports.

## What are Red Team Sprints?

Red Team Sprints are adversarial testing sessions conducted after major milestones to validate claims about accuracy, performance, and quality before proceeding to the next phase.

**Purpose:**
- Validate LLM output quality claims (e.g., "94% high confidence," "19% match rate")
- Identify false positives (incorrect matches) and false negatives (missed matches)
- Test edge cases and unusual document structures
- Calibrate confidence scoring thresholds
- Prevent costly errors in high-stakes compliance domain

**Cadence:** After each major milestone (e.g., "BPD crosswalk complete," "AA extraction complete")

## Reports in This Directory

### 2025-10-20: BPD Crosswalk Validation
- **Report:** [red_team_2025-10-20.md](red_team_2025-10-20.md)
- **Sample IDs:** [red_team_sample_ids_2025-10-20.json](red_team_sample_ids_2025-10-20.json)
- **Status:** Ready for manual review
- **Component Tested:** BPD semantic mapping (source_bpd_01 → target_bpd_05)

**Test Categories:**
1. High-confidence matches (10 samples) - Validate equivalence
2. No matches (10 samples) - Check for false negatives
3. High-impact variances (10 samples) - Validate impact classification
4. Low embedding + high LLM similarity (5 samples) - Verify semantic understanding
5. High embedding + no match (5 samples) - Verify rejection reasoning

**Claims Under Test:**
- 82 semantic matches (19.3%)
- 94% high confidence (≥90%)
- 186 high-impact variances
- 136 medium-impact variances

## How to Conduct a Red Team Sprint

### 1. Define Test Scope (15 min)
- Identify specific claims to validate
- Select representative sample size (typically 10-20 items per category)
- Define pass/fail criteria

### 2. Execute Adversarial Testing (2-4 hours)
- Manual verification of random samples
- Targeted testing of edge cases
- Cross-reference with domain expertise
- Document all failures with evidence

### 3. Document Findings (30 min)
- Record validated claims vs. discrepancies
- Classify failures by severity (Critical/High/Medium/Low)
- Propose corrective actions

### 4. Update Project Artifacts (30 min)
- Adjust accuracy claims in CLAUDE.md if needed
- Update requirements if targets unrealistic
- Iterate on prompts based on failures
- Add defensive measures to architecture

## Exit Criteria

- Either: Claims validated with documented evidence
- Or: Specific issues documented with corrective action plan
- Never: Proceed with unvalidated claims

## Integration with Development

- Red Team findings may require prompt iteration
- Failed tests block progression to next milestone
- All findings tracked in version control
- Lessons learned inform future prompt engineering

---

*Last Updated: 2025-10-20*
*Next Red Team Sprint: After AA Crosswalk completion*
