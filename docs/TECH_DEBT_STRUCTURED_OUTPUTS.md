# Technical Debt: Structured Outputs & Determinism

**Date:** 2025-10-30
**Status:** Backlog - For future optimization
**Priority:** Medium (current approach works, but this would improve reliability)

---

## Expert Feedback on Determinism

**Context:** We attempted to use `temperature=0` for deterministic outputs, but discovered GPT-5-nano doesn't support it.

**Expert insight:** Even when models accept `temperature=0`, it's NOT a guarantee of determinism. OpenAI's guidance points to **structured outputs + seed** instead.

---

## Current Approach (Works but Not Optimal)

**What we do:**
- JSON validation after response
- 3-attempt retry pattern (nano → repair → mini fallback)
- Manual field checking in `validate_json_response()`
- No temperature control (nano doesn't support it)

**Success rate:** 100% on BPD extraction (v5)

**Issues:**
- Relies on retry logic to catch inconsistencies
- No formal schema enforcement
- Manual validation code

---

## Recommended Approach (Future Optimization)

### 1. Structured Outputs with JSON Schema

**Instead of:**
```python
response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": content}],
    max_completion_tokens=16000
)
# Then manually validate with validate_json_response()
```

**Do this:**
```python
schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "pdf_page": {"type": "integer", "const": PDF_PAGE},  # Pre-filled!
            "section_number": {"type": "string"},
            "section_title": {"type": "string"},
            "provision_text": {"type": "string"},
            "provision_type": {
                "type": "string",
                "enum": ["definition", "operational", "regulatory", "unknown"]
            },
            "parent_section": {"type": ["string", "null"]}
        },
        "required": ["pdf_page", "section_number", "section_title", "provision_text", "provision_type", "parent_section"],
        "additionalProperties": false
    }
}

response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": content}],
    max_completion_tokens=16000,
    response_format={"type": "json_schema", "json_schema": {"strict": true, "schema": schema}}
)
```

**Benefits:**
- ✅ Decoder constrained at generation time (not post-validation)
- ✅ `pdf_page` pre-filled with `const` (LLM must copy exact value)
- ✅ `provision_type` limited to enum (no invalid types possible)
- ✅ `additionalProperties: false` prevents extra fields
- ✅ Required fields enforced (no missing data)

### 2. Seed for Reproducibility

```python
response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": content}],
    seed=42,  # Set seed
    ...
)

# Check system_fingerprint to verify reproducibility
system_fingerprint = response.system_fingerprint
```

**Benefits:**
- ✅ Mostly stable results across runs (when seed + fingerprint match)
- ✅ Helps with debugging (same input → same output)
- ❌ Not a hard guarantee, but better than nothing

### 3. Validator + Single-Shot Repair

**Current approach:** 3 attempts (original → repair → mini)

**Optimized approach:**
- Use structured outputs (fewer failures)
- If parse still fails, single repair attempt with schema
- No need for model escalation if schema works

---

## Implementation Checklist

When we decide to implement structured outputs:

- [ ] Create JSON schema for BPD provisions
- [ ] Create JSON schema for AA provisions (when model finalized)
- [ ] Add `response_format` parameter to extractor
- [ ] Add `seed` parameter for reproducibility
- [ ] Test on sample pages (compare success rate vs current approach)
- [ ] Remove manual validation code (replaced by schema)
- [ ] Simplify retry logic (fewer attempts needed)
- [ ] Update PIPELINE.md with structured outputs details

---

## References

**OpenAI Documentation:**
- [API Reference - Temperature](https://platform.openai.com/docs/api-reference/chat/create) - "temperature can be 0–2 on chat API, but determinism isn't promised"
- [Structured Outputs Guide](https://platform.openai.com/docs/guides/structured-outputs) - JSON schema enforcement
- [Reproducible Outputs with Seed](https://cookbook.openai.com/examples/reproducible_outputs_with_the_seed_parameter) - Seed + fingerprint approach

**Expert Quote:**
> "Temperature=0 has never been a hard determinism switch; OpenAI's docs have long framed it as just the lowest sampling randomness, and they point to schema + seed for consistency instead."

> "Structured outputs over low temp - Use response_format with a JSON Schema (strict mode if available). Enforce additionalProperties:false, put const on fields like pdf_page, and keep enums tight. This constrains the decoder so you don't have to 'freeze' it."

---

## Why This is Technical Debt (Not Critical)

**Current state:**
- ✅ BPD v5 extraction: 100% success rate
- ✅ Retry logic catches failures effectively
- ✅ Manual validation works

**Why defer:**
- Current approach is working
- AA extraction is blocking path (higher priority)
- Structured outputs require schema design time
- Not needed for MVP

**Why do it eventually:**
- Reduces retry attempts (faster, cheaper)
- Better developer experience (schema-first design)
- Future-proof as models evolve
- Easier debugging with deterministic outputs

---

## Decision

**Status:** Defer to post-MVP
**Rationale:** "Shipping > optimizing" - current approach works, focus on AA extraction first
**Revisit when:** After AA extraction working, before production scaling
