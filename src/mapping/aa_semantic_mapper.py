"""Adoption Agreement Semantic Mapper.

Implements Stage-2 semantic mapping for Adoption Agreement elections using the
schema defined in design/reconciliation/aa_mapping.md.
"""

import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import numpy as np
from anthropic import Anthropic
from openai import OpenAI
from rich.console import Console

from src.config import settings
from src.mapping.aa_input_builder import (
    build_aa_input,
    build_election_fingerprint,
    build_section_hierarchy,
)
from src.models.aa_mapping import (
    AAComparison,
    AAElectionMapping,
    Classification,
    ElectionAnchor,
    ElectionDependency,
    ConsistencyChecks,
    MatchType,
    OptionDescriptor,
    OptionMapping,
    OptionRelationship,
    QuestionAlignment,
    StructureAnalysis,
    ValueAlignment,
)
from src.models.election import Election
from src.models.mapping import ConfidenceLevel, ImpactLevel

console = Console()


def _strip_markdown_fences(response_text: str) -> str:
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _confidence_sort_key(mapping: AAElectionMapping) -> tuple:
    level_map = {
        ConfidenceLevel.HIGH: 3.0,
        ConfidenceLevel.MEDIUM: 2.0,
        ConfidenceLevel.LOW: 1.0,
    }
    return (level_map.get(mapping.classification.confidence_level, 0.0), mapping.embedding_similarity)


class AASemanticMapper:
    """Semantic mapper for Adoption Agreement elections."""

    def __init__(self, provider: Optional[str] = None, top_k: int = 3, max_workers: int = 16) -> None:
        self.provider = provider or settings.llm_provider
        self.top_k = top_k
        self.max_workers = max_workers
        self.console = console

        self.openai_client: Optional[OpenAI] = None
        self.anthropic_client: Optional[Anthropic] = None

        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)

        if self.provider == "anthropic" and settings.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)

        self.system_prompt, self.user_prompt = self._load_prompt()

    # ------------------------------------------------------------------
    # Prompt loading & LLM helpers
    # ------------------------------------------------------------------
    def _load_prompt(self) -> tuple[str, str]:
        prompt_path = Path("prompts/aa_semantic_mapping_v1.txt")
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        system_lines: List[str] = []
        user_lines: List[str] = []
        current = None

        with prompt_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.rstrip("\n")
                if line.startswith("===SYSTEM==="):
                    current = "system"
                    continue
                if line.startswith("===USER==="):
                    current = "user"
                    continue
                if line.startswith("#") and current is None:
                    continue

                if current == "system":
                    system_lines.append(line)
                elif current == "user":
                    user_lines.append(line)

        return "\n".join(system_lines).strip(), "\n".join(user_lines).strip()

    def _call_openai(self, payload_json: str) -> str:
        if not self.openai_client:
            raise RuntimeError("OPENAI_API_KEY not configured")

        user_content = self.user_prompt.replace("{payload}", payload_json)
        params = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.0,
        }

        if "gpt-5" in settings.llm_model.lower():
            params["max_completion_tokens"] = 2000
        else:
            params["max_tokens"] = 2000

        response = self.openai_client.chat.completions.create(**params)
        return response.choices[0].message.content

    def _call_anthropic(self, payload_json: str) -> str:
        if not self.anthropic_client:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")

        user_content = self.user_prompt.replace("{payload}", payload_json)
        response = self.anthropic_client.messages.create(
            model=settings.llm_model,
            max_tokens=2000,
            temperature=0.0,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text

    # ------------------------------------------------------------------
    # Embeddings & candidate search
    # ------------------------------------------------------------------
    def _generate_embeddings(self, elections: List[Election]) -> Dict[str, np.ndarray]:
        if not self.openai_client:
            raise RuntimeError("OpenAI client required for embeddings")

        fingerprints = [build_election_fingerprint(election) for election in elections]
        election_ids = [str(election.id) for election in elections]

        response = self.openai_client.embeddings.create(
            model=settings.embedding_model,
            input=fingerprints,
        )

        embeddings: Dict[str, np.ndarray] = {}
        for index, embedding in enumerate(response.data):
            embeddings[election_ids[index]] = np.array(embedding.embedding)

        return embeddings

    def _compute_similarity_matrix(
        self,
        source: List[Election],
        target: List[Election],
        source_embeddings: Dict[str, np.ndarray],
        target_embeddings: Dict[str, np.ndarray],
    ) -> Dict[str, List[tuple[Election, float]]]:
        candidates: Dict[str, List[tuple[Election, float]]] = {}

        for source_election in source:
            source_vector = source_embeddings[str(source_election.id)]
            similarities: List[tuple[Election, float]] = []

            for target_election in target:
                target_vector = target_embeddings[str(target_election.id)]
                similarity = float(
                    np.dot(source_vector, target_vector)
                    / (np.linalg.norm(source_vector) * np.linalg.norm(target_vector))
                )
                similarities.append((target_election, similarity))

            similarities.sort(key=lambda item: item[1], reverse=True)
            candidates[str(source_election.id)] = similarities[: self.top_k]

        return candidates

    # ------------------------------------------------------------------
    # Mapping verification & parsing
    # ------------------------------------------------------------------
    def _verify_mapping(
        self,
        source_election: Election,
        target_election: Election,
        *,
        embedding_similarity: float,
        candidate_rank: int,
        section_hierarchy: Dict[str, str],
        run_id: str,
    ) -> AAElectionMapping:
        payload_dict = build_aa_input(
            source_election=source_election,
            target_election=target_election,
            candidate_rank=candidate_rank,
            run_id=run_id,
            section_hierarchy=section_hierarchy,
        )
        payload_json = json.dumps(payload_dict, ensure_ascii=False)

        if self.provider == "anthropic":
            response_text = self._call_anthropic(payload_json)
        else:
            response_text = self._call_openai(payload_json)

        return self._parse_mapping(
            response_text,
            source=source_election,
            target=target_election,
            embedding_similarity=embedding_similarity,
            fallback_run_id=run_id,
        )

    def _validate_mapping(self, mapping: AAElectionMapping) -> List[str]:
        """
        Validate LLM response quality (parser guardrails).

        Returns list of validation error messages (empty list if valid).
        """
        errors = []

        # 1. Validate confidence_rationale is non-empty (post-strip)
        if not mapping.classification.confidence_rationale.strip():
            errors.append("confidence_rationale is empty")

        # 2. Validate abstain_reasons contains ≥1 entry when match_type=="abstain"
        if mapping.classification.match_type == MatchType.ABSTAIN:
            if not mapping.classification.abstain_reasons:
                errors.append("abstain_reasons is empty when match_type=abstain")

        # 3. Validate question_alignment.reasons non-empty when question_alignment.value is False
        if not mapping.structure_analysis.question_alignment.value:
            if not mapping.structure_analysis.question_alignment.reasons:
                errors.append("question_alignment.reasons is empty when alignment is false")

        # 4. Validate exact match outputs do not include partial/missing/incompatible relationships
        if mapping.classification.match_type == MatchType.EXACT:
            forbidden_relationships = {
                OptionRelationship.PARTIAL,
                OptionRelationship.MISSING,
                OptionRelationship.INCOMPATIBLE,
            }
            for opt_mapping in mapping.option_mappings:
                if opt_mapping.relationship in forbidden_relationships:
                    errors.append(
                        f"exact match has {opt_mapping.relationship.value} relationship in option_mappings"
                    )
                    break

        # 5. Validate incompatible relationships force impact to medium or high
        has_incompatible = any(
            opt_mapping.relationship == OptionRelationship.INCOMPATIBLE
            for opt_mapping in mapping.option_mappings
        )
        if has_incompatible:
            if mapping.classification.impact == ImpactLevel.NONE:
                errors.append("incompatible relationship present but impact=none")

        return errors

    def _parse_mapping(
        self,
        response_text: str,
        *,
        source: Election,
        target: Election,
        embedding_similarity: float,
        fallback_run_id: str,
    ) -> AAElectionMapping:
        payload = json.loads(_strip_markdown_fences(response_text))

        def to_confidence_level(value: str) -> ConfidenceLevel:
            mapping = {
                "high": ConfidenceLevel.HIGH,
                "medium": ConfidenceLevel.MEDIUM,
                "low": ConfidenceLevel.LOW,
            }
            return mapping.get(value.lower(), ConfidenceLevel.LOW)

        def to_match_type(value: str) -> MatchType:
            try:
                return MatchType(value)
            except ValueError:
                return MatchType.ABSTAIN

        def to_impact(value: str) -> ImpactLevel:
            mapping = {
                "none": ImpactLevel.NONE,
                "low": ImpactLevel.LOW,
                "medium": ImpactLevel.MEDIUM,
                "high": ImpactLevel.HIGH,
            }
            return mapping.get(value.lower(), ImpactLevel.LOW)

        def to_relationship(value: str) -> OptionRelationship:
            try:
                return OptionRelationship(value)
            except ValueError:
                return OptionRelationship.INCOMPATIBLE

        structure_payload = payload.get("structure_analysis", {})
        qa_payload = structure_payload.get("question_alignment", {})
        dependency_payload = structure_payload.get("election_dependency", {})

        option_mappings_payload = payload.get("option_mappings", [])
        option_mappings: List[OptionMapping] = []
        for item in option_mappings_payload:
            source_option = item.get("source_option", {})
            target_option = item.get("target_option")

            source_descriptor = OptionDescriptor(
                label=source_option.get("label"),
                text=source_option.get("text", ""),
                is_selected=source_option.get("is_selected"),
                fill_ins=source_option.get("fill_ins", []),
            )

            target_descriptor = None
            if target_option:
                target_descriptor = OptionDescriptor(
                    label=target_option.get("label"),
                    text=target_option.get("text", ""),
                    is_selected=target_option.get("is_selected"),
                    fill_ins=target_option.get("fill_ins", []),
                )

            option_mappings.append(
                OptionMapping(
                    source=source_descriptor,
                    target=target_descriptor,
                    relationship=to_relationship(item.get("relationship", "incompatible")),
                    notes=item.get("notes"),
                )
            )

        value_alignment_payload = payload.get("value_alignment", {})
        value_alignment = ValueAlignment(
            source_selected=value_alignment_payload.get("source_selected", []),
            target_selected=value_alignment_payload.get("target_selected", []),
            compatible=bool(value_alignment_payload.get("compatible", False)),
            justification=value_alignment_payload.get("justification"),
        )

        classification_payload = payload.get("classification", {})
        classification = Classification(
            match_type=to_match_type(classification_payload.get("match_type", "abstain")),
            impact=to_impact(classification_payload.get("impact", "low")),
            confidence_level=to_confidence_level(classification_payload.get("confidence_level", "low")),
            confidence_rationale=classification_payload.get("confidence_rationale", ""),
            abstain_reasons=classification_payload.get("abstain_reasons", []),
        )

        consistency_payload = payload.get("consistency_checks", {})
        consistency_checks = ConsistencyChecks(
            exact_requires_none_impact=consistency_payload.get("exact_requires_none_impact", "failed"),
            incompatible_requires_non_none_impact=consistency_payload.get("incompatible_requires_non_none_impact", "failed"),
            abstain_requires_alignment_false_or_insufficient_context=consistency_payload.get(
                "abstain_requires_alignment_false_or_insufficient_context", "failed"
            ),
            violations=consistency_payload.get("violations", []),
        )

        mapping = AAElectionMapping(
            schema_version=payload.get("schema_version", "aa-v1"),
            run_id=payload.get("run_id", fallback_run_id),
            source_election_id=source.id,
            target_election_id=target.id,
            source_anchor=ElectionAnchor(
                question_id=payload.get("source_anchor", {}).get("question_id", str(source.id)),
                section_context=payload.get("source_anchor", {}).get("section_context", source.section_context),
                page=payload.get("source_anchor", {}).get("page", getattr(source.provenance, "page", None)),
            ),
            target_anchor=ElectionAnchor(
                question_id=payload.get("target_anchor", {}).get("question_id", str(target.id)),
                section_context=payload.get("target_anchor", {}).get("section_context", target.section_context),
                page=payload.get("target_anchor", {}).get("page", getattr(target.provenance, "page", None)),
            ),
            structure_analysis=StructureAnalysis(
                question_alignment=QuestionAlignment(
                    value=bool(qa_payload.get("value", False)),
                    reasons=qa_payload.get("reasons", []),
                ),
                requires_definition=structure_payload.get("requires_definition", []),
                election_dependency=ElectionDependency(
                    status=dependency_payload.get("status", "none"),
                    evidence=dependency_payload.get("evidence", []),
                ),
            ),
            option_mappings=option_mappings,
            value_alignment=value_alignment,
            classification=classification,
            consistency_checks=consistency_checks,
            embedding_similarity=embedding_similarity,
        )

        # Validate LLM response quality (parser guardrails)
        validation_errors = self._validate_mapping(mapping)
        if validation_errors:
            console.print(f"[yellow]⚠ LLM response validation failed: {'; '.join(validation_errors)}[/yellow]")
            return self._fallback_mapping(
                source=source,
                target=target,
                embedding_similarity=embedding_similarity,
                run_id=fallback_run_id,
                error=ValueError(f"Invalid LLM response: {'; '.join(validation_errors)}"),
            )

        return mapping

    def _fallback_mapping(
        self,
        *,
        source: Election,
        target: Election,
        embedding_similarity: float,
        run_id: str,
        error: Exception,
    ) -> AAElectionMapping:
        classification = Classification(
            match_type=MatchType.ABSTAIN,
            impact=ImpactLevel.LOW,
            confidence_level=ConfidenceLevel.LOW,
            confidence_rationale=f"LLM verification failed: {error}",
            abstain_reasons=["llm_failure"],
        )

        return AAElectionMapping(
            schema_version="aa-v1",
            run_id=run_id,
            source_election_id=source.id,
            target_election_id=target.id,
            source_anchor=ElectionAnchor(
                question_id=str(source.id),
                section_context=source.section_context,
                page=getattr(source.provenance, "page", None),
            ),
            target_anchor=ElectionAnchor(
                question_id=str(target.id),
                section_context=target.section_context,
                page=getattr(target.provenance, "page", None),
            ),
            structure_analysis=StructureAnalysis(
                question_alignment=QuestionAlignment(value=False, reasons=[]),
                requires_definition=[],
                election_dependency=ElectionDependency(status="none", evidence=[]),
            ),
            option_mappings=[],
            value_alignment=ValueAlignment(),
            classification=classification,
            consistency_checks=ConsistencyChecks(
                exact_requires_none_impact="failed",
                incompatible_requires_non_none_impact="failed",
                abstain_requires_alignment_false_or_insufficient_context="failed",
                violations=["llm_response_invalid"],
            ),
            embedding_similarity=embedding_similarity,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def compare_documents(
        self,
        source_elections: List[Election],
        target_elections: List[Election],
        *,
        source_doc_id: str,
        target_doc_id: str,
    ) -> AAComparison:
        self.console.print("\n[cyan bold]Comparing AA Documents[/cyan bold]")
        self.console.print(f"[dim]Source: {source_doc_id} ({len(source_elections)} elections)[/dim]")
        self.console.print(f"[dim]Target: {target_doc_id} ({len(target_elections)} elections)[/dim]\n")

        run_id = f"aa-{uuid4()}"
        section_hierarchy = build_section_hierarchy(source_elections + target_elections)

        embeddings = self._generate_embeddings(source_elections + target_elections)
        source_embeddings = {str(e.id): embeddings[str(e.id)] for e in source_elections}
        target_embeddings = {str(e.id): embeddings[str(e.id)] for e in target_elections}

        candidates_map = self._compute_similarity_matrix(
            source_elections, target_elections, source_embeddings, target_embeddings
        )

        all_mappings: List[AAElectionMapping] = []
        verification_tasks = []

        for source_election in source_elections:
            source_id = str(source_election.id)
            for rank, (target_election, similarity) in enumerate(candidates_map[source_id], start=1):
                verification_tasks.append(
                    (source_election, target_election, similarity, rank)
                )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(
                    self._verify_mapping,
                    source_election,
                    target_election,
                    embedding_similarity=similarity,
                    candidate_rank=rank,
                    section_hierarchy=section_hierarchy,
                    run_id=f"{run_id}-c{rank}-{uuid4().hex[:6]}",
                ): (source_election, target_election)
                for source_election, target_election, similarity, rank in verification_tasks
            }

            for future in as_completed(future_to_task):
                source_election, target_election = future_to_task[future]
                try:
                    mapping = future.result()
                except Exception as error:  # pragma: no cover - defensive
                    mapping = self._fallback_mapping(
                        source=source_election,
                        target=target_election,
                        embedding_similarity=0.0,
                        run_id=run_id,
                        error=error,
                    )
                all_mappings.append(mapping)

        best_matches: List[AAElectionMapping] = []
        for source_election in source_elections:
            candidates = [m for m in all_mappings if m.source_election_id == source_election.id]
            if not candidates:
                continue
            candidates.sort(key=_confidence_sort_key, reverse=True)
            best_matches.append(candidates[0])

        matched_count = sum(1 for mapping in best_matches if mapping.match_decision())
        matched_target_ids = {
            mapping.target_election_id for mapping in best_matches if mapping.match_decision()
        }

        comparison = AAComparison(
            source_document_id=source_doc_id,
            target_document_id=target_doc_id,
            mappings=best_matches,
            total_source_elections=len(source_elections),
            total_target_elections=len(target_elections),
            matched_elections=matched_count,
            unmatched_source_elections=len(source_elections) - matched_count,
            unmatched_target_elections=len(target_elections) - len(matched_target_ids),
            completed_at=datetime.utcnow(),
        )

        return comparison


__all__ = ["AASemanticMapper"]
