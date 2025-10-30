#!/usr/bin/env python3
"""Test v5 hierarchy extraction on page 6 only"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymupdf
import json
import base64
from openai import OpenAI
from src.config import settings
from src.extraction.parallel_vision_extractor import load_prompt, validate_json_response

def main():
    print("Testing v5 with parent_section on page 6...")

    client = OpenAI(api_key=settings.openai_api_key)
    doc = pymupdf.open("test_data/raw/relius/relius_bpd_cycle3.pdf")
    prompt_template = load_prompt("provision_extraction_v5.txt")

    # Page 6 (index 5)
    page_num = 5
    pdf_page = 6

    prompt = prompt_template.replace("{{PDF_PAGE}}", str(pdf_page))

    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")
    img_base64 = base64.b64encode(img_data).decode('utf-8')

    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
    ]

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": content}],
        max_completion_tokens=16000
    )

    response_text = response.choices[0].message.content.strip()
    is_valid, items, error = validate_json_response(response_text, pdf_page)

    if is_valid:
        print(f"✓ Valid JSON, {len(items)} provisions extracted\n")

        # Show hierarchy
        for item in items:
            indent = ""
            if item["parent_section"]:
                indent = "  " * item["section_number"].count("(")
            parent = f" (parent: {item['parent_section']})" if item["parent_section"] else ""
            print(f"{indent}{item['section_number']} - {item['section_title']}{parent}")

        print("\nFull JSON:")
        print(json.dumps(items, indent=2))
    else:
        print(f"✗ Validation failed: {error}")
        print(f"Raw response:\n{response_text[:500]}")

    doc.close()

if __name__ == "__main__":
    main()
