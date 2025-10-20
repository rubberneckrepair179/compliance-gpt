#!/usr/bin/env python3
"""
Test vision extraction on a single page before running full extraction
"""

import pymupdf
import json
import base64
from pathlib import Path
from openai import OpenAI
from src.config import settings

AA_VISION_PROMPT = """You are parsing a retirement plan Adoption Agreement (AA). Extract all election questions/options from this page in structured JSON format.

For each election question on this page, extract:
- question_number: The main question number (e.g., "1", "2", "3")
- question_text: The full question text or election prompt
- election_type: One of: "checkbox", "fill_in", "radio", "multi_select"
- section_context: Any section header that applies (e.g., "EMPLOYER INFORMATION")
- options: Array of all available choices

For each option in the options array:
  - label: The option identifier (e.g., "a", "b", "1", "2")
  - text: The option text
  - value: null (if unchecked/blank), "checked" (if [X] or [✓]), or the filled-in text
  - sub_options: Array of nested options (if any), same structure

Important:
- Preserve visual hierarchy (nested options under parent options)
- For checkboxes: value is null if [ ] unchecked, "checked" if [X] or [✓]
- For fill-ins: value is null if blank (___ or empty field), or the actual text if filled
- Include ALL options visible on the page
- Return ONLY valid JSON array, no other text
"""

def test_single_page():
    """Test vision extraction on page 1 of target AA"""

    pdf_path = Path("test_data/raw/target/aa/target_aa.pdf")

    print("Opening PDF and extracting page 1 as image...")
    doc = pymupdf.open(pdf_path)
    page = doc[0]  # First page

    # Convert to image
    pix = page.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")
    img_base64 = base64.b64encode(img_data).decode('utf-8')

    doc.close()

    print("Calling GPT-5 vision...")
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": AA_VISION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    }
                ]
            }
        ],
        max_completion_tokens=16000  # Increased from 4000
    )

    print(f"\nAPI Response Debug:")
    print(f"Model: {response.model}")
    print(f"Finish reason: {response.choices[0].finish_reason}")
    print(f"Message role: {response.choices[0].message.role}")
    print(f"Has refusal: {hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal is not None}")
    if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
        print(f"Refusal reason: {response.choices[0].message.refusal}")
    print(f"Content length: {len(response.choices[0].message.content) if response.choices[0].message.content else 0}")

    response_text = response.choices[0].message.content

    print("\n" + "="*80)
    print("VISION MODEL RESPONSE:")
    print("="*80)
    print(response_text)

    # Try to parse as JSON
    print("\n" + "="*80)
    print("PARSING JSON:")
    print("="*80)

    try:
        # Remove markdown if present
        json_text = response_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()

        data = json.loads(json_text)
        print(f"✓ Successfully parsed JSON!")
        print(f"✓ Extracted {len(data)} questions/sections")
        print("\nParsed data:")
        print(json.dumps(data, indent=2))

    except json.JSONDecodeError as e:
        print(f"✗ JSON parse error: {e}")
        print(f"Response was: {response_text[:500]}...")

if __name__ == "__main__":
    test_single_page()
