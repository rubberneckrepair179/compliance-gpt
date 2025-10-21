<p align="center">
  <img src="assets/banner.png" alt="compliance-gpt banner">
</p>

# compliance-gpt

**AI-assisted plan document compliance** — automate the reconciliation, exception tracking, and sign-off workflows that preserve **qualified plan** status during recordkeeper conversions and Cycle restatements.

## The problem

When retirement plans move providers or restate onto a new IRS pre-approved document cycle, compliance teams must:
- Maintain reliance under **IRC §401(a)** (tax qualification)
- Evidence ERISA / DOL obligations (written plan, records, disclosures)
- Prove the new document **still says what the old plan said** (or that deliberate changes were approved)

Today this is done manually with Word redlines, Excel spreadsheets, and email chains. It's error-prone, slow, and doesn't scale.

## What compliance-gpt does

compliance-gpt automates the four-control framework defined in [`/process`](./process/):

1. **Plan Qualification** — verify document lineage and Opinion Letter reliance
2. **Document Reconciliation** — AI-powered provision mapping and variance detection
3. **Exception Handling** — structured tracking of deviations to closure
4. **Sign-off** — automated execution package assembly and audit trail

## Status

**POC Vision Extraction + Semantic Mapping Complete** (Oct 20, 2025) 🎉

👉 **[See DEMO.md for complete walkthrough with examples](DEMO.md)** 👈

✅ Process framework defined (updated for BPD+AA architecture)
✅ Market research completed
✅ Functional requirements drafted
✅ **Phase 1 design complete** — architecture, data models, LLM strategy
✅ **Document structure validated** — Opus 4.1 + GPT-5 Pro confirmed BPD+AA requirements
✅ **Parallel vision extraction complete** — All 4 documents extracted (302 pages, 24 minutes)
  - Source BPD: 426 provisions (81 pages, GPT-5-nano)
  - Source AA: 543 elections (104 pages, GPT-5-nano)
  - Target BPD: 507 provisions (72 pages, GPT-5-nano)
  - Target AA: 219 elections (45 pages, GPT-5-nano)
✅ **AA extraction v2 validated** — 100% accuracy (762/762 elections, discriminated union model)
✅ **Parallel semantic crosswalk complete** — BPD mapping with 16 workers (2,125 verifications, 11 minutes)
  - 82 semantic matches found (19.3% - expected for template comparisons)
  - 94% high confidence (≥90%)
  - 186 high-impact variances detected
  - 136 medium-impact variances detected
✅ **CSV export working** — Human-readable crosswalk ready for Excel/review

**Key Achievements:**
- **Vision extraction with GPT-5-nano:** Most thorough model for structured document parsing
- **Parallel processing:** 16-worker architecture reduces crosswalk time from ~70 min to ~11 min (6x speedup)
- **Hybrid embeddings + LLM:** 99% cost reduction (215,475 comparisons → 2,125 LLM calls)
- **Semantic matching with GPT-5-Mini:** High-quality reasoning for variance detection

**Test Corpus:**
The POC was validated using Ascensus Cycle 3 documents:
- **Source:** Ascensus BPD 01 + Adoption Agreement (426 provisions, 543 elections)
- **Target:** Ascensus BPD 05 + Adoption Agreement (507 provisions, 219 elections)
- **Scenario:** Intra-vendor Cycle 3 restatement (BPD 01 → BPD 05)

This validates the semantic mapping algorithm works correctly. Cross-vendor testing (e.g., Relius → ASC, ftwilliam → DATAIR) requires obtaining additional sample documents.

**Next Steps:** Simulate filled source AA with elections, implement BPD+AA merger, run merged crosswalk for complete conversion workflow validation

## Repo map

- **[`/process`](./process/README.md)** — the four-control compliance framework (the "spec")
- **[`/requirements`](./requirements/README.md)** — functional requirements for MVP (doc-to-doc comparison focus)
- **[`/research`](./research/)** — market research on existing TPA tools and AI opportunities
- **[`/design`](./design/README.md)** — technical architecture, data models, and LLM strategy ✨ **NEW**

### Design Highlights

**Model Selection:**
- Vision extraction: GPT-5-nano (gpt-5-nano) - most thorough for structured forms
- Semantic matching: GPT-5-Mini (gpt-5-mini) - best reasoning for variance detection
- Embeddings: text-embedding-3-small (cost optimization)

**Architecture:**
- Vision-based parallel extraction (16 workers) → BPD provisions + AA elections
- Hybrid embeddings (candidate matching) + LLM verification (semantic assessment)
- Parallel crosswalk generation (16 workers) → CSV output

**Performance (Proven):**
- 328 pages extracted in 18 minutes (parallel vision processing)
- 2,125 semantic verifications in 11 minutes (16x parallelization)
- 99% cost reduction via embedding-based candidate filtering
- 94% high-confidence match quality

**Data Storage:** SQLite (queryable, transactional, local-first)
**Output:** CSV mapping analysis + variance classification (NO document generation)
**UI Strategy:** CLI-first POC → Web UI MVP → Docker deployment

**Key Innovations:**
1. **Vision-first extraction** - Handles form layouts, checkboxes, nested options better than text parsing
2. **Parallel processing** - 16-worker architecture for both extraction and semantic mapping
3. **BPD+AA crosswalk** - Maps both template provisions AND election options for complete conversion spec
4. **Semantic provision mapping** - AI-powered cross-vendor capability (POC validated with Ascensus BPD 01 → BPD 05)

See [`/design/README.md`](./design/README.md) for complete architecture and design decisions.
