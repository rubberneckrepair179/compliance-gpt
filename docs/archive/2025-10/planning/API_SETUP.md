# API Key Setup Guide

This guide walks you through setting up API keys for the compliance-gpt POC.

## Required: Anthropic API Key

The Anthropic API key is **required** for provision extraction (uses Claude Sonnet 4.5).

### Step 1: Get Your API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-...`)

### Step 2: Add Key to .env File

1. Open the `.env` file in the project root (already created for you)
2. Find this line:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```
3. Replace `your_api_key_here` with your actual key:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...your-actual-key-here...
   ```
4. Save the file

**Security Note:** The `.env` file is gitignored - your API key will never be committed to version control.

### Step 3: Verify Setup

Run the verification script:
```bash
source venv/bin/activate
python scripts/verify_api_keys.py
```

You should see:
```
✓ Anthropic API: Ready for provision extraction
```

---

## Optional: OpenAI API Key

The OpenAI API key is **optional** and only needed if you plan to use OpenAI embeddings for semantic search (currently not implemented in POC).

### Setup (Optional)

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an API key
3. Add to `.env` file:
   ```
   OPENAI_API_KEY=sk-...your-openai-key...
   ```

**For POC:** You can skip this and leave it as `your_api_key_here`.

---

## Cost Estimates (POC Phase)

### Anthropic Claude Sonnet 4.5
- **Input**: $3.00 per million tokens
- **Output**: $15.00 per million tokens

### Estimated POC Costs:
- **Per document analysis** (5 provisions from 50 pages):
  - Input: ~50,000 tokens (~$0.15)
  - Output: ~2,000 tokens (~$0.03)
  - **Total: ~$0.18 per document**

- **Full POC testing** (2 document pairs = 4 documents):
  - **Estimated total: ~$0.75**

### Cost Controls in POC:
- ✅ Limited to 5 provisions per document
- ✅ Limited to first 50 pages per document
- ✅ Temperature set to 0.0 (deterministic, no wasted retries)
- ✅ Retry logic with exponential backoff (3 attempts max)

---

## Configuration Settings

The `.env` file contains these settings (defaults are already configured):

### Model Configuration
```bash
LLM_MODEL=claude-sonnet-4-5-20251022          # Claude model for provision extraction
EMBEDDING_MODEL=text-embedding-3-small         # OpenAI embeddings (future use)
```

### Confidence Thresholds
```bash
CONFIDENCE_HIGH=0.90    # 90%+ = High confidence
CONFIDENCE_MEDIUM=0.70  # 70-89% = Medium confidence
                        # <70% = Low confidence (requires review)
```

### API Retry Settings
```bash
MAX_RETRIES=3       # Maximum retry attempts for API calls
RETRY_DELAY=1.0     # Initial retry delay in seconds (exponential backoff)
```

### Application Settings
```bash
LOG_LEVEL=INFO                    # Logging level
DATABASE_PATH=data/compliance.db  # SQLite database path (future use)
```

**You typically don't need to change these defaults.**

---

## Troubleshooting

### "Anthropic API key not configured"
- Check that you've edited `.env` (not `.env.example`)
- Verify the key starts with `sk-ant-`
- Ensure no extra spaces or quotes around the key
- Make sure `.env` is in the project root directory

### "API key test failed: Authentication failed"
- Key may be invalid or expired
- Generate a new key from Anthropic Console
- Check for any typos when copying the key

### "Module 'anthropic' not found"
- Ensure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -e ".[dev]"`

### Rate Limits
Claude Sonnet 4.5 has generous rate limits:
- **Tier 1**: 50 requests/minute, 40,000 tokens/minute
- **Tier 2**: 1,000 requests/minute, 80,000 tokens/minute

POC usage is well within these limits.

---

## Testing Your Setup

### 1. Verify API Keys
```bash
python scripts/verify_api_keys.py
```

### 2. Test Provision Extraction
```bash
python scripts/test_provision_parsing.py
```

This will:
- Extract text from `pair_a_source_bpd.pdf`
- Send to Claude for provision parsing
- Extract 5 key provisions
- Display results with confidence scores
- Save JSON to `test_data/processed/`

### Expected Output
```
✓ Extracted 81 pages
✓ Extracted 5 provisions

Provision #1
  Type: eligibility
  Section: Section 2.01
  Confidence: 95%
  Entities:
    Ages: [21]
    Service Years: [1.0]
```

---

## Security Best Practices

### DO:
- ✅ Keep `.env` file in `.gitignore` (already configured)
- ✅ Use environment variables for all secrets
- ✅ Rotate API keys periodically
- ✅ Monitor API usage in Anthropic Console

### DON'T:
- ❌ Commit `.env` to version control
- ❌ Share API keys in chat/email
- ❌ Hardcode keys in source files
- ❌ Use production keys for testing

---

## Next Steps

Once your API key is verified:

1. **Run provision extraction test:**
   ```bash
   python scripts/test_provision_parsing.py
   ```

2. **Review extracted provisions:**
   - Check console output for provision details
   - Inspect JSON file in `test_data/processed/`

3. **Validate results:**
   - Confirm provision types are correct
   - Check confidence scores are reasonable (>70%)
   - Verify entities extracted (ages, percentages)

4. **Proceed to semantic mapping:**
   - Extract provisions from both documents
   - Build semantic comparison logic
   - Generate variance report

---

*For questions or issues, check the main [README_POC.md](README_POC.md) or project documentation.*
