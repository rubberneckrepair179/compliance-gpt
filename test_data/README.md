# Test Data Directory

This directory contains sample plan documents used for POC development and testing.

**⚠️ PRIVACY NOTICE**: The `/raw` and `/processed` directories are fully gitignored. No actual plan documents or extracted data will be committed to version control.

## Structure

```
test_data/
├── raw/          # Original sample documents (GITIGNORED - never committed)
└── processed/    # Extracted provisions (GITIGNORED - generated at runtime)
```

## Sample Documents

### Pair A: Basic Plan Documents (Primary Test Set)
- **pair_a_source_bpd.pdf** - Basic Plan Document (81 pages, 3.6 MB)
  - Document type: Basic Plan Document
  - Extraction: ✓ Standard text extraction works
  - Use case: Source document for cross-vendor comparison

- **pair_a_target_bpd.pdf** - Basic Plan Document (98 pages, 1.0 MB)
  - Document type: Basic Plan Document (Cycle 3)
  - Vendor: TPA platform document
  - Extraction: ✓ Standard text extraction works
  - Use case: Target document for cross-vendor comparison

### Pair B: Adoption Agreements (Advanced Test Set)
- **pair_b_source_adoption.pdf** - Adoption Agreement (104 pages, 5.1 MB)
  - Document type: Nonstandardized Adoption Agreement
  - Extraction: ✓ Standard text extraction works
  - Use case: Adoption agreement comparison baseline

- **pair_b_target_adoption_locked.pdf** - Adoption Agreement (45 pages, 1.1 MB)
  - Document type: Adoption Agreement (Cycle 3)
  - Vendor: TPA platform document
  - **⚠️ ENCRYPTED/LOCKED** - Requires vision fallback
  - Use case: Tests locked PDF handling capability

## POC Testing Strategy

### Phase 1: Build Momentum (Pair A)
Focus on unlocked Basic Plan Documents to:
1. Develop provision extraction logic
2. Build semantic mapping capability
3. Implement confidence scoring
4. Generate first comparison CSV
5. Validate end-to-end workflow

### Phase 2: Handle Locked PDFs (Pair B)
After core pipeline works, tackle encrypted documents:
1. Implement vision-based extraction
2. Validate structure preservation
3. Test on locked adoption agreement
4. Compare accuracy vs standard extraction

## Key Findings from Inspection

### Document Characteristics
- **Total documents**: 4 (2 pairs)
- **Unlocked documents**: 3 (suitable for standard extraction)
- **Locked documents**: 1 (requires vision fallback)
- **Page range**: 45-104 pages
- **Size range**: 1.0-5.1 MB

### Extraction Compatibility
- ✅ 3 documents extract cleanly via standard PDF libraries
- ⚠️ 1 document is encrypted (validates locked PDF design assumption)
- ✅ All documents are readable (no corrupted files)

### Document Types Identified
- Basic Plan Documents (BPDs): 2 documents
- Adoption Agreements: 2 documents
- Mix of vendor platforms and generic formats

## Running Inspection Tool

```bash
source venv/bin/activate
python scripts/cli.py inspect
```

The inspection tool will analyze:
- PDF metadata and structure
- Text extraction capability
- Document type indicators
- Encryption status
- File characteristics

---

*Last Updated: 2025-10-19*
*Documents analyzed and categorized for POC testing*
