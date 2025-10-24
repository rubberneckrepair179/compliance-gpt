# Semantic Fingerprinting Strategy

## Overview

**Semantic fingerprinting** is the process of extracting "semantically pure" text from provisions before generating embeddings. It strips structural artifacts (section numbers, question numbers, page references) that pollute similarity measurements while preserving meaningful legal content.

**The Problem**: Including non-semantic text in embeddings causes unrelated provisions to appear similar.

**Example**:
- "Q 3.01: Minimum age for eligibility" embedding
- "Q 3.01: Employer's State for tax purposes" embedding
- **Cosine similarity**: 100% (due to "3.01" overlap)
- **Semantic similarity**: 0% (completely different topics)

**The Solution**: Strip "3.01" before embedding, keep only "minimum age eligibility" and "employer state tax purposes". Now cosine similarity correctly shows low similarity (~10-20%).

---

## Requirements Addressed

- **REQ-021**: Semantic provision mapping (requires accurate similarity measurement)
- **REQ-024**: Confidence scoring (depends on embedding quality)
- **Red Team Finding (Oct 21)**: False positive - Age eligibility matched State address due to question number pollution

---

## Core Principle

> **"If we include non-semantics in the string we are going to skew cosine similarity"**
> — Research paper on semantic matching, Oct 21, 2025

**Corollary**: Embeddings must capture **what the provision means**, not **where it appears** or **how it's numbered**.

---

## What to Include (Semantic Content)

### 1. Legal Concepts and Terms

**Include**: Words that convey meaning about plan operation.

**Examples**:
- Eligibility, vesting, contribution, distribution, forfeiture
- Participant, employee, beneficiary, employer, administrator
- Safe harbor, QACA, EACA, top-heavy, highly compensated
- Matching, profit sharing, elective deferral, catch-up

**Why**: These words identify what the provision does and who it affects.

---

### 2. Regulatory References

**Include**: IRC sections, Code sections, ERISA sections, Treasury Regulations.

**Examples**:
- IRC §410(a)
- Code §401(k)(3)
- ERISA §404(c)
- Treas. Reg. §1.401(k)-1(e)
- Rev. Proc. 2017-41

**Why**: Regulatory references indicate which legal requirements the provision addresses, making semantically related provisions more similar.

**Important**: These must be ACTUAL references in the provision text, not hallucinated.

---

### 3. Plan Design Parameters (Types, not Values)

**Include**: Categories of parameters, not specific values.

**Examples**:
- "service requirement" (not "1 year" or "12 months")
- "age threshold" (not "21" or "18")
- "vesting schedule" (not "3-year cliff" or "6-year graded")
- "match formula" (not "50% of first 6%")

**Why**: BPD templates use placeholders ("as elected in AA"). We want templates with similar STRUCTURE to match, even if elected values differ.

**Exception**: For merged instances (BPD+AA combined), include actual values.

---

### 4. Section Context (Heading Text, Not Numbers)

**Include**: Section/article heading text that provides semantic context.

**Examples**:
- "ARTICLE III - ELIGIBILITY" → Include "ELIGIBILITY"
- "SECTION 2.01 - VESTING SCHEDULE" → Include "VESTING SCHEDULE"
- "PART A - SAFE HARBOR CONTRIBUTIONS" → Include "SAFE HARBOR CONTRIBUTIONS"

**Exclude**: Section numbers (III, 2.01, A)

**Why**: Heading text helps disambiguate provisions. "The minimum age is 21" could mean eligibility age, retirement age, or distribution age. Context clarifies which.

**Implementation**:
```python
def extract_section_context(section_heading: str) -> str:
    """Strip section numbers, keep semantic heading"""
    # Remove "ARTICLE III -" but keep "ELIGIBILITY"
    # Remove "Section 2.01:" but keep "Vesting Schedule"
    import re
    # Pattern: Optional prefix (ARTICLE/SECTION/PART) + number/letter + separator
    context = re.sub(
        r'^(?:ARTICLE|SECTION|PART)\s+[IVX\d.]+\s*[-–:]\s*',
        '',
        section_heading,
        flags=re.IGNORECASE
    )
    return context.strip()

# Examples:
extract_section_context("ARTICLE III - ELIGIBILITY")
# Returns: "ELIGIBILITY"

extract_section_context("Section 2.01: Vesting Schedule")
# Returns: "Vesting Schedule"
```

---

## What to Exclude (Structural Artifacts)

### 1. Section and Subsection Numbers

**Exclude**:
- Section numbers: "Section 3.01", "Article IV", "2.1(a)(ii)"
- Subsection markers: "(a)", "(b)(1)", "(iii)"
- Cross-references to sections: "See Section 5.02", "pursuant to Article VII"

**Why**: Section numbers are document-specific. Relius Section 3.01 ≠ Ascensus Section 3.01. Matching on section numbers causes false positives across vendors.

**Example**:
```
# BEFORE fingerprinting
"Section 3.01: An Employee shall be eligible after completing 1 year of service per Section 2.05."

# AFTER fingerprinting
"employee eligible completing service"
```

---

### 2. Question Numbers (Adoption Agreements)

**Exclude**:
- Question labels: "Q 3.01", "Question 4.02", "Election 5(a)"
- Item numbers: "Item 7", "Line 12"

**Why**: Question numbers are provenance metadata. Different vendors use different numbering. Q 3.01 in Relius ≠ Q 3.01 in Ascensus.

**Critical**: This was the root cause of Oct 21 false positive (Age Q 1.04 → State Q 4.01 matched due to "1.04" and "4.01" digit overlap).

**Example**:
```
# BEFORE fingerprinting
"Q 3.01: What is the minimum age for eligibility? (a) 18 (b) 21 (c) 25"

# AFTER fingerprinting
"minimum age eligibility"
```

---

### 3. Page Numbers and References

**Exclude**:
- Page numbers: "Page 42", "pg. 7"
- Continued on page: "Continued on page 43"
- See page references: "See page 15 for details"

**Why**: Page numbers are document formatting, not legal content. Same provision may appear on different pages in different documents.

---

### 4. Vendor Branding and Metadata

**Exclude**:
- Copyright notices: "©2020 Ascensus, LLC"
- Vendor names: "Relius", "ASC", "ftwilliam", "DATAIR"
- Document IDs: "Form #3000 (Rev. 6/2020)"
- Watermarks: "SAMPLE", "DRAFT", "CONFIDENTIAL"

**Why**: Vendor metadata is irrelevant to legal meaning. We're comparing provisions semantically, not identifying vendor.

---

### 5. Formatting Markers

**Exclude**:
- Headers/footers
- Blank lines, excessive whitespace
- Bullets, numbering (•, 1., a., i.)
- Table borders (ASCII art like "| --- |")

**Why**: Formatting varies across documents. Same provision may be bulleted in one doc, numbered in another.

---

### 6. Instruction Text (Adoption Agreements)

**Exclude**:
- "Complete this section if applicable"
- "Check all that apply"
- "Enter the plan name here: _______"
- "See instructions on page 5"
- "Do not write in this box"

**Why**: Instructions are for preparer, not plan provisions. They don't affect plan operation.

---

## Semantic Fingerprinting Algorithm

### Implementation

```python
import re
from dataclasses import dataclass

@dataclass
class SemanticFingerprint:
    """Clean semantic text suitable for embedding"""
    clean_text: str
    provision_type_tags: List[str]  # ["eligibility", "service_based"]
    regulatory_refs: List[str]       # ["IRC §410(a)"]
    original_context: str            # Full original text (for audit)

def create_semantic_fingerprint(provision) -> SemanticFingerprint:
    """
    Extract semantically pure text from provision for embedding.

    Implements the "semantic content only" principle:
    - Strip structural artifacts (section numbers, question numbers)
    - Preserve legal concepts, regulatory references
    - Include section context (heading text, not numbers)
    - Normalize whitespace and casing
    """
    text = provision.provision_text

    # Step 1: Include section context (heading without numbers)
    if provision.section_context:
        context_semantic = extract_section_context(provision.section_context)
        text = f"{context_semantic}: {text}"

    # Step 2: Remove section/question numbers
    # Pattern: "Section X.XX" or "Q X.XX" or "Article IV"
    text = re.sub(r'\b(?:Section|Article|Question|Q\.?|Item|Line)\s+[\dIVX.()]+\b', '', text, flags=re.IGNORECASE)

    # Step 3: Remove page references
    text = re.sub(r'\b(?:page|pg\.?)\s+\d+\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'continued on page \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'see page \d+ for', '', text, flags=re.IGNORECASE)

    # Step 4: Remove vendor branding
    text = re.sub(r'©\s*\d{4}\s+[\w\s,]+(?:LLC|Inc\.?)?', '', text)  # ©2020 Ascensus, LLC
    text = re.sub(r'\b(?:Relius|Ascensus|ASC|ftwilliam|DATAIR)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Form #\d+\s*\(Rev\.\s+\d+/\d+\)', '', text)  # Form #3000 (Rev. 6/2020)

    # Step 5: Remove watermarks and formatting
    text = re.sub(r'\b(?:SAMPLE|DRAFT|CONFIDENTIAL)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[-–—]{3,}', '', text)  # Em dashes used as separators
    text = re.sub(r'[│┤├┼┴┬]', '', text)  # Table borders

    # Step 6: Remove instruction text patterns
    instruction_patterns = [
        r'complete this section if',
        r'check all that apply',
        r'enter the .+ here:?\s*[_]+',
        r'see instructions',
        r'do not write in this box',
    ]
    for pattern in instruction_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Step 7: For BPD templates, normalize election placeholders
    if provision.manifestation.type == "BPD_TEMPLATE":
        # Replace "as elected in Adoption Agreement Question 3.01" with parameter type
        for ref in provision.manifestation.bpd_template.election_references:
            text = text.replace(ref.placeholder_text, f"[{ref.parameter_type}]")

    # Step 8: Normalize whitespace and casing
    text = ' '.join(text.split())  # Collapse whitespace
    text = text.lower()  # Lowercase for embedding consistency

    # Step 9: Extract regulatory references (for separate tracking)
    regulatory_refs = extract_regulatory_refs(text)

    # Step 10: Add provision type tags
    provision_type_tags = [provision.provision_type]
    if provision.manifestation.type == "BPD_TEMPLATE":
        provision_type_tags.append("template")
    elif provision.manifestation.type == "AA_ELECTION":
        provision_type_tags.append("election")

    return SemanticFingerprint(
        clean_text=text,
        provision_type_tags=provision_type_tags,
        regulatory_refs=regulatory_refs,
        original_context=provision.provision_text
    )

def extract_regulatory_refs(text: str) -> List[str]:
    """Extract IRC/ERISA/Treas.Reg. references from text"""
    refs = []

    # IRC §410(a)
    refs.extend(re.findall(r'IRC\s*§\s*[\d.]+(?:\([a-z]\))?', text, re.IGNORECASE))

    # Code §401(k)(3)
    refs.extend(re.findall(r'Code\s*§\s*[\d.]+(?:\([a-z]\)(?:\(\d+\))?)?', text, re.IGNORECASE))

    # ERISA §404(c)
    refs.extend(re.findall(r'ERISA\s*§\s*[\d.]+(?:\([a-z]\))?', text, re.IGNORECASE))

    # Treas. Reg. §1.401(k)-1(e)
    refs.extend(re.findall(r'Treas\.?\s*Reg\.?\s*§\s*[\d.]+\([a-z]\)-\d+(?:\([a-z]\))?', text, re.IGNORECASE))

    return list(set(refs))  # Deduplicate
```

---

## Fingerprinting Examples

### Example 1: BPD Provision (Eligibility Rule)

**Original Text**:
```
Section 3.01: ELIGIBILITY TO PARTICIPATE

An Employee shall be eligible to participate in the Plan upon
completing the service requirement as elected in Adoption Agreement
Question 4.02. See Section 1.07 for definition of "Employee."

©2020 Ascensus, LLC
Page 42
```

**Semantic Fingerprint**:
```
eligibility participate employee eligible plan completing [service_requirement] employee
```

**What was stripped**:
- "Section 3.01:" (section number)
- "as elected in Adoption Agreement Question 4.02" → "[service_requirement]" (parameter type)
- "See Section 1.07" (cross-reference)
- "©2020 Ascensus, LLC" (vendor branding)
- "Page 42" (page number)

**What was preserved**:
- "ELIGIBILITY" (section context)
- "Employee", "eligible", "participate", "Plan" (legal concepts)
- "[service_requirement]" (parameter type for template)

---

### Example 2: AA Election (Service Requirement)

**Original Text**:
```
Q 3.01: Eligibility Service Requirement

What is the minimum service requirement for plan participation?

☐ (a) 1 year of service (12 months, 1,000 hours)
☐ (b) 2 years of service (24 months, 1,000 hours)
☑ (c) Immediate (no service requirement)

Complete this section based on plan sponsor elections.
See instructions on page 5.
```

**Semantic Fingerprint**:
```
eligibility service requirement minimum service requirement plan participation year service months hours years service months hours immediate service requirement
```

**What was stripped**:
- "Q 3.01:" (question number)
- "☐", "☑" (checkboxes - structural)
- "(a)", "(b)", "(c)" (option labels - structural)
- "Complete this section..." (instruction text)
- "See instructions on page 5" (cross-reference)

**What was preserved**:
- "eligibility service requirement" (question semantic)
- "1 year", "12 months", "2 years", "immediate" (option semantics)
- "plan participation" (legal concept)

**Note**: For AA elections, we preserve the option VALUES because we're comparing election STRUCTURES, not matching template placeholders.

---

### Example 3: Definition Provision

**Original Text**:
```
Section 1.07: "Employee"

Means any individual who is employed by the Employer, including Leased
Employees as defined in Code §414(n), but excluding individuals described
in Code §414(q) as Highly Compensated Employees unless the Employer elects
to cover such individuals pursuant to Adoption Agreement Section 2.03.

[Relius Document #1234 (Rev. 3/2020)] SAMPLE
```

**Semantic Fingerprint**:
```
employee individual employed employer including leased employees excluding individuals highly compensated employees employer elects cover individuals code §414(n) code §414(q)
```

**What was stripped**:
- "Section 1.07:" (section number)
- "pursuant to Adoption Agreement Section 2.03" (cross-reference)
- "[Relius Document #1234 (Rev. 3/2020)]" (vendor metadata)
- "SAMPLE" (watermark)
- Quote marks around "Employee" (formatting)

**What was preserved**:
- "employee", "employer", "leased employees", "highly compensated employees" (legal terms)
- "Code §414(n)", "Code §414(q)" (regulatory references)
- Complete definition logic

**Regulatory refs extracted separately**: ["Code §414(n)", "Code §414(q)"]

---

## Integration with Embedding Generation

### Workflow

```
1. Provision Extraction (vision prompt)
   ↓
2. Semantic Fingerprinting (this module)
   ↓
3. Embedding Generation (OpenAI API)
   ↓
4. Candidate Filtering (cosine similarity)
   ↓
5. LLM Verification (semantic mapping prompt)
```

### Embedding API Call

```python
def generate_embeddings_batch(provisions: List[Provision]) -> List[np.ndarray]:
    """Generate embeddings from semantic fingerprints"""

    # Step 1: Create fingerprints
    fingerprints = [create_semantic_fingerprint(p) for p in provisions]

    # Step 2: Batch API call (100 at a time)
    embeddings = []
    for i in range(0, len(fingerprints), 100):
        batch = fingerprints[i:i+100]

        # Send clean text to embedding API
        response = openai.embeddings.create(
            input=[fp.clean_text for fp in batch],
            model="text-embedding-3-small"
        )

        embeddings.extend([np.array(e.embedding) for e in response.data])

    return embeddings
```

---

## Quality Validation

### How to Test Fingerprinting

**Test Case 1: Unrelated Provisions Should Have Low Similarity**

```python
# Two completely different provisions
age_provision = Provision(
    provision_text="Q 1.04: What is the minimum age for eligibility? (a) 18 (b) 21",
    section_context="ELIGIBILITY"
)

state_provision = Provision(
    provision_text="Q 1.04: What is the Employer's State for tax purposes? (a) CA (b) NY",
    section_context="EMPLOYER INFORMATION"
)

# Before fingerprinting (WRONG)
fp_age_raw = "Q 1.04: What is the minimum age for eligibility? (a) 18 (b) 21"
fp_state_raw = "Q 1.04: What is the Employer's State for tax purposes? (a) CA (b) NY"
similarity_raw = cosine_similarity(embed(fp_age_raw), embed(fp_state_raw))
assert similarity_raw > 0.80  # HIGH (WRONG - due to "Q 1.04" overlap)

# After fingerprinting (CORRECT)
fp_age = create_semantic_fingerprint(age_provision)  # "eligibility minimum age"
fp_state = create_semantic_fingerprint(state_provision)  # "employer state tax purposes"
similarity_clean = cosine_similarity(embed(fp_age.clean_text), embed(fp_state.clean_text))
assert similarity_clean < 0.30  # LOW (CORRECT - different topics)
```

**Test Case 2: Semantically Equivalent Provisions Should Have High Similarity**

```python
# Same concept, different wording
relius_provision = Provision(
    provision_text="Section 3.01: An Employee is eligible after 1 year of service.",
    section_context="ARTICLE III - ELIGIBILITY"
)

ascensus_provision = Provision(
    provision_text="Section 1.7: Eligibility commences upon 12 months of service.",
    section_context="PART A - PARTICIPATION"
)

# After fingerprinting
fp_relius = create_semantic_fingerprint(relius_provision)
# "eligibility employee eligible year service"

fp_ascensus = create_semantic_fingerprint(ascensus_provision)
# "participation eligibility commences months service"

similarity = cosine_similarity(embed(fp_relius.clean_text), embed(fp_ascensus.clean_text))
assert similarity > 0.70  # HIGH (CORRECT - same concept)
```

**Test Case 3: Cross-Vendor Provisions Should Match on Semantics, Not Structure**

```python
# Relius format
relius = Provision(
    provision_text="Section 5.03: Catch-up contributions per IRC §414(v) are permitted for participants age 50+.",
    section_context="ARTICLE V - CONTRIBUTIONS"
)

# Ascensus format
ascensus = Provision(
    provision_text="1.15 'Catch-Up Contribution' means elective deferrals permitted under Code §414(v) for eligible participants.",
    section_context="DEFINITIONS"
)

# After fingerprinting
fp_relius = create_semantic_fingerprint(relius)
# "contributions catch-up contributions permitted participants age irc §414(v)"

fp_ascensus = create_semantic_fingerprint(ascensus)
# "definitions catch-up contribution elective deferrals permitted eligible participants code §414(v)"

similarity = cosine_similarity(embed(fp_relius.clean_text), embed(fp_ascensus.clean_text))
assert similarity > 0.75  # HIGH despite different structure, section numbers, article placement
```

---

## Red Team Sprint Validation

### Exit Criteria for Fingerprinting Quality

1. **Unrelated provisions**: <30% embedding similarity
   - Sample 20 pairs of completely different topics
   - Measure embedding similarity after fingerprinting
   - Target: <30% average similarity

2. **Equivalent provisions**: >70% embedding similarity
   - Sample 20 pairs of semantically equivalent provisions (cross-vendor)
   - Measure embedding similarity after fingerprinting
   - Target: >70% average similarity

3. **No false positives from structural overlap**
   - Test known false positive cases (Age Q 1.04 vs State Q 4.01)
   - Verify embedding similarity <30% after fingerprinting

4. **Regulatory references preserved**
   - Verify all IRC/Code/ERISA refs extracted correctly
   - No hallucinated references introduced

5. **Section context included correctly**
   - Verify section heading text included (e.g., "ELIGIBILITY")
   - Verify section numbers stripped (e.g., "ARTICLE III" removed)

---

## Performance Considerations

### Caching Fingerprints

**Problem**: Fingerprinting is CPU-intensive (regex operations).

**Solution**: Cache fingerprints with provisions in database.

```python
# SQLite schema
CREATE TABLE provision_fingerprints (
    provision_id TEXT PRIMARY KEY,
    clean_text TEXT NOT NULL,
    provision_type_tags TEXT,  -- JSON array
    regulatory_refs TEXT,      -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# On first extraction
fingerprint = create_semantic_fingerprint(provision)
db.execute(
    "INSERT INTO provision_fingerprints (provision_id, clean_text, provision_type_tags, regulatory_refs) VALUES (?, ?, ?, ?)",
    (provision.id, fingerprint.clean_text, json.dumps(fingerprint.provision_type_tags), json.dumps(fingerprint.regulatory_refs))
)

# On subsequent runs
cached = db.execute("SELECT * FROM provision_fingerprints WHERE provision_id = ?", (provision.id,)).fetchone()
if cached:
    return SemanticFingerprint(
        clean_text=cached['clean_text'],
        provision_type_tags=json.loads(cached['provision_type_tags']),
        regulatory_refs=json.loads(cached['regulatory_refs']),
        original_context=provision.provision_text
    )
```

---

## Open Questions / Future Enhancements

1. **Should we use NLP lemmatization?**
   - "employee" vs "employees" vs "employment" → normalize to "employ"
   - Pro: Better semantic matching
   - Con: Adds dependency (spaCy, NLTK)
   - **Decision pending**: Test if embeddings already handle this

2. **Should we weight certain terms higher?**
   - Regulatory references (IRC §410(a)) more important than common words ("the", "and")
   - **Decision pending**: Embedding models may already do this (TF-IDF-like weighting)

3. **Should we handle acronym expansion?**
   - "ADP" → "Actual Deferral Percentage"
   - "HCE" → "Highly Compensated Employee"
   - Pro: Improves cross-vendor matching (some vendors use acronyms, others spell out)
   - Con: Requires glossary maintenance
   - **Decision pending**: Test if needed

4. **Should we include numerical values in fingerprints?**
   - Currently: Strip "21" from "age 21"
   - Alternative: Keep numbers for instance matching (merged provisions)
   - **Decision**: Keep current approach for templates, reconsider for instances

---

## Success Criteria

**For MVP:**
- ✅ False positive rate <5% (unrelated provisions don't match due to structural overlap)
- ✅ Equivalent provision matching >70% (cross-vendor provisions match semantically)
- ✅ No question/section number pollution in embeddings
- ✅ All regulatory references preserved
- ✅ Section context included correctly

**For Production:**
- ✅ Fingerprinting cached in database (instant on subsequent runs)
- ✅ Automated tests validate fingerprinting quality
- ✅ Red Team Sprint validates on new document types
- ✅ Performance <1 second for 1,000 provisions

---

## References

- `/design/data_models/provisional_matching.md` - Fingerprinting supports three-level matching
- `/design/llm_strategy/prompt_management.md` - Prompts reinforce fingerprinting with warnings
- `/design/performance_optimization.md` - Caching strategy for fingerprints
- Research paper (Oct 21, 2025): "If we include non-semantics in the string we are going to skew cosine similarity"
- Red Team finding (Oct 21, 2025): Age Q 1.04 → State Q 4.01 false positive due to embedding pollution

---

*Document Created: 2025-10-23*
*Author: Claude (with Sergio DuBois)*
*Status: Draft - pending Sergio's review*
*Next Review: Before extraction prompt revision and re-extraction*
