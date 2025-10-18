# Provision Data Model

## Overview

A **provision** is the atomic unit of plan document analysis. It represents a specific rule, definition, or election in a plan document (e.g., "Employees are eligible at age 21 and 1 year of service"). This model defines the structure for extracted provisions that will be semantically matched during reconciliation.

---

## Requirements Addressed

- **REQ-004:** Intermediate representation (JSON schema with lineage)
- **REQ-020:** Provision extraction (structured data by type)
- **REQ-021:** Semantic provision mapping (requires comparable structure)

---

## Design Principles

1. **Self-contained:** Each provision includes full context (no need to reference source document)
2. **Source-traceable:** Preserve lineage (document, page, section) for audit trail
3. **Type-based:** Explicit categorization enables targeted comparison (compare eligibility to eligibility, not to vesting)
4. **LLM-friendly:** Fields designed to be easily consumed by prompts (plain text, not binary data)
5. **Extensible:** `metadata` field allows custom attributes without schema changes

---

## JSON Schema

```json
{
  "provision_id": "string (UUID)",
  "document_id": "string (references source document)",
  "provision_type": "enum (see Provision Types below)",
  "section_reference": "string (e.g., 'Section 2.01', 'Article IV(A)', '3.3.1')",
  "section_title": "string | null (e.g., 'Eligibility to Participate')",
  "provision_text": "string (full extracted text of provision)",
  "normalized_text": "string | null (optional: cleaned text for comparison)",
  "page_number": "integer | null (source page in PDF)",
  "extraction_method": "enum ['text_api', 'vision_fallback']",
  "confidence_score": "float [0.0-1.0] (extraction confidence)",
  "metadata": {
    "vendor": "string | null (detected vendor: 'Relius', 'ASC', etc.)",
    "document_type": "enum ['BPD', 'AdoptionAgreement', 'Amendment', 'OpinionLetter', 'SPD']",
    "effective_date": "string | null (YYYY-MM-DD format)",
    "plan_name": "string | null",
    "custom_fields": "object (extensible key-value pairs)"
  },
  "extracted_entities": {
    "ages": ["integer[]"],
    "service_years": ["float[]"],
    "percentages": ["float[]"],
    "dollar_amounts": ["float[]"],
    "dates": ["string[] (YYYY-MM-DD)"],
    "keywords": ["string[] (e.g., ['Safe Harbor', 'Highly Compensated Employee'])"]
  },
  "created_at": "string (ISO 8601 timestamp)",
  "updated_at": "string (ISO 8601 timestamp)"
}
```

---

## Provision Types (Taxonomy)

These types map to the common provision categories found in qualified retirement plans:

| Type | Description | Example |
|------|-------------|---------|
| `eligibility` | Age and service requirements for participation | "Age 21 and 1 year of service" |
| `compensation_definition` | How compensation is calculated (W-2, 415 safe harbor, etc.) | "Compensation means W-2 wages excluding bonuses" |
| `employer_contribution` | Match, profit-sharing, safe harbor, QACA formulas | "100% match on first 3% of deferrals" |
| `employee_deferral` | Elective deferrals, catch-up, Roth options | "Employees may defer 1-100% of compensation" |
| `vesting_schedule` | Vesting rules for employer contributions | "3-year cliff" or "2-6 year graded" |
| `distribution_trigger` | When participants can receive distributions | "Termination, death, disability, age 59½" |
| `loan_provision` | Loan availability and terms | "Loans available up to $50,000" |
| `hardship_withdrawal` | Hardship distribution rules | "Safe harbor hardship reasons apply" |
| `top_heavy` | Top-heavy provisions and minimums | "3% minimum if top-heavy" |
| `coverage_testing` | ADP/ACP testing parameters | "Prior-year testing method" |
| `forfeiture_usage` | How forfeitures are allocated | "Forfeitures reduce employer contributions" |
| `plan_year` | Plan year definition | "Plan year is January 1 - December 31" |
| `normal_retirement_age` | NRA definition | "Age 65" |
| `QACA_EACA` | Auto-enrollment provisions | "QACA safe harbor with 3% default deferral" |
| `other` | Provisions not matching above categories | Miscellaneous plan rules |

**Note:** This taxonomy is **configuration-driven** (REQ-062). New types can be added via JSON config without code changes.

---

## Field Definitions

### Core Fields

**`provision_id`** (string, UUID)
- Unique identifier for this provision
- Generated on extraction
- Used for traceability in mappings and audit logs

**`document_id`** (string)
- References the source document this provision was extracted from
- Links to `documents/` folder in persistence layer

**`provision_type`** (enum)
- Category from taxonomy above
- Enables type-based comparison (only compare eligibility to eligibility)
- Extracted via LLM classification

**`section_reference`** (string)
- Original section number/letter from source document
- Examples: "Section 2.01", "Article IV, Part A", "3.3.1"
- Used for human readability and source verification

**`section_title`** (string | null)
- Human-readable section title if present
- Examples: "Eligibility to Participate", "Employer Contributions"
- May be null if document uses only section numbers

**`provision_text`** (string)
- **Full extracted text** of the provision
- This is the primary content for semantic comparison
- May include multiple sentences or paragraphs if provision spans text
- Preserves original formatting (line breaks, bullets) where possible

**`normalized_text`** (string | null)
- Optional: Cleaned/standardized version for comparison
- Examples of normalization:
  - "twenty-one" → "21"
  - "twelve months" → "1 year"
  - Remove boilerplate phrases ("as defined herein", "pursuant to IRC §401(k)")
- Generated by LLM or rule-based preprocessing
- May improve semantic matching accuracy (TBD in Phase 2 POC)

**`page_number`** (integer | null)
- Page number in source PDF where provision appears
- Used for audit trail and user verification
- May be null if document is Word format or page numbers unavailable

**`extraction_method`** (enum: `text_api` | `vision_fallback`)
- How this provision was extracted
- `text_api`: Standard PDF text extraction
- `vision_fallback`: Multimodal LLM used due to locked/encrypted PDF
- Useful for debugging extraction quality issues

**`confidence_score`** (float, 0.0-1.0)
- LLM's confidence in the extraction accuracy
- High (>0.9): Clear, well-structured provision
- Medium (0.7-0.9): Ambiguous section boundaries or complex formatting
- Low (<0.7): Uncertainty about provision boundaries or type classification
- Used to prioritize human review of extracted data

---

### Metadata Object

**`metadata.vendor`** (string | null)
- Detected document vendor: "Relius", "ASC", "ftwilliam", "DATAIR", "Unknown"
- Extracted from document headers/footers or user-specified
- Used to inform semantic mapping (vendors use different phrasing conventions)

**`metadata.document_type`** (enum)
- `BPD` (Basic Plan Document)
- `AdoptionAgreement`
- `Amendment`
- `OpinionLetter`
- `SPD` (Summary Plan Description)
- Detected via LLM classification (REQ-003)

**`metadata.effective_date`** (string | null)
- When this provision became effective (YYYY-MM-DD format)
- Extracted from document headers or amendment dates
- Used to verify timeline consistency

**`metadata.plan_name`** (string | null)
- Plan name extracted from document
- Example: "XYZ Company 401(k) Profit Sharing Plan"
- Used for qualification checklist (REQ-012)

**`metadata.custom_fields`** (object)
- Extensible key-value pairs for vendor-specific or future attributes
- Examples:
  - `{"relius_template_id": "PS-1234"}`
  - `{"asc_prototype_name": "Safe Harbor 401(k)"}`
  - `{"amendment_number": "2023-03"}`

---

### Extracted Entities Object

Structured data extracted from `provision_text` to enable:
- Faster comparison (compare numbers directly, not just text)
- Variance detection (flag if source has "21" but target has "18")
- Confidence scoring (exact number match → higher confidence)

**`ages`** (integer[])
- Age values mentioned in provision
- Example: `[21, 59.5, 65]` from "age 21 with distributions allowed at 59½ or normal retirement age 65"

**`service_years`** (float[])
- Service requirements in years
- Example: `[1.0]` from "1 year of service"
- Example: `[0.5]` from "6 months of service"

**`percentages`** (float[])
- Percentage values (stored as decimals)
- Example: `[0.03, 1.00]` from "100% match on first 3%"

**`dollar_amounts`** (float[])
- Dollar amounts mentioned
- Example: `[50000.00]` from "loans up to $50,000"

**`dates`** (string[], YYYY-MM-DD)
- Specific dates mentioned
- Example: `["2024-01-01"]` from "effective January 1, 2024"

**`keywords`** (string[])
- Important regulatory or plan-specific terms
- Examples: `["Safe Harbor", "Highly Compensated Employee", "QACA", "Top-Heavy"]`
- Used for fast filtering (e.g., "show me all Safe Harbor provisions")

---

### Timestamps

**`created_at`** (string, ISO 8601)
- When this provision was first extracted
- Example: `"2025-10-17T14:23:45Z"`

**`updated_at`** (string, ISO 8601)
- Last modification timestamp (if provision re-extracted or manually edited)
- Used for audit trail (REQ-043)

---

## Example: Complete Provision Object

```json
{
  "provision_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_id": "doc_relius_source_001",
  "provision_type": "eligibility",
  "section_reference": "Section 2.01",
  "section_title": "Eligibility to Participate",
  "provision_text": "An Employee shall be eligible to participate in the Plan upon attaining age 21 and completing one Year of Service. A Year of Service means a 12-consecutive-month period during which the Employee completes at least 1,000 Hours of Service.",
  "normalized_text": "Employee eligible at age 21 and 1 year of service (1,000 hours in 12 months).",
  "page_number": 5,
  "extraction_method": "text_api",
  "confidence_score": 0.95,
  "metadata": {
    "vendor": "Relius",
    "document_type": "BPD",
    "effective_date": "2024-01-01",
    "plan_name": "ABC Company 401(k) Plan",
    "custom_fields": {
      "relius_template_id": "PS-401k-2023"
    }
  },
  "extracted_entities": {
    "ages": [21],
    "service_years": [1.0],
    "percentages": [],
    "dollar_amounts": [],
    "dates": ["2024-01-01"],
    "keywords": ["Year of Service", "Hours of Service", "Eligibility"]
  },
  "created_at": "2025-10-17T14:23:45Z",
  "updated_at": "2025-10-17T14:23:45Z"
}
```

---

## Example: Equivalent Provision from Different Vendor

```json
{
  "provision_id": "661e9511-f30c-52e5-b827-557766551111",
  "document_id": "doc_asc_target_001",
  "provision_type": "eligibility",
  "section_reference": "Article III, Section 3.1",
  "section_title": "Conditions of Participation",
  "provision_text": "A Participant must be at least twenty-one (21) years of age and must have completed twelve (12) consecutive months of employment with at least one thousand (1,000) hours of service to be eligible for Plan participation.",
  "normalized_text": "Participant eligible at age 21 and 12 months employment with 1,000 hours.",
  "page_number": 8,
  "extraction_method": "text_api",
  "confidence_score": 0.92,
  "metadata": {
    "vendor": "ASC",
    "document_type": "BPD",
    "effective_date": "2024-01-01",
    "plan_name": "ABC Company 401(k) Plan",
    "custom_fields": {
      "asc_prototype_name": "Safe Harbor 401(k) Prototype"
    }
  },
  "extracted_entities": {
    "ages": [21],
    "service_years": [1.0],
    "percentages": [],
    "dollar_amounts": [],
    "dates": ["2024-01-01"],
    "keywords": ["Participant", "hours of service", "employment"]
  },
  "created_at": "2025-10-17T14:45:12Z",
  "updated_at": "2025-10-17T14:45:12Z"
}
```

**Key Observations for Semantic Mapping:**
- Different section numbering: "2.01" vs "Article III, Section 3.1"
- Different terminology: "Employee" vs "Participant", "Year of Service" vs "twelve months of employment"
- Different formatting: "21" vs "twenty-one (21)", "1,000" vs "one thousand (1,000)"
- **Semantically identical:** Both specify age 21 + 1 year (1,000 hours)
- **Should map with HIGH confidence** (extracted entities match exactly)

---

## Provision Extraction Workflow

**Important:** This JSON schema is the **target output format for LLM-based extraction**. Provisions are not manually created—they are automatically generated by the LLM from plan document text.

### End-to-End Process

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Document Ingestion                                      │
│ • Upload PDF (Relius BPD, ASC Adoption Agreement, etc.)        │
│ • Extract text via PyPDF2/pdfplumber                           │
│ • If locked/encrypted → Vision model fallback                  │
│ Output: Raw document text (50-150 pages)                       │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: LLM Extraction (Claude Sonnet 4.5)                     │
│                                                                  │
│ Prompt: "You are an ERISA compliance specialist. Extract all   │
│         provisions from this plan document and output JSON.     │
│                                                                  │
│         For each provision, identify:                           │
│         - provision_type (from taxonomy)                        │
│         - section_reference (e.g., 'Section 2.01')             │
│         - provision_text (full extracted text)                  │
│         - extracted_entities (ages, percentages, dates)        │
│                                                                  │
│         Output: Array of JSON objects matching schema below..." │
│                                                                  │
│ Input: Full document text (or chunked sections for >200 pages) │
│ Output: Array of provision JSON objects                        │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Validation & Quality Check                             │
│ • Verify all required fields present                           │
│ • Check provision_type is valid (from taxonomy)                │
│ • Validate extracted_entities (ages are integers, etc.)        │
│ • Flag low-confidence extractions (confidence_score < 0.8)     │
│                                                                  │
│ Human Review Trigger:                                           │
│ ⚠️  "3 provisions flagged for review (low confidence)"         │
│ ✅ "47 provisions extracted successfully"                       │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Store to SQLite Database                               │
│ • Save provision objects to database                           │
│ • Maintain linkage to source document (document_id)            │
│ • Generate embeddings for semantic search                      │
│ • Ready for semantic mapping stage (REQ-021)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Why LLM-Based Extraction?

**Plan documents are highly variable and complex:**

| Challenge | LLM Solution | Rule-Based Limitation |
|-----------|-------------|----------------------|
| **Different vendor formats** | Handles Relius, ASC, ftwilliam, DATAIR variations | Would need separate parser per vendor |
| **Varied section numbering** | Understands "Section 2.01" ≈ "Article III, 3.1" | Hardcoded regex would break |
| **Nested provisions** | Parses multi-paragraph provisions with sub-sections | Can't determine semantic boundaries |
| **Legal language variations** | Normalizes "shall", "must", "will", "may" | Keyword matching misses nuance |
| **Entity extraction** | Extracts "21" from "twenty-one (21) years" | Would need exhaustive pattern library |

**Real-world example:**

```
Relius Document (paragraph format):
"Section 2.01. Eligibility. An Employee shall become eligible to
participate in the Plan upon attaining age 21 and completing one
Year of Service. For purposes of this Section, a Year of Service
means a 12-consecutive-month period during which the Employee
completes at least 1,000 Hours of Service."

LLM Output:
{
  "provision_type": "eligibility",
  "section_reference": "Section 2.01",
  "provision_text": "An Employee shall become eligible...",
  "extracted_entities": {
    "ages": [21],
    "service_years": [1.0],
    "keywords": ["Year of Service", "Hours of Service"]
  }
}

ASC Document (outline format):
"Article III - Conditions of Participation
Section 3.1
(a) Age Requirement: twenty-one (21) years
(b) Service Requirement: twelve (12) consecutive months with
    at least one thousand (1,000) hours"

LLM Output:
{
  "provision_type": "eligibility",
  "section_reference": "Article III, Section 3.1",
  "provision_text": "Age Requirement: twenty-one (21) years...",
  "extracted_entities": {
    "ages": [21],
    "service_years": [1.0],
    "keywords": ["Age Requirement", "Service Requirement"]
  }
}
```

**Key Insight:** Despite completely different formats, the LLM extracts semantically equivalent data. This enables cross-vendor semantic mapping in the next stage.

### Human-in-the-Loop Review

**Extraction is not fully autonomous.** Users can review and correct:

**Summary View:**
```
✅ Extracted 47 provisions from "ABC Company 401(k) Plan.pdf":
   • 2 Eligibility provisions
   • 1 Compensation definition
   • 5 Contribution provisions (3 match, 2 profit-sharing)
   • 3 Vesting provisions
   • 8 Distribution provisions
   • 2 Loan provisions
   • 1 Hardship withdrawal
   • 12 Safe Harbor provisions
   • 7 Top-Heavy provisions
   • 3 Coverage/testing provisions
   • 3 Other provisions

⚠️  3 provisions flagged for review (confidence < 0.8):
   • Provision #23 (vesting) - Ambiguous section boundary
   • Provision #41 (distribution) - Cross-reference to Amendment
   • Provision #45 (other) - Unclear provision type
```

**User Actions:**
- ✅ **Approve all** (high confidence extractions)
- 🔍 **Review flagged** (inspect low-confidence items)
- ➕ **Add missing** (LLM missed a provision)
- ✏️ **Edit provision** (correct provision_type or text)
- 🗑️ **Delete provision** (LLM extracted boilerplate as provision)

**Quality Control:** Before proceeding to semantic mapping, user confirms extraction is complete and accurate.

### Extraction Prompt Strategy (High-Level)

The LLM extraction prompt includes:

1. **Role definition:** "You are an ERISA compliance specialist..."
2. **Task instruction:** "Extract provisions and classify by type..."
3. **Output schema:** Complete JSON schema (this document)
4. **Few-shot examples:** 2-3 sample provisions (eligibility, vesting, contribution)
5. **Extraction rules:**
   - Include full provision text (don't truncate)
   - Preserve section references from document
   - Extract entities (ages, percentages) accurately
   - Assign confidence score (0.0-1.0) for each provision
   - If uncertain about provision_type, use "other" and flag low confidence

**Full prompt template:** See `/design/modules/extraction/provision_extraction.md` (to be created in Phase 3)

### Validation Rules

After LLM extraction, automated validation checks:

**Required Field Validation:**
- ✅ `provision_id` is UUID format
- ✅ `provision_type` is from valid taxonomy
- ✅ `provision_text` is non-empty string
- ✅ `confidence_score` is 0.0-1.0

**Entity Validation:**
- ✅ `ages` are integers (21, 59.5, 65, etc.)
- ✅ `service_years` are positive floats
- ✅ `percentages` are 0.0-1.0 (not 0-100)
- ✅ `dates` are valid YYYY-MM-DD format

**Confidence Thresholds:**
- **High (≥0.9):** Auto-approve, no review needed
- **Medium (0.7-0.89):** Spot-check recommended
- **Low (<0.7):** Flag for mandatory human review

---

## Normalization Strategy (TBD in Phase 2)

**Question:** Should we pre-normalize provision text before semantic comparison, or rely on LLM to handle variations?

**Option A: Pre-normalization (Rule-Based)**
- Pros: Consistent input to LLM, potentially faster matching
- Cons: Hard to cover all edge cases, may introduce errors

**Option B: LLM-Native (No Pre-processing)**
- Pros: LLM already handles linguistic variation well
- Cons: Relies on model capability, harder to debug

**Option C: Hybrid (Extract Entities + Full Text)**
- Pros: Fast entity comparison (ages, percentages) + LLM for semantic nuance
- Cons: More complex pipeline

**Recommendation:** Start with Option B (LLM-native) in POC. If accuracy <70%, try Option C.

---

## Provision Extraction Workflow

```
1. Document Text → LLM Extraction Prompt
   Input: Full document text (or chunked sections)
   Prompt: "Extract all eligibility provisions from this plan document..."
   Output: Structured JSON array of provisions

2. Validate Extraction
   - Check required fields present (provision_type, provision_text)
   - Verify confidence_score is valid (0.0-1.0)
   - Flag low-confidence extractions for human review

3. Entity Extraction (Optional Enhancement)
   - Parse provision_text for ages, percentages, etc.
   - Store in extracted_entities
   - Use regex + LLM for complex cases (e.g., "three percent" → 0.03)

4. Store to Persistence Layer
   - Save to extracted/source_provisions.json (or target_provisions.json)
   - Link to source document via document_id

5. Ready for Semantic Mapping
   - Pass provisions to Reconciliation Module
```

---

## Design Decisions

### Decision 1: Provision Granularity
**Context:** How granular should provisions be? One provision per section, or split multi-part sections?

**Options:**
1. **Section-level:** One provision per document section (e.g., all of "Section 2.01")
   - Pros: Simple extraction, matches source document structure
   - Cons: May combine unrelated concepts (e.g., eligibility age + service in same section)

2. **Concept-level:** Split sections into atomic concepts (age separate from service)
   - Pros: More precise semantic matching, easier variance detection
   - Cons: Harder to extract, may lose document context

**Selected:** **Section-level for MVP** (simpler, validates semantic mapping capability). Post-MVP: Allow concept-level splitting for complex provisions.

**Rationale:** Market research shows manual reconciliation is section-by-section. Matching this workflow reduces user cognitive load.

---

### Decision 2: Normalized Text
**Context:** Should we store a cleaned/normalized version of provision_text?

**Selected:** **Optional field (nullable)** for Phase 2 experimentation.

**Rationale:**
- If LLM handles variation well (likely with Claude/GPT-5), normalization adds complexity with little benefit
- If POC shows normalization improves accuracy, we can add it later
- Storing both original and normalized preserves audit trail

---

### Decision 3: Extracted Entities
**Context:** Should we extract structured entities (ages, percentages) or rely purely on text comparison?

**Selected:** **Include extracted_entities** for hybrid comparison approach.

**Rationale:**
- Fast exact-match checks (if ages don't match, confidence should be lower)
- Enables future variance detection rules (e.g., "flag if ages differ by more than X years")
- Useful for UI display (highlight key values in review interface)
- Low implementation cost (LLMs can extract structured data reliably)

---

## Open Questions

1. **How many provisions per document?** Expect 50-150 for typical plan? (Affects performance, chunking strategy)
2. **Should we support nested provisions?** (E.g., eligibility with sub-provisions for age, service, employment status?)
3. **How to handle amendments?** Treat as separate provisions or merge into main provision text?
4. **Confidence threshold for extraction?** At what confidence do we auto-accept vs. flag for human review?

---

## Testing Strategy

**Unit Tests:**
- Validate JSON schema (all required fields present)
- Test entity extraction (ages, percentages parse correctly)
- Verify provision_type classification (sample texts → expected types)

**Integration Tests:**
- Extract provisions from sample Relius document → verify count and types
- Extract provisions from sample ASC document → verify count and types
- Compare extraction results from text_api vs vision_fallback (should produce similar provisions)

**User Testing:**
- Show extracted provisions to compliance expert → verify accuracy
- Measure: % of provisions correctly typed, % of entities correctly extracted

---

## References

- **Requirements:** [REQ-004 (Intermediate Representation)](../../requirements/functional_requirements.md#req-004-intermediate-representation)
- **Requirements:** [REQ-020 (Provision Extraction)](../../requirements/functional_requirements.md#req-020-provision-extraction)
- **System Architecture:** [/design/architecture/system_architecture.md](../architecture/system_architecture.md)
- **Next:** [Mapping Model](./mapping_model.md) (defines how provisions link source→target)

---

*Last Updated: 2025-10-17*
*Status: Phase 1 Draft - Ready for POC*
