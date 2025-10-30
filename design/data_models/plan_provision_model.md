# Plan Provision Data Model

**Version:** 1.0
**Date:** 2025-10-30
**Status:** Draft - Phase 1 POC

---

## Overview

A **Plan Provision** is the complete semantic unit for provision comparison, consisting of:
- **BPD Provision** (template language, often with conditional/placeholder text)
- **Linked AA Election(s)** (the questions/options that complete the BPD provision)

Plan Provisions are the units compared in semantic crosswalks. They represent the full provision structure, including available options, even when no specific values are selected.

---

## Terminology

| Term | Completeness | Description | Example |
|------|--------------|-------------|---------|
| **BPD Provision** | Incomplete | Template provision text with conditional language | "Employee eligible when conditions satisfied, **as elected in AA**" |
| **AA Election** | Incomplete | Election question with available options (no selection) | "Age requirement: □18 □21 □none" |
| **Plan Provision** | Complete | BPD Provision + linked AA Election(s) | BPD §3.1 + AA Q1.04 (age) + AA Q1.05 (service) |

**Note:** When filled forms are available, Plan Provisions also include the selected values. For Phase 1 POC, we work with template-level Plan Provisions (structure + options, no selections).

---

## Data Model

### PlanProvision (Complete Unit)

```json
{
  "plan_provision_id": "prov_relius_eligibility_001",
  "canonical_key": "eligibility.conditions",
  "provision_category": "eligibility|compensation|contributions|vesting|distributions|testing|other",
  "source_vendor": "Relius",
  "completeness": "template|filled",

  "bpd_component": {
    "section_number": "3.1",
    "section_title": "CONDITIONS OF ELIGIBILITY",
    "provision_text": "An Eligible Employee shall be eligible to participate hereunder on the date such Employee has satisfied the conditions of eligibility, if any, elected in the Adoption Agreement...",
    "provision_type": "operational",
    "pdf_page": 15,
    "election_references": [
      "as elected in the Adoption Agreement",
      "conditions of eligibility, if any"
    ]
  },

  "aa_components": [
    {
      "question_id": "AA.Q1.04",
      "section_number": "1.04",
      "section_title": "Age and Service Requirements",
      "provision_text": "Eligibility requirements (select one or more):\n□ a. Age 18\n□ b. Age 21\n□ c. No age requirement\n□ d. Immediate (no service)\n□ e. 6 months of Service\n□ f. 1 Year of Service",
      "provision_type": "elections",
      "pdf_page": 6,
      "form_elements": [
        {"element_type": "checkbox", "element_sequence": 1, "text_value": "Age 18"},
        {"element_type": "checkbox", "element_sequence": 2, "text_value": "Age 21"},
        {"element_type": "checkbox", "element_sequence": 3, "text_value": "No age requirement"},
        {"element_type": "checkbox", "element_sequence": 4, "text_value": "Immediate (no service)"},
        {"element_type": "checkbox", "element_sequence": 5, "text_value": "6 months of Service"},
        {"element_type": "checkbox", "element_sequence": 6, "text_value": "1 Year of Service"}
      ],
      "selected_values": null
    },
    {
      "question_id": "AA.Q1.05",
      "section_number": "1.05",
      "section_title": "Entry Dates",
      "provision_text": "Entry dates (select one):\n□ a. Monthly (first day of each month)\n□ b. Quarterly (first day of each calendar quarter)\n□ c. Semi-annually\n□ d. Annually",
      "provision_type": "elections",
      "pdf_page": 6,
      "form_elements": [
        {"element_type": "checkbox", "element_sequence": 1, "text_value": "Monthly (first day of each month)"},
        {"element_type": "checkbox", "element_sequence": 2, "text_value": "Quarterly (first day of each calendar quarter)"},
        {"element_type": "checkbox", "element_sequence": 3, "text_value": "Semi-annually"},
        {"element_type": "checkbox", "element_sequence": 4, "text_value": "Annually"}
      ],
      "selected_values": null
    }
  ],

  "linkage": {
    "link_method": "explicit_reference|keyword_matching|semantic_search",
    "confidence": 0.95,
    "reasoning": "BPD §3.1 explicitly references 'conditions of eligibility...elected in the Adoption Agreement'; AA Q1.04 is titled 'Age and Service Requirements' in eligibility section",
    "anchor_text": "elected in the Adoption Agreement"
  },

  "semantic_summary": "Eligibility provision defining when employees can participate based on age and service requirements (options: age 18/21/none, service immediate/6mo/1yr) and entry date frequency (options: monthly/quarterly/semi-annually/annually). Specific requirements to be elected by employer.",

  "metadata": {
    "created_timestamp": "2025-10-30T10:00:00Z",
    "extraction_model": "gpt-5-nano",
    "linking_model": "gpt-5-mini",
    "hash": "sha256:abc123..."
  }
}
```

---

## Linkage Methods

### Method 1: Explicit Reference (Highest Confidence)
**Pattern:** BPD provision explicitly names AA section/question

**Example:**
```
BPD: "...as elected in Adoption Agreement Section 1.04"
AA: Section 1.04 - Age and Service Requirements
→ Direct link with 100% confidence
```

### Method 2: Keyword Matching (Medium Confidence)
**Pattern:** BPD provision contains domain keywords; find matching AA questions by title/content

**Example:**
```
BPD: "...vesting schedule elected by the Employer..."
AA Q8: "Vesting Schedule Election"
→ Keyword match: "vesting schedule" with 90% confidence
```

### Method 3: Semantic Search (Lower Confidence)
**Pattern:** Use embeddings to find semantically related AA questions when no explicit reference or keyword match

**Example:**
```
BPD: "Participant's interest shall become nonforfeitable according to..."
AA Q8: "Vesting Schedule" (embedding similarity = 0.82)
→ Semantic link with 75% confidence
```

---

## Linkage Algorithm (Phase 1 POC)

```python
def link_bpd_to_aa(bpd_provision, aa_elections):
    """
    Links BPD provision to related AA election(s).

    Returns: List of (aa_election, confidence, method) tuples
    """

    links = []

    # Step 1: Explicit references
    for pattern in ["Section \\d+\\.\\d+", "Question \\d+", "as elected in.*Agreement.*\\d+"]:
        if match := re.search(pattern, bpd_provision['provision_text']):
            # Extract section/question number
            ref_number = extract_number(match.group())
            # Find matching AA
            if aa := find_aa_by_number(aa_elections, ref_number):
                links.append((aa, 1.0, "explicit_reference"))

    # Step 2: Keyword matching (if no explicit refs found)
    if not links:
        keywords = extract_keywords(bpd_provision['section_title'])
        for aa in aa_elections:
            aa_keywords = extract_keywords(aa['section_title'])
            if overlap := keywords & aa_keywords:
                confidence = len(overlap) / len(keywords)
                if confidence >= 0.6:
                    links.append((aa, confidence, "keyword_matching"))

    # Step 3: Semantic search (if still no links)
    if not links:
        bpd_embedding = embed(bpd_provision['provision_text'])
        for aa in aa_elections:
            aa_embedding = embed(aa['provision_text'])
            similarity = cosine_similarity(bpd_embedding, aa_embedding)
            if similarity >= 0.75:
                links.append((aa, similarity, "semantic_search"))

    return links
```

---

## Plan Provision Crosswalk

### Input
- **Source Plan Provisions** (Relius BPD+AA)
- **Target Plan Provisions** (Ascensus BPD+AA)

### Process
For each source Plan Provision:
1. Find candidate target Plan Provisions (embeddings + LLM verification)
2. Compare **complete structures** (BPD text + AA options available)
3. Classify relationship:
   - **Equivalent:** Same semantic meaning, similar option ranges
   - **Superset:** Target offers more options than source
   - **Subset:** Target offers fewer options than source
   - **Different:** Semantically different provisions
   - **No Match:** No corresponding target provision found

### Output (CrosswalkResult)

```json
{
  "crosswalk_result_id": "xwalk_eligibility_001",
  "source_plan_provision_id": "prov_relius_eligibility_001",
  "target_plan_provision_id": "prov_ascensus_eligibility_001",
  "relation": "equivalent|superset|subset|different|no_match",
  "variance_classification": "None|Administrative|Design|Regulatory",
  "impact_level": "Low|Medium|High",

  "bpd_comparison": {
    "text_similarity": 0.87,
    "semantic_equivalence": true,
    "notable_differences": []
  },

  "aa_comparison": {
    "option_overlap": 0.83,
    "source_unique_options": [],
    "target_unique_options": ["3 months of Service", "Semi-monthly entry dates"],
    "option_structure_equivalent": true
  },

  "rationale": "Both provisions address eligibility conditions (age, service, entry dates). BPD language is semantically equivalent. Ascensus AA offers 2 additional options (3-month service, semi-monthly entry) not available in Relius. Structural equivalence maintained.",

  "confidence": 0.91,
  "audit": {
    "run_id": "2025-10-30T12:00Z",
    "model": "gpt-5-mini"
  }
}
```

---

## Phase 1 POC Goals

### Primary Goal
Demonstrate that **Plan Provision crosswalk** (BPD+AA) produces richer, more accurate comparisons than **BPD-only crosswalk**.

### Success Criteria
1. ✅ Successfully link ≥80% of BPD provisions to their AA elections (for common provision types)
2. ✅ Plan Provision crosswalk detects option-space differences missed by BPD-only
3. ✅ Linkages are stable/accurate enough to reuse when filled forms arrive

### Out of Scope (Phase 1)
- Value substitution (no filled forms yet)
- Complex multi-provision dependencies
- Regulatory compliance validation
- Amendment detection

---

## Evolution Path

### Template Phase (Phase 1 - Current)
- Plan Provisions include BPD + AA structure/options
- No selected values
- Output: Structural equivalence map

### Filled Phase (Future)
- Plan Provisions include selected values
- `selected_values` populated in `aa_components`
- Output: Semantic equivalence with actual values
- Example: "Age 21 selected" → "Age 18 selected" (detected change)

### Value Translation Phase (Future)
- Use structural map from Phase 1 to translate values
- Example: Relius Q1.04 "Age 21" → Ascensus Q2 "Age 21"
- Automated conversion suggestion

---

**Next Steps:**
1. Implement linking algorithm (explicit references first)
2. Generate Plan Provisions for 10 test cases (5 provision types × 2 vendors)
3. Run crosswalk comparison (Plan Provisions vs BPD-only)
4. Validate hypothesis

---

*Author: Sergio DuBois (with AI assistance from Claude)*
*Related: [ADR-001: Merge Strategy](../architecture/adr_001_merge_strategy.md)*
