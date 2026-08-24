"""Core-owned orchestration for curated Lector semantic extractors."""

from __future__ import annotations

from canario.deposit.ids import utc_now

from .contracts import SemanticExtractionRequest, SemanticResult
from .registry import SemanticExtractorRegistry
from .writer import LectorWriter, SemanticReceipt


class LectorContractError(RuntimeError):
    """A curated semantic extractor violated the Lector contract."""


class LectorHost:
    """Coordinates semantic extractors; extractors never receive persistence authority."""

    def __init__(self, writer: LectorWriter, extractors: SemanticExtractorRegistry) -> None:
        self.writer = writer
        self.extractors = extractors

    def run_attempt(self, request: SemanticExtractionRequest) -> SemanticReceipt:
        material = self.writer.load_input(request)

        # Stable committed attempts remain replayable even if the historical
        # extractor is later removed or upgraded.
        replay = self.writer.replay_if_present(request)
        if replay is not None:
            return replay

        extractor = self.extractors.resolve(
            capability_key=request.capability_key,
            representation_kind=material.representation_kind,
            media_type=material.media_type,
            scopes=material.scopes,
            input_bytes=len(material.source_bytes),
            artifact_restricted=material.restricted,
            egress_allowed=request.egress.allowed,
        )
        started_at = utc_now()
        result = extractor.extract(self.writer.invocation(request, material))
        finished_at = utc_now()
        if not isinstance(result, SemanticResult):
            raise LectorContractError("semantic extractor must return SemanticResult")

        return self.writer.record_attempt(
            request=request,
            descriptor=extractor.descriptor,
            material=material,
            result=result,
            started_at=started_at,
            finished_at=finished_at,
        )
