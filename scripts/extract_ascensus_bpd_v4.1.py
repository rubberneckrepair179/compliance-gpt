#!/usr/bin/env python3
"""
Extract Relius BPD using v4.1 prompt with extraction gate and layout rules

v4.1 improvements:
- Extraction gate (complete sentences only, filters TOC/headers)
- Layout rules (two-column, hyphenation, continued sections)
- provision_classification (substantive vs heading)
- page_sequence assigned by post-processing (not LLM)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
import base64
import time
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import settings
from src.extraction.parallel_vision_extractor import validate_bpd_v4_1_response

# Load v4.1 prompt
def load_prompt(filename):
    prompt_path = Path(__file__).parent.parent / "prompts" / filename
    with open(prompt_path, 'r') as f:
        return f.read()

BPD_PROMPT_V4_1 = load_prompt("provision_extraction_v4.1.txt")

def process_page_batch(client, model, pdf_path, page_start, page_end):
    """Process a batch of pages with v4.1 validation and retry"""
    doc = pymupdf.open(pdf_path)

    all_batch_items = []
    failed_pages = []

    for page_num in range(page_start, min(page_end, len(doc))):
        pdf_page_number = page_num + 1

        # Build content with page image
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        img_base64 = base64.b64encode(img_data).decode('utf-8')

        content = [
            {"type": "text", "text": BPD_PROMPT_V4_1},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
            }
        ]

        # Try extraction with validation and retry logic
        max_attempts = 3
        current_model = model

        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(
                    model=current_model,
                    messages=[{"role": "user", "content": content}],
                    max_completion_tokens=16000
                )

                response_text = response.choices[0].message.content.strip()

                # Validate with v4.1 validator
                is_valid, items, error = validate_bpd_v4_1_response(response_text, pdf_page_number)

                if is_valid:
                    all_batch_items.extend(items)
                    break  # Success

                else:
                    # Attempt 1: Try repair prompt
                    if attempt == 0:
                        repair_content = [
                            {"type": "text", "text": "Output valid JSON only. Remove any text before/after the array. Do not change content."},
                            {"type": "text", "text": f"Previous response:\n{response_text}"}
                        ]
                        content = repair_content
                        continue

                    # Attempt 2: Try with GPT-5-mini
                    elif attempt == 1:
                        current_model = "gpt-5-mini"
                        # Reset to original content with page image
                        content = [
                            {"type": "text", "text": BPD_PROMPT_V4_1},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                            }
                        ]
                        continue

                    # Attempt 3: Failed all retries
                    else:
                        failed_pages.append({
                            "pdf_page": pdf_page_number,
                            "error": error,
                            "model": current_model,
                            "raw_response": response_text[:500]
                        })
                        break

            except Exception as e:
                if attempt == max_attempts - 1:
                    failed_pages.append({
                        "pdf_page": pdf_page_number,
                        "error": str(e),
                        "model": current_model
                    })
                    break

    doc.close()

    return {
        "success": len(failed_pages) == 0,
        "page_range": f"{page_start+1}-{page_end}",
        "items": all_batch_items,
        "count": len(all_batch_items),
        "failed_pages": failed_pages
    }

def main():
    sys.stdout.reconfigure(line_buffering=True)

    print("="*80)
    print("BPD V4.1 EXTRACTION - ASCENSUS (FULL DOCUMENT)")
    print("="*80)
    print()
    print("Configuration:")
    print("  - Prompt: provision_extraction_v4.1.txt (extraction gate + layout rules)")
    print("  - Model: gpt-5-nano with gpt-5-mini fallback")
    print("  - Workers: 16 (parallel)")
    print("  - Batch size: 1 page/request")
    print("  - Retry logic: 3 attempts (repair → mini fallback)")
    print("  - Validation: provision_classification + substantive-only filter")
    print("  - page_sequence: Assigned by post-processing based on array order")
    print()

    pdf_path = Path("test_data/raw/ascensus/ascensus_bpd.pdf")
    output_path = Path("test_data/extracted_vision_v4.1/ascensus_bpd_provisions.json")

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    print(f"Total pages: {total_pages}")
    print()

    client = OpenAI(api_key=settings.openai_api_key)
    model = "gpt-5-nano"

    # Create page batches (1 page per batch)
    batches = []
    for start in range(0, total_pages):
        batches.append((start, start + 1))

    print(f"Processing {len(batches)} batches...")
    start_time = time.time()

    all_items = []
    all_failed_pages = []
    completed = 0

    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(process_page_batch, client, model, pdf_path, start, end): (start, end)
            for start, end in batches
        }

        for future in as_completed(futures):
            result = future.result()
            completed += 1

            all_items.extend(result["items"])
            all_failed_pages.extend(result.get("failed_pages", []))

            if result["success"]:
                print(f"✓ Batch {result['page_range']}: {result['count']} provisions ({completed}/{len(batches)} batches)")
            else:
                failed_count = len(result.get("failed_pages", []))
                print(f"⚠ Batch {result['page_range']}: {result['count']} provisions, {failed_count} pages failed ({completed}/{len(batches)} batches)")

    elapsed = time.time() - start_time

    # Calculate success metrics
    successful_pages = total_pages - len(all_failed_pages)
    success_rate = (successful_pages / total_pages * 100) if total_pages > 0 else 0

    # Sort provisions by page number, then section number
    all_items_sorted = sorted(all_items, key=lambda x: (x.get("pdf_page", 0), x.get("section_number", "")))

    # Save results
    output_data = {
        "document": str(pdf_path),
        "doc_type": "BPD",
        "model": model,
        "prompt_version": "v4.1",
        "total_pages": total_pages,
        "successful_pages": successful_pages,
        "failed_pages_count": len(all_failed_pages),
        "success_rate_percent": round(success_rate, 1),
        "extraction_time_seconds": round(elapsed, 2),
        "pages_per_second": round(total_pages / elapsed, 2),
        "bpds": all_items_sorted,
        "failed_pages": all_failed_pages
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print()
    print("="*80)
    print(f"COMPLETED: {len(all_items)} provisions from {successful_pages}/{total_pages} pages ({success_rate:.1f}% success)")
    if len(all_failed_pages) > 0:
        print(f"⚠ FAILED PAGES: {[p['pdf_page'] for p in all_failed_pages]}")
    print(f"Time: {elapsed:.1f}s ({total_pages/elapsed:.2f} pages/sec)")
    print(f"Output: {output_path}")
    print("="*80)


if __name__ == "__main__":
    main()
