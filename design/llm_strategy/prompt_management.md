# Prompt Management Architecture

## Overview

This document defines the architectural strategy for managing LLM prompts in compliance-gpt. Prompts are **externalized from code** and **version controlled** as first-class design artifacts requiring domain expert approval.

**Core Principle**: Prompts are the "business logic" of LLM-first applications. They encode domain expertise (ERISA/IRC compliance rules) and must be treated with the same rigor as code.

---

## Requirements Addressed

- **REQ-021**: Semantic provision mapping (prompts define matching criteria)
- **REQ-022**: Variance detection and classification (prompts define classification logic)
- **REQ-020**: Provision extraction (prompts define extraction boundaries)
- **CLAUDE.md Workflow**: "ALWAYS seek Sergio's approval before implementing new prompts"

---

## Design Principles

### 1. Externalization (No Hardcoded Prompts)

**Rule**: Prompts must never be hardcoded in Python strings.

**Rationale**:
- Prompts change frequently during development (A/B testing, quality iteration)
- Code reviews are for logic, not domain expertise
- Version control should track prompt evolution separately from code changes
- Domain experts (Sergio) review prompts, engineers review code

**Implementation**:
```python
# ❌ WRONG - Hardcoded prompt
def extract_provisions(document):
    prompt = "Extract provisions from this document..."
    return llm.complete(prompt)

# ✅ CORRECT - External prompt
def extract_provisions(document):
    prompt = load_prompt("provision_extraction_v3.txt")
    return llm.complete(prompt)
```

---

### 2. Approval Workflow (Collaborative Design)

**Process**:
```
1. Draft       → AI proposes prompt with rationale
2. Review      → Sergio reviews for regulatory accuracy
3. Iterate     → Refine based on domain expertise feedback
4. Approve     → Sergio approves final version
5. Externalize → Save to /prompts/ with version number
6. Implement   → Code loads prompt from file
7. Test        → Validate output quality (Red Team Sprint)
8. Version     → Commit with descriptive message
```

**Why This Matters**:
- Small prompt changes = large impact on output quality
- Domain expertise (ERISA/retirement plans) critical for prompt accuracy
- Sergio owns the regulatory requirements prompts must enforce
- Prevents "prompt drift" where AI makes unauthorized changes

**Example from Project History**:
- Oct 21: AI proposed negative example for AA semantic mapping
- Sergio reviewed and approved chain-of-thought prompting
- Result: False positive rate dropped from 92% to <5% (Age→State match prevented)

---

### 3. Versioning Strategy

**Naming Convention**:
```
{operation}_{version}.txt

Examples:
- provision_extraction_v1.txt
- provision_extraction_v2.txt
- provision_extraction_v3.txt  ← Current
- aa_extraction_v3.txt
- semantic_mapping_v1.txt
- aa_semantic_mapping_v1.txt
```

**Version Increment Rules**:
- **Major change** (different output schema, different task): New v1 with different name
- **Minor change** (add examples, refine instructions): Increment version (v1→v2→v3)
- **Bug fix** (typo, clarification): Increment version (document as bug fix in commit)

**Deprecation**:
- Old versions stay in `/prompts/` for reference
- Mark as DEPRECATED in `/prompts/README.md`
- Code should only load current version

**Git Commit Messages**:
```bash
# Good commit messages
git commit -m "Add negative example to aa_semantic_mapping_v1 to prevent question number false positives"
git commit -m "Provision extraction v2→v3: Exclude section headings from output"

# Bad commit messages
git commit -m "Update prompt"
git commit -m "Fix"
```

---

## Prompt Inventory

### Current Prompts (as of Oct 23, 2025)

| Prompt File | Version | Status | Purpose | Model | Input | Output |
|-------------|---------|--------|---------|-------|-------|--------|
| `provision_extraction_v3.txt` | v3 | ✅ Active (needs revision) | Extract BPD provisions | GPT-5-nano | PDF pages (vision) | JSON provisions |
| `aa_extraction_v3.txt` | v3 | ✅ Active (needs revision) | Extract AA elections | GPT-5-nano | PDF pages (vision) | JSON elections |
| `semantic_mapping_v1.txt` | v1 | ✅ Active | Compare BPD provisions | GPT-4.1 | 2 provisions + embedding similarity | Match assessment |
| `aa_semantic_mapping_v1.txt` | v1 | ✅ Active (has false positive fix) | Compare AA elections | GPT-5-Mini | 2 elections + embedding similarity | Match assessment |
| `provision_extraction_v1.txt` | v1 | ❌ Deprecated | Text-based extraction | GPT-4.1 | Text content | JSON provisions |
| `provision_extraction_v2.txt` | v2 | ❌ Deprecated | Vision without full text | GPT-5-nano | PDF pages | JSON provisions |
| `aa_extraction_v1.txt` | v1 | ❌ Deprecated (false positive bug) | Ambiguous blank detection | GPT-5-nano | PDF pages | JSON elections |
| `aa_extraction_v2.txt` | v2 | ❌ Deprecated (discriminated union) | Over-complex model | GPT-5-nano | PDF pages | JSON elections |

### Planned Prompts (Post-MVP)

| Prompt File | Purpose | Model | Priority |
|-------------|---------|-------|----------|
| `instance_mapping_v1.txt` | Compare merged provisions (BPD+AA) | GPT-4.1 | Medium |
| `variance_classification_v1.txt` | Classify Administrative/Design/Regulatory | GPT-4.1 | High |
| `confidence_calibration_v1.txt` | Score match confidence with reasoning | GPT-4.1 | High |
| `exception_generation_v1.txt` | Generate exception log entries from variances | GPT-4.1 | Medium |

---

## Prompt Architecture in Code

### Loading Mechanism

```python
import os
from pathlib import Path

class PromptLoader:
    """Load prompts from /prompts directory"""

    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

    @classmethod
    def load(cls, prompt_name: str) -> str:
        """
        Load a prompt file by name.

        Args:
            prompt_name: Filename (e.g., "provision_extraction_v3.txt")

        Returns:
            Prompt text content

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompt_path = cls.PROMPTS_DIR / prompt_name
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt not found: {prompt_name}. "
                f"Expected at {prompt_path}"
            )

        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    @classmethod
    def load_with_substitutions(cls, prompt_name: str, **kwargs) -> str:
        """
        Load prompt and substitute variables.

        Args:
            prompt_name: Filename
            **kwargs: Variables to substitute (e.g., {provision_text})

        Returns:
            Prompt with substitutions applied

        Example:
            prompt = PromptLoader.load_with_substitutions(
                "semantic_mapping_v1.txt",
                source_provision=source.provision_text,
                target_provision=target.provision_text,
                embedding_similarity=0.85
            )
        """
        template = cls.load(prompt_name)
        return template.format(**kwargs)
```

### Integration with Extraction/Mapping Classes

```python
class VisionExtractor:
    """Extracts provisions from PDFs using vision models"""

    PROVISION_PROMPT = "provision_extraction_v3.txt"
    AA_PROMPT = "aa_extraction_v3.txt"

    def extract_provisions(self, pdf_pages: List[Image]) -> List[Provision]:
        """Extract provisions from BPD pages"""
        prompt = PromptLoader.load(self.PROVISION_PROMPT)

        # Call vision API with external prompt
        response = openai.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": page.to_base64()}}
                    for page in pdf_pages
                ]}
            ]
        )

        return self._parse_provisions(response)

class SemanticMapper:
    """Maps provisions semantically across documents"""

    MAPPING_PROMPT = "semantic_mapping_v1.txt"

    async def verify_match(
        self,
        source: Provision,
        target: Provision,
        embedding_similarity: float
    ) -> MatchResult:
        """Verify if provisions match semantically"""
        prompt = PromptLoader.load_with_substitutions(
            self.MAPPING_PROMPT,
            source_provision=source.provision_text,
            target_provision=target.provision_text,
            embedding_similarity=f"{embedding_similarity:.0%}",
            source_section=source.section_context,
            target_section=target.section_context
        )

        response = await openai.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0  # Deterministic for consistency
        )

        return self._parse_match_result(response)
```

---

## Prompt Design Patterns

### Pattern 1: Structured Output with JSON Schema

**Problem**: LLM returns unstructured text, hard to parse.

**Solution**: Request JSON output with explicit schema.

**Example**:
```
You are extracting provisions from a plan document.

Output Format (JSON):
{
  "provisions": [
    {
      "id": "uuid",
      "provision_text": "full text",
      "section_context": "ARTICLE III - ELIGIBILITY (no section number)",
      "provision_type": "eligibility_rule | contribution_formula | definition | ...",
      "page_number": 42
    }
  ]
}

IMPORTANT: Return ONLY valid JSON, no markdown code fences.
```

---

### Pattern 2: Few-Shot Learning with Examples

**Problem**: LLM doesn't understand task from instructions alone.

**Solution**: Provide 2-3 concrete examples.

**Example**:
```
Task: Classify variance as Administrative, Design, or Regulatory.

Example 1:
Source: "Plan Administrator" (section 2.01)
Target: "Employer" (section 1.05)
Classification: ADMINISTRATIVE
Reasoning: Terminology change only, same legal entity, no substantive impact.

Example 2:
Source: "Eligibility: Age 21 and 1 year of service" (section 3.01)
Target: "Eligibility: Age 18 and 6 months of service" (section 4.02)
Classification: DESIGN
Reasoning: Different eligibility requirements, changes who can participate.

Example 3:
Source: "Catch-up contributions: $6,500" (section 5.03)
Target: "Catch-up contributions: $7,500" (section 6.01)
Classification: REGULATORY
Reasoning: IRS updated catch-up limit for 2024, required by law change.

Now classify this variance:
[Insert actual variance here]
```

---

### Pattern 3: Chain-of-Thought Reasoning

**Problem**: LLM jumps to conclusions without showing work.

**Solution**: Request step-by-step reasoning before answer.

**Example**:
```
Compare these two provisions and determine if they match semantically.

Step 1: Identify the core legal concept in each provision.
Step 2: Compare the concepts - are they addressing the same plan design element?
Step 3: Identify any differences (wording, structure, scope).
Step 4: Assess whether differences are substantive or cosmetic.
Step 5: Provide final assessment (MATCH / NO MATCH) with confidence score.

Provision A: [...]
Provision B: [...]

Think through each step:
```

**Why it works**: Forces LLM to decompose task, reduces hallucination.

---

### Pattern 4: Negative Examples (Prevent False Positives)

**Problem**: LLM over-matches due to superficial similarities.

**Solution**: Show examples of what NOT to match.

**Example from aa_semantic_mapping_v1.txt**:
```
CRITICAL: Do not match based on question numbers alone.

NEGATIVE EXAMPLE (DO NOT MATCH):
Source Q 1.04: "What is the minimum age for eligibility?"
Target Q 1.04: "What is the Employer's State for tax purposes?"
Embedding Similarity: 100% (due to "1.04" overlap)
Correct Assessment: NO MATCH (completely different topics)
Reasoning: Question numbers are provenance metadata, not semantic content.
```

**Result**: Prevented false positive (Age eligibility → State address at 92% confidence).

---

### Pattern 5: Confidence Calibration with Explicit Thresholds

**Problem**: LLM confidence scores don't match human judgment.

**Solution**: Define confidence thresholds with examples.

**Example**:
```
Provide a confidence score (0-100%) with this calibration:

90-100% (High Confidence):
- Provisions are semantically identical despite different wording
- Example: "Plan Administrator" vs "Employer" (same entity, different term)
- Evidence: Both reference same IRC sections, same responsibilities

70-89% (Medium Confidence):
- Provisions likely match but have minor ambiguities
- Example: "Eligibility: 1 year service" vs "Eligibility: 12 months service"
- Evidence: Semantically equivalent but need to verify if "year" = 12 months exactly

<70% (Low Confidence - ABSTAIN):
- Provisions may be related but substantive differences exist
- Provisions are on different topics
- Insufficient information to make determination
- When in doubt, abstain and flag for manual review

Your confidence score: [score]%
Your reasoning: [explain why this score, cite specific evidence]
```

---

## Prompt Testing Strategy

### Pre-Approval Testing (Before Sergio Review)

1. **Syntax Validation**: Ensure prompt loads without errors
2. **Output Format Check**: Verify JSON schema compliance
3. **Sample Document Test**: Run on 5-10 test provisions
4. **Edge Case Test**: Unusual formatting, missing data, ambiguous text
5. **Parse Results**: Ensure downstream code can process output

**Example Test Script**:
```python
def test_prompt_output():
    """Validate prompt produces parseable output"""
    prompt = PromptLoader.load("provision_extraction_v3.txt")

    # Test on sample page
    response = call_llm(prompt, sample_page)

    # Can we parse it?
    try:
        provisions = json.loads(response)
        assert "provisions" in provisions
        assert len(provisions["provisions"]) > 0
    except (json.JSONDecodeError, AssertionError) as e:
        raise ValueError(f"Prompt output not valid JSON: {e}")
```

---

### Post-Approval Validation (Red Team Sprint)

1. **Manual Sample Review**: Sergio reviews 20-40 random outputs
2. **False Positive Check**: Look for incorrect matches
3. **False Negative Check**: Look for missed matches
4. **Confidence Calibration**: Do 90% scores = 90% accuracy?
5. **Edge Case Performance**: How does prompt handle unusual documents?

**Exit Criteria** (from Red Team Sprint methodology):
- ✅ <5% false positive rate for matches
- ✅ <10% false negative rate for obvious matches
- ✅ Confidence scores correlate with human judgment (±10%)
- ✅ No hallucinated IRC/ERISA references
- ✅ JSON output parses 100% of the time

---

## Prompt Evolution Based on Quality Findings

### Example: Provision Extraction Prompt Evolution

**v1 → v2** (Oct 19, 2025): Text extraction → Vision extraction
- **Finding**: Complex tables and forms not parsed correctly
- **Change**: Switch from text API to vision API (GPT-5-nano)
- **Result**: Captures checkboxes, nested options, fill-ins

**v2 → v3** (Oct 21, 2025): Include full provision text
- **Finding**: Extraction only captured summaries, not full legal text
- **Change**: Add instruction "Include complete provision text, not summaries"
- **Result**: Provisions now include full legal language for comparison

**v3 → v4** (Pending, Oct 23, 2025): Exclude section headings
- **Finding**: Section headings extracted as provisions (e.g., "REQUIRED MINIMUM DISTRIBUTIONS" with no content)
- **Change**: Add explicit exclusion rule "Do not extract section headings without substantive content"
- **Expected Result**: Only extract provisions with actual legal language

---

### Example: AA Semantic Mapping Prompt Evolution

**v1 (Oct 21, 2025)**: Initial implementation with false positive
- **Finding**: Age eligibility (Q 1.04) matched State address (Q 1.04) at 92% confidence
- **Root Cause**: Embeddings polluted with question numbers → 100% similarity on "1.04"
- **Change**:
  1. Add negative example (Age ≠ State)
  2. Add chain-of-thought reasoning
  3. Add explicit warning about question numbers
- **Result**: Embedding similarity drops to 47%, LLM correctly rejects with 99% confidence

**Lesson Learned**: Prompt fixes can compensate for upstream data quality issues, but better to fix root cause (semantic fingerprinting).

---

## Integration with Semantic Fingerprinting

**Relationship**: Prompts and fingerprinting work together.

**Semantic Fingerprinting** (upstream):
- Strips section/question numbers BEFORE embedding
- Prevents false positives from structural artifacts
- See `/design/reconciliation/semantic_fingerprinting.md`

**Prompt Instructions** (downstream):
- Reinforces fingerprinting with explicit warnings
- Adds chain-of-thought reasoning for validation
- Provides negative examples to prevent LLM hallucination

**Example Flow**:
```
1. Provision extraction prompt → Captures provision with section context
2. Semantic fingerprinting → Strips section number, keeps "ELIGIBILITY"
3. Embedding generation → Vector based on clean semantic text
4. Candidate filtering → Finds provisions with similar concepts
5. LLM verification prompt → Confirms match with reasoning, warned not to over-rely on structural similarities
```

**Why Both Are Needed**:
- Fingerprinting prevents false positives at embedding layer (cheap, fast)
- Prompt instructions prevent false positives at LLM layer (expensive, slow, last line of defense)
- Defense in depth: If fingerprinting misses something, prompt catches it

---

## Prompt Maintenance Workflow

### When to Revise a Prompt

1. **Red Team Sprint finds quality issues** (high priority)
   - False positives/negatives above threshold
   - Confidence miscalibration
   - Hallucinated references

2. **New edge case discovered** (medium priority)
   - Unusual document format not handled
   - New vendor template structure
   - Ambiguous provision type

3. **Model upgrade** (low priority)
   - OpenAI releases GPT-6
   - Prompt may need adjustment for new model behavior

4. **Domain knowledge evolves** (low priority)
   - New IRS guidance affects classification
   - Market research identifies new provision pattern

### Revision Process

1. **Document finding** in Red Team Sprint report or issue tracker
2. **Propose change** with rationale and expected impact
3. **Draft revised prompt** with version increment
4. **Test on samples** to validate improvement
5. **Submit for Sergio's review** with before/after comparison
6. **Iterate based on feedback**
7. **Approve and deploy** once validated
8. **Update `/prompts/README.md`** with change log entry
9. **Commit with descriptive message**

---

## Open Questions / Future Decisions

1. **Should we implement prompt A/B testing?**
   - Run two prompt versions in parallel, compare accuracy
   - Useful for iterating without risking production quality
   - **Decision pending**: Post-MVP enhancement

2. **Should we track prompt performance metrics?**
   - Parse errors, confidence distribution, accuracy by prompt version
   - Would inform prompt optimization priorities
   - **Decision pending**: Implement basic metrics in MVP

3. **Should we use prompt templates with variables?**
   - Currently: Simple string substitution (`{variable}`)
   - Alternative: Jinja2 templates with logic
   - **Decision**: Keep simple for now, revisit if complexity grows

4. **Should we have different prompts for different vendors?**
   - Relius-specific prompt vs Ascensus-specific vs generic
   - Pro: Optimize for each vendor's document structure
   - Con: Maintenance burden (multiple prompts to keep in sync)
   - **Decision pending**: Try generic first, specialize only if necessary

5. **How to handle prompt context limits?**
   - Long documents may exceed prompt size limits
   - Chunking strategy needed
   - **Decision pending**: Design context management strategy

---

## Success Criteria

**For MVP:**
- ✅ All prompts externalized (no hardcoded strings)
- ✅ All prompts approved by Sergio before deployment
- ✅ Version controlled with descriptive commit messages
- ✅ Documented in `/prompts/README.md` with change log
- ✅ Tested in Red Team Sprint before production use
- ✅ Code uses PromptLoader pattern consistently

**For Production:**
- ✅ Prompt performance metrics tracked (parse errors, confidence distribution)
- ✅ A/B testing infrastructure for safe prompt iteration
- ✅ Automated testing suite for prompt outputs
- ✅ Prompt versioning strategy documented and enforced
- ✅ Regular review cycle (quarterly) to update prompts based on findings

---

## References

- `/prompts/README.md` - Implementation-level prompt documentation
- `/design/data_models/provisional_matching.md` - Prompts support three-level matching
- `/design/reconciliation/semantic_fingerprinting.md` - Upstream data cleaning before prompts
- `/design/data_models/variance_model.md` - Prompts implement classification logic
- `/CLAUDE.md` - Project context, prompt approval workflow

---

*Document Created: 2025-10-23*
*Author: Claude (with Sergio DuBois)*
*Status: Draft - pending Sergio's review*
*Next Review: Before extraction prompt revision (v3 → v4)*
