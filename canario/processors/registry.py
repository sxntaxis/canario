"""Explicit curated processor composition; no plugin discovery."""

from __future__ import annotations

from .contracts import Processor, ProcessorDescriptor, TargetSnapshot


class ProcessorResolutionError(RuntimeError):
    """No curated processor can satisfy a bounded processing request."""


class ProcessorRegistry:
    def __init__(self, processors: tuple[Processor, ...]) -> None:
        if not isinstance(processors, tuple):
            raise TypeError("processors must be an explicit tuple")
        seen: set[str] = set()
        for processor in processors:
            if not isinstance(processor, Processor):
                raise TypeError("registered processors must implement the Processor protocol")
            descriptor = processor.descriptor
            if not isinstance(descriptor, ProcessorDescriptor):
                raise TypeError("processor descriptor must be ProcessorDescriptor")
            if descriptor.key in seen:
                raise ValueError(f"duplicate processor key: {descriptor.key}")
            seen.add(descriptor.key)
        self._processors = processors

    @property
    def processors(self) -> tuple[Processor, ...]:
        return self._processors

    def eligible(
        self,
        *,
        capability_key: str,
        media_type: str,
        scopes: tuple[TargetSnapshot, ...],
        input_bytes: int,
        artifact_restricted: bool,
        egress_allowed: bool,
    ) -> tuple[Processor, ...]:
        scope_kinds = {scope.selector_kind for scope in scopes}
        eligible: list[Processor] = []
        for processor in self._processors:
            descriptor = processor.descriptor
            if descriptor.capability_key != capability_key:
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
            eligible.append(processor)
        return tuple(eligible)

    def resolve(
        self,
        *,
        capability_key: str,
        media_type: str,
        scopes: tuple[TargetSnapshot, ...],
        input_bytes: int,
        artifact_restricted: bool,
        egress_allowed: bool,
    ) -> Processor:
        eligible = self.eligible(
            capability_key=capability_key,
            media_type=media_type,
            scopes=scopes,
            input_bytes=input_bytes,
            artifact_restricted=artifact_restricted,
            egress_allowed=egress_allowed,
        )
        if not eligible:
            raise ProcessorResolutionError("no curated processor is eligible for request")
        return eligible[0]

    def available_capabilities(
        self,
        *,
        media_type: str,
        scopes: tuple[TargetSnapshot, ...],
        input_bytes: int,
        artifact_restricted: bool,
        egress_allowed: bool,
    ) -> frozenset[str]:
        values: set[str] = set()
        for processor in self._processors:
            descriptor: ProcessorDescriptor = processor.descriptor
            if self.eligible(
                capability_key=descriptor.capability_key,
                media_type=media_type,
                scopes=scopes,
                input_bytes=input_bytes,
                artifact_restricted=artifact_restricted,
                egress_allowed=egress_allowed,
            ):
                values.add(descriptor.capability_key)
        return frozenset(values)
