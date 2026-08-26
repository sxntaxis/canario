"""Core-owned orchestration for replaceable Derivation and Verification backends."""

from __future__ import annotations

from canario.deposit.ids import utc_now

from .contracts import (
    DerivationBackend,
    DerivationExecutionResult,
    DerivationRequest,
    VerificationBackend,
    VerificationExecutionResult,
    VerificationRequest,
)
from .writer import DerivationReceipt, ReasoningWriter, VerificationReceipt


class ReasoningBackendContractError(RuntimeError):
    """An untrusted reasoning backend returned a value outside its typed contract."""


class ReasoningHost:
    """Invokes backends without giving them SQLite or archive write authority."""

    def __init__(self, writer: ReasoningWriter) -> None:
        self.writer = writer

    def run_derivation(
        self, request: DerivationRequest, backend: DerivationBackend
    ) -> DerivationReceipt:
        replay = self.writer.replay_derivation(request, backend.descriptor)
        if replay is not None:
            return replay
        material = self.writer.load_derivation_inputs(request)
        self.writer.validate_derivation_before_invocation(request, backend.descriptor, material)
        started_at = utc_now()
        result = backend.derive(self.writer.derivation_invocation(request, material))
        finished_at = utc_now()
        if not isinstance(result, DerivationExecutionResult):
            raise ReasoningBackendContractError("Derivation backend must return DerivationExecutionResult")
        return self.writer.record_derivation_attempt(
            request=request,
            descriptor=backend.descriptor,
            material=material,
            result=result,
            started_at=started_at,
            finished_at=finished_at,
        )

    def run_verification(
        self, request: VerificationRequest, backend: VerificationBackend
    ) -> VerificationReceipt:
        replay = self.writer.replay_verification(request, backend.descriptor)
        if replay is not None:
            return replay
        invocation = self.writer.load_verification_invocation(request)
        self.writer.validate_verification_before_invocation(
            request, backend.descriptor, invocation
        )
        started_at = utc_now()
        result = backend.verify(invocation)
        finished_at = utc_now()
        if not isinstance(result, VerificationExecutionResult):
            raise ReasoningBackendContractError(
                "Verification backend must return VerificationExecutionResult"
            )
        return self.writer.record_verification_attempt(
            request=request,
            descriptor=backend.descriptor,
            invocation=invocation,
            result=result,
            started_at=started_at,
            finished_at=finished_at,
        )
