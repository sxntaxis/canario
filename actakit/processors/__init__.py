"""Generic Representation Processor / Workbench production boundary."""

from .contracts import (
    DerivativeOutput,
    EgressAuthorization,
    ProcessingRequest,
    Processor,
    ProcessorDescriptor,
    ProcessorInvocation,
    ProcessorResult,
    QualitySignal,
    TargetSnapshot,
)
from .host import PlanReceipt, PlannedStep, ProcessingPlan, ProcessorContractError, WorkbenchHost
from .quality import (
    PolicyContext,
    QualityContractError,
    QualityDecision,
    QualityPolicy,
    QualityRegistry,
    ReferenceEscalationPolicy,
)
from .registry import ProcessorRegistry, ProcessorResolutionError
from .targets import TargetContractError, TargetRegistration, TargetRegistry
from .writer import (
    AttemptReceipt,
    DerivedRepresentationReceipt,
    PersistedDecision,
    WorkbenchIdentityCollision,
    WorkbenchInvariantError,
    WorkbenchWriteError,
    WorkbenchWriter,
)

__all__ = [
    "AttemptReceipt",
    "DerivativeOutput",
    "DerivedRepresentationReceipt",
    "EgressAuthorization",
    "PersistedDecision",
    "PlanReceipt",
    "PlannedStep",
    "PolicyContext",
    "ProcessingPlan",
    "ProcessingRequest",
    "Processor",
    "ProcessorContractError",
    "ProcessorDescriptor",
    "ProcessorInvocation",
    "ProcessorRegistry",
    "ProcessorResolutionError",
    "ProcessorResult",
    "QualityContractError",
    "QualityDecision",
    "QualityPolicy",
    "QualityRegistry",
    "QualitySignal",
    "ReferenceEscalationPolicy",
    "TargetContractError",
    "TargetRegistration",
    "TargetRegistry",
    "TargetSnapshot",
    "WorkbenchHost",
    "WorkbenchIdentityCollision",
    "WorkbenchInvariantError",
    "WorkbenchWriteError",
    "WorkbenchWriter",
]
