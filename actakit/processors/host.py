"""Core-owned Workbench orchestration for curated Representation processors."""

from __future__ import annotations

from dataclasses import dataclass

from actakit.deposit.ids import new_id, utc_now, validate_id

from .contracts import (
    EgressAuthorization,
    ProcessingRequest,
    Processor,
    ProcessorResult,
    require_token,
    validate_sha256,
)
from .quality import PolicyContext, QualityDecision, QualityPolicy, ReferenceEscalationPolicy
from .registry import ProcessorRegistry
from .writer import AttemptReceipt, InputMaterial, PersistedDecision, WorkbenchWriter


class ProcessorContractError(RuntimeError):
    """A curated processor violated the generic Workbench contract."""


class WorkbenchPlanError(RuntimeError):
    """An escalation plan and persisted policy decisions are inconsistent."""


@dataclass(frozen=True, slots=True)
class PlannedStep:
    capability_key: str
    process_run_id: str
    configuration_hash: str | None = None

    def __post_init__(self) -> None:
        require_token(self.capability_key, "planned capability")
        validate_id(self.process_run_id, "prun_")
        validate_sha256(self.configuration_hash, "planned configuration hash")

    @classmethod
    def allocate(cls, capability_key: str, configuration_hash: str | None = None) -> "PlannedStep":
        return cls(capability_key, new_id("prun_"), configuration_hash)


@dataclass(frozen=True, slots=True)
class ProcessingPlan:
    representation_id: str
    target_ids: tuple[str, ...]
    steps: tuple[PlannedStep, ...]
    egress: EgressAuthorization = EgressAuthorization.forbidden()

    def __post_init__(self) -> None:
        validate_id(self.representation_id, "rep_")
        if not self.target_ids:
            raise ValueError("ProcessingPlan requires at least one target")
        if len(set(self.target_ids)) != len(self.target_ids):
            raise ValueError("ProcessingPlan target IDs cannot repeat")
        for target_id in self.target_ids:
            validate_id(target_id, "rtgt_")
        if not self.steps:
            raise ValueError("ProcessingPlan requires at least one processor step")
        if len({step.process_run_id for step in self.steps}) != len(self.steps):
            raise ValueError("ProcessingPlan ProcessRun IDs must be unique")


@dataclass(frozen=True, slots=True)
class PlanReceipt:
    attempts: tuple[AttemptReceipt, ...]
    terminal_decisions: tuple[PersistedDecision, ...]


class WorkbenchHost:
    """Coordinates processors; processors themselves never receive persistence authority."""

    def __init__(
        self,
        writer: WorkbenchWriter,
        processors: ProcessorRegistry,
        *,
        policy: QualityPolicy | None = None,
    ) -> None:
        self.writer = writer
        self.processors = processors
        self.policy = policy or ReferenceEscalationPolicy()

    def run_attempt(self, request: ProcessingRequest) -> AttemptReceipt:
        material = self.writer.load_input(request)

        # A committed stable attempt is canonical independently of whether its
        # adapter remains installed after an upgrade. New work resolves a current
        # curated processor only after replay has been ruled out.
        replay = self.writer.replay_if_present(request)
        if replay is not None:
            return replay

        processor = self._resolve(request, material)
        descriptor = processor.descriptor
        started_at = utc_now()
        result = processor.process(self.writer.invocation(request, material))
        finished_at = utc_now()
        if not isinstance(result, ProcessorResult):
            raise ProcessorContractError("processor must return ProcessorResult")

        # Validate every signal before policy sees it. Unknown/malformed backend
        # metadata therefore cannot influence or enter canonical decisions.
        signal_identities: set[tuple[str, str, str]] = set()
        for signal in result.evidence:
            self.writer.quality_registry.validate(signal)
            identity = (signal.target_id, signal.signal_key, signal.signal_version)
            if identity in signal_identities:
                raise ProcessorContractError(
                    "processor emitted duplicate QualityEvidence signal identity"
                )
            signal_identities.add(identity)

        context = PolicyContext(
            self.processors.available_capabilities(
                media_type=material.media_type,
                scopes=material.scopes,
                input_bytes=len(material.source_bytes),
                artifact_restricted=material.artifact_restricted,
                egress_allowed=request.egress.allowed,
            )
        )
        decisions: list[QualityDecision] = []
        for target in material.scopes:
            target_evidence = tuple(
                signal for signal in result.evidence if signal.target_id == target.id
            )
            decision = self.policy.evaluate(
                descriptor=descriptor,
                result=result,
                target=target,
                evidence=target_evidence,
                context=context,
            )
            if not isinstance(decision, QualityDecision):
                raise ProcessorContractError("quality policy must return QualityDecision")
            if decision.target_id != target.id:
                raise ProcessorContractError("quality policy returned decision for wrong target")
            decisions.append(decision)

        return self.writer.record_attempt(
            request=request,
            descriptor=descriptor,
            material=material,
            result=result,
            decisions=tuple(decisions),
            started_at=started_at,
            finished_at=finished_at,
        )

    def run_plan(self, plan: ProcessingPlan) -> PlanReceipt:
        remaining = plan.target_ids
        attempts: list[AttemptReceipt] = []
        terminal: list[PersistedDecision] = []
        for index, step in enumerate(plan.steps):
            if not remaining:
                break
            request = ProcessingRequest(
                plan.representation_id,
                remaining,
                step.capability_key,
                step.configuration_hash,
                plan.egress,
                step.process_run_id,
            )
            receipt = self.run_attempt(request)
            attempts.append(receipt)

            next_capability = plan.steps[index + 1].capability_key if index + 1 < len(plan.steps) else None
            escalated: list[str] = []
            for decision in receipt.decisions:
                if decision.decision == "escalate":
                    if next_capability is None:
                        raise WorkbenchPlanError(
                            "quality policy escalated but ProcessingPlan has no next step"
                        )
                    if decision.next_capability_key != next_capability:
                        raise WorkbenchPlanError(
                            "quality policy next capability does not match ProcessingPlan"
                        )
                    escalated.append(decision.target_id)
                else:
                    terminal.append(decision)
            remaining = tuple(escalated)

        if remaining:
            raise WorkbenchPlanError("ProcessingPlan ended before escalated targets reached terminal state")
        return PlanReceipt(tuple(attempts), tuple(terminal))

    def _resolve(self, request: ProcessingRequest, material: InputMaterial) -> Processor:
        return self.processors.resolve(
            capability_key=request.capability_key,
            media_type=material.media_type,
            scopes=material.scopes,
            input_bytes=len(material.source_bytes),
            artifact_restricted=material.artifact_restricted,
            egress_allowed=request.egress.allowed,
        )
