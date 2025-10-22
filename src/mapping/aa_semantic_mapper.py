"""
AA Semantic Mapper

Compares elections across Adoption Agreement documents using embedding-based
candidate matching followed by LLM verification.

Similar to SemanticMapper but adapted for election structures instead of prose provisions.
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import numpy as np
from openai import OpenAI
from rich.console import Console

from src.config import settings

console = Console()


class AASemanticMapper:
    """
    Maps elections across AA documents using hybrid embedding + LLM approach.

    Key differences from BPD mapper:
    - Elections have question_text + options (not prose provision_text)
    - Need to compare option structures semantically
    - Question numbering changes across BPD versions (can't rely on numbers)
    """

    def __init__(self, provider: str = None, top_k: int = 3, max_workers: int = 16) -> None:
        """
        Initialize AA semantic mapper.

        Args:
            provider: 'openai' or 'anthropic' (defaults to settings.llm_provider)
            top_k: Number of candidates to verify with LLM (default 3)
            max_workers: Number of parallel workers for LLM verification (default 16)
        """
        self.provider = provider or settings.llm_provider
        self.top_k = top_k
        self.max_workers = max_workers
        self.console = console

        # Initialize OpenAI client (required for embeddings)
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError("OpenAI API key required for AA semantic mapping")

        # Load prompt
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load AA semantic mapping prompt from external file."""
        prompt_path = Path("prompts/aa_semantic_mapping_v1.txt")
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _election_to_text(self, election: Dict[str, Any]) -> str:
        """
        Convert election structure to text for embedding.

        CRITICAL: Question numbers are stripped to prevent false positives.
        Section numbers are provenance only and have NO BEARING on semantic similarity.

        Research finding: Including question numbers caused 1.0 embedding similarity
        for unrelated elections (e.g., Age eligibility vs State address both numbered 1.04).

        Format:
        Section: {section_context}
        {question_text} (question number stripped)
        Type: {kind}
        Options:
        - {option_text}
        """
        # Strip question number prefix if present (e.g., "Question 1.04: Text" → "Text")
        question_text = election['question_text']
        if ':' in question_text and question_text.split(':')[0].strip().startswith('Question'):
            question_text = question_text.split(':', 1)[1].strip()

        parts = [
            f"Section: {election.get('section_context', 'Unknown')}",
            question_text,
            f"Type: {election.get('kind', 'unknown')}"
        ]

        if election.get('options'):
            parts.append("Options:")
            for opt in election['options']:
                parts.append(f"- {opt['label']}. {opt['option_text']}")

        return "\n".join(parts)

    def generate_embeddings(self, elections: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for all elections.

        Args:
            elections: List of election dicts from AA extraction

        Returns:
            Dict mapping election_id to embedding vector
        """
        self.console.print(
            f"[cyan]Generating embeddings for {len(elections)} elections...[/cyan]"
        )

        embeddings = {}

        # Convert elections to text
        texts = [self._election_to_text(e) for e in elections]
        election_ids = [e['id'] for e in elections]

        try:
            response = self.openai_client.embeddings.create(
                model=settings.embedding_model, input=texts
            )

            for i, embedding_obj in enumerate(response.data):
                embeddings[election_ids[i]] = np.array(embedding_obj.embedding)

            self.console.print(f"[green]✓ Generated {len(embeddings)} embeddings[/green]\n")

        except Exception as e:
            self.console.print(f"[red]Error generating embeddings: {e}[/red]")
            raise

        return embeddings

    def compute_similarity_matrix(
        self,
        source_elections: List[Dict[str, Any]],
        target_elections: List[Dict[str, Any]],
        source_embeddings: Dict[str, np.ndarray],
        target_embeddings: Dict[str, np.ndarray],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compute cosine similarity matrix and find top candidates.

        Returns:
            Dict mapping source_election_id to list of top candidates
            Each candidate: {target_id, similarity}
        """
        self.console.print(
            f"[cyan]Computing similarity matrix ({len(source_elections)}×{len(target_elections)})...[/cyan]"
        )

        candidates_map = {}

        for source_election in source_elections:
            source_id = source_election['id']
            source_vec = source_embeddings[source_id]

            similarities = []

            for target_election in target_elections:
                target_id = target_election['id']
                target_vec = target_embeddings[target_id]

                # Cosine similarity
                similarity = float(
                    np.dot(source_vec, target_vec)
                    / (np.linalg.norm(source_vec) * np.linalg.norm(target_vec))
                )

                similarities.append({
                    'target_id': target_id,
                    'similarity': similarity
                })

            # Sort by similarity and take top K
            top_candidates = sorted(
                similarities, key=lambda x: x['similarity'], reverse=True
            )[: self.top_k]

            candidates_map[source_id] = top_candidates

        self.console.print(
            f"[green]✓ Found top {self.top_k} candidates for each source election[/green]\n"
        )

        return candidates_map

    def verify_mapping(
        self,
        source_election: Dict[str, Any],
        target_election: Dict[str, Any],
        embedding_score: float
    ) -> Dict[str, Any]:
        """
        Use LLM to verify semantic mapping between two elections.

        Returns:
            Dict with mapping result:
            {
                source_id, target_id, embedding_similarity,
                is_match, confidence_score, reasoning,
                variance_type, impact_level
            }
        """
        # Build prompt
        prompt = self.prompt_template.format(
            source_number=source_election['question_number'],
            source_question=source_election['question_text'],
            source_options=self._format_options(source_election.get('options', [])),
            target_number=target_election['question_number'],
            target_question=target_election['question_text'],
            target_options=self._format_options(target_election.get('options', []))
        )

        # Call LLM
        try:
            response_text = self._call_openai(prompt)
            result = self._parse_llm_response(response_text)

            # Build mapping result
            mapping = {
                'source_id': source_election['id'],
                'target_id': target_election['id'],
                'source_question_number': source_election['question_number'],
                'target_question_number': target_election['question_number'],
                'embedding_similarity': embedding_score,
                'is_match': result['is_match'],
                'confidence_score': result['confidence_score'],
                'reasoning': result['reasoning'],
                'variance_type': result.get('variance_type', 'none'),
                'impact_level': result.get('impact_level', 'none')
            }

            return mapping

        except Exception as e:
            self.console.print(f"[yellow]⚠️  Error verifying mapping: {e}[/yellow]")
            # Return low-confidence mapping on error
            return {
                'source_id': source_election['id'],
                'target_id': target_election['id'],
                'source_question_number': source_election['question_number'],
                'target_question_number': target_election['question_number'],
                'embedding_similarity': embedding_score,
                'is_match': False,
                'confidence_score': 0.0,
                'reasoning': f"LLM verification failed: {str(e)}",
                'variance_type': 'none',
                'impact_level': 'none'
            }

    def _format_options(self, options: List[Dict[str, Any]]) -> str:
        """Format election options for prompt."""
        if not options:
            return "(No options - text field)"

        lines = []
        for opt in options:
            lines.append(f"{opt['label']}. {opt['option_text']}")
        return "\n".join(lines)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = self.openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an ERISA compliance specialist analyzing Adoption Agreement elections. Return ONLY valid JSON, no other text.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.0,
        )
        return response.choices[0].message.content

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

    def compare_aa_documents(
        self,
        source_elections: List[Dict[str, Any]],
        target_elections: List[Dict[str, Any]],
        source_doc_id: str,
        target_doc_id: str,
    ) -> Dict[str, Any]:
        """
        Complete AA document comparison workflow.

        Returns:
            Dict with comparison results and statistics
        """
        self.console.print(f"\n[cyan bold]Comparing AA Documents[/cyan bold]")
        self.console.print(f"[dim]Source: {source_doc_id} ({len(source_elections)} elections)[/dim]")
        self.console.print(
            f"[dim]Target: {target_doc_id} ({len(target_elections)} elections)[/dim]\n"
        )

        # Step 1: Generate embeddings
        all_elections = source_elections + target_elections
        all_embeddings = self.generate_embeddings(all_elections)

        source_embeddings = {e['id']: all_embeddings[e['id']] for e in source_elections}
        target_embeddings = {e['id']: all_embeddings[e['id']] for e in target_elections}

        # Step 2: Find candidates
        candidates_map = self.compute_similarity_matrix(
            source_elections, target_elections, source_embeddings, target_embeddings
        )

        # Step 3: LLM verification (parallel)
        self.console.print(
            f"[cyan]Verifying top candidates with LLM ({self.provider.upper()}, {self.max_workers} workers)...[/cyan]"
        )

        all_mappings = []
        total_verifications = len(source_elections) * self.top_k

        # Build target election map
        target_election_map = {e['id']: e for e in target_elections}

        # Build verification tasks
        verification_tasks = []
        for source_election in source_elections:
            source_id = source_election['id']
            candidates = candidates_map[source_id]

            for candidate in candidates:
                target_id = candidate['target_id']
                target_election = target_election_map[target_id]
                verification_tasks.append((
                    source_election,
                    target_election,
                    candidate['similarity']
                ))

        # Parallel verification
        verified_count = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(
                    self.verify_mapping,
                    source_election,
                    target_election,
                    emb_score
                ): (source_election, target_election)
                for source_election, target_election, emb_score in verification_tasks
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
                    source_election, target_election = future_to_task[future]
                    self.console.print(
                        f"[red]Error verifying {source_election['question_number']}: {e}[/red]"
                    )

        self.console.print(f"[green]✓ Completed {verified_count} verifications[/green]\n")

        # Step 4: Select best matches
        best_matches = self._select_best_matches(all_mappings, source_elections)

        # Step 5: Calculate statistics
        matched_count = sum(1 for m in best_matches if m['is_match'])
        unmatched_source = len(source_elections) - matched_count
        matched_target_ids = {m['target_id'] for m in best_matches if m['is_match']}
        unmatched_target = len(target_elections) - len(matched_target_ids)

        # Confidence distribution
        high_confidence = sum(1 for m in best_matches if m['confidence_score'] >= 0.9)
        medium_confidence = sum(
            1 for m in best_matches
            if 0.7 <= m['confidence_score'] < 0.9
        )
        low_confidence = sum(1 for m in best_matches if m['confidence_score'] < 0.7)

        comparison = {
            'source_document_id': source_doc_id,
            'target_document_id': target_doc_id,
            'mappings': best_matches,
            'statistics': {
                'total_source_elections': len(source_elections),
                'total_target_elections': len(target_elections),
                'matched_elections': matched_count,
                'unmatched_source_elections': unmatched_source,
                'unmatched_target_elections': unmatched_target,
                'high_confidence': high_confidence,
                'medium_confidence': medium_confidence,
                'low_confidence': low_confidence,
            },
            'completed_at': datetime.utcnow().isoformat(),
        }

        return comparison

    def _select_best_matches(
        self,
        all_mappings: List[Dict[str, Any]],
        source_elections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Select the best match for each source election.

        Each source election gets exactly one mapping (highest confidence match).
        """
        best_matches = []

        for source_election in source_elections:
            # Get all candidates for this source
            candidates = [
                m for m in all_mappings
                if m['source_id'] == source_election['id']
            ]

            if not candidates:
                continue

            # Select highest confidence match
            best_match = max(candidates, key=lambda m: m['confidence_score'])
            best_matches.append(best_match)

        return best_matches
