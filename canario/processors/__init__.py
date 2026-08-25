"""Generic Representation Processor / Workbench production boundary."""

from .codex import (
    CodexConfigurationError,
    CodexUnavailableError,
    CodexVisualConfig,
    CodexVisualTranscriptionProcessor,
)
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
from .ocr import (
    OcrConfigurationError,
    OcrPdfConfig,
    OcrPdfProcessor,
    OcrUnavailableError,
)
from .media import MediaInspectionProcessor
from .structured_table import StructuredTableConfig, StructuredTableProcessor
from .host import PlanReceipt, PlannedStep, ProcessingPlan, ProcessorContractError, WorkbenchHost
from .poppler import (
    PopplerConfigurationError,
    PopplerPdfTextConfig,
    PopplerPdfTextProcessor,
    PopplerUnavailableError,
)
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
    "CodexConfigurationError",
    "CodexUnavailableError",
    "CodexVisualConfig",
    "CodexVisualTranscriptionProcessor",
    "DerivativeOutput",
    "DerivedRepresentationReceipt",
    "EgressAuthorization",
    "PersistedDecision",
    "OcrUnavailableError",
    "OcrPdfProcessor",
    "OcrPdfConfig",
    "OcrConfigurationError",
    "MediaInspectionProcessor",
    "PlanReceipt",
    "PlannedStep",
    "PolicyContext",
    "PopplerConfigurationError",
    "PopplerPdfTextConfig",
    "PopplerPdfTextProcessor",
    "PopplerUnavailableError",
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
    "StructuredTableConfig",
    "StructuredTableProcessor",
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
