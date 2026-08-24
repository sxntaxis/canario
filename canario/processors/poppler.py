"""Production D0/D1 PDF text extraction through the trusted Poppler CLI suite."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .contracts import (
    DerivativeOutput,
    ProcessorDescriptor,
    ProcessorInvocation,
    ProcessorResult,
    QualitySignal,
)

_VERSION_RE = re.compile(r"(?:pdftotext|pdfinfo|pdfimages) version (?P<version>[^\s]+)")
_PAGES_RE = re.compile(r"^Pages:\s+(?P<count>[1-9][0-9]*)\s*$", re.MULTILINE)
_IMAGE_ROW_RE = re.compile(r"^\s*(?P<page>[1-9][0-9]*)\s+[0-9]+\s+", re.MULTILINE)


class PopplerUnavailableError(RuntimeError):
    """The trusted Poppler toolchain is unavailable or internally inconsistent."""


class PopplerConfigurationError(RuntimeError):
    """A request does not identify the exact Poppler adapter configuration."""


@dataclass(frozen=True, slots=True)
class PopplerPdfTextConfig:
    """Trusted adapter configuration; never derived from document-controlled data."""

    layout: bool = True
    timeout_seconds: int = 30
    attempt_timeout_seconds: int = 120
    max_pages: int = 2_000
    max_output_bytes: int = 64 * 1024 * 1024
    max_input_bytes: int = 256 * 1024 * 1024
    max_scopes: int = 512

    def __post_init__(self) -> None:
        for field_name in (
            "timeout_seconds",
            "attempt_timeout_seconds",
            "max_pages",
            "max_output_bytes",
            "max_input_bytes",
            "max_scopes",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{field_name} must be a positive integer")
        if not isinstance(self.layout, bool):
            raise TypeError("layout must be boolean")

    def canonical_hash(self) -> str:
        payload = json.dumps(
            {
                "encoding": "UTF-8",
                "eol": "unix",
                "layout": self.layout,
                "attempt_timeout_seconds": self.attempt_timeout_seconds,
                "max_input_bytes": self.max_input_bytes,
                "max_output_bytes": self.max_output_bytes,
                "max_pages": self.max_pages,
                "max_scopes": self.max_scopes,
                "timeout_seconds": self.timeout_seconds,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class _Toolchain:
    pdftotext: str
    pdfinfo: str
    pdfimages: str
    version: str


class PopplerPdfTextProcessor:
    """Extract born-digital PDF text without granting Poppler persistence authority.

    The adapter accepts explicit whole-document or `pdf_page:v1` scopes. It preserves
    page boundaries and computes per-page evidence so mixed native/image-only PDFs
    cannot pass merely because a document-level command returned success.
    """

    def __init__(
        self,
        toolchain: _Toolchain,
        *,
        config: PopplerPdfTextConfig | None = None,
    ) -> None:
        self._toolchain = toolchain
        self.config = config or PopplerPdfTextConfig()
        self.configuration_hash = self.config.canonical_hash()
        self._descriptor = ProcessorDescriptor(
            key="poppler.pdf_text",
            capability_key="text_extract",
            implementation_version=toolchain.version,
            execution_venue="local_deterministic",
            input_media_types=frozenset({"application/pdf"}),
            output_kinds=frozenset({"extracted_text"}),
            scope_kinds=frozenset({"whole", "pdf_page"}),
            requires_egress=False,
            max_input_bytes=self.config.max_input_bytes,
            max_scopes=self.config.max_scopes,
        )

    @classmethod
    def discover(
        cls,
        *,
        config: PopplerPdfTextConfig | None = None,
        pdftotext: str = "pdftotext",
        pdfinfo: str = "pdfinfo",
        pdfimages: str = "pdfimages",
    ) -> "PopplerPdfTextProcessor":
        resolved = {
            "pdftotext": shutil.which(pdftotext),
            "pdfinfo": shutil.which(pdfinfo),
            "pdfimages": shutil.which(pdfimages),
        }
        missing = [name for name, path in resolved.items() if path is None]
        if missing:
            raise PopplerUnavailableError(
                "required Poppler executables are unavailable: " + ", ".join(missing)
            )
        assert all(path is not None for path in resolved.values())
        versions = {
            name: cls._probe_version(path)  # type: ignore[arg-type]
            for name, path in resolved.items()
        }
        if len(set(versions.values())) != 1:
            raise PopplerUnavailableError(
                f"Poppler executable versions disagree: {versions!r}"
            )
        return cls(
            _Toolchain(
                resolved["pdftotext"] or "",
                resolved["pdfinfo"] or "",
                resolved["pdfimages"] or "",
                versions["pdftotext"],
            ),
            config=config,
        )

    @property
    def descriptor(self) -> ProcessorDescriptor:
        return self._descriptor

    @staticmethod
    def _probe_version(executable: str) -> str:
        try:
            completed = subprocess.run(
                [executable, "-v"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=_clean_env(),
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PopplerUnavailableError(f"cannot execute {executable!r}") from exc
        text = (completed.stdout + "\n" + completed.stderr).strip()
        match = _VERSION_RE.search(text)
        if completed.returncode != 0 or match is None:
            raise PopplerUnavailableError(
                f"cannot determine Poppler version for {executable!r}"
            )
        return match.group("version")

    def process(self, invocation: ProcessorInvocation) -> ProcessorResult:
        if invocation.request.configuration_hash != self.configuration_hash:
            raise PopplerConfigurationError(
                "ProcessingRequest.configuration_hash does not match trusted Poppler configuration"
            )
        if invocation.media_type != "application/pdf":
            raise PopplerConfigurationError("PopplerPdfTextProcessor requires application/pdf")
        if len(invocation.source_bytes) > self.config.max_input_bytes:
            return ProcessorResult("failed", error_code="input_too_large")

        try:
            with tempfile.TemporaryDirectory(prefix="canario-poppler-") as tempdir:
                pdf_path = Path(tempdir) / "input.pdf"
                pdf_path.write_bytes(invocation.source_bytes)
                deadline = time.monotonic() + self.config.attempt_timeout_seconds

                page_count = self._page_count(pdf_path, deadline)
                if page_count > self.config.max_pages:
                    return ProcessorResult("failed", error_code="page_limit_exceeded")

                image_counts = self._image_counts(pdf_path, deadline)
                scope_pages = self._scope_pages(invocation, page_count)
                page_text = self._extract_requested_pages(
                    pdf_path,
                    Path(tempdir),
                    scope_pages,
                    page_count,
                    deadline,
                )

                evidence: list[QualitySignal] = []
                ordered_chunks: list[bytes] = []
                for scope in invocation.scopes:
                    pages = scope_pages[scope.id]
                    chunks = tuple(page_text[page] for page in pages)
                    ordered_chunks.extend(chunks)
                    if scope.selector_kind == "whole":
                        evidence.extend(
                            self._whole_evidence(
                                scope.id,
                                chunks,
                                image_counts,
                                page_count,
                            )
                        )
                    else:
                        page = pages[0]
                        evidence.extend(
                            self._page_evidence(
                                scope.id,
                                chunks[0],
                                image_counts.get(page, 0),
                            )
                        )

                output = b"".join(ordered_chunks)
                if len(output) > self.config.max_output_bytes:
                    return ProcessorResult("failed", error_code="output_too_large")
                outputs = (
                    DerivativeOutput(
                        output,
                        "extracted_text",
                        "text/plain",
                        invocation.language,
                        "utf-8",
                    ),
                ) if output.strip() else ()
                diagnostics = self._diagnostics(invocation, page_text, image_counts, scope_pages)
                return ProcessorResult(
                    "success",
                    outputs,
                    tuple(evidence),
                    diagnostic_codes=diagnostics,
                )
        except subprocess.TimeoutExpired:
            return ProcessorResult("failed", error_code="processor_timeout")
        except _PopplerCommandError as exc:
            return ProcessorResult("failed", error_code=exc.error_code)

    def _page_count(self, pdf_path: Path, deadline: float) -> int:
        completed = self._run([self._toolchain.pdfinfo, str(pdf_path)], deadline)
        match = _PAGES_RE.search(completed.stdout.decode("utf-8", errors="replace"))
        if match is None:
            raise _PopplerCommandError("pdfinfo_invalid_output")
        return int(match.group("count"))

    def _image_counts(self, pdf_path: Path, deadline: float) -> dict[int, int]:
        completed = self._run([self._toolchain.pdfimages, "-list", str(pdf_path)], deadline)
        text = completed.stdout.decode("utf-8", errors="replace")
        counts: dict[int, int] = {}
        for match in _IMAGE_ROW_RE.finditer(text):
            page = int(match.group("page"))
            counts[page] = counts.get(page, 0) + 1
        return counts

    def _extract_requested_pages(
        self,
        pdf_path: Path,
        tempdir: Path,
        scope_pages: dict[str, tuple[int, ...]],
        page_count: int,
        deadline: float,
    ) -> dict[int, bytes]:
        all_pages = tuple(range(1, page_count + 1))
        if len(scope_pages) == 1 and next(iter(scope_pages.values())) == all_pages:
            output = tempdir / "whole.txt"
            self._run_pdftotext(pdf_path, output, deadline=deadline)
            payload = self._read_bounded_output(output)
            chunks = payload.split(b"\f")
            if chunks and chunks[-1] == b"":
                chunks.pop()
            if len(chunks) != page_count:
                raise _PopplerCommandError("page_boundary_mismatch")
            return {page: chunks[page - 1] + b"\f" for page in all_pages}

        result: dict[int, bytes] = {}
        requested_pages = sorted({page for pages in scope_pages.values() for page in pages})
        total = 0
        for page in requested_pages:
            output = tempdir / f"page-{page}.txt"
            self._run_pdftotext(
                pdf_path, output, first_page=page, last_page=page, deadline=deadline
            )
            payload = self._read_bounded_output(output)
            total += len(payload)
            if total > self.config.max_output_bytes:
                raise _PopplerCommandError("output_too_large")
            result[page] = payload
        return result

    def _run_pdftotext(
        self,
        pdf_path: Path,
        output_path: Path,
        *,
        first_page: int | None = None,
        last_page: int | None = None,
        deadline: float,
    ) -> None:
        command = [self._toolchain.pdftotext]
        if first_page is not None:
            assert last_page is not None
            command.extend(["-f", str(first_page), "-l", str(last_page)])
        command.extend(["-enc", "UTF-8", "-eol", "unix"])
        if self.config.layout:
            command.append("-layout")
        command.extend([str(pdf_path), str(output_path)])
        self._run(command, deadline)

    def _read_bounded_output(self, output_path: Path) -> bytes:
        try:
            size = output_path.stat().st_size
        except FileNotFoundError as exc:
            raise _PopplerCommandError("pdftotext_missing_output") from exc
        if size > self.config.max_output_bytes:
            raise _PopplerCommandError("output_too_large")
        return output_path.read_bytes()

    def _run(
        self, command: list[str], deadline: float
    ) -> subprocess.CompletedProcess[bytes]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(command, self.config.attempt_timeout_seconds)
        timeout = min(float(self.config.timeout_seconds), remaining)
        try:
            completed = subprocess.run(
                command,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=_clean_env(),
                timeout=timeout,
            )
        except OSError as exc:
            raise _PopplerCommandError("poppler_unavailable") from exc
        if completed.returncode != 0:
            raise _PopplerCommandError("poppler_failed")
        return completed

    @staticmethod
    def _scope_pages(
        invocation: ProcessorInvocation, page_count: int
    ) -> dict[str, tuple[int, ...]]:
        if any(scope.selector_kind == "whole" for scope in invocation.scopes):
            if len(invocation.scopes) != 1:
                raise _PopplerCommandError("overlapping_scope")
            scope = invocation.scopes[0]
            if scope.selector_kind != "whole" or scope.selector_version != "v1":
                raise _PopplerCommandError("unsupported_scope")
            return {scope.id: tuple(range(1, page_count + 1))}

        selected: dict[str, tuple[int, ...]] = {}
        seen_pages: set[int] = set()
        for scope in invocation.scopes:
            if scope.selector_kind != "pdf_page" or scope.selector_version != "v1":
                raise _PopplerCommandError("unsupported_scope")
            payload = json.loads(scope.selector_payload_json)
            page = payload["page_ordinal"]
            if page > page_count:
                raise _PopplerCommandError("page_out_of_range")
            if page in seen_pages:
                raise _PopplerCommandError("duplicate_page_scope")
            seen_pages.add(page)
            selected[scope.id] = (page,)
        return selected

    @staticmethod
    def _page_evidence(
        target_id: str, text: bytes, raster_image_count: int
    ) -> tuple[QualitySignal, ...]:
        present = bool(text.strip())
        content = _text_content(text)
        replacement_ratio = _replacement_character_ratio(content)
        return (
            QualitySignal(target_id, "core.output_nonempty", "v1", present),
            QualitySignal(target_id, "native.page_text_present", "v1", present),
            QualitySignal(target_id, "native.page_text_coverage", "v1", 1.0 if present else 0.0),
            QualitySignal(target_id, "native.replacement_character_ratio", "v1", replacement_ratio),
            QualitySignal(target_id, "native.page_character_count", "v1", len(content)),
            QualitySignal(target_id, "native.page_raster_image_count", "v1", raster_image_count),
        )

    @staticmethod
    def _whole_evidence(
        target_id: str,
        chunks: tuple[bytes, ...],
        image_counts: dict[int, int],
        page_count: int,
    ) -> tuple[QualitySignal, ...]:
        present = tuple(bool(chunk.strip()) for chunk in chunks)
        nonempty_pages = sum(present)
        coverage = nonempty_pages / page_count
        all_present = nonempty_pages == page_count
        contents = tuple(_text_content(chunk) for chunk in chunks)
        total_chars = sum(len(content) for content in contents)
        replacement_count = sum(content.count("\ufffd") for content in contents)
        replacement_ratio = replacement_count / total_chars if total_chars else 0.0
        total_images = sum(image_counts.values())
        empty_ordinals = [index for index, value in enumerate(present, 1) if not value]
        return (
            QualitySignal(target_id, "core.output_nonempty", "v1", nonempty_pages > 0),
            QualitySignal(target_id, "native.page_text_present", "v1", all_present),
            QualitySignal(target_id, "native.page_text_coverage", "v1", coverage),
            QualitySignal(target_id, "native.replacement_character_ratio", "v1", replacement_ratio),
            QualitySignal(target_id, "native.page_character_count", "v1", total_chars),
            QualitySignal(target_id, "native.page_raster_image_count", "v1", total_images),
            QualitySignal(target_id, "native.selected_page_count", "v1", page_count),
            QualitySignal(target_id, "native.empty_page_count", "v1", page_count - nonempty_pages),
            QualitySignal(target_id, "native.empty_page_ordinals", "v1", empty_ordinals),
            QualitySignal(
                target_id,
                "native.mixed_page_modes",
                "v1",
                0 < nonempty_pages < page_count,
            ),
        )

    @staticmethod
    def _diagnostics(
        invocation: ProcessorInvocation,
        page_text: dict[int, bytes],
        image_counts: dict[int, int],
        scope_pages: dict[str, tuple[int, ...]],
    ) -> tuple[str, ...]:
        pages = tuple(
            page
            for scope in invocation.scopes
            for page in scope_pages[scope.id]
        )
        nonempty = [page for page in pages if page_text[page].strip()]
        empty = [page for page in pages if not page_text[page].strip()]
        diagnostics: list[str] = []
        if empty:
            diagnostics.append("native_empty_pages")
        if nonempty and empty:
            diagnostics.append("mixed_native_image_pages")
        if any(image_counts.get(page, 0) > 0 for page in pages):
            diagnostics.append("raster_images_present")
        return tuple(diagnostics)


class _PopplerCommandError(RuntimeError):
    def __init__(self, error_code: str) -> None:
        self.error_code = error_code
        super().__init__(error_code)


def _text_content(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").replace("\f", "").strip()


def _replacement_character_ratio(content: str) -> float:
    return content.count("\ufffd") / len(content) if content else 0.0


def _clean_env() -> dict[str, str]:
    # Poppler is a deterministic local processor and has no reason to inherit
    # caller credentials, account variables, proxy settings, or other host
    # environment state. Executable paths are resolved before invocation.
    return {"LC_ALL": "C", "LANG": "C"}
