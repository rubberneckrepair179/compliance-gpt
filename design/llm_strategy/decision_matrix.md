# LLM Strategy Decision Matrix
## Quick Reference for Technical Implementation

**Last Updated:** October 17, 2025
**Full Report:** See `llm_research_report.md`

---

## Model Selection Decision

### ✅ Recommended: Claude Sonnet 4.5

| Decision Factor | Score | Notes |
|----------------|-------|-------|
| **Legal Reasoning** | ⭐⭐⭐⭐⭐ | 87% on legal tasks (historical benchmark), proven case law analysis |
| **Context Window** | ⭐⭐⭐⭐⭐ | 200K tokens (56% more than GPT-5 historical) |
| **Financial Analysis** | ⭐⭐⭐⭐⭐ | Outperformed human analysts (60% vs 53% in historical study) |
| **Cost** | ⭐⭐⭐ | Pricing as of Oct 2025 TBD |
| **Speed** | ⭐⭐⭐ | 36% slower than GPT-5 (historical benchmarks) |
| **Structured Output** | ⭐⭐⭐⭐ | Via tool calling (requires setup) |

**Pricing:**
- Input: Pricing as of Oct 2025 TBD
- Output: Pricing as of Oct 2025 TBD
- Batch discount: 40% cost reduction

**When to Use GPT-5 Instead:**
- Budget constraints (if pricing favorable)
- High-volume processing (if speed advantage maintained)
- Need native Structured Outputs API (simpler implementation)

---

## Architecture Decision

### ✅ Recommended: Hybrid Embeddings + LLM

```
Flow:
1. Extract provisions → Generate embeddings (text-embedding-3-large)
2. Find top-5 candidates via cosine similarity
3. LLM comparison on candidates only
4. Confidence scoring + classification

Cost Savings: 95% reduction in LLM API calls
Accuracy: Maintained (embeddings for filtering, LLM for precision)
```

**Alternative: Direct LLM Comparison**
- Use when: Documents <200K tokens, <10 document pairs, maximum accuracy required
- Trade-off: 10-50x higher cost, slower processing

---

## Confidence Scoring Strategy

### ✅ Multi-Signal Approach

```python
Final Confidence = (
    40% LLM self-assessment +
    25% Embedding similarity +
    15% Reasoning completeness +
    10% Domain keywords +
    10% Self-consistency check
)
```

### Graduated Thresholds (REQ-024)

| Range | Tier | Action | Validation |
|-------|------|--------|------------|
| 90-100% | **High** | Suggest bulk approval | Spot-check 10% |
| 70-89% | **Medium** | Require individual review | Review all |
| <70% | **Low** | Abstain + flag | Expert review |

### Calibration Method

**MVP:** Isotonic regression
- Train on 100+ validated examples
- Monitor high-confidence accuracy
- Recalibrate if acceptance rate <85%

---

## Context Management

### Documents <200 Pages
✅ **Use full context window** (no chunking needed)

### Documents >200 Pages
✅ **Hierarchical chunking:**
- Chunk size: 500-1000 tokens (section-level)
- Overlap: 50-100 tokens
- Add summary augmentation (inject global context)

### RAG Implementation
Use when:
- Document library >200K tokens total
- Need historical version references
- Cross-reference regulatory guidance

**Vector DB:** Milvus or Pinecone
**Embedding:** text-embedding-3-large ($0.13 per 1M tokens)

---

## Prompt Engineering Template

```markdown
## Role
ERISA compliance specialist, 15+ years experience

## Context
- Source: [Vendor, Type, Date]
- Target: [Vendor, Type, Date]
- Category: [Eligibility/Vesting/Contributions/etc.]

## Task
Compare provisions:
1. Semantic equivalence?
2. Classify variance type
3. Assess impact
4. Confidence score with reasoning

## Instructions
- Compare substance, not wording
- Check: mandatory vs discretionary, thresholds, timing
- Cite specific text
- Abstain if <70% confident

## Output
{JSON schema}

## Examples
{2-3 few-shot examples}

## Provisions
Source: {text}
Target: {text}
```

**Key Elements:**
- Role definition ✓
- Step-by-step instructions ✓
- Few-shot examples (2-3) ✓
- Citation requirement ✓
- Explicit abstention threshold ✓

---

## Cost Optimization

### Estimated Cost per Document Pair

| Component | Cost |
|-----------|------|
| Document parsing (GPT-5-mini) | Pricing as of Oct 2025 TBD |
| Embeddings (text-embedding-3-large) | $0.008 |
| LLM comparison (Claude Sonnet 4.5, hybrid) | Pricing as of Oct 2025 TBD |
| **Subtotal** | **Pricing as of Oct 2025 TBD** |
| **Batch discount (40%)** | **~$1.12 (estimate)** |

**ROI Comparison:**
- Manual comparison: $1,500-6,000 (20-40 hours @ $75-150/hr)
- AI-assisted: $150-600 (2-4 hours review + $1.12 LLM)
- **Savings: 75-90%**

### Optimization Tactics

1. **Batch Processing** → 40% cost reduction
2. **Embedding Filter** → 95% fewer LLM calls
3. **Tiered Processing:**
   - Exact match (5-10%) → Free
   - Clear mismatch via embeddings (20-30%) → $0.001
   - LLM needed (60-75%) → Full cost
4. **Mixed Models:**
   - Extraction: GPT-5-mini (pricing as of Oct 2025 TBD)
   - Comparison: Claude Sonnet 4.5 (pricing as of Oct 2025 TBD)

---

## Accuracy Targets

### Industry Benchmarks
- LegalBench: 84.6% (historical GPT-4), 87% (referred to as Claude 3 Opus in Feb 2025 study)
- Document review systems: 90-95%
- **compliance-gpt target: 70-90%** (aligned with PlanPort)

### Expected Performance by Provision Type

| Type | Accuracy | Confidence Threshold |
|------|----------|---------------------|
| Eligibility | 85-95% | 90% safe |
| Vesting | 90-95% | 90% safe |
| Compensation | 70-85% | Lower to 80% or manual review all |
| Contributions | 75-90% | 90% with caution |
| Distributions | 70-80% | Lower to 80% |
| Safe Harbor | 80-90% | 90% safe |

### Improvement Strategies
1. **Few-shot prompting** → +15-25% accuracy
2. **Fine-tuned embeddings** → +5-10% accuracy
3. **Iterative prompt refinement** → +10-15% accuracy
4. **Active learning from feedback** → Ongoing improvement

---

## Technology Stack (POC)

### Core Components
- **LLM:** Claude Sonnet 4.5 (Anthropic API)
- **Embeddings:** OpenAI text-embedding-3-large
- **Framework:** LangChain + Instructor (Pydantic)
- **Vector DB:** FAISS (in-memory for POC) → Milvus (production)

### API Integrations
```python
# Anthropic
from anthropic import Anthropic
client = Anthropic(api_key="...")

# OpenAI (embeddings only)
from openai import OpenAI
openai_client = OpenAI(api_key="...")

# Instructor (structured outputs)
import instructor
client = instructor.from_anthropic(client)
```

### Batch Processing
```python
# Anthropic Batch API (40% discount)
batch = client.batches.create(
    requests=[...],
    model="claude-sonnet-4-5"  # Model ID as of Oct 2025
)
```

---

## Implementation Phases

### Phase 1: POC (2-3 weeks)
- [ ] Set up Claude API + Instructor
- [ ] Implement hybrid embeddings + LLM workflow
- [ ] Test on 5 document pairs (50-100 provisions)
- [ ] Validate confidence scoring calibration
- [ ] **Success Criteria:** 70%+ accuracy, <$10 total cost

### Phase 2: MVP (4-6 weeks)
- [ ] Batch document ingestion (PDF/Word)
- [ ] OCR fallback for locked PDFs
- [ ] CSV output (plan_comparison_workbook.csv)
- [ ] Exception log auto-population
- [ ] **Success Criteria:** 20 document pairs, <$2 per comparison

### Phase 3: Production (ongoing)
- [ ] Fine-tune embeddings on plan document corpus
- [ ] Prompt optimization (A/B testing)
- [ ] Caching layer (document + provision level)
- [ ] Multi-model fallback (GPT-4o for cost-sensitive)
- [ ] **Success Criteria:** 100+ pairs per batch, sub-10 min processing

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **LLM hallucinations (58% in historical legal studies)** | Citation requirement, contradiction detection |
| **Overconfidence on complex tasks** | Multi-signal confidence, external validation |
| **Locked PDF text extraction** | Vision fallback (OCR/Claude vision), accept 5-10% accuracy loss |
| **Context window overflow (>200K tokens)** | Hierarchical chunking with summary augmentation |
| **Cost overruns** | Batch processing, embedding filter, tiered approach |
| **Vendor-specific defaults missed** | Build default matrix (Relius/ASC/ftwilliam) |
| **Confidence calibration drift** | Monitor acceptance rates, recalibrate quarterly |

---

## Open Questions for POC

1. **Confidence calibration accuracy:** Do 90%+ predictions actually get 90%+ acceptance?
2. **Few-shot example count:** 2 vs 3 vs 5 examples - optimal accuracy/cost?
3. **Locked PDF accuracy:** How much degradation from vision-based extraction?
4. **Vendor default handling:** Can LLM infer defaults or need explicit matrix?
5. **Cross-reference resolution:** Auto-resolve or require manual section inclusion?

---

## Quick Decision Tree

```
START: Need to compare plan provisions?
  │
  ├─ Single document pair, <200 pages?
  │   └─ YES → Use full context, direct LLM comparison
  │   └─ NO → Continue
  │
  ├─ Multiple documents or batch processing?
  │   └─ YES → Use hybrid embeddings + LLM
  │
  ├─ Budget constrained or high volume?
  │   └─ YES → Use GPT-5 (compare current pricing)
  │   └─ NO → Use Claude Sonnet 4.5 (best accuracy based on historical benchmarks)
  │
  ├─ Documents >200 pages?
  │   └─ YES → Hierarchical chunking + RAG
  │   └─ NO → Full context window
  │
  ├─ Need confidence scores?
  │   └─ YES → Multi-signal approach + isotonic calibration
  │
  └─ Output format?
      └─ Machine processing → Structured JSON (tool calling)
      └─ Human review → Natural language + JSON hybrid
```

---

## References

**Full Research Report:** `/Users/sergio/sentientsergio/compliance-gpt/design/llm_strategy/llm_research_report.md`

**Key Sources:**
- LegalBench (Stanford HAI)
- Anthropic Claude Sonnet 4.5 Documentation
- OpenAI Embeddings API
- Artificial Intelligence and Law journal (2025 study referencing Claude 3 Opus)
- compliance-gpt requirements (REQ-021, REQ-022, REQ-024)

---

**Next Steps:**
1. Review this decision matrix with project stakeholders
2. Proceed to POC implementation using recommended stack
3. Collect validation data for confidence calibration
4. Iterate on prompt engineering with real document examples

*Last updated: 2025-10-17*
