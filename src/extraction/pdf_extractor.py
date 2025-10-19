"""
PDF Text Extraction Module

Handles extraction of text from plan documents with fallback for locked PDFs.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pypdf
import pdfplumber
from rich.console import Console

console = Console()


@dataclass
class ExtractedPage:
    """Represents text extracted from a single page."""

    page_number: int
    text: str
    extraction_method: str  # 'text_api' or 'vision_fallback'
    confidence: float = 1.0  # 1.0 for text_api, variable for vision


@dataclass
class ExtractedDocument:
    """Complete extracted document with metadata."""

    filename: str
    total_pages: int
    pages: List[ExtractedPage]
    is_encrypted: bool
    extraction_method: str
    metadata: Dict[str, str]


class PDFExtractor:
    """
    Extracts text from PDF documents.

    Handles both standard extraction and locked/encrypted PDFs (vision fallback).
    """

    def __init__(self) -> None:
        self.console = console

    def extract(self, pdf_path: Path) -> ExtractedDocument:
        """
        Extract text from a PDF document.

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractedDocument with pages and metadata

        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If extraction fails completely
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self.console.print(f"[cyan]Extracting text from:[/cyan] {pdf_path.name}")

        # Check if encrypted
        is_encrypted = self._is_encrypted(pdf_path)

        if is_encrypted:
            self.console.print(
                "[yellow]⚠️  Document is encrypted - vision fallback would be needed[/yellow]"
            )
            self.console.print(
                "[yellow]   For POC: Skipping encrypted documents (Phase 2)[/yellow]"
            )
            raise ValueError(
                f"Document {pdf_path.name} is encrypted. Vision fallback not yet implemented."
            )

        # Extract with standard method
        return self._extract_standard(pdf_path)

    def _is_encrypted(self, pdf_path: Path) -> bool:
        """Check if PDF is encrypted/locked."""
        try:
            reader = pypdf.PdfReader(pdf_path)
            return reader.is_encrypted
        except Exception as e:
            self.console.print(f"[red]Error checking encryption: {e}[/red]")
            return False

    def _extract_standard(self, pdf_path: Path) -> ExtractedDocument:
        """
        Extract text using standard PDF text API (pdfplumber).

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractedDocument with extracted pages
        """
        pages: List[ExtractedPage] = []
        metadata: Dict[str, str] = {}

        with pdfplumber.open(pdf_path) as pdf:
            # Extract metadata
            if pdf.metadata:
                metadata = {
                    "title": pdf.metadata.get("Title", ""),
                    "author": pdf.metadata.get("Author", ""),
                    "creator": pdf.metadata.get("Creator", ""),
                    "producer": pdf.metadata.get("Producer", ""),
                }

            total_pages = len(pdf.pages)
            self.console.print(f"[dim]Processing {total_pages} pages...[/dim]")

            # Extract text from each page
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()

                if text:
                    pages.append(
                        ExtractedPage(
                            page_number=page_num,
                            text=text.strip(),
                            extraction_method="text_api",
                            confidence=1.0,
                        )
                    )
                else:
                    # Empty page or extraction failed
                    self.console.print(
                        f"[yellow]⚠️  Page {page_num}: No text extracted[/yellow]"
                    )
                    pages.append(
                        ExtractedPage(
                            page_number=page_num,
                            text="",
                            extraction_method="text_api",
                            confidence=0.0,
                        )
                    )

                # Progress indicator
                if page_num % 10 == 0:
                    self.console.print(f"[dim]   Processed {page_num}/{total_pages} pages[/dim]")

        self.console.print(
            f"[green]✓ Extracted text from {len(pages)} pages[/green]"
        )

        return ExtractedDocument(
            filename=pdf_path.name,
            total_pages=total_pages,
            pages=pages,
            is_encrypted=False,
            extraction_method="text_api",
            metadata=metadata,
        )

    def get_full_text(self, extracted_doc: ExtractedDocument) -> str:
        """
        Get all text from document as single string.

        Args:
            extracted_doc: Extracted document

        Returns:
            Concatenated text from all pages
        """
        return "\n\n".join(
            f"[PAGE {page.page_number}]\n{page.text}" for page in extracted_doc.pages if page.text
        )

    def get_page_text(self, extracted_doc: ExtractedDocument, page_number: int) -> Optional[str]:
        """
        Get text from a specific page.

        Args:
            extracted_doc: Extracted document
            page_number: Page number (1-indexed)

        Returns:
            Page text or None if page doesn't exist
        """
        for page in extracted_doc.pages:
            if page.page_number == page_number:
                return page.text
        return None

    def save_extracted_text(self, extracted_doc: ExtractedDocument, output_path: Path) -> None:
        """
        Save extracted text to file.

        Args:
            extracted_doc: Extracted document
            output_path: Path to save text file
        """
        full_text = self.get_full_text(extracted_doc)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_text, encoding="utf-8")

        self.console.print(f"[green]✓ Saved extracted text to:[/green] {output_path}")
