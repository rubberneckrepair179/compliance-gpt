# Future Prompt Enhancements

This document tracks planned improvements to prompts and context as the project matures beyond POC.

## Provision Extraction Enhancements

### 1. Definition-Aware Extraction (Two-Pass Approach)
**Purpose:** Capture operational provisions WITH their referenced definitions
**Priority:** High
**Status:** Not yet implemented (POC uses operational-only extraction)

**Problem identified:**
Operational provisions frequently reference defined terms:
- "An Employee shall be eligible at age 21 and 1 Year of Service"
- References: "Employee", "Year of Service" (defined elsewhere)

**Proposed solution:**
```python
# Pass 1: Extract operational provisions
operational_provisions = extract_operational_provisions(document)

# Pass 2: Identify referenced terms and extract definitions
for provision in operational_provisions:
    referenced_terms = identify_referenced_terms(provision.text)
    definitions = extract_definitions(document, referenced_terms)
    provision.definitions = definitions
```

**Data model enhancement:**
```python
class Provision:
    provision_text: str  # Operational rule
    referenced_terms: List[str]  # ["Year of Service", "Eligible Employee"]
    definitions: Dict[str, str]  # Term → Definition mapping
```

**Benefits:**
- Complete semantic context for comparison
- Can detect when same operational rule uses different underlying definitions
- Enables definition-level variance detection

**Example use case:**
Both documents say "eligible at 1 Year of Service" but:
- Source defines it as "1,000 hours in 12 months"
- Target defines it as "500 hours in 12 months"
→ Flag as DESIGN variance despite identical operational text

---

### 2. Operational vs Definitional Classification
**Purpose:** Distinguish between provisions that establish rules vs those that define terms
**Priority:** High
**Status:** Partially implemented in v1 prompt (needs refinement)

**Heuristics for classification:**
- **Operational**: Uses SHALL, WILL, MUST, imperative language; specifies conditions/schedules
- **Definitional**: Uses "means", appears in quotes, defines terms for use elsewhere

**Prompt guidance needed:**
```
OPERATIONAL (extract these):
✓ "An Employee shall be eligible to participate upon attaining age 21..."
✓ "The vesting schedule shall be: 0% years 1-2, 100% year 3..."

DEFINITIONAL (skip unless referenced):
✗ "'Eligible Employee' means any Employee as elected in the Adoption Agreement..."
✗ "'Year of Service' means a 12-consecutive-month period..."
```

**Future enhancement:**
Add `provision_category: "operational" | "definitional"` field to track this explicitly

---

## Context Documents to Develop

### 1. Term Glossary/Thesaurus
**Purpose:** Map equivalent terminology across different vendor documents
**Priority:** High
**Status:** Not yet implemented

**Examples of entries:**
```json
{
  "canonical_term": "Year of Service",
  "equivalents": [
    "Service Year",
    "Eligibility Year",
    "12-consecutive-month period with 1,000 Hours of Service",
    "1,000 Hour Year"
  ],
  "definition": "IRC §410(a)(3) - 12-month period with 1,000+ hours"
}
```

**Generation strategy:**
1. Bootstrap with common terms from research
2. Extract variations from actual document corpus
3. Use LLM to synthesize additional equivalents
4. Maintain and version as corpus grows

---

### 2. Sponsor Approval Rules
**Purpose:** Determine when provision changes require sponsor approval vs automatic
**Priority:** High
**Status:** Not yet implemented

**Examples of rules:**
```json
{
  "provision_type": "vesting_schedule",
  "rule": "Any change to vesting schedule requires sponsor approval",
  "authority": "IRC §411(a), ERISA §203",
  "exceptions": ["Immediate 100% vesting - always allowed"]
},
{
  "provision_type": "eligibility",
  "rule": "More restrictive = sponsor approval; Less restrictive = may be automatic",
  "authority": "IRC §410",
  "examples": [
    "Age 21 → Age 18: Less restrictive, may be automatic",
    "Age 21 → Age 25: More restrictive, requires approval"
  ]
}
```

**Complexity:**
- Requires deep ERISA/IRC knowledge
- May vary by plan type (401(k) vs profit-sharing)
- Sergio's domain expertise critical for this

---

### 3. Regulatory Change Catalog
**Purpose:** Identify if variance is due to required law change (SECURE Act, etc.)
**Priority:** Medium
**Status:** Not yet implemented

**Examples:**
```json
{
  "law": "SECURE Act 2.0",
  "effective_date": "2023-01-01",
  "changes": [
    {
      "provision_type": "distribution_trigger",
      "old_rule": "RMDs start at age 70.5",
      "new_rule": "RMDs start at age 73 (born 1951-1959) or 75 (born 1960+)",
      "authority": "SECURE 2.0 §107"
    }
  ]
}
```

**Use case:** If source says age 70.5 and target says age 73, flag as "regulatory" not "design"

---

### 4. Variance Classification Examples
**Purpose:** Train consistent variance classification across document pairs
**Priority:** Medium
**Status:** Partially included in semantic_mapping_v1.txt (needs expansion)

**Needs:**
- More examples of each classification type
- Edge cases and ambiguous situations
- Real-world examples from actual document pairs
- Negative examples (what NOT to flag as variance)

---

### 5. Missing Provision Handling Rules
**Purpose:** Determine when absence of provision is significant vs assumed default
**Priority:** High
**Status:** Not yet implemented

**Examples:**
```json
{
  "provision_type": "forfeiture_allocation",
  "rule": "If source specifies but target silent, flag as HIGH risk",
  "reasoning": "No IRC default - sponsor must elect",
  "severity": "high"
},
{
  "provision_type": "elective_deferral_vesting",
  "rule": "If target silent, assume 100% vested",
  "reasoning": "IRC §411(a)(4) requires immediate vesting",
  "severity": "low"
}
```

---

## Prompt Evolution Strategy

### Phase 1: POC (Current)
- Simple prompts with inline examples
- No external context injection
- Manual review of all matches

### Phase 2: Enhanced Context
- Load term glossary at runtime
- Inject relevant regulatory rules
- Use sponsor approval rules for impact classification

### Phase 3: Learning System
- Generate glossaries from document corpus
- Learn common variance patterns
- Suggest new context entries based on edge cases

### Phase 4: Domain-Specific Models
- Fine-tune embeddings on retirement plan corpus
- Specialized classifiers for variance types
- Automated confidence calibration

---

## Context Maintenance Workflow

1. **Identify gap** - Encounter term/rule not in context
2. **Research** - Verify with regulatory sources (IRC, ERISA, Rev. Proc.)
3. **Draft entry** - Create JSON structure
4. **Review with Sergio** - Validate regulatory accuracy
5. **Version** - Add to appropriate context file
6. **Test** - Verify prompt improvement with test documents
7. **Deploy** - Update production context

---

## Metrics to Track

As we enhance context:
- **Coverage**: % of provisions with relevant context available
- **Accuracy**: Match rate improvement after context added
- **Precision**: Reduction in false positives (over-flagging variance)
- **Recall**: Reduction in false negatives (missing real variance)
- **Confidence**: Correlation between LLM confidence and human agreement

---

*Last Updated: 2025-10-19*
*Owner: Sergio (regulatory expertise) + AI (technical implementation)*
