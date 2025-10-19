"""
Provision Parser

Uses LLM (OpenAI or Anthropic) to identify and extract provision boundaries from plan documents.
POC Version: Focuses on key provision types (eligibility, contributions, vesting).
"""

from typing import List, Optional
from pathlib import Path
import json
from anthropic import Anthropic
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console

from src.config import settings
from src.models.provision import Provision, ProvisionType, ExtractionMethod, ExtractedEntities
from src.extraction.pdf_extractor import ExtractedDocument

console = Console()


class ProvisionParser:
    """
    Parses extracted document text to identify provision boundaries and extract structured data.

    Supports both OpenAI (GPT-5) and Anthropic (Claude) models.
    """

    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None, prompt_version: str = "v1") -> None:
        """
        Initialize provision parser.

        Args:
            provider: 'openai' or 'anthropic' (defaults to settings.llm_provider)
            api_key: API key (defaults to appropriate key from settings)
            prompt_version: Prompt version to use (v1, v2, etc.)
        """
        self.provider = provider or settings.llm_provider
        self.model = settings.llm_model
        self.prompt_version = prompt_version
        self.console = console

        if self.provider == "openai":
            self.api_key = api_key or settings.openai_api_key
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not found in environment or settings")
            self.client = OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            self.api_key = api_key or settings.anthropic_api_key
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment or settings")
            self.client = Anthropic(api_key=self.api_key)
        else:
            raise ValueError(f"Unknown provider: {self.provider}. Use 'openai' or 'anthropic'")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def parse_provisions(
        self,
        extracted_doc: ExtractedDocument,
        document_id: str,
        provision_types: Optional[List[ProvisionType]] = None,
        max_provisions: int = 5,
    ) -> List[Provision]:
        """
        Parse provisions from extracted document.

        POC Version: Extracts a limited number of key provisions for testing.

        Args:
            extracted_doc: Extracted document with text
            document_id: Unique document identifier
            provision_types: Provision types to extract (defaults to key types)
            max_provisions: Maximum provisions to extract (POC limitation)

        Returns:
            List of extracted provisions
        """
        if provision_types is None:
            # Focus on key provision types for POC
            provision_types = [
                ProvisionType.ELIGIBILITY,
                ProvisionType.VESTING_SCHEDULE,
                ProvisionType.EMPLOYER_CONTRIBUTION,
            ]

        self.console.print(
            f"\n[cyan]Parsing provisions from {extracted_doc.filename}...[/cyan]"
        )
        self.console.print(
            f"[dim]Provider: {self.provider.upper()} | Model: {self.model}[/dim]"
        )
        self.console.print(
            f"[dim]Target types: {', '.join([pt.value for pt in provision_types])}[/dim]"
        )
        self.console.print(f"[dim]Max provisions: {max_provisions} (POC limit)[/dim]\n")

        # Get full document text (limited for POC to manage token usage)
        full_text = self._get_text_sample(extracted_doc, max_pages=20)

        # Build prompt
        prompt = self._build_extraction_prompt(provision_types, max_provisions)

        # Call LLM based on provider
        try:
            self.console.print(f"[dim]Calling {self.provider.upper()} API...[/dim]")

            if self.provider == "openai":
                response_text = self._call_openai(prompt, full_text)
            else:  # anthropic
                response_text = self._call_anthropic(prompt, full_text)

            # Parse response
            provisions = self._parse_llm_response(
                response_text, document_id, extracted_doc.filename
            )

            self.console.print(
                f"[green]✓ Extracted {len(provisions)} provision(s)[/green]\n"
            )

            return provisions

        except Exception as e:
            self.console.print(f"[red]Error calling {self.provider.upper()} API: {e}[/red]")
            raise

    def _call_openai(self, prompt: str, document_text: str) -> str:
        """Call OpenAI API."""
        # GPT-4.1 and other chat models use max_tokens, GPT-5 uses max_completion_tokens
        # Try to determine which parameter to use
        params = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an ERISA compliance specialist expert at analyzing retirement plan documents. Extract provisions with high precision and output structured JSON.",
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nDOCUMENT TEXT:\n\n{document_text}",
                },
            ],
        }

        # GPT-5 uses max_completion_tokens, GPT-4.x uses max_tokens
        if "gpt-5" in self.model.lower():
            params["max_completion_tokens"] = 4000
        else:
            params["max_tokens"] = 4000
            params["temperature"] = 0.0  # Only supported by non-reasoning models

        response = self.client.chat.completions.create(**params)

        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str, document_text: str) -> str:
        """Call Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,  # Claude 3.5 Sonnet max is 8192
            temperature=0.0,  # Deterministic for extraction
            system="You are an ERISA compliance specialist expert at analyzing retirement plan documents. Extract provisions with high precision.",
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nDOCUMENT TEXT:\n\n{document_text}",
                }
            ],
        )

        return response.content[0].text

    def _get_text_sample(self, extracted_doc: ExtractedDocument, max_pages: int = None) -> str:
        """
        Get text sample from document.

        Args:
            extracted_doc: Extracted document
            max_pages: Maximum pages to include (None = all pages)
        """
        pages_text = []
        pages_to_use = extracted_doc.pages if max_pages is None else extracted_doc.pages[:max_pages]

        for page in pages_to_use:
            if page.text:
                pages_text.append(f"[PAGE {page.page_number}]\n{page.text}")

        return "\n\n".join(pages_text)

    def _build_extraction_prompt(
        self, provision_types: List[ProvisionType], max_provisions: int
    ) -> str:
        """Build LLM prompt for provision extraction by loading from external file."""
        # Load prompt template from file
        prompt_file = Path(f"prompts/provision_extraction_{self.prompt_version}.txt")

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_file, "r", encoding="utf-8") as f:
            # Skip header lines (comments starting with #)
            lines = []
            for line in f:
                if not line.strip().startswith("#"):
                    lines.append(line)
            template = "".join(lines)

        # Format with parameters
        types_str = ", ".join([f'"{pt.value}"' for pt in provision_types])
        return template.format(
            max_provisions=max_provisions,
            provision_types=types_str
        )

    def _build_extraction_prompt_old(
        self, provision_types: List[ProvisionType], max_provisions: int
    ) -> str:
        """OLD: Hardcoded prompt (deprecated - kept for reference)."""
        types_str = ", ".join([f'"{pt.value}"' for pt in provision_types])

        return f"""Extract up to {max_provisions} key provisions from this retirement plan document.

PROVISION TYPES TO EXTRACT:
{types_str}

For each provision, output a JSON object with these fields:
- provision_type: One of the types listed above
- section_reference: The section number/letter from the document (e.g., "Section 2.01", "Article III")
- section_title: The section title if present
- provision_text: The FULL text of the provision (don't truncate)
- confidence_score: Your confidence in the extraction (0.0-1.0)
- extracted_entities: Object with:
  - ages: List of age values mentioned
  - service_years: List of service requirements in years
  - percentages: List of percentages as decimals (e.g., 0.03 for 3%)
  - keywords: Important terms (e.g., ["Safe Harbor", "Highly Compensated Employee"])

EXTRACTION RULES:
1. Extract complete provision text (don't truncate mid-sentence)
2. Preserve original section numbers from document
3. If you're uncertain about provision type, use lower confidence score
4. Extract at most {max_provisions} provisions total
5. Focus on the most important/substantive provisions

OUTPUT FORMAT:
Return a JSON array of provision objects. Example:

```json
[
  {{
    "provision_type": "eligibility",
    "section_reference": "Section 2.01",
    "section_title": "Eligibility to Participate",
    "provision_text": "Full text of the provision here...",
    "confidence_score": 0.95,
    "extracted_entities": {{
      "ages": [21],
      "service_years": [1.0],
      "percentages": [],
      "keywords": ["Year of Service", "Hours of Service"]
    }}
  }}
]
```

Return ONLY the JSON array, no other text."""

    def _parse_llm_response(
        self, response_text: str, document_id: str, filename: str
    ) -> List[Provision]:
        """Parse LLM's JSON response into Provision objects."""
        # Extract JSON from response (handle code blocks)
        json_text = response_text.strip()

        # Remove markdown code blocks if present
        if json_text.startswith("```json"):
            json_text = json_text[7:]  # Remove ```json
        if json_text.startswith("```"):
            json_text = json_text[3:]  # Remove ```
        if json_text.endswith("```"):
            json_text = json_text[:-3]  # Remove closing ```

        json_text = json_text.strip()

        # Parse JSON
        try:
            provisions_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            self.console.print(f"[red]Failed to parse JSON response: {e}[/red]")
            self.console.print(f"[dim]Response text:\n{response_text[:500]}...[/dim]")
            raise

        # Convert to Provision objects
        provisions: List[Provision] = []

        for prov_data in provisions_data:
            try:
                # Build ExtractedEntities
                entities = ExtractedEntities(
                    ages=prov_data.get("extracted_entities", {}).get("ages", []),
                    service_years=prov_data.get("extracted_entities", {}).get(
                        "service_years", []
                    ),
                    percentages=prov_data.get("extracted_entities", {}).get("percentages", []),
                    dollar_amounts=prov_data.get("extracted_entities", {}).get(
                        "dollar_amounts", []
                    ),
                    dates=prov_data.get("extracted_entities", {}).get("dates", []),
                    keywords=prov_data.get("extracted_entities", {}).get("keywords", []),
                )

                # Build Provision
                provision = Provision(
                    document_id=document_id,
                    provision_type=ProvisionType(prov_data["provision_type"]),
                    section_reference=prov_data["section_reference"],
                    section_title=prov_data.get("section_title"),
                    provision_text=prov_data["provision_text"],
                    extraction_method=ExtractionMethod.TEXT_API,
                    confidence_score=prov_data["confidence_score"],
                    extracted_entities=entities,
                )

                provisions.append(provision)

            except Exception as e:
                self.console.print(f"[yellow]⚠️  Skipped provision due to error: {e}[/yellow]")
                continue

        return provisions

    def save_provisions(self, provisions: List[Provision], output_path: Path) -> None:
        """Save provisions to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        provisions_dict = [prov.model_dump(mode="json") for prov in provisions]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(provisions_dict, f, indent=2, default=str)

        self.console.print(f"[green]✓ Saved {len(provisions)} provisions to:[/green] {output_path}")
