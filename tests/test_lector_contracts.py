from __future__ import annotations

import json
import unittest

from actakit.deposit.ids import new_id
from actakit.lector import (
    ClaimDraft,
    ClaimRelationDraft,
    ClaimRevisionRef,
    EntityMentionDraft,
    EvidenceDraft,
    ResolutionCandidateDraft,
    SemanticExtractorDescriptor,
    SemanticExtractorRegistry,
    SemanticLocatorError,
    SemanticResult,
    TagAssignmentDraft,
    TargetRef,
    reopen_selector,
)
from actakit.lector.registry import SemanticExtractorResolutionError
from actakit.processors.contracts import TargetSnapshot


class StubExtractor:
    def __init__(self, descriptor: SemanticExtractorDescriptor) -> None:
        self._descriptor = descriptor

    @property
    def descriptor(self) -> SemanticExtractorDescriptor:
        return self._descriptor

    def extract(self, invocation):  # pragma: no cover - registry test only
        return SemanticResult("success")


def descriptor(**changes) -> SemanticExtractorDescriptor:
    values = dict(
        key="lector.stub",
        capability_key="claim_extract",
        implementation_version="1",
        origin_kind="machine",
        execution_venue="local_deterministic",
        input_media_types=frozenset({"text/plain"}),
        input_representation_kinds=frozenset({"extracted_text"}),
        scope_kinds=frozenset({"whole", "text_quote"}),
    )
    values.update(changes)
    return SemanticExtractorDescriptor(**values)


class LectorContractTests(unittest.TestCase):
    def test_source_assertion_requires_active_supporting_evidence(self) -> None:
        target = TargetRef.existing(new_id("rtgt_"))
        with self.assertRaisesRegex(ValueError, "supports/quotes"):
            ClaimDraft(
                "c1",
                "source_assertion",
                "El Concejo discutió el asunto.",
                (EvidenceDraft(target, "contextualizes", "active"),),
            )

    def test_new_links_cannot_be_born_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            EvidenceDraft(TargetRef.existing(new_id("rtgt_")), lifecycle="rejected")
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            TagAssignmentDraft(new_id("tag_"), lifecycle="rejected")

    def test_descriptor_rejects_unknown_representation_kind(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown input Representation"):
            descriptor(input_representation_kinds=frozenset({"made_up"}))

    def test_mentions_preserve_raw_text_and_only_candidate_entity_refs(self) -> None:
        entity_id = new_id("ent_")
        mention = EntityMentionDraft(
            "AyA",
            TargetRef.existing(new_id("rtgt_")),
            (ResolutionCandidateDraft(entity_id, 0.8),),
        )
        self.assertEqual(mention.observed_text, "AyA")
        self.assertEqual(mention.resolution_candidates[0].entity_id, entity_id)

    def test_semantic_result_relations_can_only_reference_same_result_claims(self) -> None:
        target = TargetRef.existing(new_id("rtgt_"))
        claim = ClaimDraft(
            "c1",
            "source_assertion",
            "Se aprobó el acuerdo.",
            (EvidenceDraft(target),),
        )
        relation = ClaimRelationDraft(
            ClaimRevisionRef.local("c1"),
            ClaimRevisionRef.local("missing"),
            "updates",
            "analyst_inference",
            rationale="Comparación local",
        )
        with self.assertRaisesRegex(ValueError, "unknown local claim"):
            SemanticResult("success", (claim,), (relation,))

    def test_failed_result_cannot_smuggle_semantic_outputs(self) -> None:
        target = TargetRef.existing(new_id("rtgt_"))
        claim = ClaimDraft(
            "c1",
            "source_assertion",
            "Se aprobó el acuerdo.",
            (EvidenceDraft(target),),
        )
        with self.assertRaisesRegex(ValueError, "failed SemanticResult"):
            SemanticResult("failed", (claim,), error_code="extract_failed")

    def test_text_quote_offsets_must_reopen_exact_bytes(self) -> None:
        text = "Inicio. SE ACUERDA aprobar el proyecto. Fin."
        start = text.index("SE ACUERDA")
        exact = "SE ACUERDA"
        payload = json.dumps(
            {"exact": exact, "start_char": start, "end_char": start + len(exact)}
        )
        reopen_selector("text_quote", "v1", payload, source_bytes=text.encode(), charset="utf-8")
        bad = json.dumps(
            {"exact": "NO EXISTE", "start_char": start, "end_char": start + 9}
        )
        with self.assertRaises(SemanticLocatorError):
            reopen_selector("text_quote", "v1", bad, source_bytes=text.encode(), charset="utf-8")

    def test_text_quote_without_offsets_must_be_unique(self) -> None:
        payload = json.dumps({"exact": "AyA"})
        with self.assertRaisesRegex(SemanticLocatorError, "exactly one"):
            reopen_selector(
                "text_quote", "v1", payload, source_bytes=b"AyA y AyA", charset="utf-8"
            )

    def test_table_range_must_reopen_exact_rows(self) -> None:
        source = json.dumps({"rows": [["A", 1], ["B", 2]]}).encode()
        good = json.dumps({"row_start": 2, "row_end": 2, "observed_values": [["B", 2]]})
        reopen_selector("table_range", "v1", good, source_bytes=source, charset="utf-8")
        bad = json.dumps({"row_start": 2, "row_end": 2, "observed_values": [["B", 3]]})
        with self.assertRaises(SemanticLocatorError):
            reopen_selector("table_range", "v1", bad, source_bytes=source, charset="utf-8")

    def test_registry_blocks_egress_for_restricted_input(self) -> None:
        cloud = StubExtractor(
            descriptor(
                key="lector.cloud",
                execution_venue="subscription_agent",
                requires_egress=True,
            )
        )
        registry = SemanticExtractorRegistry((cloud,))
        scope = TargetSnapshot(new_id("rtgt_"), new_id("rep_"), "whole", "v1", "{}")
        with self.assertRaises(SemanticExtractorResolutionError):
            registry.resolve(
                capability_key="claim_extract",
                representation_kind="extracted_text",
                media_type="text/plain",
                scopes=(scope,),
                input_bytes=100,
                artifact_restricted=True,
                egress_allowed=True,
            )

    def test_registry_respects_size_bounds(self) -> None:
        local = StubExtractor(descriptor(max_input_bytes=10))
        registry = SemanticExtractorRegistry((local,))
        scope = TargetSnapshot(new_id("rtgt_"), new_id("rep_"), "whole", "v1", "{}")
        self.assertEqual(
            registry.eligible(
                capability_key="claim_extract",
                representation_kind="extracted_text",
                media_type="text/plain",
                scopes=(scope,),
                input_bytes=11,
                artifact_restricted=False,
                egress_allowed=False,
            ),
            (),
        )


if __name__ == "__main__":
    unittest.main()
