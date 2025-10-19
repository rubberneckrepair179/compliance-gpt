# compliance-gpt POC Setup

## Status: Phase 2A - POC Environment Ready ✅

The development environment is now configured and ready for POC implementation.

## What's Been Completed

### 1. Python Environment ✅
- Virtual environment created (`venv/`)
- Python 3.10.11 confirmed
- All dependencies installed successfully

### 2. Project Structure ✅
```
compliance-gpt/
├── src/                    # Main source code
│   ├── extraction/        # PDF extraction & provision parsing
│   ├── mapping/           # Semantic mapping & confidence scoring
│   ├── models/            # Data models (Pydantic)
│   ├── classification/    # Variance classification
│   └── export/            # CSV output generation
├── tests/                 # Unit and integration tests
│   └── fixtures/          # Test data fixtures
├── test_data/             # Sample plan documents
│   ├── raw/              # Original PDFs (gitignored)
│   └── processed/        # Extracted data (generated)
├── scripts/              # CLI tools
│   └── cli.py           # Main entry point
├── data/                 # SQLite database (gitignored)
└── venv/                 # Python virtual environment
```

### 3. Dependencies Installed ✅
- **PDF Extraction**: pypdf, pdfplumber, pillow
- **LLM Integration**: anthropic, openai
- **Data Models**: pydantic, pydantic-settings
- **Database**: sqlalchemy
- **CLI/UX**: click, rich
- **Dev Tools**: pytest, black, ruff, mypy

### 4. Configuration Files ✅
- `pyproject.toml` - Python packaging and dependencies
- `.env.example` - Environment variable template
- `.gitignore` - Protecting sensitive data and generated files

## Next Steps (CRAWL Phase - Week 1)

### Immediate: Document Analysis
1. **Place your documents**: Copy your 4 plan documents to `test_data/raw/` (keep original filenames)
2. **Run inspection tool**: `python scripts/cli.py inspect`
   - Analyzes document metadata, structure, vendor
   - Tests text extraction capability
   - Identifies locked/encrypted PDFs
   - Displays summary table and recommendations
3. **Review together**: We'll analyze the inspection results to:
   - Determine document types (BPD, adoption agreement, amendment)
   - Identify vendor platforms vs generic formats
   - Pair documents for comparison testing
   - Plan extraction strategy based on characteristics

### Day 1-2: Document Analysis & Extraction ✅
- ✅ Inspected document structure and characteristics
- ✅ Identified 2 document pairs (BPDs and Adoption Agreements)
- ✅ Confirmed 1 locked PDF requiring vision fallback
- ✅ Renamed files with source/target structure
- **Next**: Build provision extraction for unlocked documents

### Day 2-3: Provision Detection POC
- Use Claude API to identify provision boundaries
- Extract structured provision data
- Display results (JSON to terminal)

### Day 3-4: First Semantic Mapping
- Compare 2 provisions from different documents
- Generate confidence scores
- Display reasoning

## Usage

### Activate Virtual Environment
```bash
source venv/bin/activate
```

### Test Setup
```bash
python scripts/cli.py test-setup
```

### Available Commands
```bash
# Inspect documents (analyzes metadata, vendor, extraction capability)
python scripts/cli.py inspect

# Extract provisions from a document (stub)
python scripts/cli.py extract test_data/raw/document.pdf

# Compare two documents (stub)
python scripts/cli.py compare test_data/raw/doc1.pdf test_data/raw/doc2.pdf
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `ANTHROPIC_API_KEY` - Your Anthropic API key (for Claude)
- `OPENAI_API_KEY` - Your OpenAI API key (for embeddings, optional)

## Development Workflow

1. **Activate environment**: `source venv/bin/activate`
2. **Make changes** to code in `src/`
3. **Run tests**: `pytest tests/`
4. **Format code**: `black src/ tests/`
5. **Lint**: `ruff check src/ tests/`
6. **Type check**: `mypy src/`

## Exit Criteria for CRAWL Phase

- [ ] Successfully extract text from at least 1 document
- [ ] Identify 3-5 provision types automatically
- [ ] Map 3-5 provision pairs with confidence scores
- [ ] Handle at least 1 locked PDF (if applicable)

## Resources

- **Process Framework**: `/process/control_002_document_reconciliation.md`
- **Requirements**: `/requirements/functional_requirements.md`
- **Design Docs**: `/design/`
- **Project Context**: `CLAUDE.md`

---

*POC Setup Completed: October 19, 2025*
*Ready for document ingestion and extraction testing*
