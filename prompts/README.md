# LLM Prompts Directory

This directory contains all LLM prompts used in the compliance-gpt project. Prompts are externalized from code to enable:

- **Version control** - Track changes and rationale over time
- **Collaborative review** - Domain expert approval before deployment
- **Easy iteration** - Modify prompts without changing Python code
- **Documentation** - Explain prompt design decisions

## Prompt Development Workflow

1. **Draft**: AI assistant proposes draft prompt with rationale
2. **Review**: Sergio reviews and provides feedback on regulatory accuracy
3. **Iterate**: Refine prompt based on domain expertise
4. **Approve**: Sergio approves final prompt version
5. **Externalize**: Save approved prompt to this directory
6. **Implement**: Python code loads prompt from file at runtime
7. **Version**: Track changes in git with descriptive commit messages

## Naming Convention

- Use descriptive names: `{task}_{version}.txt`
- Version incrementally: `v1`, `v2`, `v3`
- Include metadata header in each file

## Context vs Prompt

**Prompts** = Instructions/task definition for the LLM
**Context** = Domain knowledge injected into prompts (glossaries, rules, examples)

### Context Directory
```
/prompts/context/
├── term_glossary_v1.json         # Equivalent terminology mappings
├── regulatory_rules_v1.json      # IRC/ERISA requirements
├── variance_examples_v1.json     # Classification examples
└── provision_patterns_v1.json    # Common structural patterns
```

**Context management strategy:**
1. **Bootstrap**: Manual creation of key domain knowledge
2. **Learn**: Extract patterns from actual document corpus
3. **Synthesize**: Use LLM to generate glossaries from variations encountered
4. **Maintain**: Version control and update as project evolves
5. **Apply**: Programmatically inject relevant context into prompts at runtime

**POC Status:** Context directory not yet implemented (post-POC enhancement)

## Current Prompts

### provision_extraction_v2.txt
- **Status**: ❌ DEPRECATED - Extracted section headings without substantive content
- **Purpose**: Extract provision boundaries from Basic Plan Documents
- **Model**: OpenAI GPT-5-nano (vision)
- **Issue**: No classification of heading vs substantive, caused false positives in semantic matching
- **Superseded by**: provision_extraction_v3.txt

### provision_extraction_v3.txt
- **Status**: ❌ DEPRECATED - Still extracted section headings, lacked semantic fingerprinting support
- **Purpose**: Extract provision boundaries from Basic Plan Documents
- **Model**: OpenAI GPT-5-nano (vision)
- **Issue**: Added page_sequence but didn't exclude headings
- **Superseded by**: provision_extraction_v4.txt

### provision_extraction_v4.txt
- **Status**: ✅ APPROVED (Oct 24, 2025)
- **Purpose**: Extract provision boundaries from Basic Plan Documents with semantic fingerprinting support
- **Model**: OpenAI GPT-5-nano (vision)
- **Input**: PDF pages as images
- **Output**: JSON array of provisions with full text
- **Key Changes from v3**:
  - Add provision_classification (heading vs substantive) - ONLY extract substantive
  - Add semantic fingerprinting guidance (question numbers are provenance only)
  - Enhanced provision_type categorization for downstream filtering
  - Explicit rules to skip section headings, TOC entries, page headers
- **Expected Impact**: Eliminate false positives from section heading matches

### aa_extraction_v1.txt
- **Status**: ❌ DEPRECATED - Had false positive bug (blank template misidentified as completed)
- **Purpose**: Extract election questions from Adoption Agreements
- **Model**: OpenAI GPT-5-nano (vision)
- **Issue**: Ambiguous value field, no clear rules for blank vs completed elections
- **Superseded by**: aa_extraction_v2.txt

### aa_extraction_v2.txt
- **Status**: ❌ DEPRECATED - No semantic fingerprinting guidance
- **Purpose**: Extract election questions from Adoption Agreements with discriminated union model
- **Model**: OpenAI GPT-5-nano (vision)
- **Issue**: No guidance that question numbers are provenance only
- **Superseded by**: aa_extraction_v3.txt

### aa_extraction_v3.txt
- **Status**: ❌ DEPRECATED - Lacked explicit semantic fingerprinting warnings
- **Purpose**: Extract election questions from Adoption Agreements
- **Model**: OpenAI GPT-5-nano (vision)
- **Issue**: Question number embedding pollution caused false positives (Age Q 1.04 → State Q 4.01)
- **Superseded by**: aa_extraction_v4.txt

### aa_extraction_v4.txt
- **Status**: ✅ APPROVED (Oct 24, 2025)
- **Purpose**: Extract election questions from Adoption Agreements with semantic fingerprinting
- **Model**: OpenAI GPT-5-nano (vision)
- **Input**: PDF pages as images
- **Output**: JSON array of elections with kind-based structure (text, single_select, multi_select)
- **Key Features**:
  - Discriminated union by "kind" field
  - Clear status triage: unanswered/answered/ambiguous/conflict
  - Nested fill-ins within options
  - Provenance tracking (page, question_number)
  - Confidence scoring
- **Key Changes from v3**:
  - Add explicit semantic fingerprinting context section
  - Emphasize question_number is PROVENANCE ONLY (excluded from embeddings)
  - Add examples of false positive prevention (Age ≠ State)
  - Reinforce focus on semantic content (question_text, option_text)
- **Expected Impact**: Eliminate embedding pollution false positives

### semantic_mapping_v1.txt
- **Status**: ✅ Approved (implemented in POC)
- **Purpose**: Compare provisions across different vendor documents
- **Model**: OpenAI GPT-5-Mini
- **Input**: Two provision objects with embedding similarity score
- **Output**: Similarity assessment, variance classification, reasoning
- **Performance**: 82 matches found (19.3%), 94% high confidence (≥90%)

## Prompt Engineering Guidelines

### Domain Requirements
- **Regulatory accuracy** - Must not hallucinate IRC/ERISA references
- **Cross-vendor compatibility** - Handle different document formats (Relius, ASC, ftwilliam)
- **Semantic understanding** - Match provisions by meaning, not keywords
- **Confidence calibration** - Abstain when uncertain (< 70% confidence)

### Technical Requirements
- **Structured output** - Always request JSON for downstream processing
- **Error handling** - Include fallback instructions for edge cases
- **Token efficiency** - Balance detail with cost (target <50K tokens input)
- **Reproducibility** - Use temperature=0 when possible for deterministic results

### Testing
- Test each prompt version on sample documents before approval
- Compare outputs across model providers (OpenAI vs Anthropic)
- Validate JSON parsing and schema compliance
- Measure confidence score accuracy against human review

## Modification History

| Date | Prompt | Version | Change | Rationale |
|------|--------|---------|--------|-----------|
| 2025-10-19 | provision_extraction | v2 | Vision-based extraction with full text | POC implementation |
| 2025-10-19 | provision_extraction | v3 | Add page_sequence for deterministic IDs | Fix ID generation reliability |
| 2025-10-24 | provision_extraction | v4 | Add heading classification, semantic fingerprinting support | Red Team finding: section headings matched to provisions |
| 2025-10-19 | semantic_mapping | v1 | Hybrid embeddings + LLM verification | POC implementation |
| 2025-10-20 | aa_extraction | v1 | Initial AA extraction (DEPRECATED) | False positive bug on blank templates |
| 2025-10-20 | aa_extraction | v2 | Discriminated union model | Advisor's model: kind-based structure with status triage |
| 2025-10-21 | aa_extraction | v3 | Add page_sequence, refine status triage | Consistency with provision extraction |
| 2025-10-24 | aa_extraction | v4 | Add semantic fingerprinting context | Red Team finding: question number embedding pollution (Age→State false positive) |

---

*For questions about prompt design decisions, see `/design/llm_strategy/`*
