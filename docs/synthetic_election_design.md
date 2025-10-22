# Synthetic Election Data Design

**Sprint Goal:** Create realistic filled source AA to simulate a complete retirement plan conversion workflow

**Date:** October 21, 2025

---

## Overview

We need to create a realistic set of 543 filled elections for the source Adoption Agreement that represents an actual employer's retirement plan choices. This will enable us to:

1. Test BPD+AA merger (substituting elections into template provisions)
2. Generate conversion mappings (source elections → target elections)
3. Run merged crosswalk (source complete provisions ↔ target complete provisions)
4. Validate the full end-to-end conversion workflow

---

## Election Distribution

From source AA extraction:
- **543 total elections**
- **Text elections:** 194 (35.7%)
- **Single-select elections:** 295 (54.3%)
- **Multi-select elections:** 54 (9.9%)

---

## Synthetic Plan Profile

We'll design elections for a **realistic mid-sized employer** with the following characteristics:

### Employer Profile
- **Company:** TechCorp Solutions, Inc.
- **Type:** C Corporation (tech/software company)
- **Employees:** ~250 employees
- **Plan Type:** 401(k) Profit Sharing Plan
- **Safe Harbor:** Yes (Basic Match 100% up to 3%, 50% from 3-5%)
- **Auto-enrollment:** Yes (QACA with 3% default deferral)

### Plan Design Philosophy
- **Conservative vesting:** 6-year graded (0-2yr: 0%, 3yr: 20%, 4yr: 40%, 5yr: 60%, 6yr: 100%)
- **Broad eligibility:** Age 21, no service requirement (immediate entry)
- **Standard compensation:** W-2 wages
- **Normal retirement age:** 65
- **Distributions:** Standard 401(k) (in-service at 59½, hardship allowed, loans allowed)

---

## Election Categories and Strategy

### Part A: Employer Information (Questions 1.01 - 1.20)
**Text fields** for employer identification:
- Name: "TechCorp Solutions, Inc."
- Address: "1234 Innovation Drive, Austin, TX 78701"
- EIN: "12-3456789"
- Fiscal year: Calendar year
- Type of business: C Corporation
- Plan name: "TechCorp Solutions 401(k) Plan"
- Plan number: 001
- Effective date: January 1, 2018

### Part B: Plan Type and Contributions
**Key elections:**
- Plan type: 401(k) Profit Sharing Plan
- Safe Harbor: Yes (Basic Match)
- Auto-enrollment: Yes (QACA)
- Matching contributions: Safe Harbor Basic Match
- Profit sharing: Discretionary (pro-rata allocation)

### Part C: Eligibility
**Key elections:**
- Age: 21
- Service: None (0 months)
- Entry dates: Immediate (first day of month following hire)
- Excludes: Leased employees, nonresident aliens

### Part D: Compensation
**Key elections:**
- Definition: W-2 wages
- Include: Bonuses, commissions, overtime
- Exclude: Reimbursements, fringe benefits

### Part E: Vesting
**Key elections:**
- Schedule: 6-year graded
- Computation period: Plan year
- Safe Harbor contributions: Immediate 100%

### Part F: Distributions
**Key elections:**
- Normal retirement age: 65
- In-service withdrawals: Age 59½
- Hardship: Allowed (safe harbor reasons)
- Loans: Allowed (max $50k or 50% of vested balance)

### Part G: Beneficiaries
**Key elections:**
- Spouse consent: Required for non-spouse beneficiaries
- No QJSA/QPSA (profit sharing plan exemption)

---

## Realistic Constraints

### Internal Consistency
Elections must be logically consistent:
- If "Safe Harbor" = Yes, then safe harbor match formula must be selected
- If "QACA" = Yes, then auto-enrollment must be specified
- If "Loans" = Yes, then loan limits and terms must be specified
- Vesting schedule for safe harbor must be 100% immediate
- Vesting schedule for discretionary can be up to 6-year graded

### Regulatory Compliance
- Minimum age ≤ 21, minimum service ≤ 1 year (IRC §410(a)(1))
- Vesting schedules within safe harbors (IRC §411(a)(2))
- Safe harbor match formula matches IRS requirements (IRC §401(k)(12))
- QACA default deferral ≥ 3% (IRC §401(k)(13))

### Common Patterns
- Tech companies often use immediate eligibility (competitive labor market)
- Safe harbor to avoid ADP/ACP testing (administrative simplicity)
- QACA for auto-enrollment (automatic savings, employer FICA credit)
- Discretionary profit sharing (flexibility based on company performance)
- Loans allowed (employee recruitment/retention tool)

---

## Implementation Approach

### Phase 1: Core Elections (Critical Path)
Focus on the ~50-75 elections that directly affect BPD provisions:
1. Employer identification (name, EIN, plan name)
2. Plan type (401(k), profit sharing)
3. Safe harbor elections (yes/no, formula)
4. Eligibility (age, service, entry dates)
5. Compensation definition
6. Vesting schedule
7. Distribution rules

### Phase 2: Supporting Elections
Fill in remaining elections with realistic defaults:
- Administrative details (plan year, recordkeeper)
- Optional features (catch-up, Roth, auto-enrollment specifics)
- Exclusions and special rules

### Phase 3: Validation
Verify internal consistency:
- Run logic checks (if X then Y must be...)
- Compare to BPD references (ensure all AA-dependent provisions can be filled)
- Spot-check 10-20 elections for realism

---

## Output Format

```json
{
  "document": "test_data/raw/source/aa/source_aa.pdf",
  "doc_type": "AA",
  "model": "synthetic_v1",
  "total_elections": 543,
  "filled_elections": 543,
  "aas": [
    {
      "id": "q1_01",
      "kind": "text",
      "question_number": "1.01",
      "question_text": "Name of Adopting Employer",
      "section_context": "Part A - Adopting Employer",
      "status": "answered",
      "confidence": 1.0,
      "provenance": {
        "page": 1,
        "question_number": "1.01"
      },
      "value": "TechCorp Solutions, Inc."
    },
    {
      "id": "q1_09",
      "kind": "single_select",
      "question_number": "1.09",
      "question_text": "Type of Business (select one)",
      "status": "answered",
      "confidence": 1.0,
      "provenance": {
        "page": 2,
        "question_number": "1.09"
      },
      "value": {
        "option_id": "q1_09_opt_c"
      },
      "options": [
        {
          "option_id": "q1_09_opt_a",
          "label": "a",
          "option_text": "Sole Proprietorship",
          "is_selected": false
        },
        {
          "option_id": "q1_09_opt_b",
          "label": "b",
          "option_text": "Partnership",
          "is_selected": false
        },
        {
          "option_id": "q1_09_opt_c",
          "label": "c",
          "option_text": "C Corporation",
          "is_selected": true
        }
      ]
    }
  ]
}
```

---

## Next Steps

1. ✅ Design complete (this document)
2. ⏳ **Seek Sergio's approval** on plan profile and election strategy
3. ⏳ Create Python script to generate synthetic elections
4. ⏳ Validate internal consistency
5. ⏳ Export to `test_data/synthetic/source_aa_filled.json`

---

## Questions for Sergio

Before implementing, please review:

1. **Plan profile realistic?** - Does TechCorp profile represent a common client scenario?
2. **Elections strategy sound?** - Safe Harbor + QACA + 6-year vesting is common pattern?
3. **Phase 1 scope appropriate?** - Should we fill all 543 or focus on critical ~75 for POC?
4. **Validation approach?** - Manual spot-check sufficient or automated consistency checks needed?

---

*Document Status: Draft - Awaiting Approval*
*Next: Implementation Script Design*
