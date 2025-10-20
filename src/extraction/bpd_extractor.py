#!/usr/bin/env python3
"""
BPD Provision Extractor for Crosswalk Generation

Extracts provisions from BPD templates while preserving:
- Section numbers
- Section titles
- Provision text (template language intact)
- Topic classification

Designed for building BPD 01 ↔ BPD 05 mapping specification.
"""

import pymupdf
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class ProvisionExtraction:
    """Represents an extracted provision with metadata"""
    section_number: str
    section_title: str
    provision_text: str
    page_number: int
    topic: Optional[str] = None
    subsections: List[Dict] = None

    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []

class BPDExtractor:
    """Extracts structured provisions from BPD templates"""

    # Common topics in plan documents
    TOPICS = [
        "Plan Information",
        "Definitions",
        "Eligibility",
        "Contributions",
        "Compensation",
        "Vesting",
        "Distributions",
        "Loans",
        "Hardship",
        "Safe Harbor",
        "Top Heavy",
        "Coverage Testing",
        "Forfeitures",
        "Administration",
        "Amendment and Termination",
        "Claims Procedures",
        "ERISA Rights"
    ]

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.doc = pymupdf.open(pdf_path)
        self.provisions: List[ProvisionExtraction] = []

    def extract_table_of_contents(self) -> List[Dict]:
        """
        Extract table of contents to understand document structure.
        This helps identify section numbers and titles.
        """
        toc = []

        # Try to use PDF's built-in TOC if available
        pdf_toc = self.doc.get_toc()
        if pdf_toc:
            for level, title, page_num in pdf_toc:
                toc.append({
                    "level": level,
                    "title": title,
                    "page": page_num,
                })

        # If no TOC, we'll need to parse section headers manually
        if not toc:
            print("No embedded TOC found. Will parse sections manually.")
            toc = self._parse_sections_manually()

        return toc

    def _parse_sections_manually(self) -> List[Dict]:
        """
        Parse section headers by looking for common patterns:
        - "ARTICLE 1", "Section 1.1", etc.
        - Bold or larger font text
        - Specific formatting patterns
        """
        sections = []

        # Common section number patterns
        section_patterns = [
            r'^ARTICLE\s+(\d+)',
            r'^SECTION\s+([\d\.]+)',
            r'^(\d+\.[\d\.]*)\s+',
            r'^Article\s+(\d+)',
            r'^Section\s+([\d\.]+)',
        ]

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text()
            lines = text.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check if line matches section pattern
                for pattern in section_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        sections.append({
                            "section_number": match.group(1),
                            "title": line,
                            "page": page_num + 1,
                            "raw_text": line
                        })
                        break

        return sections

    def extract_provision(self, section_number: str, start_page: int, end_page: Optional[int] = None) -> Optional[ProvisionExtraction]:
        """
        Extract a single provision given section number and page range.
        """
        if end_page is None:
            end_page = start_page + 1

        provision_text = []

        for page_num in range(start_page - 1, min(end_page, len(self.doc))):
            page = self.doc[page_num]
            text = page.get_text()
            provision_text.append(text)

        full_text = "\n".join(provision_text)

        # Try to extract section title
        title = self._extract_section_title(full_text, section_number)

        return ProvisionExtraction(
            section_number=section_number,
            section_title=title,
            provision_text=full_text[:2000],  # Limit text length
            page_number=start_page,
        )

    def _extract_section_title(self, text: str, section_number: str) -> str:
        """Extract section title from text"""
        lines = text.split('\n')

        # Look for line containing section number
        for i, line in enumerate(lines):
            if section_number in line:
                # Title is usually the same line or next line
                title_line = line.strip()
                # Remove section number from title
                title = re.sub(r'^(ARTICLE|SECTION|Article|Section)?\s*[\d\.]+\s*', '', title_line)
                return title.strip()

        return "Unknown Title"

    def classify_topic(self, provision: ProvisionExtraction) -> str:
        """
        Classify provision by topic based on title and content.
        This is a simple keyword-based approach.
        """
        text_to_check = (provision.section_title + " " + provision.provision_text).lower()

        topic_keywords = {
            "Eligibility": ["eligibility", "eligible", "participation"],
            "Contributions": ["contribution", "elective deferral", "matching", "profit sharing"],
            "Compensation": ["compensation", "415 compensation", "414(s)"],
            "Vesting": ["vesting", "forfeiture", "years of service"],
            "Distributions": ["distribution", "withdrawal", "payment"],
            "Loans": ["loan", "participant loan"],
            "Safe Harbor": ["safe harbor", "qaca", "eaca"],
            "Top Heavy": ["top heavy", "top-heavy", "key employee"],
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in text_to_check for kw in keywords):
                return topic

        return "Other"

    def extract_all_provisions(self) -> List[ProvisionExtraction]:
        """
        Main extraction method.
        Strategy: Extract TOC, then extract each section.
        """
        print(f"Extracting provisions from {self.pdf_path.name}...")
        print(f"Total pages: {len(self.doc)}")

        # Get document structure
        toc = self.extract_table_of_contents()

        print(f"Found {len(toc)} sections in TOC")

        # Extract each section
        for i, section_info in enumerate(toc):
            section_num = section_info.get("section_number", f"SECTION_{i+1}")
            start_page = section_info.get("page", 1)

            # End page is start of next section (or end of doc)
            end_page = toc[i+1]["page"] if i+1 < len(toc) else len(self.doc)

            provision = self.extract_provision(section_num, start_page, end_page)

            if provision:
                # Classify topic
                provision.topic = self.classify_topic(provision)
                self.provisions.append(provision)

        print(f"Extracted {len(self.provisions)} provisions")

        return self.provisions

    def save_to_json(self, output_path: Path):
        """Save extracted provisions to JSON"""
        output_data = {
            "source_document": self.pdf_path.name,
            "total_provisions": len(self.provisions),
            "provisions": [asdict(p) for p in self.provisions]
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Saved to {output_path}")

    def close(self):
        """Close PDF document"""
        self.doc.close()


def main():
    """Extract provisions from both BPD documents"""

    # Paths
    source_bpd = Path("test_data/raw/source/bpd/source_bpd_01.pdf")
    target_bpd = Path("test_data/raw/target/bpd/target_bpd_05.pdf")

    output_dir = Path("test_data/extracted")
    output_dir.mkdir(exist_ok=True)

    # Extract from source BPD 01
    print("\n" + "="*80)
    print("EXTRACTING SOURCE BPD 01")
    print("="*80)

    source_extractor = BPDExtractor(source_bpd)
    source_provisions = source_extractor.extract_all_provisions()
    source_extractor.save_to_json(output_dir / "source_bpd_01_provisions.json")
    source_extractor.close()

    # Extract from target BPD 05
    print("\n" + "="*80)
    print("EXTRACTING TARGET BPD 05")
    print("="*80)

    target_extractor = BPDExtractor(target_bpd)
    target_provisions = target_extractor.extract_all_provisions()
    target_extractor.save_to_json(output_dir / "target_bpd_05_provisions.json")
    target_extractor.close()

    # Summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    print(f"Source BPD 01: {len(source_provisions)} provisions extracted")
    print(f"Target BPD 05: {len(target_provisions)} provisions extracted")
    print(f"\nOutput saved to: {output_dir}")


if __name__ == "__main__":
    main()
