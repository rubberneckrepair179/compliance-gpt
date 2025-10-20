#!/usr/bin/env python3
"""
AA (Adoption Agreement) Election Extractor

Extracts election questions and options from AA templates for crosswalk mapping.
Different from BPD extraction - focuses on questions, checkboxes, and fill-in fields.
"""

import pymupdf
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class AAElection:
    """Represents an election question/option in an Adoption Agreement"""
    question_number: str
    section_title: str
    question_text: str
    election_type: str  # "checkbox", "fill_in", "radio", "text_entry"
    options: List[str]  # List of checkbox options or fill-in prompts
    page_number: int
    topic: Optional[str] = None
    notes: Optional[str] = None

class AAExtractor:
    """Extracts election questions from Adoption Agreement templates"""

    # Common AA section topics
    TOPICS = [
        "Employer Information",
        "Plan Status",
        "Effective Date",
        "Plan Year",
        "Eligibility",
        "Compensation Definition",
        "Contributions",
        "Elective Deferrals",
        "Matching Contributions",
        "Profit Sharing",
        "Safe Harbor",
        "Vesting",
        "Distributions",
        "Loans",
        "Top Heavy",
        "Plan Administration",
    ]

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.doc = pymupdf.open(pdf_path)
        self.elections: List[AAElection] = []

    def extract_elections(self) -> List[AAElection]:
        """
        Main extraction method.
        Strategy: Parse each page, identify question patterns.
        """
        print(f"Extracting elections from {self.pdf_path.name}...")
        print(f"Total pages: {len(self.doc)}")

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text()

            # Parse elections from page
            page_elections = self._parse_page_elections(text, page_num + 1)
            self.elections.extend(page_elections)

        print(f"Extracted {len(self.elections)} elections")

        return self.elections

    def _parse_page_elections(self, text: str, page_num: int) -> List[AAElection]:
        """
        Parse election questions from a page of text.

        AA election patterns to detect:
        1. Numbered questions: "1. EMPLOYER'S NAME"
        2. Lettered sub-questions: "a. [  ] Option A"
        3. Fill-in fields: "Name: __________"
        4. Checkbox patterns: "[  ]", "[ ]", "☐"
        """
        elections = []

        # Split into lines for parsing
        lines = text.split('\n')

        current_question = None
        current_options = []

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Pattern 1: Main question number (e.g., "1. EMPLOYER'S NAME")
            main_q_match = re.match(r'^(\d+)\.\s+(.+)', line)
            if main_q_match:
                # Save previous question if exists
                if current_question:
                    elections.append(self._create_election(
                        current_question,
                        current_options,
                        page_num
                    ))

                # Start new question
                q_num = main_q_match.group(1)
                q_text = main_q_match.group(2)

                current_question = {
                    "number": q_num,
                    "text": q_text,
                    "section_title": self._extract_section_title(q_text),
                }
                current_options = []
                continue

            # Pattern 2: Checkbox options (e.g., "a. [  ] Corporation")
            checkbox_match = re.match(r'^([a-z]\.?|\d+\.)\s*\[[\s\u2610X✓x]*\]\s*(.+)', line)
            if checkbox_match and current_question:
                option_label = checkbox_match.group(1)
                option_text = checkbox_match.group(2)
                current_options.append(f"{option_label} {option_text}")
                continue

            # Pattern 3: Fill-in fields (e.g., "Name: ___________")
            fill_match = re.search(r'(\w[\w\s]+):\s*_{3,}', line)
            if fill_match and current_question:
                field_label = fill_match.group(1).strip()
                current_options.append(f"FILL_IN: {field_label}")
                continue

            # If we're in a question and line looks like continuation, add to text
            if current_question and len(line) > 20:
                current_question["text"] += " " + line

        # Save last question
        if current_question:
            elections.append(self._create_election(
                current_question,
                current_options,
                page_num
            ))

        return elections

    def _create_election(
        self,
        question_data: Dict,
        options: List[str],
        page_num: int
    ) -> AAElection:
        """Create AAElection object from parsed data"""

        # Determine election type
        if any("FILL_IN:" in opt for opt in options):
            election_type = "fill_in"
        elif len(options) > 1:
            election_type = "checkbox"
        elif len(options) == 1:
            election_type = "radio"
        else:
            election_type = "text_entry"

        # Classify topic
        topic = self._classify_topic(question_data["text"])

        return AAElection(
            question_number=question_data["number"],
            section_title=question_data.get("section_title", ""),
            question_text=question_data["text"][:500],  # Limit length
            election_type=election_type,
            options=options[:20],  # Limit options
            page_number=page_num,
            topic=topic,
        )

    def _extract_section_title(self, text: str) -> str:
        """Extract section title from question text"""
        # Remove all-caps titles (common in AAs)
        if text.isupper() and len(text) < 100:
            return text

        # Otherwise return first 100 chars
        return text[:100]

    def _classify_topic(self, text: str) -> str:
        """Classify question by topic based on keywords"""
        text_lower = text.lower()

        topic_keywords = {
            "Employer Information": ["employer", "name", "address", "tin", "fiscal year"],
            "Plan Status": ["new plan", "amendment", "restatement", "cycle"],
            "Effective Date": ["effective date", "adoption date"],
            "Eligibility": ["eligibility", "eligible", "age", "service", "entry date"],
            "Compensation Definition": ["compensation", "414(s)", "415"],
            "Elective Deferrals": ["elective deferral", "401(k)", "pre-tax", "roth"],
            "Matching Contributions": ["matching", "match"],
            "Profit Sharing": ["profit sharing", "discretionary"],
            "Safe Harbor": ["safe harbor", "qaca", "eaca"],
            "Vesting": ["vesting", "forfeiture"],
            "Distributions": ["distribution", "hardship", "withdrawal"],
            "Loans": ["loan", "participant loan"],
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return topic

        return "Other"

    def save_to_json(self, output_path: Path):
        """Save extracted elections to JSON"""
        output_data = {
            "source_document": self.pdf_path.name,
            "total_elections": len(self.elections),
            "elections": [asdict(e) for e in self.elections]
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Saved to {output_path}")

    def close(self):
        """Close PDF document"""
        self.doc.close()


def main():
    """Extract elections from both AA documents"""

    # Paths
    source_aa = Path("test_data/raw/source/aa/source_aa.pdf")
    target_aa = Path("test_data/raw/target/aa/target_aa.pdf")

    output_dir = Path("test_data/extracted")
    output_dir.mkdir(exist_ok=True)

    # Extract from source AA
    print("\n" + "="*80)
    print("EXTRACTING SOURCE AA")
    print("="*80)

    source_extractor = AAExtractor(source_aa)
    source_elections = source_extractor.extract_elections()
    source_extractor.save_to_json(output_dir / "source_aa_elections.json")
    source_extractor.close()

    # Extract from target AA
    print("\n" + "="*80)
    print("EXTRACTING TARGET AA")
    print("="*80)

    target_extractor = AAExtractor(target_aa)
    target_elections = target_extractor.extract_elections()
    target_extractor.save_to_json(output_dir / "target_aa_elections.json")
    target_extractor.close()

    # Summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    print(f"Source AA: {len(source_elections)} elections extracted")
    print(f"Target AA: {len(target_elections)} elections extracted")
    print(f"\nOutput saved to: {output_dir}")


if __name__ == "__main__":
    main()
