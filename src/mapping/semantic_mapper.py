"""
Semantic Mapper

Compares provisions across documents using embedding-based candidate matching
followed by LLM verification.

Architecture:
1. Generate embeddings for all provisions (cheap, fast)
2. Compute cosine similarity matrix (find top candidates)
3. LLM verification for top candidates only (expensive, accurate)
"""

from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import numpy as np
from openai import OpenAI
from anthropic import Anthropic
from rich.console import Console

from src.config import settings
from src.models.provision import Provision
from src.models.mapping import (
    ProvisionMapping,
    MappingCandidate,
    DocumentComparison,
    VarianceType,
    ImpactLevel,
)

console = Console()


class SemanticMapper:
    """
    Maps provisions across documents using hybrid embedding + LLM approach.

    Cost-optimized: Uses cheap embeddings for candidate matching,
    expensive LLM calls only for verification.
    """

    def __init__(self, provider: str = None, top_k: int = 3, max_workers: int = 16) -> None:
        """
        Initialize semantic mapper.

        Args:
            provider: 'openai' or 'anthropic' (defaults to settings.llm_provider)
            top_k: Number of candidates to verify with LLM (default 3)
            max_workers: Number of parallel workers for LLM verification (default 16)
        """
        self.provider = provider or settings.llm_provider
        self.top_k = top_k
        self.max_workers = max_workers
        self.console = console

        # Initialize clients
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.openai_client = None

        if self.provider == "anthropic" and settings.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
        else:
            self.anthropic_client = None

        # Load prompt
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load semantic mapping prompt from external file."""
        prompt_path = Path("prompts/semantic_mapping_v1.txt")
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            # Skip header lines (comments starting with #)
            lines = []
            for line in f:
                if not line.strip().startswith("#"):
                    lines.append(line)
            return "".join(lines)

    def generate_embeddings(self, provisions: List[Provision]) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for all provisions.

        Args:
            provisions: List of provisions to embed

        Returns:
            Dict mapping provision_id to embedding vector
        """
        if not self.openai_client:
            raise ValueError("OpenAI client required for embeddings")

        self.console.print(
            f"[cyan]Generating embeddings for {len(provisions)} provisions...[/cyan]"
        )

        embeddings = {}

        # Batch embed (OpenAI supports up to 2048 inputs per batch)
        texts = [prov.provision_text for prov in provisions]
        provision_ids = [str(prov.provision_id) for prov in provisions]

        try:
            response = self.openai_client.embeddings.create(
                model=settings.embedding_model, input=texts
            )

            for i, embedding_obj in enumerate(response.data):
                embeddings[provision_ids[i]] = np.array(embedding_obj.embedding)

            self.console.print(f"[green]✓ Generated {len(embeddings)} embeddings[/green]\n")

        except Exception as e:
            self.console.print(f"[red]Error generating embeddings: {e}[/red]")
            raise

        return embeddings

    def compute_similarity_matrix(
        self,
        source_provisions: List[Provision],
        target_provisions: List[Provision],
        source_embeddings: Dict[str, np.ndarray],
        target_embeddings: Dict[str, np.ndarray],
    ) -> Dict[str, List[MappingCandidate]]:
        """
        Compute cosine similarity matrix and find top candidates.

        Args:
            source_provisions: Source document provisions
            target_provisions: Target document provisions
            source_embeddings: Source embeddings dict
            target_embeddings: Target embeddings dict

        Returns:
            Dict mapping source_provision_id to list of top candidates
        """
        self.console.print(
            f"[cyan]Computing similarity matrix ({len(source_provisions)}×{len(target_provisions)})...[/cyan]"
        )

        candidates_map = {}

        for source_prov in source_provisions:
            source_id = str(source_prov.provision_id)
            source_vec = source_embeddings[source_id]

            similarities = []

            for target_prov in target_provisions:
                target_id = str(target_prov.provision_id)
                target_vec = target_embeddings[target_id]

                # Cosine similarity
                similarity = float(
                    np.dot(source_vec, target_vec)
                    / (np.linalg.norm(source_vec) * np.linalg.norm(target_vec))
                )

                similarities.append(
                    MappingCandidate(
                        target_provision_id=target_prov.provision_id,
                        embedding_similarity=similarity,
                    )
                )

            # Sort by similarity and take top K
            top_candidates = sorted(
                similarities, key=lambda x: x.embedding_similarity, reverse=True
            )[: self.top_k]

            candidates_map[source_id] = top_candidates

        self.console.print(
            f"[green]✓ Found top {self.top_k} candidates for each source provision[/green]\n"
        )

        return candidates_map

    def verify_mapping(
        self, source_prov: Provision, target_prov: Provision, embedding_score: float
    ) -> ProvisionMapping:
        """
        Use LLM to verify semantic mapping between two provisions.

        Args:
            source_prov: Source provision
            target_prov: Target provision
            embedding_score: Cosine similarity score from embeddings

        Returns:
            ProvisionMapping with LLM assessment
        """
        # Build prompt with provision details
        prompt = self.prompt_template.format(
            source_type=source_prov.provision_type.value,
            source_section=source_prov.section_reference,
            source_text=source_prov.provision_text,
            target_type=target_prov.provision_type.value,
            target_section=target_prov.section_reference,
            target_text=target_prov.provision_text,
        )

        # Call LLM
        try:
            if self.provider == "openai":
                response_text = self._call_openai(prompt)
            else:
                response_text = self._call_anthropic(prompt)

            # Parse JSON response
            result = self._parse_llm_response(response_text)

            # Create mapping
            mapping = ProvisionMapping(
                source_provision_id=source_prov.provision_id,
                target_provision_id=target_prov.provision_id,
                embedding_similarity=embedding_score,
                llm_similarity=result["similarity_score"],
                is_match=result["is_match"],
                variance_type=VarianceType(result["variance_type"]),
                impact_level=ImpactLevel(result["impact_level"]),
                reasoning=result["reasoning"],
                confidence_score=result["confidence_score"],
            )

            return mapping

        except Exception as e:
            self.console.print(f"[yellow]⚠️  Error verifying mapping: {e}[/yellow]")
            # Return low-confidence mapping on error
            return ProvisionMapping(
                source_provision_id=source_prov.provision_id,
                target_provision_id=target_prov.provision_id,
                embedding_similarity=embedding_score,
                llm_similarity=0.0,
                is_match=False,
                variance_type=VarianceType.NONE,
                impact_level=ImpactLevel.NONE,
                reasoning=f"LLM verification failed: {str(e)}",
                confidence_score=0.0,
            )

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = self.openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an ERISA compliance specialist. Return ONLY valid JSON, no other text.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.0,
        )
        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        response = self.anthropic_client.messages.create(
            model=settings.llm_model,
            max_tokens=1000,
            temperature=0.0,
            system="You are an ERISA compliance specialist. Return ONLY valid JSON.",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse LLM JSON response."""
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
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            self.console.print(f"[red]Failed to parse LLM response: {e}[/red]")
            self.console.print(f"[dim]Response: {response_text[:200]}...[/dim]")
            raise

    def compare_documents(
        self,
        source_provisions: List[Provision],
        target_provisions: List[Provision],
        source_doc_id: str,
        target_doc_id: str,
    ) -> DocumentComparison:
        """
        Complete document comparison workflow.

        Args:
            source_provisions: Source document provisions
            target_provisions: Target document provisions
            source_doc_id: Source document ID
            target_doc_id: Target document ID

        Returns:
            DocumentComparison with all mappings
        """
        self.console.print(f"\n[cyan bold]Comparing Documents[/cyan bold]")
        self.console.print(f"[dim]Source: {source_doc_id} ({len(source_provisions)} provisions)[/dim]")
        self.console.print(
            f"[dim]Target: {target_doc_id} ({len(target_provisions)} provisions)[/dim]\n"
        )

        # Step 1: Generate embeddings
        all_provisions = source_provisions + target_provisions
        all_embeddings = self.generate_embeddings(all_provisions)

        source_embeddings = {
            str(p.provision_id): all_embeddings[str(p.provision_id)]
            for p in source_provisions
        }
        target_embeddings = {
            str(p.provision_id): all_embeddings[str(p.provision_id)]
            for p in target_provisions
        }

        # Step 2: Find candidates
        candidates_map = self.compute_similarity_matrix(
            source_provisions, target_provisions, source_embeddings, target_embeddings
        )

        # Step 3: LLM verification (parallel)
        self.console.print(
            f"[cyan]Verifying top candidates with LLM ({self.provider.upper()}, {self.max_workers} workers)...[/cyan]"
        )

        all_mappings = []
        total_verifications = len(source_provisions) * self.top_k

        # Get target provision objects
        target_prov_map = {str(p.provision_id): p for p in target_provisions}

        # Build verification tasks
        verification_tasks = []
        for source_prov in source_provisions:
            source_id = str(source_prov.provision_id)
            candidates = candidates_map[source_id]

            for candidate in candidates:
                target_id = str(candidate.target_provision_id)
                target_prov = target_prov_map[target_id]
                verification_tasks.append((source_prov, target_prov, candidate.embedding_similarity))

        # Parallel verification
        verified_count = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.verify_mapping, source_prov, target_prov, emb_score): (source_prov, target_prov)
                for source_prov, target_prov, emb_score in verification_tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_task):
                try:
                    mapping = future.result()
                    all_mappings.append(mapping)
                    verified_count += 1

                    if verified_count % 50 == 0:
                        self.console.print(
                            f"[dim]  Verified {verified_count}/{total_verifications}...[/dim]"
                        )
                except Exception as e:
                    source_prov, target_prov = future_to_task[future]
                    self.console.print(f"[red]Error verifying {source_prov.section_reference}: {e}[/red]")

        self.console.print(f"[green]✓ Completed {verified_count} verifications[/green]\n")

        # Step 4: Select best matches
        best_matches = self._select_best_matches(all_mappings, source_provisions)

        # Step 5: Calculate statistics
        matched_count = sum(1 for m in best_matches if m.is_match)
        unmatched_source = len(source_provisions) - matched_count
        matched_target_ids = {m.target_provision_id for m in best_matches if m.is_match}
        unmatched_target = len(target_provisions) - len(matched_target_ids)

        # Count variances by impact
        high_impact = sum(
            1 for m in best_matches if m.impact_level == ImpactLevel.HIGH
        )
        medium_impact = sum(
            1 for m in best_matches if m.impact_level == ImpactLevel.MEDIUM
        )
        low_impact = sum(
            1 for m in best_matches if m.impact_level == ImpactLevel.LOW
        )

        comparison = DocumentComparison(
            source_document_id=source_doc_id,
            target_document_id=target_doc_id,
            mappings=best_matches,
            total_source_provisions=len(source_provisions),
            total_target_provisions=len(target_provisions),
            matched_provisions=matched_count,
            unmatched_source_provisions=unmatched_source,
            unmatched_target_provisions=unmatched_target,
            high_impact_variances=high_impact,
            medium_impact_variances=medium_impact,
            low_impact_variances=low_impact,
            completed_at=datetime.utcnow(),
        )

        return comparison

    def _select_best_matches(
        self, all_mappings: List[ProvisionMapping], source_provisions: List[Provision]
    ) -> List[ProvisionMapping]:
        """
        Select the best match for each source provision.

        Each source provision gets exactly one mapping (highest confidence match).
        """
        best_matches = []

        for source_prov in source_provisions:
            # Get all candidates for this source
            candidates = [
                m for m in all_mappings if m.source_provision_id == source_prov.provision_id
            ]

            if not candidates:
                continue

            # Select highest confidence match
            best_match = max(candidates, key=lambda m: m.confidence_score)
            best_matches.append(best_match)

        return best_matches
