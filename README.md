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

**POC Architecture Pivot** (Oct 19, 2025)

✅ Process framework defined (updated for BPD+AA architecture)
✅ Market research completed
✅ Functional requirements drafted
✅ **Phase 1 design complete** — architecture, data models, LLM strategy
✅ **Document structure validated** — Opus 4.1 + GPT-5 Pro confirmed BPD+AA requirements
✅ **Semantic mapping algorithm proven** — Works correctly on proper inputs

**Critical Discovery:** Plan documents are BPD (template) + Adoption Agreement (elections) pairs. Initial POC approach was comparing templates to templates. Architecture pivot required to implement document merger layer before semantic comparison.

**Current Focus:** Fixing extraction to preserve template language, then implementing BPD+AA merger for accurate provision comparison.

## Repo map

- **[`/process`](./process/README.md)** — the four-control compliance framework (the "spec")
- **[`/requirements`](./requirements/README.md)** — functional requirements for MVP (doc-to-doc comparison focus)
- **[`/research`](./research/)** — market research on existing TPA tools and AI opportunities
- **[`/design`](./design/README.md)** — technical architecture, data models, and LLM strategy ✨ **NEW**

### Design Highlights

**Model Selection:** OpenAI GPT-4.1 + text-embedding-3-small (switched from Claude due to rate limits)
**Architecture:** Hybrid embeddings (candidate matching) + LLM verification (semantic assessment)
**Data Storage:** SQLite (queryable, transactional, local-first)
**Document Processing:** BPD+AA merger layer → complete provisions → semantic comparison
**Output:** CSV mapping analysis + natural language executive summary (NO document generation)
**UI Strategy:** CLI-first POC → Web UI MVP → Docker deployment
**Expected Accuracy:** 70-90% automation (vs 4-8 hours manual)
**Cost Estimate:** ~$0.25 per document pair (reduced via embedding optimization)

**Key Innovation:** First tool to handle cross-vendor document conversions by merging template frameworks (BPD) with actual plan elections (Adoption Agreement) for accurate semantic comparison.

See [`/design/README.md`](./design/README.md) for complete architecture and design decisions.
