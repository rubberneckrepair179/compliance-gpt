# BPD Crosswalk Mapping Model

**Purpose:** Define the structure for provision-to-provision mapping specifications between different BPD versions.

**Use Cases:**
1. Human-readable reference for compliance teams performing conversions
2. Training data for AI semantic mapping models
3. Validation reference for AI-generated mappings
4. Documentation of regulatory/design differences between BPD versions

---

## Data Model

### Crosswalk Entry

Each mapping entry represents a conceptual relationship between provisions in source and target BPDs.

```json
{
  "mapping_id": "string (unique identifier, e.g., 'MAP-001')",
  "source": {
    "document": "string (e.g., 'BPD 01')",
    "section_number": "string (e.g., '3.2(a)')",
    "section_title": "string (e.g., 'Eligibility - Age Requirement')",
    "provision_text": "string (template language preserved)",
    "topic": "string (e.g., 'Eligibility', 'Vesting', 'Contributions')"
  },
  "target": {
    "document": "string (e.g., 'BPD 05')",
    "section_number": "string | null (null if no mapping)",
    "section_title": "string | null",
    "provision_text": "string | null (template language preserved)",
    "topic": "string"
  },
  "mapping_metadata": {
    "mapping_type": "enum: '1:1' | 'with_constraints' | 'with_exceptions' | 'no_mapping' | 'new_in_target'",
    "confidence_score": "float (0-100, AI-generated)",
    "constraints": [
      {
        "condition": "string (when this mapping applies)",
        "rationale": "string (why this constraint exists)"
      }
    ],
    "exceptions": [
      {
        "scenario": "string (when this mapping does NOT apply)",
        "alternative": "string (what to do instead)"
      }
    ],
    "notes": "string (regulatory/design differences, migration guidance)",
    "requires_manual_review": "boolean",
    "review_reason": "string (why manual review is needed)"
  },
  "analysis": {
    "semantic_similarity": "string (explanation of how provisions relate conceptually)",
    "key_differences": ["string (list of substantive differences)"],
    "regulatory_impact": "enum: 'none' | 'administrative' | 'design_change' | 'qualification_risk'",
    "migration_complexity": "enum: 'low' | 'medium' | 'high'"
  }
}
```

---

## Mapping Type Definitions

### 1:1 Mapping
- Source and target provisions express identical concept
- Language may differ but semantic meaning is equivalent
- No conditional logic required

**Example:**
```
Source (BPD 01 § 3.1): "Employee must be age 21 as elected in the Adoption Agreement"
Target (BPD 05 § 2.1): "Minimum age requirement as specified in Adoption Agreement"
Mapping Type: 1:1
```

### With Constraints
- Mapping applies only under specific conditions
- Multiple target provisions may map to single source (or vice versa)
- Requires conditional logic based on elections

**Example:**
```
Source (BPD 01 § 5.2): "Forfeitures may be used to reduce employer contributions"
Target (BPD 05 § 4.3): "Forfeiture allocation method as elected"
Mapping Type: with_constraints
Constraint: "Only maps if AA elects 'reduce contributions' option (not 'allocate to participants')"
```

### With Exceptions
- General mapping applies except in specific scenarios
- Requires fallback logic

**Example:**
```
Source (BPD 01 § 6.1): "Safe harbor contributions vest immediately"
Target (BPD 05 § 5.1): "Safe harbor vesting as required by IRC §401(k)(12)"
Mapping Type: with_exceptions
Exception: "QACA safe harbor allows 2-year cliff vesting - see BPD 05 § 5.2"
```

### No Mapping
- Provision exists in source but has no equivalent in target
- May indicate deprecated feature or regulatory change
- Requires manual review for impact assessment

**Example:**
```
Source (BPD 01 § 7.5): "Qualified Roth Contribution Program (pre-2006)"
Target: null
Mapping Type: no_mapping
Notes: "Deprecated provision. Roth 401(k) now handled in § 3.4 of BPD 05"
```

### New in Target
- Provision exists in target but not in source
- May indicate new regulatory requirement or design option
- Requires affirmative election or default selection

**Example:**
```
Source: null
Target (BPD 05 § 8.9): "Qualified Birth or Adoption Distribution (SECURE Act)"
Mapping Type: new_in_target
Notes: "New provision required by SECURE Act 2019. Must elect in or out."
```

---

## CSV Output Schema

For compatibility with `/process/templates/plan_comparison_workbook.csv`:

```csv
mapping_id,source_section,source_title,source_text,target_section,target_title,target_text,mapping_type,confidence,constraints,exceptions,notes,requires_review,review_reason,semantic_similarity,key_differences,regulatory_impact,migration_complexity
MAP-001,3.2(a),Eligibility - Age,Employee must be age 21...,2.1(a),Minimum Age,Age requirement as elected...,1:1,95,"","",Language differs but meaning identical,false,"",Both provisions enforce same IRC 410(a) requirement,[Minor wording change only],none,low
MAP-002,5.2,Forfeiture Use,Forfeitures may reduce...,4.3,Forfeiture Allocation,Method as elected...,with_constraints,85,"Only if AA elects 'reduce contributions'","",BPD 05 adds allocation option,true,Multiple target options available,Both comply with IRC 401(a)(8),[BPD 05 adds participant allocation option],design_change,medium
```

---

## JSON Output Schema

For programmatic use:

```json
{
  "crosswalk_metadata": {
    "created_date": "2025-10-19",
    "source_document": "Ascensus BPD 01",
    "target_document": "Ascensus BPD 05 (Cycle 3)",
    "total_mappings": 150,
    "mapping_summary": {
      "1:1": 85,
      "with_constraints": 35,
      "with_exceptions": 15,
      "no_mapping": 8,
      "new_in_target": 7
    },
    "confidence_distribution": {
      "high (90-100)": 100,
      "medium (70-89)": 40,
      "low (<70)": 10
    }
  },
  "mappings": [
    { /* mapping entry */ },
    { /* mapping entry */ }
  ]
}
```

---

## Usage Example

### Scenario: Compliance team converting client from BPD 01 to BPD 05

**Step 1:** Locate provision in source AA
- Client elected "Age 21" for eligibility in BPD 01 AA

**Step 2:** Look up in crosswalk
- Find mapping MAP-001: BPD 01 § 3.2(a) → BPD 05 § 2.1(a)
- Mapping type: 1:1, confidence: 95%

**Step 3:** Apply to target AA
- Check BPD 05 § 2.1(a) in new template
- Confirm equivalent election exists
- Make same election in new AA

**Step 4:** Handle exceptions
- If mapping has constraints, verify conditions are met
- If mapping has exceptions, check if any apply
- If no mapping exists, flag for manual review

---

## Validation Rules

1. **Every source provision must have a mapping entry** (even if mapping_type = "no_mapping")
2. **New target provisions must be documented** (mapping_type = "new_in_target")
3. **Confidence < 70% must have `requires_manual_review = true`**
4. **Constraints and exceptions must be mutually exclusive** (can't have both)
5. **Regulatory impact != "none" must have explanation in notes**

---

## Next Steps for POC

1. Extract provisions from BPD 01 and BPD 05
2. Generate initial mappings using LLM semantic analysis
3. Populate crosswalk entries with mapping metadata
4. Output both CSV and JSON formats
5. Manual review and refinement of low-confidence mappings

---

*Last Updated: 2025-10-19*
