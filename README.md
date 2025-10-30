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

**ADR-001 Approved: Merge Strategy Defined** (Oct 30, 2025) ✅

👉 **[See ADR-001 for architectural decision details](design/architecture/adr_001_merge_strategy.md)** 👈

✅ Process framework defined (updated for BPD+AA architecture)
✅ Market research completed
✅ Functional requirements drafted
✅ **Phase 1 design complete** — architecture, data models, LLM strategy
✅ **Document structure validated** — BPD+AA architecture confirmed
✅ **Extraction pipeline complete** — 4,901 provisions extracted (Relius + Ascensus, BPDs + AAs)
  - GPT-5-nano vision extraction with 100% accuracy validation
  - Embedding pollution fix (false positives eliminated)
  - Red Team Sprint A validation
✅ **ADR-001: Merger Strategy** — Merge-then-crosswalk approach formally documented
  - Data models defined (MergedProvision, CrosswalkResult)
  - 10 merge rule patterns catalogued
  - Evaluation plan with golden set and metrics
  - Phased implementation roadmap (proof-of-concept → MVP → pipeline)

**Key Achievements:**
- **Vision extraction with GPT-5-nano:** Most thorough model for structured document parsing
- **Parallel processing:** 16-worker architecture for extraction and semantic mapping
- **Hybrid embeddings + LLM:** 99% cost reduction (candidate filtering before LLM verification)
- **Semantic matching with GPT-5-Mini:** High-quality reasoning for variance detection
- **Architectural rigor:** Formal ADR process with advisor feedback, decision hygiene, exit criteria

**Test Corpus:**
- **Source:** Relius BPD Cycle 3 + Adoption Agreement (623 provisions, 182 elections)
- **Target:** Ascensus BPD 05 + Adoption Agreement (426 provisions, 550 elections)
- **Scenario:** Cross-vendor conversion (hardest use case - different template structures)

**Next Phase: BPD+AA Merger Implementation**

**Phase 1 (2-3 days):** Proof-of-concept with 20-provision golden set
- Manually merge election-heavy provisions (eligibility, compensation, match, vesting, HCE/top-heavy)
- Compare merged vs template-only crosswalk quality
- Exit criteria: ≥20% recall gain at ≥0.85 precision

**Phase 2 (4-6 days):** Smart merger MVP
- Implement top 10 merge patterns (anchors, conditionals, vendor synonyms)
- Target ≥80% auto-merge coverage for high-impact provisions
- Full provenance tracking (BPD + AA → merged provision)

**Phase 3 (2-3 days):** Full pipeline integration
- End-to-end merged crosswalk (Relius → Ascensus)
- Executive summary generation
- Demo-ready artifact

## Repo map

- **[`/process`](./process/README.md)** — the four-control compliance framework (the "spec")
- **[`/requirements`](./requirements/README.md)** — functional requirements for MVP (doc-to-doc comparison focus)
- **[`/research`](./research/)** — market research on existing TPA tools and AI opportunities
- **[`/design`](./design/README.md)** — technical architecture, data models, and LLM strategy
- **[`/design/architecture/adr_001_merge_strategy.md`](./design/architecture/adr_001_merge_strategy.md)** — Architectural Decision Record: Merge Strategy ✨ **NEW**

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
3. **Merge-then-crosswalk** - Substitute AA elections into BPD provisions BEFORE semantic comparison (prevents false negatives on election-dependent provisions)
4. **Semantic provision mapping** - AI-powered cross-vendor capability with full provenance tracking
5. **Formal ADR process** - Decision hygiene with data models, merge rules, evaluation plan, exit criteria

See [`/design/README.md`](./design/README.md) for complete architecture and design decisions.
