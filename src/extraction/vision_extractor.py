#!/usr/bin/env python3
"""
Vision-Based Document Extractor

Uses GPT-5 vision to extract:
- BPD provisions (legal rules/definitions)
- AA election options/elections (with values if filled)

Unified vision approach for reliable extraction across all document formats.
"""

import pymupdf
import json
import base64
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from io import BytesIO
from PIL import Image
from openai import OpenAI

from src.config import settings


# Vision extraction prompts
BPD_VISION_PROMPT = """You are parsing a retirement plan Basic Plan Document (BPD). Extract all provisions from this page in structured JSON format.

For each provision on this page, extract:
- section_number: The section/article reference (e.g., "1.1", "Article IV", "Section 3.2(a)")
- section_title: The section heading or defined term (if present)
- provision_text: The full legal text of the provision (preserve paragraph structure)
- provision_type: One of: "definition", "eligibility", "contribution", "vesting", "distribution", "loan", "administrative", "other"

Output JSON array:
[
  {
    "section_number": "1.1",
    "section_title": "Account",
    "provision_text": "\"Account\" means any separate notational account...",
    "provision_type": "definition"
  }
]

Important:
- Capture the complete provision text, including sub-paragraphs (a), (b), (1), (2)
- Preserve legal language exactly as written
- If a section spans multiple columns or continues, include all text
- Return ONLY the JSON array, no other text
"""

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

Output JSON array:
[
  {
    "question_number": "2",
    "question_text": "TYPE OF ENTITY",
    "election_type": "checkbox",
    "section_context": "EMPLOYER INFORMATION",
    "options": [
      {
        "label": "a",
        "text": "Corporation (including tax-exempt or non-profit Corporation)",
        "value": null
      },
      {
        "label": "d",
        "text": "Limited Liability Company that is taxed as:",
        "value": null,
        "sub_options": [
          {"label": "1", "text": "a partnership or sole proprietorship", "value": null},
          {"label": "2", "text": "a Corporation", "value": null},
          {"label": "3", "text": "an S Corporation", "value": null}
        ]
      }
    ]
  }
]

Important:
- Preserve visual hierarchy (nested options under parent options)
- For checkboxes: value is null if [ ] unchecked, "checked" if [X] or [✓]
- For fill-ins: value is null if blank (___ or empty field), or the actual text if filled
- Include ALL options visible on the page
- Return ONLY the JSON array, no other text
"""


@dataclass
class VisionExtractionResult:
    """Result from vision extraction of a single page"""
    page_number: int
    extracted_data: List[Dict[str, Any]]
    raw_response: str
    success: bool
    error: str = None


class VisionExtractor:
    """Extract document content using GPT-5 vision"""

    def __init__(self, model: str = None):
        self.model = model or settings.llm_model  # Use config default if not specified
        self.client = OpenAI(api_key=settings.openai_api_key)

    def extract_bpd(self, pdf_path: Path, output_path: Path = None) -> List[Dict]:
        """Extract provisions from BPD using vision"""
        print(f"\n{'='*80}")
        print(f"VISION EXTRACTION: {pdf_path.name} (BPD)")
        print('='*80)

        return self._extract_document(
            pdf_path=pdf_path,
            prompt=BPD_VISION_PROMPT,
            output_path=output_path,
            doc_type="BPD"
        )

    def extract_aa(self, pdf_path: Path, output_path: Path = None) -> List[Dict]:
        """Extract election options from AA using vision"""
        print(f"\n{'='*80}")
        print(f"VISION EXTRACTION: {pdf_path.name} (AA)")
        print('='*80)

        return self._extract_document(
            pdf_path=pdf_path,
            prompt=AA_VISION_PROMPT,
            output_path=output_path,
            doc_type="AA"
        )

    def _extract_document(
        self,
        pdf_path: Path,
        prompt: str,
        output_path: Path,
        doc_type: str
    ) -> List[Dict]:
        """Generic document extraction using vision"""

        doc = pymupdf.open(pdf_path)
        all_items = []

        print(f"Total pages: {len(doc)}")
        print(f"Processing with vision model: {self.model}\n")

        for page_num in range(len(doc)):
            print(f"Processing page {page_num + 1}/{len(doc)}...", end=" ")

            # Convert page to image
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)  # Higher DPI for better OCR
            img_data = pix.tobytes("png")

            # Encode image to base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')

            # Call GPT-5 vision
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_completion_tokens=16000  # Increased - GPT-5 needs higher limit for complex AA pages
                )

                response_text = response.choices[0].message.content

                # Parse JSON response
                page_items = self._parse_vision_response(response_text, page_num + 1)

                if page_items:
                    all_items.extend(page_items)
                    print(f"✓ Extracted {len(page_items)} items")
                else:
                    print(f"⚠ No items found")

            except Exception as e:
                print(f"✗ Error: {str(e)[:50]}")

        doc.close()

        # Save results
        if output_path:
            output_data = {
                "source_document": pdf_path.name,
                "document_type": doc_type,
                "total_items": len(all_items),
                "items": all_items
            }

            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)

            print(f"\n✓ Saved {len(all_items)} items to {output_path}")

        return all_items

    def _parse_vision_response(self, response_text: str, page_num: int) -> List[Dict]:
        """Parse JSON response from vision model"""

        # Remove markdown code blocks if present
        json_text = response_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]

        json_text = json_text.strip()

        try:
            items = json.loads(json_text)

            # Add page number to each item
            if isinstance(items, list):
                for item in items:
                    item["page_number"] = page_num

            return items if isinstance(items, list) else []

        except json.JSONDecodeError as e:
            print(f"\n⚠ JSON parse error: {e}")
            print(f"Response preview: {response_text[:200]}...")
            return []


def main():
    """Extract all 4 documents using vision"""

    extractor = VisionExtractor()

    # Paths
    source_bpd = Path("test_data/raw/source/bpd/source_bpd_01.pdf")
    target_bpd = Path("test_data/raw/target/bpd/target_bpd_05.pdf")
    source_aa = Path("test_data/raw/source/aa/source_aa.pdf")
    target_aa = Path("test_data/raw/target/aa/target_aa.pdf")

    output_dir = Path("test_data/extracted_vision")
    output_dir.mkdir(exist_ok=True)

    print("\n" + "="*80)
    print("VISION-BASED EXTRACTION FOR ALL DOCUMENTS")
    print("="*80)

    # Extract BPDs
    extractor.extract_bpd(source_bpd, output_dir / "source_bpd_01_provisions.json")
    extractor.extract_bpd(target_bpd, output_dir / "target_bpd_05_provisions.json")

    # Extract AAs
    extractor.extract_aa(source_aa, output_dir / "source_aa_elections.json")
    extractor.extract_aa(target_aa, output_dir / "target_aa_elections.json")

    print("\n" + "="*80)
    print("VISION EXTRACTION COMPLETE")
    print("="*80)
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
