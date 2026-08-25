"""Trusted deterministic media inspection at the Workbench boundary."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .contracts import DerivativeOutput, ProcessorDescriptor, ProcessorInvocation, ProcessorResult, QualitySignal


class MediaInspectionProcessor:
    def __init__(self, *, ffprobe: str = "ffprobe", max_input_bytes: int = 512 * 1024 * 1024) -> None:
        executable = shutil.which(ffprobe)
        if executable is None:
            raise RuntimeError("ffprobe is unavailable")
        self.ffprobe = executable
        self.max_input_bytes = max_input_bytes
        self._descriptor = ProcessorDescriptor(
            key="core.ffprobe_media_index",
            capability_key="media_inspect",
            implementation_version="ffprobe-8.1.2",
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
            duration = probe.get("format", {}).get("duration")
            if not isinstance(duration, str):
                return ProcessorResult("failed", error_code="media_duration_missing")
            duration_us = int(round(float(duration) * 1_000_000))
            if duration_us <= 0:
                return ProcessorResult("failed", error_code="media_duration_invalid")
            payload = {
                "format": "canario.media_index.v1",
                "source_sha256": hashlib.sha256(invocation.source_bytes).hexdigest(),
                "duration_us": duration_us,
                "probe": probe,
            }
            data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
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
