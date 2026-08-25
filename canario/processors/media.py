"""Trusted deterministic media inspection at the Workbench boundary."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from .contracts import DerivativeOutput, ProcessorDescriptor, ProcessorInvocation, ProcessorResult, QualitySignal


class MediaIndexError(ValueError):
    """A canonical media index is malformed or does not match retained media bytes."""


def duration_us_from_probe(probe: object) -> int:
    """Derive canonical integer microseconds from ffprobe format.duration."""
    if not isinstance(probe, dict):
        raise MediaIndexError("media index probe must be an object")
    format_info = probe.get("format")
    if not isinstance(format_info, dict):
        raise MediaIndexError("media index probe has no format object")
    duration = format_info.get("duration")
    if not isinstance(duration, str):
        raise MediaIndexError("media index probe has no string format.duration")
    try:
        value = int(
            (Decimal(duration) * Decimal(1_000_000)).to_integral_value(
                rounding=ROUND_HALF_UP
            )
        )
    except InvalidOperation as exc:
        raise MediaIndexError("media index probe duration is invalid") from exc
    if value <= 0:
        raise MediaIndexError("media index probe duration must be positive")
    return value


def validate_media_index(source_bytes: bytes, index_bytes: bytes) -> dict[str, object]:
    """Validate one canonical media-index derivative against exact retained bytes.

    ``duration_us`` is derived evidence, not an independently trusted assertion: it
    must exactly match deterministic conversion of the retained ffprobe payload.
    """
    try:
        value = json.loads(index_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MediaIndexError("media index is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise MediaIndexError("media index must be an object")
    if set(value) != {"format", "source_sha256", "duration_us", "probe"}:
        raise MediaIndexError("media index has unexpected or missing top-level fields")
    if value.get("format") != "canario.media_index.v1":
        raise MediaIndexError("media index has an unknown format")
    digest = hashlib.sha256(source_bytes).hexdigest()
    if value.get("source_sha256") != digest:
        raise MediaIndexError("media index does not describe the retained source bytes")
    duration_us = value.get("duration_us")
    if isinstance(duration_us, bool) or not isinstance(duration_us, int) or duration_us <= 0:
        raise MediaIndexError("media index has no positive integer duration_us")
    probe = value.get("probe")
    expected_duration_us = duration_us_from_probe(probe)
    if duration_us != expected_duration_us:
        raise MediaIndexError("media index duration_us disagrees with ffprobe format.duration")
    assert isinstance(probe, dict)
    format_info = probe.get("format")
    assert isinstance(format_info, dict)
    if "filename" in format_info:
        raise MediaIndexError("canonical media index must not retain execution-path filename")
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if canonical != index_bytes:
        raise MediaIndexError("media index bytes are not canonical deterministic JSON")
    return value


class MediaInspectionProcessor:
    def __init__(self, *, ffprobe: str = "ffprobe", max_input_bytes: int = 512 * 1024 * 1024) -> None:
        executable = shutil.which(ffprobe)
        if executable is None:
            raise RuntimeError("ffprobe is unavailable")
        self.ffprobe = executable
        self.ffprobe_version = self._version(executable)
        self.max_input_bytes = max_input_bytes
        self._descriptor = ProcessorDescriptor(
            key="core.ffprobe_media_index",
            capability_key="media_inspect",
            implementation_version=f"ffprobe-{self.ffprobe_version}",
            execution_venue="local_deterministic",
            input_media_types=frozenset({"video/mp4", "audio/mp4", "video/webm", "audio/mpeg"}),
            output_kinds=frozenset({"other"}),
            scope_kinds=frozenset({"whole"}),
            max_input_bytes=max_input_bytes,
            max_scopes=8,
        )

    @property
    def descriptor(self) -> ProcessorDescriptor:
        return self._descriptor

    def process(self, invocation: ProcessorInvocation) -> ProcessorResult:
        if invocation.media_type not in self.descriptor.input_media_types:
            return ProcessorResult("failed", error_code="unsupported_media_type")
        if len(invocation.source_bytes) > self.max_input_bytes:
            return ProcessorResult("failed", error_code="input_too_large")
        try:
            with tempfile.TemporaryDirectory(prefix="canario-ffprobe-") as directory:
                path = Path(directory) / "input.media"
                path.write_bytes(invocation.source_bytes)
                completed = subprocess.run(
                    [self.ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=120,
                    env={"PATH": str(Path(self.ffprobe).parent)},
                )
            if completed.returncode != 0:
                return ProcessorResult("failed", error_code="media_probe_failed")
            probe = json.loads(completed.stdout)
            try:
                duration_us = duration_us_from_probe(probe)
            except MediaIndexError:
                return ProcessorResult("failed", error_code="media_duration_invalid")
            # ffprobe reports the temporary input path in format.filename. That
            # path is execution noise and would make an otherwise identical
            # media-index derivative nondeterministic across runs/hosts.
            format_info = probe.get("format")
            if isinstance(format_info, dict):
                format_info.pop("filename", None)
            payload = {
                "format": "canario.media_index.v1",
                "source_sha256": hashlib.sha256(invocation.source_bytes).hexdigest(),
                "duration_us": duration_us,
                "probe": probe,
            }
            data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            try:
                validate_media_index(invocation.source_bytes, data)
            except MediaIndexError:
                return ProcessorResult("failed", error_code="media_probe_failed")
            evidence = tuple(
                QualitySignal(scope.id, "media.duration_us", "v1", duration_us)
                for scope in invocation.scopes
            )
            return ProcessorResult(
                "success",
                (DerivativeOutput(data, "other", "application/vnd.canario.media-index+json", charset="utf-8"),),
                evidence,
            )
        except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired):
            return ProcessorResult("failed", error_code="media_probe_failed")

    @staticmethod
    def _version(executable: str) -> str:
        try:
            completed = subprocess.run(
                [executable, "-version"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True,
                env={"PATH": str(Path(executable).parent)},
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError("ffprobe version probe failed") from exc
        first = completed.stdout.splitlines()[0] if completed.stdout else ""
        parts = first.split()
        if completed.returncode != 0 or len(parts) < 3 or parts[:2] != ["ffprobe", "version"]:
            raise RuntimeError("ffprobe version is unavailable")
        return parts[2]
