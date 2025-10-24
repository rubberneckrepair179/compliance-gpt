# Variance Classification Model

## Overview

A **variance** is a detected difference between source and target provisions during semantic reconciliation. Variances must be classified by:
1. **Type**: Administrative / Design / Regulatory
2. **Impact Level**: High / Medium / Low / None

This model defines the classification system, decision criteria, and examples that guide both LLM prompts and human review.

---

## Requirements Addressed

- **REQ-022**: Variance detection and classification
- **Market Research Finding**: Real-world example of missed variance (Relius→ASC HCE safe harbor contribution)
- **Control 002**: Document Reconciliation - variance tracking to closure

---

## Variance Types

### Administrative Variance

**Definition**: Differences in wording, formatting, or document structure that do NOT change the substantive operation of the plan.

**Characteristics**:
- Same legal effect, different phrasing
- Terminology updates (e.g., "Plan Administrator" → "Employer")
- Section reorganization or renumbering
- Clarifying language that doesn't change meaning
- Formatting changes (bullet points → numbered list)

**Examples**:

| Source Provision | Target Provision | Reasoning |
|------------------|------------------|-----------|
| "The Plan Administrator shall..." | "The Employer shall..." | Same legal entity referenced, different term used |
| "Participants may elect deferrals from 1% to 100% of compensation" | "Elective deferrals may be made in whole percentages from 1% through 100% of pay" | Same deferral range, slightly different wording |
| "Top-Heavy Plan" (defined in Section 9.2) | "Top-Heavy Plan" (defined in Section 7.19) | Same definition, different section number |
| "Matching contribution: 50% of first 6% of deferrals" (paragraph format) | "Matching contribution:\n• 50% of deferrals\n• up to 6% of compensation" (bulleted format) | Same formula, reformatted for readability |

**Action Required**: Informational only, typically bulk-approved.

---

### Design Variance

**Definition**: Differences that reflect employer **choices** about how the plan operates. These are discretionary elections that affect plan participants but are within IRS/DOL rules.

**Characteristics**:
- Employer election changed (different option selected in AA)
- Eligibility, vesting, or contribution formulas differ
- Benefit calculation methods changed
- Investment options or loan provisions modified
- Changes to in-service distributions or hardship rules

**Examples**:

| Source Provision | Target Provision | Reasoning |
|------------------|------------------|-----------|
| "Eligibility: Age 21 and 1 year of service" | "Eligibility: Age 18 and 6 months of service" | Employer changed eligibility requirements (more liberal in target) |
| "Vesting: 3-year cliff" | "Vesting: 6-year graded" | Employer changed vesting schedule |
| "Match: 100% of first 3% of deferrals" | "Match: 50% of first 6% of deferrals" | Employer changed match formula (economically equivalent but different structure) |
| "Safe harbor contributions include HCEs" (default in Relius) | "Safe harbor contributions EXCLUDE HCEs unless elected in AA Section X" (requires explicit election in Ascensus) | **CRITICAL**: This is the real-world example from market research where variance was missed, causing year-end correction |
| "In-service distributions: Age 59½" | "In-service distributions: Not permitted" | Employer removed in-service distribution feature |

**Action Required**: Requires plan sponsor approval. Must document in exception log and track to closure.

---

### Regulatory Variance

**Definition**: Differences resulting from changes in **IRS/DOL law or regulations** that require plan updates regardless of sponsor preference.

**Characteristics**:
- Required by Cycle restatement (e.g., Cycle 2 → Cycle 3)
- Statutory limit changes (e.g., $19,500 → $22,500 deferral limit)
- New IRS guidance implemented (e.g., SECURE Act provisions)
- Compliance rule updates (e.g., RMD age 70½ → 72 → 73)
- Opinion Letter requirements (pre-approved plan language changes)

**Examples**:

| Source Provision | Target Provision | Reasoning |
|------------------|------------------|-----------|
| "Elective deferral limit: $19,500 (2021)" | "Elective deferral limit: $22,500 (2023)" | IRS increased limit per IRC §402(g) |
| "Catch-up contributions: $6,500" | "Catch-up contributions: $7,500" | IRS increased limit for 2024 |
| "Required Minimum Distributions begin at age 70½" | "Required Minimum Distributions begin at age 73" | SECURE 2.0 Act changed RMD age |
| "QACA auto-enrollment: 3% initial default" | "QACA auto-enrollment: 3-10% escalation to 10% (SECURE 2.0)" | New regulatory requirement for QACAs |
| "Hardship distributions: Financial need determination required" | "Hardship distributions: Safe harbor deemed distributions permitted per IRS Notice 2020-68" | New IRS guidance simplified hardship rules |

**Action Required**: Informational, document rationale (cite IRS guidance). No plan sponsor decision required.

---

## Impact Levels

### High Impact

**Definition**: Variance affects **participant rights**, **contribution calculations**, **qualification status**, or **fiduciary liability**.

**Consequences if Missed**:
- Plan could lose qualified status
- Participants affected incorrectly (contributions, distributions, vesting)
- Employer faces potential IRS/DOL penalties
- Requires EPCRS correction if error not caught

**Examples**:
- Eligibility changes (who can participate)
- Vesting schedule changes (when participants own contributions)
- Contribution formula changes (how much employer puts in)
- HCE inclusion/exclusion in safe harbor (the market research example)
- Distribution restrictions changed
- Top-heavy minimum contribution requirements

**User Action**: Flag for immediate review, escalate to plan sponsor and legal counsel.

---

### Medium Impact

**Definition**: Variance has **operational impact** but is correctable through plan amendment or procedural adjustment without disqualification risk.

**Consequences if Missed**:
- Plan operates under old rules temporarily (correctable)
- Administrative burden to fix (amendment, participant communication)
- May require makeup contributions or retroactive corrections
- Could cause participant confusion but no loss of qualified status

**Examples**:
- Loan provisions changed (affects participants who want loans)
- Investment menu changes (affects participant investment choices)
- Hardship distribution rules modified (affects access to funds)
- Beneficiary designation rules updated (affects estate planning)
- Rollover eligibility changed (affects portability)

**User Action**: Document in exception log, schedule plan amendment, communicate to participants if needed.

---

### Low Impact

**Definition**: Variance has **minimal operational effect** or is purely administrative in nature.

**Consequences if Missed**:
- No participant impact
- No compliance risk
- May cause minor recordkeeping confusion but easily addressed

**Examples**:
- Terminology changes ("Plan Administrator" → "Employer")
- Section renumbering (references updated)
- Formatting changes (bullets vs. paragraphs)
- Cross-reference updates (Section X → Section Y)
- Definition clarifications that don't change meaning

**User Action**: Informational, bulk-approve during review.

---

### None (Identical)

**Definition**: Provisions match semantically. No variance detected.

**Output**: Not included in variance report (only matched provisions in crosswalk).

---

## Classification Decision Tree

```
┌─ START: Variance Detected ─┐
│                             │
│ Are provisions IDENTICAL    │
│ in legal effect?            │
├─ YES ───────────────────────┤
│   └─ Administrative         │
│       └─ Impact: LOW        │
│                             │
├─ NO ────────────────────────┤
│                             │
│ Is difference due to        │
│ IRS/DOL law change or       │
│ Cycle restatement req?      │
├─ YES ───────────────────────┤
│   └─ Regulatory             │
│       ├─ Affects participant│
│       │   rights/calc?      │
│       │   ├─ YES: HIGH      │
│       │   └─ NO: MEDIUM     │
│                             │
├─ NO ────────────────────────┤
│                             │
│ Is difference due to        │
│ employer election change?   │
├─ YES ───────────────────────┤
│   └─ Design                 │
│       ├─ Affects participant│
│       │   rights/eligibility│
│       │   vesting/contrib?  │
│       │   ├─ YES: HIGH      │
│       │   ├─ Operational    │
│       │   │   change? MED   │
│       │   └─ Minor? LOW     │
│                             │
├─ UNCERTAIN ─────────────────┤
│   └─ Flag for manual review│
│       Mark confidence <70%  │
│                             │
└─────────────────────────────┘
```

---

## Classification Examples (Comprehensive)

### Example 1: Terminology Change (Administrative, Low)

**Source**: "The Plan Administrator shall provide annual notices to participants per ERISA §101."
**Target**: "The Employer shall provide annual notices to participants per ERISA §101."

**Analysis**:
- **Same legal obligation**: ERISA notice requirement unchanged
- **Same actor**: "Plan Administrator" = "Employer" in this plan (confirmed in adoption agreement)
- **No participant impact**: Notices still required annually

**Classification**: Administrative
**Impact**: Low
**Reasoning**: Terminology modernization, no substantive change
**Action**: Bulk-approve

---

### Example 2: Eligibility Liberalization (Design, High)

**Source**: "Employees are eligible after age 21 and 1 year of service (1,000 hours)."
**Target**: "Employees are eligible immediately upon hire."

**Analysis**:
- **Employer election changed**: More permissive eligibility in target
- **Participant rights expanded**: More employees eligible sooner
- **Coverage testing impact**: May affect ADP/ACP test demographics
- **Recordkeeper impact**: Must enroll employees earlier

**Classification**: Design
**Impact**: High
**Reasoning**: Expanded participant rights, affects who can participate and when
**Action**: Requires sponsor approval, document in exception log, communicate to affected employees, update admin procedures

---

### Example 3: IRC Limit Update (Regulatory, Medium)

**Source**: "Elective deferral limit: $19,500 (2021) per IRC §402(g)."
**Target**: "Elective deferral limit: $22,500 (2023) per IRC §402(g)."

**Analysis**:
- **IRS law change**: Statutory limit increased for 2023
- **Automatic application**: Participants can defer more regardless of plan amendment
- **No employer discretion**: IRC §402(g) applies automatically
- **Participant benefit**: Higher deferral capacity

**Classification**: Regulatory
**Impact**: Medium (informational, automatic application)
**Reasoning**: IRS statutory limit change, cite IRC §402(g) cost-of-living adjustment
**Action**: Document, communicate new limits to participants, update payroll system

---

### Example 4: Safe Harbor HCE Inclusion (Design, High) ⭐ MARKET RESEARCH EXAMPLE

**Source** (Relius - implicit default):
"Safe harbor contributions are made to all eligible participants, including Highly Compensated Employees."

**Target** (Ascensus - explicit election required):
"Safe harbor contributions are made to Non-Highly Compensated Employees. To include Highly Compensated Employees, check box in Adoption Agreement Section 5.03(b)."

**Analysis**:
- **Vendor default difference**: Relius includes HCEs by default, Ascensus requires explicit election
- **If box not checked in target AA**: HCEs excluded from safe harbor (PLAN DESIGN CHANGE)
- **Participant rights affected**: HCEs lose safe harbor contribution if not elected
- **Financial impact**: Employer may save money (fewer HCEs covered) but HCEs harmed
- **Compliance risk**: If unintended, could cause HCE dissatisfaction or discrimination claim

**Classification**: Design
**Impact**: High
**Reasoning**: Affects participant eligibility for contributions, potential unintended consequence of cross-vendor conversion
**Action**: **CRITICAL** - Flag for immediate sponsor review, verify intent, check target AA election status, amend if needed

**This is the exact scenario from market research (page 3) where TPA missed the difference during Relius→ASC conversion.**

---

### Example 5: RMD Age Change (Regulatory, High)

**Source**: "Required Minimum Distributions begin at age 70½ per IRC §401(a)(9)."
**Target**: "Required Minimum Distributions begin at age 73 per IRC §401(a)(9) as amended by SECURE 2.0 Act."

**Analysis**:
- **Law change**: SECURE 2.0 Act increased RMD age
- **Participant benefit**: Allows tax deferral 2.5 years longer
- **No employer discretion**: IRC §401(a)(9) mandatory
- **Effective date**: January 1, 2023 for most participants

**Classification**: Regulatory
**Impact**: High (affects distribution timing, but required by law)
**Reasoning**: SECURE 2.0 Act §107 amended IRC §401(a)(9), mandatory compliance
**Action**: Document, communicate to participants nearing RMD age, update distribution procedures

---

### Example 6: Section Renumbering (Administrative, Low)

**Source**: "Definition of 'Compensation' per Section 2.05"
**Target**: "Definition of 'Compensation' per Section 1.12"

**Analysis**:
- **Same definition**: Text identical, just moved
- **Cross-references updated**: Other sections point to new location
- **No substantive change**: Legal meaning unchanged

**Classification**: Administrative
**Impact**: Low
**Reasoning**: Document reorganization, section references updated
**Action**: Bulk-approve, note in comparison workbook for audit trail

---

### Example 7: Vesting Schedule Change (Design, High)

**Source**: "Employer contributions vest: 3-year cliff (0% before 3 years, 100% at 3 years)."
**Target**: "Employer contributions vest: 6-year graded (20% per year after year 2)."

**Analysis**:
- **Employer election changed**: Different vesting schedule
- **Participant rights affected**: Employees who terminate before 3 years get nothing in source, but 40-60% vested in target if they have 4-5 years of service
- **IRC §411 compliance**: Both schedules legal, but different
- **Recordkeeper impact**: Must track vesting differently

**Classification**: Design
**Impact**: High
**Reasoning**: Affects participant ownership of employer contributions, significant financial impact for terminating employees
**Action**: Requires sponsor approval, may need transition rules for existing participants, document in exception log

---

### Example 8: Hardship Distribution Rules (Regulatory, Medium)

**Source**: "Hardship distributions require demonstration of immediate and heavy financial need per Treas. Reg. §1.401(k)-1(d)(3)."
**Target**: "Hardship distributions deemed to satisfy financial need requirement if for one of the six safe harbor reasons per IRS Notice 2020-68."

**Analysis**:
- **IRS guidance change**: Notice 2020-68 simplified hardship procedures
- **Administrative relief**: Plan can rely on safe harbor instead of individual determinations
- **Participant impact**: Easier to qualify for hardship distributions
- **No employer discretion**: Regulatory change, optional to adopt but common practice

**Classification**: Regulatory
**Impact**: Medium (operational improvement, but no negative participant impact)
**Reasoning**: IRS Notice 2020-68 safe harbor election, cite notice
**Action**: Document, communicate to participants, update hardship request forms

---

## LLM Prompt Guidance

### Prompt Template for Variance Classification

```
You are classifying a detected variance between source and target plan provisions.

VARIANCE TYPES:
1. ADMINISTRATIVE - Wording/formatting changes, no substantive impact
2. DESIGN - Employer election changes (discretionary plan features)
3. REGULATORY - Required by IRS/DOL law changes or Cycle restatements

IMPACT LEVELS:
1. HIGH - Affects participant rights, contribution calculations, or qualification
2. MEDIUM - Operational impact, correctable through amendment
3. LOW - Minimal or no operational effect

CLASSIFICATION RULES:
- If provisions are semantically identical → ADMINISTRATIVE, LOW
- If difference due to IRC/ERISA/SECURE Act change → REGULATORY, then assess impact
- If difference due to employer election (AA option changed) → DESIGN, then assess impact
- If uncertain → Mark confidence <70%, flag for manual review

CRITICAL EXAMPLES:
[Include examples 1, 4, 5, 7 from above as few-shot learning]

SOURCE PROVISION:
{source_provision_text}
Section: {source_section_context}

TARGET PROVISION:
{target_provision_text}
Section: {target_section_context}

Step 1: Identify the core difference
Step 2: Determine if difference is wording-only, election-based, or law-mandated
Step 3: Assess participant impact (rights, eligibility, contributions, distributions)
Step 4: Classify variance type and impact level
Step 5: Provide reasoning with specific evidence

Output (JSON):
{
  "variance_type": "ADMINISTRATIVE | DESIGN | REGULATORY",
  "impact_level": "HIGH | MEDIUM | LOW",
  "confidence": 85,
  "reasoning": "Detailed explanation citing specific differences and their consequences",
  "participant_impact": "Description of how participants are affected, if at all",
  "regulatory_reference": "IRC/ERISA section or IRS guidance if applicable",
  "recommended_action": "Specific next steps for user"
}
```

---

## Variance Output Schema

```json
{
  "variance_id": "uuid",
  "source_provision_id": "uuid",
  "target_provision_id": "uuid",

  "variance_type": "ADMINISTRATIVE | DESIGN | REGULATORY",
  "impact_level": "HIGH | MEDIUM | LOW",
  "confidence": 0.85,

  "difference_summary": "Eligibility changed from age 21 + 1 year to immediate",

  "reasoning": "The target provision removes all eligibility requirements, expanding participant rights significantly. This is a discretionary employer election (Design variance) with High impact as it affects who can participate and when.",

  "participant_impact": "Employees can now participate immediately upon hire instead of waiting until age 21 and 1 year of service. Estimated 40 additional employees become eligible.",

  "regulatory_reference": null,  // Or "IRC §401(a)(9) per SECURE 2.0 Act §107"

  "recommended_action": "Requires plan sponsor approval. Document in exception log. Communicate to newly eligible employees. Update enrollment procedures.",

  "evidence": {
    "source_text": "Employees are eligible after age 21 and 1 year of service.",
    "target_text": "Employees are eligible immediately upon hire.",
    "key_differences": ["age requirement removed", "service requirement removed"]
  },

  "metadata": {
    "detected_at": "2025-10-23T14:30:00Z",
    "detection_method": "semantic_mapping_v1",
    "reviewer": null,  // User who reviewed
    "review_status": "pending | approved | rejected",
    "exception_log_id": null  // If elevated to exception tracking
  }
}
```

---

## Exception Log Integration

### When to Escalate Variance to Exception

**Rule**: Design variances with High or Medium impact → Auto-generate exception log entry

**Workflow**:
```
1. Variance detected and classified (LLM)
2. If variance_type == "DESIGN" AND impact_level IN ["HIGH", "MEDIUM"]:
   ├─ Generate exception log entry
   ├─ Assign unique exception ID
   ├─ Link to source/target provision IDs
   ├─ Set status = "Open"
   └─ Add to exception tracking queue
3. User reviews exception
4. User marks exception as:
   ├─ Approved (plan sponsor accepts change)
   ├─ Rejected (plan sponsor wants old provision)
   └─ Requires Amendment (plan sponsor wants different election)
5. Exception status → "Closed" when resolved
```

**Exception Log Entry** (from `/process/templates/exception_log.csv`):
```csv
Exception ID,Provision Reference,Category,Description,Risk Level,Detected Date,Assigned To,Status,Resolution Notes
EX-001,Source 3.01 → Target 1.7,Design,Eligibility changed from age 21+1yr to immediate,HIGH,2025-10-23,Plan Sponsor,Open,Awaiting sponsor approval
```

---

## Open Questions / Future Decisions

1. **Should we train a specialized classifier model?**
   - Current: LLM prompt-based classification
   - Alternative: Fine-tuned model on labeled variance examples
   - **Decision pending**: LLM approach sufficient for MVP, revisit if accuracy < 80%

2. **How to handle multi-faceted variances?**
   - Example: Provision has both Administrative (wording) AND Design (election) changes
   - Current: Classify by most significant change
   - **Decision pending**: Allow multiple variance types per provision?

3. **Should confidence threshold vary by variance type?**
   - Regulatory variances easier to classify (cite IRS guidance)
   - Design variances harder (requires understanding participant impact)
   - **Decision pending**: Implement type-specific thresholds?

4. **How to handle vendor-specific defaults?**
   - Relius includes HCEs by default, Ascensus requires election
   - These look identical in BPD text but differ in AA elections
   - **Solution**: Requires BPD + AA merger for accurate detection

---

## Success Criteria

**For MVP:**
- ✅ Classification accuracy ≥80% (validated by SME review)
- ✅ High-impact Design variances flagged 100% of the time
- ✅ Regulatory variances cite correct IRS/DOL guidance
- ✅ Administrative variances don't overwhelm user with false alarms
- ✅ Exception log auto-populates from Design variances

**For Production:**
- ✅ Classification accuracy ≥90%
- ✅ Variance types correlate with user actions (approve vs. amend vs. reject)
- ✅ Impact levels correlate with sponsor escalations
- ✅ Zero critical variances missed (like HCE safe harbor example)

---

## References

- `/requirements/functional_requirements.md` - REQ-022 (variance detection and classification)
- `/process/control_002_document_reconciliation.md` - Variance tracking workflow
- `/process/templates/exception_log.csv` - Exception log schema
- `/research/market_research.pdf` - Real-world Relius→ASC HCE safe harbor example (page 3)
- `/design/data_models/provisional_matching.md` - Variance detection after provisional match confirmation

---

*Document Created: 2025-10-23*
*Author: Claude (with Sergio DuBois)*
*Status: Draft - pending Sergio's review*
*Next Review: Before variance classification prompt creation*
