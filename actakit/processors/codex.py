"""Bounded page-scoped visual transcription through the official Codex CLI."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
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

_CODEX_VERSION_RE = re.compile(r"(?:codex-cli|OpenAI Codex v?)\s*(?P<version>[0-9]+(?:\.[0-9]+){2,3})", re.I)
_POPPLER_VERSION_RE = re.compile(r"version\s+(?P<version>[0-9]+(?:\.[0-9]+){1,3})", re.I)
_PAGES_RE = re.compile(r"^Pages:\s+(?P<count>[1-9][0-9]*)\s*$", re.MULTILINE)
_PAGE_SIZE_RE = re.compile(
    r"^Page\s+(?:[0-9]+\s+)?size:\s+(?P<width>[0-9]+(?:\.[0-9]+)?)\s+x\s+"
    r"(?P<height>[0-9]+(?:\.[0-9]+)?)\s+pts\b",
    re.MULTILINE,
)

_PROMPT_VERSION = "codex_visual_transcription_v1"
_EXEC_POLICY_VERSION = "codex_exec_policy_v2"
_STATIC_CODEX_CONFIG_OVERRIDES = (
    'model_reasoning_effort="none"',
    'model_reasoning_summary="none"',
    'hide_agent_reasoning=true',
    'show_raw_agent_reasoning=false',
    'project_doc_max_bytes=0',
    'skills.bundled.enabled=false',
    'web_search="disabled"',
    'features.view_image=false',
    'features.shell_tool=false',
    'features.unified_exec=false',
    'features.hooks=false',
    'features.plugins=false',
    'features.apps=false',
    'features.tool_suggest=false',
    'features.image_generation=false',
    'features.browser_use=false',
    'features.browser_use_external=false',
    'features.computer_use=false',
    'features.multi_agent=false',
    'features.multi_agent_v2.enabled=false',
)
_PROMPT = """You are performing bounded document representation processing, not civic interpretation.
Transcribe only the single attached civic-record page image.

Security and scope rules:
- Do not run shell commands or other tools.
- Do not inspect the filesystem, environment, skills, apps, repositories, or network.
- Use only the attached page image as document evidence.
- Process the attached image exactly once and return its filename stem as page_id.

Transcription rules:
- Return exact visible text; do not summarize or explain.
- Preserve visible reading order and page identity.
- Do not normalize names, numbers, punctuation, or accents unless the pixels show them that way.
- Do not infer civic meaning, election results, entities, relations, or claims.
- Do not invent unreadable text. Put a short description in uncertain_spans instead.
- Put rows in tables only when visible structure supports them.
- Return only data valid under the supplied JSON Schema.
"""


class CodexUnavailableError(RuntimeError):
    """The qualified subscription-backed Codex execution profile is unavailable."""


class CodexConfigurationError(RuntimeError):
    """A request does not match the qualified Codex visual-transcription configuration."""


@dataclass(frozen=True, slots=True)
class CodexVisualConfig:
    """Qualified reference configuration for one-page visual transcription."""

    model: str = "gpt-5.6-sol"
    qualified_codex_versions: tuple[str, ...] = ("0.149.0",)
    endpoint_profile: str = "openai_codex_subscription"
    auth_profile_key: str = "actakit_codex"
    auth_store_mode: str = "keyring"
    render_dpi: int = 300
    render_timeout_seconds: int = 60
    codex_timeout_seconds: int = 180
    attempt_timeout_seconds: int = 240
    max_input_bytes: int = 256 * 1024 * 1024
    max_document_pages: int = 2_000
    max_render_mpixels: int = 50
    max_image_bytes: int = 32 * 1024 * 1024
    max_output_json_bytes: int = 8 * 1024 * 1024
    max_transcription_chars: int = 2_000_000
    max_uncertain_spans: int = 32
    max_uncertain_span_chars: int = 200
    max_tables: int = 64
    max_rows_per_table: int = 2_048
    max_cells_per_row: int = 256
    max_cell_chars: int = 8_192
    max_scopes: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.model, str) or not self.model.strip() or any(c.isspace() for c in self.model):
            raise ValueError("model must be one non-empty Codex model token")
        if not isinstance(self.qualified_codex_versions, tuple) or not self.qualified_codex_versions:
            raise ValueError("qualified_codex_versions must be a non-empty tuple")
        if len(set(self.qualified_codex_versions)) != len(self.qualified_codex_versions):
            raise ValueError("qualified_codex_versions cannot repeat")
        if not all(re.fullmatch(r"[0-9]+(?:\.[0-9]+){2,3}", v) for v in self.qualified_codex_versions):
            raise ValueError("qualified Codex versions must be numeric semantic versions")
        for token_name in ("endpoint_profile", "auth_profile_key"):
            token = getattr(self, token_name)
            if not isinstance(token, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", token):
                raise ValueError(f"{token_name} must be a lowercase package-like token")
        if self.auth_store_mode != "keyring":
            raise ValueError("reference Codex execution requires keyring auth storage")
        for name in (
            "render_dpi",
            "render_timeout_seconds",
            "codex_timeout_seconds",
            "attempt_timeout_seconds",
            "max_input_bytes",
            "max_document_pages",
            "max_render_mpixels",
            "max_image_bytes",
            "max_output_json_bytes",
            "max_transcription_chars",
            "max_uncertain_spans",
            "max_uncertain_span_chars",
            "max_tables",
            "max_rows_per_table",
            "max_cells_per_row",
            "max_cell_chars",
            "max_scopes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.max_scopes != 1:
            raise ValueError("reference Codex visual transcription is exactly one page per ProcessRun")
        if self.attempt_timeout_seconds < self.codex_timeout_seconds:
            raise ValueError("attempt timeout cannot be shorter than Codex timeout")

    @property
    def prompt_hash(self) -> str:
        return hashlib.sha256(_PROMPT.encode("utf-8")).hexdigest()

    @property
    def output_schema(self) -> dict[str, object]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pages": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "page_id": {
                                "type": "string",
                                "pattern": r"^page_[0-9]{6}$",
                            },
                            "transcription": {
                                "type": "string",
                                "maxLength": self.max_transcription_chars,
                            },
                            "uncertain_spans": {
                                "type": "array",
                                "maxItems": self.max_uncertain_spans,
                                "items": {
                                    "type": "string",
                                    "maxLength": self.max_uncertain_span_chars,
                                },
                            },
                            "tables": {
                                "type": "array",
                                "maxItems": self.max_tables,
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "rows": {
                                            "type": "array",
                                            "maxItems": self.max_rows_per_table,
                                            "items": {
                                                "type": "array",
                                                "maxItems": self.max_cells_per_row,
                                                "items": {
                                                    "type": "string",
                                                    "maxLength": self.max_cell_chars,
                                                },
                                            },
                                        }
                                    },
                                    "required": ["rows"],
                                },
                            },
                        },
                        "required": ["page_id", "transcription", "uncertain_spans", "tables"],
                    },
                }
            },
            "required": ["pages"],
        }

    @property
    def output_schema_bytes(self) -> bytes:
        return (
            json.dumps(self.output_schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n"
        ).encode("utf-8")

    @property
    def output_schema_hash(self) -> str:
        return hashlib.sha256(self.output_schema_bytes).hexdigest()

    def canonical_hash(self) -> str:
        payload = json.dumps(
            {
                "attempt_timeout_seconds": self.attempt_timeout_seconds,
                "auth_profile_key": self.auth_profile_key,
                "auth_store_mode": self.auth_store_mode,
                "codex_timeout_seconds": self.codex_timeout_seconds,
                "endpoint_profile": self.endpoint_profile,
                "exec": {
                    "policy_version": _EXEC_POLICY_VERSION,
                    "config_overrides": _STATIC_CODEX_CONFIG_OVERRIDES,
                    "ephemeral": True,
                    "ignore_rules": True,
                    "ignore_user_config": True,
                    "model_reasoning_effort": "none",
                    "sandbox": "read-only",
                    "skip_git_repo_check": True,
                    "tools": "transcription_only",
                    "bundled_skills": False,
                },
                "max_cells_per_row": self.max_cells_per_row,
                "max_cell_chars": self.max_cell_chars,
                "max_document_pages": self.max_document_pages,
                "max_image_bytes": self.max_image_bytes,
                "max_input_bytes": self.max_input_bytes,
                "max_output_json_bytes": self.max_output_json_bytes,
                "max_render_mpixels": self.max_render_mpixels,
                "max_rows_per_table": self.max_rows_per_table,
                "max_scopes": self.max_scopes,
                "max_tables": self.max_tables,
                "max_transcription_chars": self.max_transcription_chars,
                "max_uncertain_span_chars": self.max_uncertain_span_chars,
                "max_uncertain_spans": self.max_uncertain_spans,
                "model": self.model,
                "output_schema_hash": self.output_schema_hash,
                "prompt_hash": self.prompt_hash,
                "prompt_version": _PROMPT_VERSION,
                "qualified_codex_versions": self.qualified_codex_versions,
                "render_dpi": self.render_dpi,
                "render_timeout_seconds": self.render_timeout_seconds,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class _CodexToolchain:
    codex: str
    pdfinfo: str
    pdftoppm: str
    codex_version: str
    poppler_version: str
    codex_home: Path

    @property
    def implementation_version(self) -> str:
        return f"codex-cli-{self.codex_version}+poppler-{self.poppler_version}"


class CodexVisualTranscriptionProcessor:
    """Use Codex only as a bounded, schema-constrained one-page visual executor."""

    def __init__(
        self,
        toolchain: _CodexToolchain,
        *,
        config: CodexVisualConfig | None = None,
    ) -> None:
        self._toolchain = toolchain
        self.config = config or CodexVisualConfig()
        if toolchain.codex_version not in self.config.qualified_codex_versions:
            raise CodexUnavailableError(
                f"Codex CLI {toolchain.codex_version} is not in the benchmark-qualified version set"
            )
        self._validate_isolated_codex_home(toolchain.codex_home)
        self.configuration_hash = self.config.canonical_hash()
        self.request_template_hash = self.config.prompt_hash
        self.output_schema_hash = self.config.output_schema_hash
        self._descriptor = ProcessorDescriptor(
            key="codex.visual_transcribe_pdf_page",
            capability_key="visual_transcribe",
            implementation_version=toolchain.implementation_version,
            execution_venue="subscription_agent",
            input_media_types=frozenset({"application/pdf"}),
            output_kinds=frozenset({"transcript", "table"}),
            scope_kinds=frozenset({"pdf_page"}),
            requires_egress=True,
            model_provider="openai",
            model_name=self.config.model,
            max_input_bytes=self.config.max_input_bytes,
            max_scopes=1,
        )

    @classmethod
    def discover(
        cls,
        *,
        codex_home: str | Path,
        config: CodexVisualConfig | None = None,
        codex: str = "codex",
        pdfinfo: str = "pdfinfo",
        pdftoppm: str = "pdftoppm",
    ) -> "CodexVisualTranscriptionProcessor":
        resolved = {
            "codex": shutil.which(codex),
            "pdfinfo": shutil.which(pdfinfo),
            "pdftoppm": shutil.which(pdftoppm),
        }
        missing = [name for name, path in resolved.items() if path is None]
        if missing:
            raise CodexUnavailableError(
                "required Codex reference executables unavailable: " + ", ".join(missing)
            )
        paths = {name: path or "" for name, path in resolved.items()}
        codex_version = cls._probe_codex_version(paths["codex"])
        pdfinfo_version = cls._probe_poppler_version(paths["pdfinfo"])
        pdftoppm_version = cls._probe_poppler_version(paths["pdftoppm"])
        if pdfinfo_version != pdftoppm_version:
            raise CodexUnavailableError("Poppler render executable versions disagree")
        home = Path(codex_home).expanduser().resolve()
        return cls(
            _CodexToolchain(
                paths["codex"],
                paths["pdfinfo"],
                paths["pdftoppm"],
                codex_version,
                pdfinfo_version,
                home,
            ),
            config=config,
        )

    @property
    def descriptor(self) -> ProcessorDescriptor:
        return self._descriptor

    @staticmethod
    def _probe_codex_version(executable: str) -> str:
        try:
            run = subprocess.run(
                [executable, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                env={"LC_ALL": "C", "LANG": "C", "PATH": os.environ.get("PATH", os.defpath)},
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise CodexUnavailableError("cannot execute Codex CLI") from exc
        text = (run.stdout + "\n" + run.stderr).strip()
        match = _CODEX_VERSION_RE.search(text)
        if run.returncode != 0 or match is None:
            raise CodexUnavailableError("cannot determine Codex CLI version")
        return match.group("version")

    @staticmethod
    def _probe_poppler_version(executable: str) -> str:
        try:
            run = subprocess.run(
                [executable, "-v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                env={"LC_ALL": "C", "LANG": "C", "PATH": os.defpath},
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise CodexUnavailableError(f"cannot execute Poppler tool {executable!r}") from exc
        text = (run.stdout + "\n" + run.stderr).strip()
        match = _POPPLER_VERSION_RE.search(text)
        if run.returncode != 0 or match is None:
            raise CodexUnavailableError(f"cannot determine Poppler version for {executable!r}")
        return match.group("version")

    @staticmethod
    def _validate_isolated_codex_home(codex_home: Path) -> None:
        if not codex_home.is_absolute() or not codex_home.is_dir():
            raise CodexUnavailableError("Codex reference profile must be an existing absolute directory")
        if os.name == "posix" and (codex_home.stat().st_mode & 0o077):
            raise CodexUnavailableError("Codex reference profile directory must be private (mode 0700)")
        default = (Path.home() / ".codex").resolve()
        if codex_home == default:
            raise CodexUnavailableError(
                "reference execution requires a dedicated Codex home, not the interactive default profile"
            )
        if (codex_home / "auth.json").exists():
            raise CodexUnavailableError(
                "reference Codex profile must use keyring auth; auth.json is not accepted"
            )
        if (codex_home / "config.toml").exists():
            raise CodexUnavailableError(
                "reference Codex profile must not depend on ambient config.toml"
            )
        skills = codex_home / "skills"
        if skills.is_dir():
            unexpected = [child.name for child in skills.iterdir() if child.name != ".system"]
            if unexpected:
                raise CodexUnavailableError(
                    "reference Codex profile contains user skills and is not isolated"
                )
        admin_skills = Path("/etc/codex/skills")
        if os.name == "posix" and admin_skills.is_dir():
            try:
                has_admin_skills = any(admin_skills.iterdir())
            except OSError as exc:
                raise CodexUnavailableError("cannot verify absence of admin Codex skills") from exc
            if has_admin_skills:
                raise CodexUnavailableError(
                    "reference Codex execution does not permit ambient /etc/codex skills"
                )

    def process(self, invocation: ProcessorInvocation) -> ProcessorResult:
        if invocation.request.configuration_hash != self.configuration_hash:
            raise CodexConfigurationError(
                "ProcessingRequest.configuration_hash does not match trusted Codex configuration"
            )
        if invocation.media_type != "application/pdf":
            raise CodexConfigurationError("Codex visual processor requires application/pdf")
        if len(invocation.source_bytes) > self.config.max_input_bytes:
            return ProcessorResult("failed", error_code="input_too_large", egress_bytes=0)
        self._validate_egress_authorization(invocation)
        if len(invocation.scopes) != 1:
            raise CodexConfigurationError("Codex visual processor requires exactly one page target")
        target = invocation.scopes[0]
        if target.selector_kind != "pdf_page" or target.selector_version != "v1":
            raise CodexConfigurationError("Codex visual processor accepts only pdf_page:v1")
        try:
            payload = json.loads(target.selector_payload_json)
            page_ordinal = payload["page_ordinal"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CodexConfigurationError("invalid pdf_page:v1 selector payload") from exc
        if isinstance(page_ordinal, bool) or not isinstance(page_ordinal, int) or page_ordinal < 1:
            raise CodexConfigurationError("invalid page ordinal")

        egress_bytes = 0
        image_size = 0
        try:
            with tempfile.TemporaryDirectory(prefix="actakit-codex-") as tempdir_str:
                root = Path(tempdir_str)
                render_dir = root / "render"
                scratch = root / "scratch"
                render_dir.mkdir(mode=0o700)
                scratch.mkdir(mode=0o700)
                deadline = time.monotonic() + self.config.attempt_timeout_seconds

                input_pdf = render_dir / "input.pdf"
                input_pdf.write_bytes(invocation.source_bytes)
                page_count = self._page_count(input_pdf, render_dir, deadline)
                if page_count > self.config.max_document_pages:
                    return ProcessorResult("failed", error_code="page_limit_exceeded", egress_bytes=0)
                if page_ordinal > page_count:
                    return ProcessorResult("failed", error_code="page_out_of_range", egress_bytes=0)
                self._validate_page_render_size(input_pdf, page_ordinal, render_dir, deadline)
                rendered = self._render_page(input_pdf, page_ordinal, render_dir, deadline)
                image_size = rendered.stat().st_size
                if image_size <= 0:
                    return ProcessorResult("failed", error_code="render_empty", egress_bytes=0)
                if image_size > self.config.max_image_bytes:
                    return ProcessorResult("failed", error_code="render_image_too_large", egress_bytes=0)

                page_id = f"page_{page_ordinal:06d}"
                image = scratch / f"{page_id}.png"
                shutil.copyfile(rendered, image)
                # Source PDF is not present when the cloud executor starts. Codex receives only
                # the bounded rendered page, the static schema, and the static prompt.
                try:
                    input_pdf.unlink()
                except FileNotFoundError:
                    pass
                schema = scratch / "output-schema.json"
                schema.write_bytes(self.config.output_schema_bytes)
                output = scratch / "result.json"

                self._run_codex(scratch, image, schema, output, deadline)
                # A successful executor return proves the bounded page attachment reached
                # the egress executor. Protocol framing is deliberately not guessed.
                egress_bytes = image_size
                value = self._read_and_validate_output(output, page_id)
                return self._result_from_value(
                    target.id, page_ordinal, value, egress_bytes, invocation.language
                )
        except _CodexRunError as exc:
            if exc.handed_off:
                egress_bytes = image_size
            evidence = ()
            if exc.error_code in {"codex_schema_invalid", "codex_output_invalid"}:
                evidence = (
                    QualitySignal(target.id, "multimodal.schema_valid", "v1", False),
                )
            return ProcessorResult(
                "failed",
                evidence=evidence,
                error_code=exc.error_code,
                egress_bytes=egress_bytes,
            )

    def _validate_egress_authorization(self, invocation: ProcessorInvocation) -> None:
        egress = invocation.request.egress
        if not egress.allowed:
            raise CodexConfigurationError("Codex execution requires explicit egress authorization")
        if egress.endpoint_profile != self.config.endpoint_profile:
            raise CodexConfigurationError("Codex endpoint profile does not match trusted configuration")
        if egress.request_template_hash != self.request_template_hash:
            raise CodexConfigurationError("egress authorization does not cover this request template")
        if egress.policy_profile == "no_egress" or egress.data_control_profile == "no_egress":
            raise CodexConfigurationError("Codex execution cannot use a no-egress policy profile")

    def _page_count(self, input_pdf: Path, cwd: Path, deadline: float) -> int:
        run = self._run_local(
            [self._toolchain.pdfinfo, str(input_pdf)], cwd, deadline, self.config.render_timeout_seconds
        )
        text = run.stdout.decode("utf-8", errors="replace")
        match = _PAGES_RE.search(text)
        if match is None:
            raise _CodexRunError("pdfinfo_invalid")
        return int(match.group("count"))

    def _validate_page_render_size(
        self, input_pdf: Path, page: int, cwd: Path, deadline: float
    ) -> None:
        run = self._run_local(
            [self._toolchain.pdfinfo, "-f", str(page), "-l", str(page), str(input_pdf)],
            cwd,
            deadline,
            self.config.render_timeout_seconds,
        )
        text = run.stdout.decode("utf-8", errors="replace")
        match = _PAGE_SIZE_RE.search(text)
        if match is None:
            raise _CodexRunError("page_geometry_unknown")
        width = float(match.group("width"))
        height = float(match.group("height"))
        pixels = width * height * (self.config.render_dpi / 72.0) ** 2
        if pixels > self.config.max_render_mpixels * 1_000_000:
            raise _CodexRunError("render_megapixel_limit")

    def _render_page(self, input_pdf: Path, page: int, cwd: Path, deadline: float) -> Path:
        prefix = cwd / "page"
        self._run_local(
            [
                self._toolchain.pdftoppm,
                "-f", str(page),
                "-l", str(page),
                "-singlefile",
                "-r", str(self.config.render_dpi),
                "-png",
                str(input_pdf),
                str(prefix),
            ],
            cwd,
            deadline,
            self.config.render_timeout_seconds,
        )
        output = cwd / "page.png"
        if not output.is_file():
            raise _CodexRunError("render_missing")
        return output

    def _run_local(
        self,
        command: list[str],
        cwd: Path,
        deadline: float,
        command_timeout: int,
    ) -> subprocess.CompletedProcess[bytes]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _CodexRunError("attempt_timeout", handed_off=False)
        timeout = min(float(command_timeout), remaining)
        try:
            run = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env={"LC_ALL": "C", "LANG": "C", "PATH": os.defpath},
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise _CodexRunError("render_timeout", handed_off=False) from exc
        except OSError as exc:
            raise _CodexRunError("render_tool_unavailable", handed_off=False) from exc
        if run.returncode != 0:
            raise _CodexRunError("render_failed")
        return run

    def _codex_command(
        self, scratch: Path, image: Path, schema: Path, output: Path
    ) -> list[str]:
        return [
            self._toolchain.codex,
            "exec",
            "--strict-config",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox", "read-only",
            "--skip-git-repo-check",
            "--model", self.config.model,
            "--output-schema", str(schema),
            "--output-last-message", str(output),
            "--cd", str(scratch),
            "--image", str(image),
            "-c", f'cli_auth_credentials_store="{self.config.auth_store_mode}"',
            *[part for override in _STATIC_CODEX_CONFIG_OVERRIDES for part in ("-c", override)],
            "-",
        ]

    def _run_codex(
        self,
        scratch: Path,
        image: Path,
        schema: Path,
        output: Path,
        deadline: float,
    ) -> None:
        command = self._codex_command(scratch, image, schema, output)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _CodexRunError("attempt_timeout", handed_off=False)
        timeout = min(float(self.config.codex_timeout_seconds), remaining)
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=scratch,
                env=self._codex_env(scratch),
                start_new_session=(os.name == "posix"),
            )
        except OSError as exc:
            raise _CodexRunError("codex_unavailable", handed_off=False) from exc
        try:
            process.communicate(_PROMPT.encode("utf-8"), timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            process.communicate()
            raise _CodexRunError("codex_timeout", handed_off=True)
        if process.returncode != 0:
            raise _CodexRunError("codex_exec_failed", handed_off=True)
        if not output.is_file():
            raise _CodexRunError("codex_output_missing", handed_off=True)

    def _codex_env(self, scratch: Path) -> dict[str, str]:
        home = scratch / "home"
        home.mkdir(mode=0o700, exist_ok=True)
        env = {
            "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8",
            "PATH": os.defpath,
            "HOME": str(home),
            "CODEX_HOME": str(self._toolchain.codex_home),
            "TMPDIR": str(scratch),
            "TERM": "dumb",
        }
        # Only pass host plumbing required for keyring/TLS. Deliberately exclude API keys,
        # proxy URLs, account identifiers and arbitrary CODEX_* configuration.
        for key in (
            "DBUS_SESSION_BUS_ADDRESS",
            "XDG_RUNTIME_DIR",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
        ):
            value = os.environ.get(key)
            if value:
                env[key] = value
        return env

    def _read_and_validate_output(self, output: Path, page_id: str) -> dict[str, object]:
        try:
            size = output.stat().st_size
        except FileNotFoundError as exc:
            raise _CodexRunError("codex_output_missing", handed_off=True) from exc
        if size <= 0 or size > self.config.max_output_json_bytes:
            raise _CodexRunError("codex_output_invalid", handed_off=True)
        try:
            value = json.loads(output.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
            raise _CodexRunError("codex_output_invalid", handed_off=True) from exc
        try:
            self._validate_value(value, page_id)
        except (TypeError, ValueError) as exc:
            raise _CodexRunError("codex_schema_invalid", handed_off=True) from exc
        return value

    def _validate_value(self, value: object, page_id: str) -> None:
        if not isinstance(value, dict) or set(value) != {"pages"}:
            raise ValueError("unexpected top-level output")
        pages = value["pages"]
        if not isinstance(pages, list) or len(pages) != 1:
            raise ValueError("Codex output must contain exactly one page")
        page = pages[0]
        if not isinstance(page, dict) or set(page) != {
            "page_id", "transcription", "uncertain_spans", "tables"
        }:
            raise ValueError("Codex page output violates exact contract")
        if page["page_id"] != page_id:
            raise ValueError("Codex output page identity mismatch")
        transcription = page["transcription"]
        if not isinstance(transcription, str) or len(transcription) > self.config.max_transcription_chars:
            raise ValueError("invalid transcription")
        uncertain = page["uncertain_spans"]
        if (
            not isinstance(uncertain, list)
            or len(uncertain) > self.config.max_uncertain_spans
            or not all(isinstance(item, str) and len(item) <= self.config.max_uncertain_span_chars for item in uncertain)
        ):
            raise ValueError("invalid uncertain spans")
        tables = page["tables"]
        if not isinstance(tables, list) or len(tables) > self.config.max_tables:
            raise ValueError("invalid tables")
        for table in tables:
            if not isinstance(table, dict) or set(table) != {"rows"}:
                raise ValueError("invalid table")
            rows = table["rows"]
            if not isinstance(rows, list) or len(rows) > self.config.max_rows_per_table:
                raise ValueError("invalid table rows")
            for row in rows:
                if (
                    not isinstance(row, list)
                    or len(row) > self.config.max_cells_per_row
                    or not all(isinstance(cell, str) and len(cell) <= self.config.max_cell_chars for cell in row)
                ):
                    raise ValueError("invalid table cells")

    def _result_from_value(
        self,
        target_id: str,
        page_ordinal: int,
        value: dict[str, object],
        egress_bytes: int,
        language: str | None,
    ) -> ProcessorResult:
        pages = value["pages"]
        assert isinstance(pages, list) and len(pages) == 1
        page = pages[0]
        assert isinstance(page, dict)
        transcription = page["transcription"]
        uncertain = page["uncertain_spans"]
        tables = page["tables"]
        assert isinstance(transcription, str)
        assert isinstance(uncertain, list)
        assert isinstance(tables, list)

        outputs: list[DerivativeOutput] = []
        if transcription:
            outputs.append(
                DerivativeOutput(
                    transcription.encode("utf-8"),
                    "transcript",
                    "text/plain",
                    language=language,
                    charset="utf-8",
                )
            )
        nonempty_tables = [
            table
            for table in tables
            if isinstance(table, dict)
            and isinstance(table.get("rows"), list)
            and any(any(bool(str(cell)) for cell in row) for row in table["rows"] if isinstance(row, list))
        ]
        if nonempty_tables:
            table_payload = json.dumps(
                {"page_ordinal": page_ordinal, "tables": nonempty_tables},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            outputs.append(
                DerivativeOutput(
                    table_payload, "table", "application/json", language=language, charset="utf-8"
                )
            )

        evidence = (
            QualitySignal(target_id, "core.output_nonempty", "v1", bool(outputs)),
            QualitySignal(target_id, "multimodal.schema_valid", "v1", True),
            QualitySignal(target_id, "multimodal.uncertain_span_count", "v1", len(uncertain)),
            QualitySignal(target_id, "multimodal.uncertain_spans", "v1", uncertain),
            QualitySignal(
                target_id,
                "multimodal.transcription_character_count",
                "v1",
                len(transcription),
            ),
            QualitySignal(target_id, "multimodal.table_count", "v1", len(tables)),
        )
        return ProcessorResult(
            "success",
            tuple(outputs),
            evidence,
            egress_bytes=egress_bytes,
        )


class _CodexRunError(RuntimeError):
    def __init__(self, error_code: str, *, handed_off: bool = False) -> None:
        self.error_code = error_code
        self.handed_off = handed_off
        super().__init__(error_code)
