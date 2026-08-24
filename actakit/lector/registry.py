"""Explicit composition of curated semantic extractors."""

from __future__ import annotations

from actakit.processors.contracts import TargetSnapshot

from .contracts import SemanticExtractor, SemanticExtractorDescriptor


class SemanticExtractorResolutionError(RuntimeError):
    """No curated Lector backend can satisfy a bounded request."""


class SemanticExtractorRegistry:
    def __init__(self, extractors: tuple[SemanticExtractor, ...]) -> None:
        if not isinstance(extractors, tuple):
            raise TypeError("extractors must be an explicit tuple")
        seen: set[str] = set()
        for extractor in extractors:
            if not isinstance(extractor, SemanticExtractor):
                raise TypeError("registered extractors must implement SemanticExtractor")
            descriptor = extractor.descriptor
            if not isinstance(descriptor, SemanticExtractorDescriptor):
                raise TypeError("extractor descriptor must be SemanticExtractorDescriptor")
            if descriptor.key in seen:
                raise ValueError(f"duplicate semantic extractor key: {descriptor.key}")
            seen.add(descriptor.key)
        self._extractors = extractors

    @property
    def extractors(self) -> tuple[SemanticExtractor, ...]:
        return self._extractors

    def eligible(
        self,
        *,
        capability_key: str,
        representation_kind: str,
        media_type: str,
        scopes: tuple[TargetSnapshot, ...],
        input_bytes: int,
        artifact_restricted: bool,
        egress_allowed: bool,
    ) -> tuple[SemanticExtractor, ...]:
        scope_kinds = {scope.selector_kind for scope in scopes}
        eligible: list[SemanticExtractor] = []
        for extractor in self._extractors:
            descriptor = extractor.descriptor
            if descriptor.capability_key != capability_key:
                continue
            if representation_kind not in descriptor.input_representation_kinds:
                continue
            if media_type not in descriptor.input_media_types:
                continue
            if not scope_kinds.issubset(descriptor.scope_kinds):
                continue
            if descriptor.max_input_bytes is not None and input_bytes > descriptor.max_input_bytes:
                continue
            if descriptor.max_scopes is not None and len(scopes) > descriptor.max_scopes:
                continue
            if descriptor.requires_egress and (artifact_restricted or not egress_allowed):
                continue
            eligible.append(extractor)
        return tuple(eligible)

    def resolve(self, **kwargs) -> SemanticExtractor:
        eligible = self.eligible(**kwargs)
        if not eligible:
            raise SemanticExtractorResolutionError(
                "no curated semantic extractor is eligible for request"
            )
        return eligible[0]
