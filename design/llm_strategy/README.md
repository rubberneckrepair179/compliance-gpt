# LLM Strategy Documentation

This directory contains research and strategic decisions for LLM implementation in compliance-gpt, specifically focused on semantic provision mapping (REQ-021) and variance detection (REQ-022).

---

## Documents in This Directory

### 1. `llm_research_report.md` (Comprehensive Research)
**Purpose:** Full research analysis across all LLM strategy dimensions
**Length:** ~12,000 words with code samples and examples
**Use When:** Deep dive needed on any topic, architecture decisions, or implementation details

**Contents:**
- Model selection analysis (Claude vs GPT-4 vs GPT-4o)
- Semantic matching approaches (embeddings vs prompt-based vs hybrid)
- Confidence scoring and calibration methods
- Context management for long documents (RAG, chunking strategies)
- Accuracy benchmarks and industry comparisons
- Prompt engineering best practices with full template
- Cost optimization strategies
- Implementation roadmap (POC → MVP → Production)
- Sample code (confidence calibration, multi-signal scoring)

**Key Findings:**
- **Recommended Model:** Claude Sonnet 4.5 (200K context, 87% legal task accuracy in historical benchmarks; pricing as of Oct 2025 TBD)
- **Architecture:** Hybrid embeddings + LLM (95% cost reduction vs LLM-only)
- **Accuracy Target:** 70-90% automation achievable (aligned with industry benchmarks)
- **Cost:** ~$1.12 per document pair with batch processing estimate (vs $1,500-6,000 manual)

---

### 2. `decision_matrix.md` (Quick Reference)
**Purpose:** Condensed decision-making guide for technical implementation
**Length:** ~2,500 words, table-heavy format
**Use When:** Need quick answers, comparing options, or making tactical decisions

**Contents:**
- Model selection scorecards
- Architecture decision flow
- Confidence scoring formula
- Context management rules
- Prompt template (condensed)
- Cost breakdown
- Accuracy targets by provision type
- Technology stack (POC/MVP/Production)
- Implementation phases checklist
- Risk mitigation matrix
- Quick decision tree

**Use Cases:**
- "Which model should I use for this use case?"
- "What's the cost per document pair?"
- "What accuracy can I expect for vesting provisions?"
- "Should I use chunking or full context?"

---

### 3. `README.md` (This File)
**Purpose:** Navigation and context for the llm_strategy directory

---

## Quick Start Guide

### If You're Starting the POC:
1. Read: `decision_matrix.md` → "Technology Stack (POC)" section
2. Review: `llm_research_report.md` → "8.1 Phase 1: POC" + "Appendix A: Sample Prompt Template"
3. Implement: Hybrid architecture with Claude 3.5 Sonnet + text-embedding-3-large
4. Test: 5 document pairs, validate 70%+ accuracy, measure confidence calibration

### If You're Making an Architecture Decision:
1. Check: `decision_matrix.md` → "Quick Decision Tree"
2. Review: `llm_research_report.md` → Section 2 (Semantic Matching Approaches)
3. Compare: Trade-offs table for your specific use case

### If You're Optimizing Costs:
1. Read: `decision_matrix.md` → "Cost Optimization" section
2. Review: `llm_research_report.md` → Section 7 (detailed strategies)
3. Implement: Batch processing + embedding filter + tiered processing

### If You're Improving Accuracy:
1. Check: `decision_matrix.md` → "Accuracy Targets" by provision type
2. Review: `llm_research_report.md` → Section 5.5 (Accuracy Improvement Strategies)
3. Implement: Few-shot prompting (expect +15-25% accuracy gain)

---

## Key Recommendations Summary

| Decision Area | Recommendation | Rationale |
|---------------|---------------|-----------|
| **Primary Model** | Claude Sonnet 4.5 | 87% legal task accuracy (historical benchmark), 200K context, financial analysis proven |
| **Fallback Model** | GPT-5 | Compare current pricing/performance, native structured outputs |
| **Architecture** | Hybrid (embeddings → LLM) | 95% cost reduction, maintained accuracy |
| **Embeddings** | text-embedding-3-large | $0.13 per 1M tokens, proven for legal documents |
| **Confidence Strategy** | Multi-signal (5 inputs) | More robust than LLM self-assessment alone |
| **Thresholds** | 90/70/abstain | High (bulk approve), Medium (review), Low (expert) |
| **Context Management** | Full context <200 pages, hierarchical chunking >200 pages | Leverages Claude's 200K window |
| **Prompt Approach** | Few-shot (2-3 examples) | +15-25% accuracy vs zero-shot |
| **Cost Optimization** | Batch processing + embedding filter | 40% + 95% cost reductions compounded |
| **Vector DB** | FAISS (POC) → Milvus (production) | In-memory for testing, persistent for scale |

---

## Research Methodology

This research synthesized information from:

**Academic Sources (5):**
- Artificial Intelligence and Law journal (Feb 2025) - 87.13% accuracy (referred to as Claude 3 Opus in the study)
- Stanford HAI LegalBench - 162 legal reasoning tasks
- ArXiv papers on RAG, chunking, confidence calibration
- Journal of Legal Analysis - LLM hallucination rates in legal contexts

**Industry Reports (10+):**
- University of Chicago - LLM financial analysis study
- Codesphere - AI document comparison for compliance
- NVIDIA - LLM inference optimization
- Anthropic, OpenAI, Cleanlab technical documentation

**Internal Documents (4):**
- `/Users/sergio/sentientsergio/compliance-gpt/CLAUDE.md` - Project context, 70-90% automation target
- `/Users/sergio/sentientsergio/compliance-gpt/requirements/functional_requirements.md` - REQ-021, REQ-022, REQ-024
- `/Users/sergio/sentientsergio/compliance-gpt/research/market_research.pdf` - PlanPort benchmark, TPA tools analysis
- `/Users/sergio/sentientsergio/compliance-gpt/process/control_002_document_reconciliation.md` - Core workflow

**Research Date:** October 17, 2025
**Sources Analyzed:** 25+ unique sources across academic, industry, and technical categories

---

## How These Documents Align with Requirements

### REQ-021: Semantic Provision Mapping
**Addressed In:**
- `llm_research_report.md` Section 2: Semantic Matching Approaches
- `llm_research_report.md` Appendix A: Provision comparison prompt template
- `decision_matrix.md`: Hybrid architecture recommendation

**Key Findings:**
- Hybrid embeddings + LLM approach balances cost (95% reduction) and accuracy
- Few-shot prompting with 2-3 examples of substantive vs administrative differences
- Expected accuracy: 75-90% depending on provision type
- Claude Sonnet 4.5 chosen for superior legal reasoning (87% on legal tasks in historical benchmarks)

### REQ-022: Variance Detection and Classification
**Addressed In:**
- `llm_research_report.md` Appendix A: Classification logic (Administrative/Design/Regulatory)
- `decision_matrix.md`: Prompt template with classification instructions

**Key Findings:**
- Structured JSON output with variance type, impact level, legal_impact explanation
- Citation requirement prevents hallucinations (LLMs hallucinate 58% in legal contexts)
- Few-shot examples distinguish mandatory ("shall") vs discretionary ("may") language

### REQ-024: Confidence Scoring and Abstention
**Addressed In:**
- `llm_research_report.md` Section 3: Confidence Scoring & Calibration
- `llm_research_report.md` Appendix B: Python code for multi-signal confidence + isotonic calibration
- `decision_matrix.md`: Graduated thresholds (90/70/abstain)

**Key Findings:**
- Multi-signal approach (LLM 40%, embeddings 25%, validation 35%) more reliable than LLM alone
- Isotonic regression calibration trained on 100+ validated examples
- Monitor high-confidence accuracy; recalibrate if <85% acceptance
- Abstain (<70%) for complex provisions (e.g., distributions with conditional logic)

---

## Validation Plan

### POC Validation (Phase 1)
**Dataset:**
- 5 document pairs (Relius ↔ ASC, ASC ↔ ftwilliam, etc.)
- 50-100 manually validated provision mappings
- Mix of provision types (eligibility, vesting, contributions, distributions)

**Metrics:**
- Overall accuracy (target: 70%+)
- Accuracy by provision type (validate table in decision_matrix.md)
- Confidence calibration (do 90%+ predictions get 90%+ acceptance?)
- Cost per document pair (target: <$10 for POC, <$2 for production)

### MVP Validation (Phase 2)
**Dataset:**
- 20 document pairs with ground truth
- Cross-vendor validation (all major TPA platforms)
- User acceptance testing with compliance professionals

**Metrics:**
- 70-90% automation rate (human review time reduction)
- Confidence tier accuracy (high/medium/low)
- False positive rate (provisions marked as different when identical)
- False negative rate (provisions marked as identical when different - CRITICAL RISK)

---

## Open Questions for POC

These questions will be answered during POC implementation:

1. **Confidence Calibration:**
   - Do 90%+ confidence predictions actually get 90%+ user acceptance?
   - Is the multi-signal approach better than LLM self-assessment alone?
   - How many validated examples needed for isotonic regression to converge?

2. **Few-Shot Prompting:**
   - 2 vs 3 vs 5 examples - what's the optimal accuracy/cost tradeoff?
   - Which example types most effective (mandatory vs discretionary, missing provisions, new provisions)?

3. **Locked PDF Handling:**
   - What's the accuracy degradation from OCR vs native PDF text extraction?
   - Is GPT-4V or Claude 3.5 vision better for locked PDF extraction?
   - Cost implications (vision tokens more expensive)?

4. **Vendor-Specific Defaults:**
   - Can LLM infer vendor defaults (e.g., Relius auto-includes HCEs) from context?
   - Or do we need explicit default matrix provided in prompt?
   - Example: "Relius BPD v04 includes HCEs in safe harbor by default unless opted out"

5. **Cross-Reference Resolution:**
   - "As defined in Section 1.4" - auto-resolve or require manual section inclusion?
   - How often do cross-references break semantic comparison?

6. **Provision Type Classification:**
   - Can LLM auto-classify provision type (eligibility vs vesting vs contributions)?
   - Or should this be done via rule-based parsing (section numbers, headers)?

---

## Future Research Areas

### Post-MVP (Phase 3)

1. **Fine-Tuning Evaluation:**
   - Would fine-tuning Claude/GPT-4 on plan document corpus improve accuracy by 10%+?
   - Cost-benefit: Fine-tuning effort + maintenance vs prompt engineering
   - Open-source alternative: Fine-tune LLaMA 3 70B for cost reduction?

2. **Active Learning:**
   - Incorporate user feedback (accepted/rejected mappings) to improve prompts
   - RLHF (Reinforcement Learning from Human Feedback) for provision comparison task
   - Continuously update few-shot examples based on error patterns

3. **Multi-Document Comparison:**
   - Current scope: 1-to-1 comparison (source → target)
   - Future: 1-to-many (source → multiple vendor options)
   - Challenge: Combinatorial explosion (N × M comparisons)

4. **Regulatory Knowledge Updates:**
   - Keep LLM current with IRS regulation changes (SECURE 2.0, future cycles)
   - RAG with IRS guidance documents vs relying on model training cutoff
   - Frequency: Re-validate after each IRS cycle restatement

5. **Explainability Enhancements:**
   - Generate natural language explanation for compliance professionals
   - Visualize provision differences (side-by-side highlighting)
   - Audit trail: Why did LLM classify as "Design Change" vs "Administrative"?

---

## Usage Examples

### Example 1: Starting POC Implementation

```bash
# 1. Review decision matrix
cat decision_matrix.md | grep "Technology Stack (POC)"

# Output shows: Claude 3.5 Sonnet + text-embedding-3-large + LangChain + FAISS

# 2. Review full prompt template
cat llm_research_report.md | sed -n '/## Appendix A/,/## Appendix B/p'

# 3. Implement confidence scoring
cat llm_research_report.md | sed -n '/## Appendix B/,$p' > confidence_scoring.py
```

### Example 2: Making Model Selection Decision

```bash
# Review comparison matrix
cat decision_matrix.md | grep -A 10 "Model Selection Decision"

# Check cost implications
cat llm_research_report.md | grep -A 20 "1.1 Comparison Matrix"

# Decision: Claude 3.5 for legal accuracy, accept 20% higher cost
```

### Example 3: Debugging Low Accuracy

```bash
# Check expected accuracy by provision type
cat decision_matrix.md | grep -A 10 "Expected Performance by Provision Type"

# If "Distributions" provisions failing: Expected (70-80%), may need to lower threshold to 80%

# Review improvement strategies
cat llm_research_report.md | grep -A 30 "5.5 Accuracy Improvement Strategies"

# Implement: Few-shot prompting with distribution-specific examples
```

---

## Document Maintenance

**Update Frequency:**
- **After POC completion:** Update with actual accuracy metrics, calibration results
- **After MVP deployment:** Add production performance data, user feedback insights
- **Quarterly:** Review for new LLM releases (Claude 4, GPT-5), updated pricing
- **After each IRS cycle:** Validate regulatory knowledge is current

**Change Log:**
- 2025-10-17: Initial research report and decision matrix created
- (Future updates will be logged here)

---

## Related Documentation

**Parent Directory:** `/Users/sergio/sentientsergio/compliance-gpt/design/README.md`
**Requirements:** `/Users/sergio/sentientsergio/compliance-gpt/requirements/functional_requirements.md`
**Process Framework:** `/Users/sergio/sentientsergio/compliance-gpt/process/control_002_document_reconciliation.md`
**Market Research:** `/Users/sergio/sentientsergio/compliance-gpt/research/market_research.pdf`

---

## Contact

**Questions about LLM strategy?**
- Review `llm_research_report.md` for deep dives
- Check `decision_matrix.md` for quick answers
- Refer to source research (references section in report)

**Next Steps:**
1. ✅ Review decision matrix
2. ✅ Read prompt template (Appendix A)
3. ⬜ Set up Claude API + Instructor
4. ⬜ Implement hybrid embeddings + LLM workflow
5. ⬜ Test on 5 document pairs
6. ⬜ Validate confidence calibration
7. ⬜ Document findings, update this directory

---

*Last Updated: 2025-10-17*
*Maintained by: compliance-gpt project team*
