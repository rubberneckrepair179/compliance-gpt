# Performance Optimization Strategy

## Overview

This document analyzes the match validation workflow for parallelization opportunities and defines optimization strategies for the compliance-gpt semantic mapping pipeline.

**Key Insight**: The workflow is heavily I/O-bound (vision extraction, embeddings, LLM API calls), making it ideal for async/parallel optimization. Current POC achieves 6x speedup with ThreadPoolExecutor; additional optimizations can reduce total processing time by 50%+.

---

## Current Workflow Performance (Baseline)

### POC Results (Oct 19, 2025)

| Operation | Items Processed | Time | Parallelization | Bottleneck |
|-----------|----------------|------|-----------------|------------|
| **Vision Extraction** | 4 docs, 328 pages | 18 min | 16 workers (ThreadPool) | I/O-bound (API calls) |
| **BPD Crosswalk** | 425 × 507 = 215K comparisons → 2,125 LLM calls | 11 min | 16 workers (ThreadPool) | I/O-bound (API calls) |
| **AA Crosswalk** | 521 × 235 = 122K comparisons → ~1,500 LLM calls | ~10 min (estimated) | 16 workers (ThreadPool) | I/O-bound (API calls) |
| **Total (Steps 1+2)** | - | **39 min** | Sequential steps | Orchestration |

**Speedup from parallelization:** ~6x (18 min parallel vs ~108 min sequential if single-threaded)

**Current bottleneck:** Steps run sequentially even though BPD and AA crosswalks are independent.

---

## Workflow Architecture

### Logical Steps (from `provisional_matching.md`)

```
Step 1: BPD Template Crosswalk
├─ Extract BPD provisions (vision API)         ← I/O-bound, parallelizable
├─ Generate semantic fingerprints (CPU)        ← CPU-bound, parallelizable
├─ Generate embeddings (embedding API)         ← I/O-bound, parallelizable, BATCHABLE
├─ Embedding-based candidate filtering         ← CPU-bound, fast (<1 sec)
├─ LLM semantic verification (LLM API)         ← I/O-bound, parallelizable
└─ Output: Provisional matches (with dependencies tracked)

Step 2: AA Election Structure Crosswalk
├─ Extract AA elections (vision API)           ← I/O-bound, parallelizable
├─ Generate semantic fingerprints (CPU)        ← CPU-bound, parallelizable
├─ Generate embeddings (embedding API)         ← I/O-bound, parallelizable, BATCHABLE
├─ Embedding-based candidate filtering         ← CPU-bound, fast (<1 sec)
├─ LLM option compatibility verification       ← I/O-bound, parallelizable
└─ Output: Election structure matches

Step 3: Confirm Provisional Matches
├─ For each provisional BPD match:
│   ├─ Lookup referenced elections in AA crosswalk ← CPU-bound, dict lookup
│   ├─ If all elections mapped → CONFIRMED     ← State update
│   ├─ If no elections mapped → BLOCKED        ← State update
│   └─ If partial mapping → CONDITIONAL        ← State update
└─ Output: Confirmed template matches

Step 4: Generate Merged Instance Crosswalk (Post-MVP)
├─ Substitute elected values into BPD templates  ← CPU-bound, parallelizable
├─ Generate embeddings for merged provisions     ← I/O-bound, parallelizable, BATCHABLE
├─ LLM comparison of merged provisions           ← I/O-bound, parallelizable
└─ Output: Instance-level variance report
```

### Dependency Graph

```
        [Step 1: BPD Crosswalk]  [Step 2: AA Crosswalk]
                    ↓                      ↓
                    └──────────┬───────────┘
                               ↓
                [Step 3: Confirm Provisional Matches]
                               ↓
                [Step 4: Merged Instance Crosswalk]
```

**Key observation:** Steps 1 and 2 are **independent** and can run **in parallel**.

---

## Optimization Opportunities

### Tier 1: Immediate Wins (Low Effort, High Impact)

#### 1.1 Parallel Steps 1 & 2 Execution

**Current State:**
```python
# Sequential execution
bpd_crosswalk = extract_and_map_bpd(source, target)  # 11 min
aa_crosswalk = extract_and_map_aa(source, target)     # 10 min
# Total: 21 min
```

**Optimized:**
```python
import asyncio

async def run_crosswalks_parallel(source_docs, target_docs):
    """Run BPD and AA crosswalks in parallel"""
    bpd_task = asyncio.create_task(
        extract_and_map_bpd(source_docs['bpd'], target_docs['bpd'])
    )
    aa_task = asyncio.create_task(
        extract_and_map_aa(source_docs['aa'], target_docs['aa'])
    )

    # Both run concurrently, return when both complete
    bpd_crosswalk, aa_crosswalk = await asyncio.gather(bpd_task, aa_task)

    return bpd_crosswalk, aa_crosswalk

# Total: max(11, 10) = 11 min
```

**Time Savings:** 10 minutes (32% reduction in Steps 1+2)
**Implementation Effort:** 2-4 hours (refactor to async/await)
**Risk:** Low (well-understood Python async patterns)

---

#### 1.2 Batch Embedding Generation

**Current State:**
```python
# Individual API calls for each provision
embeddings = []
for provision in provisions:
    embedding = openai.embeddings.create(
        input=provision.semantic_fingerprint,
        model="text-embedding-3-small"
    )
    embeddings.append(embedding)
# 426 provisions × ~50ms per call = ~21 seconds
```

**Optimized:**
```python
# Batch API calls (OpenAI supports up to 2048 inputs per call)
BATCH_SIZE = 100

def generate_embeddings_batch(provisions, batch_size=100):
    embeddings = []
    for i in range(0, len(provisions), batch_size):
        batch = provisions[i:i+batch_size]
        fingerprints = [p.semantic_fingerprint for p in batch]

        response = openai.embeddings.create(
            input=fingerprints,  # Send 100 at once
            model="text-embedding-3-small"
        )
        embeddings.extend(response.data)

    return embeddings

# 426 provisions ÷ 100 per batch × ~200ms per batch = ~1 second
```

**Time Savings:** ~20 seconds per document pair (40 sec total for source+target BPD+AA)
**Cost Savings:** None (same number of tokens)
**Implementation Effort:** 1-2 hours
**Risk:** Low (OpenAI SDK supports this natively)

---

#### 1.3 Embedding Cache (SQLite)

**Current State:**
- Re-generate embeddings on every run
- Extraction → embeddings takes ~1 minute per document

**Optimized:**
```python
def get_or_create_embedding(provision_id, semantic_fingerprint, db):
    """Check cache first, generate if missing"""
    # Check cache
    cached = db.execute(
        "SELECT embedding FROM embeddings WHERE provision_id = ? AND fingerprint = ?",
        (provision_id, semantic_fingerprint)
    ).fetchone()

    if cached:
        return cached['embedding']

    # Generate if not cached
    embedding = openai.embeddings.create(
        input=semantic_fingerprint,
        model="text-embedding-3-small"
    )

    # Store in cache
    db.execute(
        "INSERT INTO embeddings (provision_id, fingerprint, embedding) VALUES (?, ?, ?)",
        (provision_id, semantic_fingerprint, embedding)
    )

    return embedding
```

**Time Savings:**
- First run: No change
- Subsequent runs: ~2 min → ~5 sec (only new/changed provisions)
- Re-running Red Team Sprint: Instant

**Implementation Effort:** 2-3 hours (schema + cache logic)
**Risk:** Low (standard caching pattern)

---

#### 1.4 Smart Candidate Filtering (Provision Type Matching)

**Current State:**
```python
# Compare all provisions regardless of type
# Eligibility rule compared to vesting schedule (semantically incompatible)
# Results in wasted LLM calls with low similarity scores
```

**Optimized:**
```python
def filter_candidates_by_type(source_provision, target_provisions, embedding_threshold=0.70):
    """Only compare compatible provision types"""
    candidates = []

    for target in target_provisions:
        # Skip if types are incompatible
        if not are_types_compatible(source_provision.provision_type, target.provision_type):
            continue

        # Check embedding similarity
        similarity = cosine_similarity(source_provision.embedding, target.embedding)
        if similarity >= embedding_threshold:
            candidates.append((target, similarity))

    return candidates

def are_types_compatible(source_type, target_type):
    """Define which provision types can match"""
    # Exact match
    if source_type == target_type:
        return True

    # Compatible groups (e.g., eligibility rules can match participation rules)
    compatible_groups = [
        {"eligibility_rule", "participation_rule"},
        {"contribution_formula", "allocation_formula"},
        {"definition", "definition"},  # Definitions only match definitions
    ]

    for group in compatible_groups:
        if source_type in group and target_type in group:
            return True

    return False
```

**Time Savings:**
- Reduce LLM calls by 30-50% (skip incompatible comparisons)
- For 2,125 LLM calls → ~1,000-1,400 calls (save 5-7 min)

**Implementation Effort:** 4-6 hours (requires provision type classification in extraction)
**Risk:** Medium (depends on accurate type classification)

---

### Tier 2: Medium Wins (Moderate Effort, Moderate Impact)

#### 2.1 Streaming Pipeline Architecture

**Current State:**
```python
# Extract all provisions, then map all at once
provisions_source = extract_all_provisions(source_bpd)  # Wait for all
provisions_target = extract_all_provisions(target_bpd)  # Wait for all
crosswalk = generate_crosswalk(provisions_source, provisions_target)  # Then map
```

**Optimized (Streaming):**
```python
async def streaming_crosswalk(source_bpd, target_bpd):
    """Start mapping as soon as provisions are extracted"""
    # Start extraction (returns async generator)
    source_stream = stream_extract_provisions(source_bpd)
    target_provisions = await extract_all_provisions(target_bpd)  # Need full target set

    # Process source provisions as they arrive
    async for source_provision in source_stream:
        # Generate embedding immediately
        source_provision.embedding = await generate_embedding(source_provision)

        # Find candidates and verify immediately
        candidates = filter_candidates(source_provision, target_provisions)

        for target_candidate in candidates:
            match = await verify_with_llm(source_provision, target_candidate)
            yield match  # Emit result immediately
```

**Time Savings:**
- Overlap extraction + mapping (currently sequential)
- Estimated 15-20% reduction in total time

**Implementation Effort:** 8-12 hours (significant refactor to streaming architecture)
**Risk:** Medium (more complex error handling, partial result management)

---

#### 2.2 Adaptive Worker Pool Sizing

**Current State:**
```python
# Fixed 16 workers for all operations
with ThreadPoolExecutor(max_workers=16) as executor:
    # Same pool for vision, embeddings, LLM calls
```

**Optimized:**
```python
import os

# Adjust based on operation type and rate limits
VISION_WORKERS = min(32, os.cpu_count() * 2)      # Vision API has high rate limit
EMBEDDING_WORKERS = min(16, os.cpu_count())       # Embeddings batch, fewer concurrent calls
LLM_WORKERS = min(8, os.cpu_count())              # LLM has lower rate limit, more expensive

async def extract_provisions(documents):
    async with asyncio.Semaphore(VISION_WORKERS):
        # Use higher concurrency for vision extraction
        ...

async def verify_with_llm(source, target):
    async with asyncio.Semaphore(LLM_WORKERS):
        # Use lower concurrency for LLM (respect rate limits, avoid throttling)
        ...
```

**Time Savings:**
- Vision extraction: Potential 2x speedup (32 workers vs 16)
- LLM verification: Avoid rate limit errors, smoother execution

**Implementation Effort:** 2-3 hours
**Risk:** Low (requires monitoring rate limits)

---

### Tier 3: Future Optimizations (High Effort, High Impact)

#### 3.1 Multi-Document Parallel Processing

**Use Case:** User uploads 10 plan conversions at once

**Current State:**
```python
# Process one at a time
for conversion in conversions:
    crosswalk = process_conversion(conversion)
# 10 conversions × 21 min = 210 min (3.5 hours)
```

**Optimized:**
```python
async def process_conversions_parallel(conversions):
    # Process all conversions concurrently (limited by API rate limits)
    tasks = [process_conversion(c) for c in conversions]
    results = await asyncio.gather(*tasks)
    return results

# 10 conversions × 21 min = ~30 min (if rate limits allow, otherwise 60-90 min)
```

**Time Savings:**
- Best case: 210 min → 30 min (7x speedup)
- Realistic: 210 min → 60 min (3.5x speedup, accounting for rate limits)

**Implementation Effort:** 4-6 hours (rate limit management, result aggregation)
**Risk:** Medium (requires careful API quota management)

---

#### 3.2 Local LLM for Candidate Pre-Filtering

**Current State:**
- Send all embedding-filtered candidates to GPT-4.1 (expensive)
- 2,125 LLM calls × $0.002 per call = ~$4.25 per crosswalk

**Optimized:**
```python
# Use local fast model (Llama 3.2 3B) for quick pre-filter
# Only send high-confidence candidates to GPT-4.1 for final verification

async def two_stage_verification(source, target):
    # Stage 1: Local fast model (Llama 3.2 3B, <100ms per call)
    local_score = await local_llm_quick_score(source, target)

    if local_score < 0.50:
        # Definite no-match, skip expensive GPT-4.1 call
        return {"match": False, "confidence": local_score, "stage": "local_filter"}

    # Stage 2: GPT-4.1 for final verification (only for promising candidates)
    gpt_result = await openai_verify(source, target)
    return gpt_result

# Reduce GPT-4.1 calls by 60-70% (local model filters out obvious non-matches)
# 2,125 calls → ~700 calls (save $2.50 per crosswalk, 4-5 min faster)
```

**Time Savings:** 4-5 minutes per crosswalk
**Cost Savings:** ~60% reduction in LLM API costs
**Implementation Effort:** 12-16 hours (local model setup, prompt engineering, two-stage logic)
**Risk:** High (requires local GPU/CPU, model management, accuracy validation)

---

## Performance Budget (Target Metrics)

### MVP Goals

| Metric | Current (POC) | Target (MVP) | Stretch Goal |
|--------|--------------|--------------|--------------|
| **Total Time (BPD + AA crosswalk)** | 39 min | 20 min | 10 min |
| **Vision Extraction** | 18 min | 10 min | 5 min |
| **Semantic Mapping (per crosswalk)** | 11 min | 7 min | 4 min |
| **API Cost (per crosswalk)** | $4.25 | $4.25 | $1.50 |
| **Subsequent Runs (cached)** | 39 min | 5 min | 2 min |

### Optimization Roadmap to Hit MVP Targets

**Phase 1: Immediate Wins (Week 1)**
- ✅ Parallel Steps 1 & 2: 39 min → 29 min (25% reduction)
- ✅ Batch embeddings: 29 min → 28 min (minor but free)
- ✅ Embedding cache: Subsequent runs 39 min → 5 min (87% reduction)

**Phase 2: Medium Wins (Week 2-3)**
- ⚠️ Smart type filtering: 28 min → 22 min (21% reduction)
- ⚠️ Adaptive worker pools: 22 min → 20 min (9% reduction)

**Result: 39 min → 20 min = 49% reduction** ✅ **MVP Target Achieved**

**Phase 3: Future (Post-MVP)**
- ⬜ Streaming pipeline: 20 min → 17 min (15% reduction)
- ⬜ Local LLM pre-filter: $4.25 → $1.50 (65% cost reduction)
- ⬜ Multi-document parallel: Linear scaling for batch processing

**Result: 39 min → 17 min = 56% reduction** 🎯 **Stretch Goal**

---

## Implementation Strategy

### Python Async/Await Refactor

**Current Architecture:**
```python
# ThreadPoolExecutor-based (POC)
class SemanticMapper:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=16)

    def map_provisions(self, source, target):
        # Submit all tasks to thread pool
        futures = [self.executor.submit(self._verify, s, t) for s, t in pairs]
        results = [f.result() for f in futures]
        return results
```

**Optimized Architecture:**
```python
# AsyncIO-based (MVP)
import asyncio
import aiohttp

class AsyncSemanticMapper:
    def __init__(self, max_concurrency=16):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None  # Shared aiohttp session

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    async def map_provisions(self, source_provisions, target_provisions):
        """Map provisions using async/await"""
        tasks = []
        for source in source_provisions:
            candidates = await self._filter_candidates(source, target_provisions)
            for target in candidates:
                task = self._verify_match(source, target)
                tasks.append(task)

        # Run all verifications concurrently (limited by semaphore)
        results = await asyncio.gather(*tasks)
        return results

    async def _verify_match(self, source, target):
        """Verify match with rate limiting"""
        async with self.semaphore:
            # Use shared session for connection pooling
            response = await self.session.post(
                "https://api.openai.com/v1/chat/completions",
                json={...}
            )
            return await response.json()

# Usage
async def main():
    async with AsyncSemanticMapper(max_concurrency=16) as mapper:
        # Run BPD and AA crosswalks in parallel
        bpd_task = mapper.map_provisions(bpd_source, bpd_target)
        aa_task = mapper.map_provisions(aa_source, aa_target)

        bpd_crosswalk, aa_crosswalk = await asyncio.gather(bpd_task, aa_task)

# Run
asyncio.run(main())
```

**Benefits:**
- Native async/await syntax (cleaner than ThreadPoolExecutor)
- Shared connection pooling (aiohttp session reuse)
- Fine-grained rate limiting (semaphores per operation type)
- Natural parallelization (gather multiple tasks)

---

## Monitoring and Observability

### Performance Metrics to Track

```python
@dataclass
class PerformanceMetrics:
    """Track performance for each crosswalk operation"""
    operation: str  # "vision_extraction", "embedding_generation", "llm_verification"

    # Timing
    start_time: datetime
    end_time: datetime
    duration_seconds: float

    # Throughput
    items_processed: int
    items_per_second: float

    # API Usage
    api_calls: int
    tokens_used: int
    api_cost_usd: float

    # Concurrency
    max_workers: int
    actual_concurrency: float  # Average concurrent tasks

    # Errors
    errors: int
    retries: int
    rate_limit_hits: int

# Example output
"""
Vision Extraction: 18.2 min, 328 pages, 0.3 pages/sec, $1.20, 32 workers
Embedding Generation: 1.1 min, 933 provisions, 14.2 prov/sec, $0.02, 16 workers (batched)
LLM Verification: 11.4 min, 2,125 calls, 3.1 calls/sec, $4.25, 16 workers, 3 rate limit hits
Total: 30.7 min, $5.47
"""
```

### Bottleneck Detection

```python
def analyze_bottlenecks(metrics: List[PerformanceMetrics]):
    """Identify performance bottlenecks"""
    total_time = sum(m.duration_seconds for m in metrics)

    bottlenecks = []
    for metric in metrics:
        percentage = (metric.duration_seconds / total_time) * 100

        if percentage > 40:
            bottlenecks.append({
                "operation": metric.operation,
                "time_percentage": percentage,
                "recommendation": get_optimization_recommendation(metric)
            })

    return bottlenecks

def get_optimization_recommendation(metric: PerformanceMetrics):
    """Suggest optimization based on metric characteristics"""
    if metric.rate_limit_hits > 0:
        return f"Reduce concurrency (currently {metric.max_workers} workers)"

    if metric.actual_concurrency < metric.max_workers * 0.5:
        return "Increase batch size or concurrency (underutilized workers)"

    if metric.items_per_second < 1.0:
        return "Consider caching or pre-filtering to reduce workload"

    return "Performance is acceptable"
```

---

## Cost Analysis

### Current Costs (POC - Per Crosswalk)

| Operation | Model | Items | Cost per Item | Total Cost |
|-----------|-------|-------|--------------|------------|
| Vision Extraction (4 docs) | GPT-5-nano | 328 pages | $0.0037/page | $1.20 |
| Embeddings (source + target) | text-embedding-3-small | 933 provisions | $0.00002/provision | $0.02 |
| LLM Verification (BPD) | GPT-4.1 | 2,125 calls | $0.002/call | $4.25 |
| LLM Verification (AA) | GPT-4.1 | ~1,500 calls | $0.002/call | $3.00 |
| **Total per conversion** | - | - | - | **$8.47** |

### Optimized Costs (With Tier 1 + 2 Optimizations)

| Operation | Optimization | Cost Reduction |
|-----------|-------------|----------------|
| Vision Extraction | None (already optimal) | $1.20 |
| Embeddings | Batch generation | $0.02 (no change, same tokens) |
| Embeddings (cached runs) | Cache hits | $0.00 (100% reduction on reruns) |
| LLM Verification (BPD) | Type filtering (30% reduction) | $2.98 |
| LLM Verification (AA) | Type filtering (30% reduction) | $2.10 |
| **Total per conversion** | - | **$6.30** (26% reduction) |

### Cost at Scale

| Scenario | Conversions per Month | Cost (Current) | Cost (Optimized) |
|----------|----------------------|----------------|------------------|
| Small TPA | 10 | $85 | $63 |
| Medium TPA | 100 | $847 | $630 |
| Large TPA | 1,000 | $8,470 | $6,300 |

**Additional savings:**
- Cached reruns (Red Team Sprints, QA, demos): ~50% of runs → save $3,150/month for large TPA

---

## Design Decision: AsyncIO vs ThreadPoolExecutor

### Comparison

| Feature | ThreadPoolExecutor (Current POC) | AsyncIO (Recommended MVP) |
|---------|----------------------------------|---------------------------|
| **Syntax** | `executor.submit(fn, *args)` | `await async_fn(*args)` |
| **Concurrency Model** | Thread pool (OS threads) | Event loop (coroutines) |
| **I/O-Bound Performance** | ✅ Good (GIL not an issue) | ✅ Excellent (no thread overhead) |
| **CPU-Bound Performance** | ⚠️ GIL limits (but not relevant) | ⚠️ Single-threaded (but not relevant) |
| **Memory Overhead** | ~8MB per thread × 16 = 128MB | ~50KB per coroutine × 1000s = negligible |
| **Rate Limiting** | Manual (semaphores) | Native (asyncio.Semaphore) |
| **Connection Pooling** | Manual | Native (aiohttp.ClientSession) |
| **Orchestration (gather)** | `as_completed()` or `map()` | `asyncio.gather()` natural syntax |
| **Error Handling** | Try/catch in each thread | Native async exception handling |
| **Ecosystem** | ✅ Works with all libraries | ⚠️ Requires async-compatible libraries (aiohttp, asyncio-openai) |

### Recommendation: **AsyncIO for MVP**

**Rationale:**
1. ✅ **Natural async syntax** - `await asyncio.gather(task1, task2)` is cleaner than ThreadPoolExecutor orchestration
2. ✅ **Better resource utilization** - Thousands of coroutines vs dozens of threads
3. ✅ **Native rate limiting** - `asyncio.Semaphore` is built for this
4. ✅ **Connection pooling** - aiohttp session reuse reduces latency
5. ✅ **I/O-bound workload** - Async shines for network I/O (our use case)
6. ⚠️ **Migration effort** - ~8-12 hours to refactor POC code to async/await
7. ⚠️ **Library compatibility** - OpenAI SDK has async support, but may need wrappers

**Migration Path:**
- Phase 1: Keep ThreadPoolExecutor for POC/testing
- Phase 2: Refactor to AsyncIO for MVP (parallel with Red Team Sprint fixes)
- Phase 3: Optimize async code (streaming, adaptive concurrency)

---

## Open Questions / Future Decisions

1. **Should we implement streaming pipeline in MVP or defer to post-MVP?**
   - Pro: 15-20% speedup, better user experience (see results as they arrive)
   - Con: Significant complexity, may delay MVP launch
   - **Decision pending**: Prioritize based on MVP timeline

2. **What's the optimal worker pool size for different operations?**
   - Need to test against OpenAI rate limits (10K RPM for Tier 2)
   - **Decision pending**: Run benchmarks with 8, 16, 32, 64 workers

3. **Should we cache extraction results or only embeddings?**
   - Caching extraction saves vision API costs (~$1.20 per rerun)
   - Caching embeddings only saves time, not cost
   - **Decision**: Cache both (extraction in `extracted/`, embeddings in SQLite)

4. **How to handle rate limit errors gracefully?**
   - Exponential backoff with retry
   - Adaptive concurrency reduction
   - **Decision pending**: Implement both strategies

5. **Should we support local LLM option for cost-sensitive users?**
   - Reduce API costs by 60-70%
   - Requires user to run local model (Llama 3.2, Ollama)
   - **Decision pending**: Post-MVP feature, gauge user interest

---

## Success Criteria

**For MVP Launch:**
- ✅ Total processing time: <20 min per conversion (49% improvement)
- ✅ Cached reruns: <5 min (87% improvement)
- ✅ Zero rate limit errors under normal load (16 workers)
- ✅ API costs: <$7 per conversion (17% improvement)
- ✅ Monitoring: Track performance metrics for all operations

**For Production (Post-MVP):**
- ✅ Total processing time: <10 min per conversion (74% improvement)
- ✅ API costs: <$3 per conversion (65% improvement with local LLM)
- ✅ Multi-document processing: 10 conversions in <60 min (linear scaling)
- ✅ Auto-scaling: Adjust concurrency based on rate limit feedback

---

## References

- Node.js async/await patterns (inspiration for Python AsyncIO approach)
- OpenAI API rate limits: https://platform.openai.com/docs/guides/rate-limits
- Python AsyncIO best practices: https://docs.python.org/3/library/asyncio.html
- `/design/data_models/provisional_matching.md` - Workflow architecture

---

*Document Created: 2025-10-23*
*Author: Claude (with Sergio DuBois)*
*Status: Draft - pending implementation prioritization*
*Next Review: After Red Team Sprint completion, before MVP refactor*
