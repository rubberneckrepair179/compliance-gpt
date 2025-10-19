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

### provision_extraction_v1.txt
- **Status**: ✅ Approved (implemented in POC)
- **Purpose**: Extract provision boundaries from plan documents
- **Model**: OpenAI GPT-4.1
- **Input**: Raw PDF text (up to 20 pages)
- **Output**: JSON array of provisions with metadata
- **Performance**: 90-95% confidence on test documents

### semantic_mapping_v1.txt
- **Status**: 🟡 Pending approval
- **Purpose**: Compare provisions across different vendor documents
- **Model**: TBD (OpenAI GPT-4.1 or Claude Sonnet 4.5)
- **Input**: Two provision objects
- **Output**: Similarity score, variance classification, reasoning

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
| 2025-10-19 | provision_extraction | v1 | Initial implementation | POC baseline |
| 2025-10-19 | semantic_mapping | v1 | Draft pending | Next phase requirement |

---

*For questions about prompt design decisions, see `/design/llm_strategy/`*
