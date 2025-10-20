#!/usr/bin/env python3
"""
AA Chunk Extractor - Simplified Approach

Instead of parsing complex AA structure, extract text in logical chunks
(sections/questions) and let LLM semantic mapping handle the matching.

This is faster and more robust than complex regex parsing.
"""

import pymupdf
import json
import re
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict


@dataclass
class AAChunk:
    """A chunk of AA text (could be a section, question block, or page)"""
    chunk_id: str
    chunk_text: str
    page_number: int
    chunk_type: str  # "section", "question_block", "page"
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AAChunkExtractor:
    """Extract AA content in chunks for semantic mapping"""

    def __init__(self, pdf_path: Path, chunk_size: int = 1000):
        self.pdf_path = pdf_path
        self.doc = pymupdf.open(pdf_path)
        self.chunk_size = chunk_size  # Target chars per chunk
        self.chunks: List[AAChunk] = []

    def extract_chunks(self) -> List[AAChunk]:
        """
        Extract AA in chunks.

        Strategy: Split by pages, then by section headers where possible.
        If no clear structure, chunk by character count.
        """
        print(f"Extracting chunks from {self.pdf_path.name}...")
        print(f"Total pages: {len(self.doc)}, Target chunk size: {self.chunk_size} chars")

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text()

            # Try to split by section headers
            sections = self._split_by_sections(text, page_num + 1)

            if sections:
                self.chunks.extend(sections)
            else:
                # Fallback: chunk by size
                page_chunks = self._chunk_by_size(text, page_num + 1)
                self.chunks.extend(page_chunks)

        print(f"Extracted {len(self.chunks)} chunks")

        return self.chunks

    def _split_by_sections(self, text: str, page_num: int) -> List[AAChunk]:
        """
        Split page text by individual AA questions.

        Strategy: Split by numbered questions (1., 2., 3., etc.) to get
        question-level granularity for semantic mapping.
        """
        questions = []

        # Split by numbered questions
        lines = text.split('\n')

        current_question = []
        current_question_num = ""
        current_section_title = ""

        for line in lines:
            stripped = line.strip()

            # Detect question number at start of line: "1.", "2.", etc.
            # But NOT sub-questions like "a.", "b.", or "1.1", "1.2"
            question_match = re.match(r'^(\d+)\.\s+(.+)', stripped)

            # Also detect ALL CAPS section headers as context
            is_section_header = stripped.isupper() and 10 < len(stripped) < 100

            if question_match and current_question:
                # This is a new question, save the previous one
                question_text = '\n'.join(current_question)
                if len(question_text.strip()) > 50:  # Min length filter
                    questions.append(AAChunk(
                        chunk_id=f"page_{page_num}_q_{current_question_num}",
                        chunk_text=question_text[:2500],  # Limit length
                        page_number=page_num,
                        chunk_type="question",
                        metadata={
                            "question_number": current_question_num,
                            "section_title": current_section_title
                        }
                    ))

                # Start new question
                current_question = [line]
                current_question_num = question_match.group(1)
            elif is_section_header:
                # Update section context but don't split
                current_section_title = stripped
                current_question.append(line)
            else:
                # Continue current question
                current_question.append(line)

        # Save last question
        if current_question and current_question_num:
            question_text = '\n'.join(current_question)
            if len(question_text.strip()) > 50:
                questions.append(AAChunk(
                    chunk_id=f"page_{page_num}_q_{current_question_num}",
                    chunk_text=question_text[:2500],
                    page_number=page_num,
                    chunk_type="question",
                    metadata={
                        "question_number": current_question_num,
                        "section_title": current_section_title
                    }
                ))

        return questions

    def _chunk_by_size(self, text: str, page_num: int) -> List[AAChunk]:
        """Fallback: chunk by character count"""
        chunks = []

        for i in range(0, len(text), self.chunk_size):
            chunk_text = text[i:i + self.chunk_size]
            if len(chunk_text.strip()) > 50:  # Min length
                chunks.append(AAChunk(
                    chunk_id=f"page_{page_num}_chunk_{i}",
                    chunk_text=chunk_text,
                    page_number=page_num,
                    chunk_type="text_chunk"
                ))

        return chunks

    def save_to_json(self, output_path: Path):
        """Save chunks to JSON"""
        output_data = {
            "source_document": self.pdf_path.name,
            "total_chunks": len(self.chunks),
            "chunks": [asdict(c) for c in self.chunks]
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Saved to {output_path}")

    def close(self):
        """Close PDF"""
        self.doc.close()


def main():
    """Extract chunks from both AA documents"""

    source_aa = Path("test_data/raw/source/aa/source_aa.pdf")
    target_aa = Path("test_data/raw/target/aa/target_aa.pdf")

    output_dir = Path("test_data/extracted")
    output_dir.mkdir(exist_ok=True)

    # Extract from source AA
    print("\n" + "="*80)
    print("EXTRACTING SOURCE AA (chunk-based)")
    print("="*80)

    source_extractor = AAChunkExtractor(source_aa, chunk_size=1500)
    source_chunks = source_extractor.extract_chunks()
    source_extractor.save_to_json(output_dir / "source_aa_chunks.json")
    source_extractor.close()

    # Extract from target AA
    print("\n" + "="*80)
    print("EXTRACTING TARGET AA (chunk-based)")
    print("="*80)

    target_extractor = AAChunkExtractor(target_aa, chunk_size=1500)
    target_chunks = target_extractor.extract_chunks()
    target_extractor.save_to_json(output_dir / "target_aa_chunks.json")
    target_extractor.close()

    # Summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    print(f"Source AA: {len(source_chunks)} chunks extracted")
    print(f"Target AA: {len(target_chunks)} chunks extracted")
    print(f"\nOutput saved to: {output_dir}")


if __name__ == "__main__":
    main()
