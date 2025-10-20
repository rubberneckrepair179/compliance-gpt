#!/usr/bin/env python3
"""
Test GPT-5-nano vision extraction on first 5 pages to compare with mini.
"""
import sys
from pathlib import Path
import pymupdf
import json
import base64
from openai import OpenAI
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import settings

AA_PROMPT = """You are parsing a retirement plan Adoption Agreement (AA). Extract all election questions/options from this page in structured JSON format.

For each election question on this page, extract:
- question_number: The main question number (e.g., "1", "2", "3")
- question_text: The full question text or election prompt
- election_type: One of: "checkbox", "fill_in", "radio", "multi_select"
- section_context: Any section header that applies (e.g., "EMPLOYER INFORMATION")
- options: Array of all available choices

For each option:
  - label: The option identifier (e.g., "a", "b", "1", "2")
  - text: The option text
  - value: null (if unchecked/blank), "checked" (if [X] or [✓]), or the filled-in text
  - sub_options: Array of nested options (if any), same structure

Return ONLY the JSON array, no other text."""

def main():
    sys.stdout.reconfigure(line_buffering=True)

    print("Testing GPT-5-NANO on first 5 pages of target AA...\n")

    client = OpenAI(api_key=settings.openai_api_key)
    pdf_path = Path("test_data/raw/target/aa/target_aa.pdf")
    doc = pymupdf.open(pdf_path)

    all_items = []
    start_time = time.time()

    for page_num in range(min(5, len(doc))):
        print(f"Page {page_num + 1}/5...", end=" ", flush=True)

        # Convert to image
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        img_base64 = base64.b64encode(img_data).decode('utf-8')

        # Call GPT-5-nano
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": AA_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            }],
            max_completion_tokens=16000
        )

        try:
            items = json.loads(response.choices[0].message.content)
            all_items.extend(items)
            print(f"✓ Extracted {len(items)} items")
        except json.JSONDecodeError as e:
            print(f"✗ JSON error: {e}")

    doc.close()
    elapsed = time.time() - start_time

    # Save results
    output_path = Path("test_data/extracted_vision/test_5_pages_gpt5nano.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump({
            "pages": 5,
            "model": "gpt-5-nano",
            "elapsed_seconds": round(elapsed, 2),
            "elections": all_items
        }, f, indent=2)

    print(f"\n{'='*80}")
    print(f"RESULTS: {len(all_items)} total items from 5 pages")
    print(f"Time: {elapsed:.1f} seconds ({elapsed/5:.1f}s per page)")
    print(f"Saved to: {output_path}")
    print(f"{'='*80}\n")

    # Show first 2 items
    for i, item in enumerate(all_items[:2], 1):
        print(f"{i}. Q{item.get('question_number')}: {item.get('question_text', '')[:70]}")
        print(f"   Type: {item.get('election_type')}, Options: {len(item.get('options', []))}\n")

if __name__ == "__main__":
    main()
