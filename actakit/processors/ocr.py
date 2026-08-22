"""Production D2 PDF OCR through OCRmyPDF + Tesseract."""

from __future__ import annotations

import hashlib
import os
import signal
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

_VERSION_TOKEN_RE = re.compile(r"(?P<version>[0-9]+(?:\.[0-9]+){1,3}(?:[-+._a-zA-Z0-9]*)?)")
_PAGES_RE = re.compile(r"^Pages:\s+(?P<count>[1-9][0-9]*)\s*$", re.MULTILINE)
_TESSDATA_PATH_RE = re.compile(r'^List of available languages in "(?P<path>[^"]+)"')


class OcrUnavailableError(RuntimeError):
    """The trusted OCRmyPDF/Tesseract reference toolchain is unavailable."""


class OcrConfigurationError(RuntimeError):
    """A request does not identify the exact trusted OCR adapter configuration."""


@dataclass(frozen=True, slots=True)
class OcrPdfConfig:
    """Trusted, benchmark-derived reference configuration for PDF OCR."""

    languages: tuple[str, ...] = ("spa", "eng")
    rotate_pages: bool = True
    deskew: bool = True
    jobs: int = 1
    omp_thread_limit: int = 1
    tesseract_timeout_seconds: int = 180
    command_timeout_seconds: int = 240
    attempt_timeout_seconds: int = 300
    max_input_bytes: int = 256 * 1024 * 1024
    max_output_bytes: int = 64 * 1024 * 1024
    max_intermediate_pdf_bytes: int = 384 * 1024 * 1024
    max_image_mpixels: int = 250
    max_document_pages: int = 2_000
    max_ocr_pages_per_attempt: int = 32
    max_scopes: int = 32

    def __post_init__(self) -> None:
        if not isinstance(self.languages, tuple) or not self.languages:
            raise ValueError("languages must be a non-empty tuple")
        if len(set(self.languages)) != len(self.languages):
            raise ValueError("languages cannot repeat")
        for language in self.languages:
            if not re.fullmatch(r"[a-z0-9_]+", language):
                raise ValueError("OCR language keys must be lowercase Tesseract tokens")
        for name in (
            "jobs",
            "omp_thread_limit",
            "tesseract_timeout_seconds",
            "command_timeout_seconds",
            "attempt_timeout_seconds",
            "max_input_bytes",
            "max_output_bytes",
            "max_intermediate_pdf_bytes",
            "max_image_mpixels",
            "max_document_pages",
            "max_ocr_pages_per_attempt",
            "max_scopes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.rotate_pages, bool) or not isinstance(self.deskew, bool):
            raise TypeError("rotate_pages and deskew must be booleans")
        if self.max_ocr_pages_per_attempt > self.max_document_pages:
            raise ValueError("max_ocr_pages_per_attempt cannot exceed max_document_pages")

    def canonical_hash(self) -> str:
        payload = json.dumps(
            {
                "attempt_timeout_seconds": self.attempt_timeout_seconds,
                "command_timeout_seconds": self.command_timeout_seconds,
                "deskew": self.deskew,
                "jobs": self.jobs,
                "languages": self.languages,
                "max_document_pages": self.max_document_pages,
                "max_input_bytes": self.max_input_bytes,
                "max_ocr_pages_per_attempt": self.max_ocr_pages_per_attempt,
                "max_output_bytes": self.max_output_bytes,
                "max_intermediate_pdf_bytes": self.max_intermediate_pdf_bytes,
                "max_image_mpixels": self.max_image_mpixels,
                "max_scopes": self.max_scopes,
                "mode": "skip",
                "ocr_engine": "tesseract",
                "omp_thread_limit": self.omp_thread_limit,
                "optimize": 0,
                "rasterizer": "pypdfium",
                "output_type": "pdf",
                "rotate_pages": self.rotate_pages,
                "tesseract_timeout_seconds": self.tesseract_timeout_seconds,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class _OcrToolchain:
    ocrmypdf: str
    tesseract: str
    pdfinfo: str
    pdftotext: str
    ocrmypdf_version: str
    tesseract_version: str
    poppler_version: str
    pypdfium2_version: str
    fpdf2_version: str
    uharfbuzz_version: str
    pikepdf_version: str
    tesseract_languages: frozenset[str]
    tessdata_hashes: tuple[tuple[str, str], ...]

    @property
    def implementation_version(self) -> str:
        return (
            f"ocrmypdf-{self.ocrmypdf_version}"
            f"+tesseract-{self.tesseract_version}"
            f"+pypdfium2-{self.pypdfium2_version}"
            f"+fpdf2-{self.fpdf2_version}"
            f"+uharfbuzz-{self.uharfbuzz_version}"
            f"+pikepdf-{self.pikepdf_version}"
            f"+poppler-{self.poppler_version}"
        )


class OcrPdfProcessor:
    """OCR PDF pages without granting OCRmyPDF canonical persistence authority."""

    def __init__(
        self,
        toolchain: _OcrToolchain,
        *,
        config: OcrPdfConfig | None = None,
    ) -> None:
        self._toolchain = toolchain
        self.config = config or OcrPdfConfig()
        required_languages = set(self.config.languages)
        if self.config.rotate_pages:
            required_languages.add("osd")
        missing_languages = required_languages - toolchain.tesseract_languages
        if missing_languages:
            raise OcrUnavailableError(
                "required Tesseract language data unavailable: "
                + ", ".join(sorted(missing_languages))
            )
        self.configuration_hash = self.config.canonical_hash()
        model_languages = self.config.languages + (("osd",) if self.config.rotate_pages else ())
        tessdata = dict(toolchain.tessdata_hashes)
        missing_hashes = [language for language in model_languages if language not in tessdata]
        if missing_hashes:
            raise OcrUnavailableError(
                "required Tesseract model hashes unavailable: "
                + ", ".join(missing_hashes)
            )
        model_digest = _aggregate_tessdata_hashes(model_languages, tessdata)
        self._descriptor = ProcessorDescriptor(
            key="ocrmypdf.tesseract_pdf",
            capability_key="ocr",
            implementation_version=toolchain.implementation_version,
            execution_venue="local_deterministic",
            input_media_types=frozenset({"application/pdf"}),
            output_kinds=frozenset({"ocr_text"}),
            scope_kinds=frozenset({"whole", "pdf_page"}),
            requires_egress=False,
            model_provider="tesseract",
            model_name=f"{'+'.join(model_languages)}@sha256:{model_digest}",
            max_input_bytes=self.config.max_input_bytes,
            max_scopes=self.config.max_scopes,
        )

    @classmethod
    def discover(
        cls,
        *,
        config: OcrPdfConfig | None = None,
        ocrmypdf: str = "ocrmypdf",
        tesseract: str = "tesseract",
        pdfinfo: str = "pdfinfo",
        pdftotext: str = "pdftotext",
    ) -> "OcrPdfProcessor":
        effective_config = config or OcrPdfConfig()
        names = {
            "ocrmypdf": ocrmypdf,
            "tesseract": tesseract,
            "pdfinfo": pdfinfo,
            "pdftotext": pdftotext,
        }
        resolved = {name: shutil.which(value) for name, value in names.items()}
        missing = [name for name, path in resolved.items() if path is None]
        if missing:
            raise OcrUnavailableError(
                "required OCR reference executables unavailable: " + ", ".join(missing)
            )
        paths = {name: path or "" for name, path in resolved.items()}
        ocr_version = cls._probe_simple_version([paths["ocrmypdf"], "--version"])
        pypdfium_version = cls._probe_sibling_python_package_version(
            paths["ocrmypdf"], "pypdfium2"
        )
        fpdf2_version = cls._probe_sibling_python_package_version(paths["ocrmypdf"], "fpdf2")
        uharfbuzz_version = cls._probe_sibling_python_package_version(
            paths["ocrmypdf"], "uharfbuzz"
        )
        pikepdf_version = cls._probe_sibling_python_package_version(paths["ocrmypdf"], "pikepdf")
        tess_version = cls._probe_simple_version([paths["tesseract"], "--version"])
        pdfinfo_version = cls._probe_poppler_version(paths["pdfinfo"])
        pdftotext_version = cls._probe_poppler_version(paths["pdftotext"])
        if pdfinfo_version != pdftotext_version:
            raise OcrUnavailableError(
                "Poppler executable versions disagree inside OCR toolchain"
            )
        required_models = effective_config.languages + (
            ("osd",) if effective_config.rotate_pages else ()
        )
        languages, tessdata_hashes = cls._probe_tesseract_languages(
            paths["tesseract"], required_models
        )
        return cls(
            _OcrToolchain(
                paths["ocrmypdf"],
                paths["tesseract"],
                paths["pdfinfo"],
                paths["pdftotext"],
                ocr_version,
                tess_version,
                pdfinfo_version,
                pypdfium_version,
                fpdf2_version,
                uharfbuzz_version,
                pikepdf_version,
                frozenset(languages),
                tessdata_hashes,
            ),
            config=effective_config,
        )

    @property
    def descriptor(self) -> ProcessorDescriptor:
        return self._descriptor

    @staticmethod
    def _probe_simple_version(command: list[str]) -> str:
        try:
            run = subprocess.run(
                command,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={
                    "LC_ALL": "C",
                    "LANG": "C",
                    "PATH": f"{Path(command[0]).resolve().parent}:{os.defpath}",
                },
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise OcrUnavailableError(f"cannot execute {command[0]!r}") from exc
        text = (run.stdout + "\n" + run.stderr).strip()
        match = _VERSION_TOKEN_RE.search(text)
        if run.returncode != 0 or match is None:
            raise OcrUnavailableError(f"cannot determine version for {command[0]!r}")
        return match.group("version")

    @classmethod
    def _probe_poppler_version(cls, executable: str) -> str:
        return cls._probe_simple_version([executable, "-v"])

    @staticmethod
    def _probe_sibling_python_package_version(executable: str, package: str) -> str:
        bin_dir = Path(executable).resolve().parent
        interpreter = next(
            (candidate for candidate in (bin_dir / "python", bin_dir / "python3") if candidate.is_file()),
            None,
        )
        if interpreter is None:
            raise OcrUnavailableError(
                f"cannot locate Python interpreter beside {executable!r} to identify {package}"
            )
        code = (
            "import importlib.metadata as m; "
            f"print(m.version({package!r}))"
        )
        try:
            run = subprocess.run(
                [str(interpreter), "-c", code],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={"LC_ALL": "C", "LANG": "C"},
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise OcrUnavailableError(f"cannot identify Python package {package!r}") from exc
        version = run.stdout.strip()
        if run.returncode != 0 or not _VERSION_TOKEN_RE.fullmatch(version):
            raise OcrUnavailableError(f"cannot determine version for Python package {package!r}")
        return version

    @staticmethod
    def _probe_tesseract_languages(
        executable: str, required_models: tuple[str, ...]
    ) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
        try:
            run = subprocess.run(
                [executable, "--list-langs"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={
                    "LC_ALL": "C",
                    "LANG": "C",
                    "PATH": f"{Path(executable).resolve().parent}:{os.defpath}",
                },
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise OcrUnavailableError("cannot query Tesseract languages") from exc
        if run.returncode != 0:
            raise OcrUnavailableError("cannot query Tesseract languages")
        lines = run.stdout.splitlines()
        if not lines:
            raise OcrUnavailableError("Tesseract language listing is empty")
        path_match = _TESSDATA_PATH_RE.match(lines[0].strip())
        if path_match is None:
            raise OcrUnavailableError("cannot identify Tesseract model directory")
        tessdata_dir = Path(path_match.group("path"))
        languages = tuple(line.strip() for line in lines[1:] if line.strip())
        hashes: list[tuple[str, str]] = []
        for language in required_models:
            model_path = tessdata_dir / f"{language}.traineddata"
            try:
                digest = _sha256_file(model_path)
            except OSError as exc:
                raise OcrUnavailableError(
                    f"cannot hash Tesseract model {language!r}"
                ) from exc
            hashes.append((language, digest))
        return languages, tuple(hashes)

    def process(self, invocation: ProcessorInvocation) -> ProcessorResult:
        if invocation.request.configuration_hash != self.configuration_hash:
            raise OcrConfigurationError(
                "ProcessingRequest.configuration_hash does not match trusted OCR configuration"
            )
        if invocation.media_type != "application/pdf":
            raise OcrConfigurationError("OcrPdfProcessor requires application/pdf")
        if len(invocation.source_bytes) > self.config.max_input_bytes:
            return ProcessorResult("failed", error_code="input_too_large")

        try:
            with tempfile.TemporaryDirectory(prefix="actakit-ocr-") as tempdir_str:
                tempdir = Path(tempdir_str)
                input_pdf = tempdir / "input.pdf"
                output_pdf = tempdir / "ocr.pdf"
                input_pdf.write_bytes(invocation.source_bytes)
                deadline = time.monotonic() + self.config.attempt_timeout_seconds

                page_count = self._page_count(input_pdf, tempdir, deadline)
                if page_count > self.config.max_document_pages:
                    return ProcessorResult("failed", error_code="page_limit_exceeded")
                scope_pages = self._scope_pages(invocation, page_count)
                selected_pages = tuple(
                    dict.fromkeys(
                        page for scope in invocation.scopes for page in scope_pages[scope.id]
                    )
                )
                native_text = self._extract_pages(
                    input_pdf, selected_pages, page_count, tempdir, deadline, "native"
                )
                native_present = {page: bool(native_text[page].strip()) for page in selected_pages}
                explicit_page_scope = all(scope.selector_kind == "pdf_page" for scope in invocation.scopes)
                if explicit_page_scope and any(native_present.values()):
                    return ProcessorResult(
                        "failed", error_code="native_text_present_for_ocr_scope"
                    )
                if all(native_present.values()):
                    return ProcessorResult("failed", error_code="ocr_not_required")
                ocr_pages = tuple(page for page in selected_pages if not native_present[page])
                if len(ocr_pages) > self.config.max_ocr_pages_per_attempt:
                    return ProcessorResult("failed", error_code="ocr_page_limit_exceeded")

                self._run_ocrmypdf(
                    input_pdf,
                    output_pdf,
                    ocr_pages,
                    tempdir,
                    deadline,
                )
                if not output_pdf.exists():
                    return ProcessorResult("failed", error_code="ocr_output_missing")
                if output_pdf.stat().st_size > self.config.max_intermediate_pdf_bytes:
                    return ProcessorResult("failed", error_code="intermediate_pdf_too_large")

                post_text = self._extract_pages(
                    output_pdf, selected_pages, page_count, tempdir, deadline, "postocr"
                )
                evidence: list[QualitySignal] = []
                ordered_chunks: list[bytes] = []
                for scope in invocation.scopes:
                    pages = scope_pages[scope.id]
                    chunks = tuple(post_text[page] for page in pages)
                    ordered_chunks.extend(chunks)
                    evidence.extend(
                        self._scope_evidence(
                            scope.id,
                            pages,
                            chunks,
                            native_present,
                        )
                    )

                output = b"".join(ordered_chunks)
                if len(output) > self.config.max_output_bytes:
                    return ProcessorResult("failed", error_code="output_too_large")
                outputs = (
                    DerivativeOutput(
                        output,
                        "ocr_text",
                        "text/plain",
                        invocation.language,
                        "utf-8",
                    ),
                ) if output.strip() else ()
                diagnostics: list[str] = []
                if not output.strip():
                    diagnostics.append("ocr_output_empty")
                if any(native_present.values()) and not all(native_present.values()):
                    diagnostics.append("ocr_mixed_native_scan")
                return ProcessorResult(
                    "success",
                    outputs,
                    tuple(evidence),
                    diagnostic_codes=tuple(diagnostics),
                )
        except subprocess.TimeoutExpired:
            return ProcessorResult("failed", error_code="processor_timeout")
        except _OcrCommandError as exc:
            return ProcessorResult("failed", error_code=exc.error_code)

    def _run_ocrmypdf(
        self,
        input_pdf: Path,
        output_pdf: Path,
        selected_pages: tuple[int, ...],
        tempdir: Path,
        deadline: float,
    ) -> None:
        command = [
            self._toolchain.ocrmypdf,
            "--mode", "skip",
            "--ocr-engine", "tesseract",
            "--rasterizer", "pypdfium",
            "--output-type", "pdf",
            "--optimize", "0",
            "--max-image-mpixels", str(self.config.max_image_mpixels),
            "--jobs", str(self.config.jobs),
            "--language", "+".join(self.config.languages),
            "--tesseract-timeout", str(self.config.tesseract_timeout_seconds),
        ]
        if self.config.rotate_pages:
            command.append("--rotate-pages")
        if self.config.deskew:
            command.append("--deskew")
        command.extend(["--pages", _page_spec(selected_pages), str(input_pdf), str(output_pdf)])
        self._run(command, tempdir, deadline)

    def _page_count(self, pdf: Path, tempdir: Path, deadline: float) -> int:
        run = self._run([self._toolchain.pdfinfo, str(pdf)], tempdir, deadline)
        match = _PAGES_RE.search(run.stdout.decode("utf-8", errors="replace"))
        if match is None:
            raise _OcrCommandError("pdfinfo_invalid_output")
        return int(match.group("count"))

    def _extract_pages(
        self,
        pdf: Path,
        pages: tuple[int, ...],
        page_count: int,
        tempdir: Path,
        deadline: float,
        prefix: str,
    ) -> dict[int, bytes]:
        unique_pages = tuple(sorted(set(pages)))
        if unique_pages == tuple(range(1, page_count + 1)):
            output = tempdir / f"{prefix}-whole.txt"
            self._run(
                [
                    self._toolchain.pdftotext,
                    "-enc", "UTF-8",
                    "-eol", "unix",
                    "-layout",
                    str(pdf),
                    str(output),
                ],
                tempdir,
                deadline,
            )
            payload = self._read_bounded_text_output(output)
            chunks = payload.split(b"\f")
            if chunks and not chunks[-1]:
                chunks.pop()
            if len(chunks) != page_count:
                raise _OcrCommandError("page_boundary_mismatch")
            return {page: chunks[page - 1] + b"\f" for page in unique_pages}

        result: dict[int, bytes] = {}
        total = 0
        for page in unique_pages:
            output = tempdir / f"{prefix}-{page}.txt"
            self._run(
                [
                    self._toolchain.pdftotext,
                    "-f", str(page),
                    "-l", str(page),
                    "-enc", "UTF-8",
                    "-eol", "unix",
                    "-layout",
                    str(pdf),
                    str(output),
                ],
                tempdir,
                deadline,
            )
            payload = self._read_bounded_text_output(output)
            total += len(payload)
            if total > self.config.max_output_bytes:
                raise _OcrCommandError("output_too_large")
            result[page] = payload
        return result

    def _read_bounded_text_output(self, output: Path) -> bytes:
        try:
            size = output.stat().st_size
        except FileNotFoundError as exc:
            raise _OcrCommandError("pdftotext_missing_output") from exc
        if size > self.config.max_output_bytes:
            raise _OcrCommandError("output_too_large")
        return output.read_bytes()

    def _run(
        self,
        command: list[str],
        tempdir: Path,
        deadline: float,
    ) -> subprocess.CompletedProcess[bytes]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(command, self.config.attempt_timeout_seconds)
        timeout = min(float(self.config.command_timeout_seconds), remaining)
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=tempdir,
                env=self._clean_env(tempdir),
                start_new_session=(os.name == "posix"),
            )
        except OSError as exc:
            raise _OcrCommandError("ocr_tool_unavailable") from exc
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            process.communicate()
            raise
        run = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        if run.returncode != 0:
            if command[0] == self._toolchain.ocrmypdf:
                raise _OcrCommandError("ocrmypdf_failed")
            raise _OcrCommandError("ocr_support_tool_failed")
        return run

    def _clean_env(self, tempdir: Path) -> dict[str, str]:
        paths = []
        for executable in (
            self._toolchain.ocrmypdf,
            self._toolchain.tesseract,
            self._toolchain.pdfinfo,
            self._toolchain.pdftotext,
        ):
            parent = str(Path(executable).resolve().parent)
            if parent not in paths:
                paths.append(parent)
        home = tempdir / "home"
        cache = tempdir / "cache"
        home.mkdir(exist_ok=True)
        cache.mkdir(exist_ok=True)
        return {
            "LC_ALL": "C",
            "LANG": "C",
            "PATH": ":".join(paths),
            "HOME": str(home),
            "XDG_CACHE_HOME": str(cache),
            "TMPDIR": str(tempdir),
            "OMP_THREAD_LIMIT": str(self.config.omp_thread_limit),
        }

    @staticmethod
    def _scope_pages(
        invocation: ProcessorInvocation, page_count: int
    ) -> dict[str, tuple[int, ...]]:
        if any(scope.selector_kind == "whole" for scope in invocation.scopes):
            if len(invocation.scopes) != 1:
                raise _OcrCommandError("overlapping_scope")
            scope = invocation.scopes[0]
            if scope.selector_kind != "whole" or scope.selector_version != "v1":
                raise _OcrCommandError("unsupported_scope")
            return {scope.id: tuple(range(1, page_count + 1))}
        selected: dict[str, tuple[int, ...]] = {}
        seen: set[int] = set()
        for scope in invocation.scopes:
            if scope.selector_kind != "pdf_page" or scope.selector_version != "v1":
                raise _OcrCommandError("unsupported_scope")
            payload = json.loads(scope.selector_payload_json)
            page = payload["page_ordinal"]
            if page > page_count:
                raise _OcrCommandError("page_out_of_range")
            if page in seen:
                raise _OcrCommandError("duplicate_page_scope")
            seen.add(page)
            selected[scope.id] = (page,)
        return selected

    @staticmethod
    def _scope_evidence(
        target_id: str,
        pages: tuple[int, ...],
        chunks: tuple[bytes, ...],
        native_present: dict[int, bool],
    ) -> tuple[QualitySignal, ...]:
        present = tuple(bool(chunk.strip()) for chunk in chunks)
        nonempty = sum(present)
        total = len(pages)
        empty_ordinals = [page for page, has_text in zip(pages, present, strict=True) if not has_text]
        native_count = sum(1 for page in pages if native_present[page])
        ocr_ordinals = [page for page in pages if not native_present[page]]
        ocr_count = len(ocr_ordinals)
        character_count = sum(len(_text_content(chunk)) for chunk in chunks)
        return (
            QualitySignal(target_id, "core.output_nonempty", "v1", nonempty > 0),
            QualitySignal(target_id, "ocr.page_text_coverage", "v1", nonempty / total),
            QualitySignal(target_id, "ocr.page_character_count", "v1", character_count),
            QualitySignal(target_id, "ocr.selected_page_count", "v1", total),
            QualitySignal(target_id, "ocr.empty_page_count", "v1", total - nonempty),
            QualitySignal(target_id, "ocr.empty_page_ordinals", "v1", empty_ordinals),
            QualitySignal(target_id, "ocr.native_page_count", "v1", native_count),
            QualitySignal(target_id, "ocr.ocr_page_count", "v1", ocr_count),
            QualitySignal(target_id, "ocr.ocr_page_ordinals", "v1", ocr_ordinals),
            QualitySignal(
                target_id,
                "ocr.needs_visual_review",
                "v1",
                True,
                "conservative_reference_policy",
            ),
        )


class _OcrCommandError(RuntimeError):
    def __init__(self, error_code: str) -> None:
        self.error_code = error_code
        super().__init__(error_code)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _aggregate_tessdata_hashes(
    languages: tuple[str, ...], tessdata_hashes: dict[str, str]
) -> str:
    payload = json.dumps(
        [(language, tessdata_hashes[language]) for language in languages],
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _page_spec(pages: tuple[int, ...]) -> str:
    return ",".join(str(page) for page in sorted(set(pages)))


def _text_content(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").replace("\f", "").strip()
