from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import unittest
import zlib
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from canario.deposit import (
    AcquisitionObservation,
    AcquisitionWrite,
    CapturedArtifact,
    DepositWriter,
    SourceLocatorRegistration,
    SourceRegistration,
    new_id,
)
from canario.persistence import database
import canario.processors.codex as codex_module
from canario.processors import (
    EgressAuthorization,
    ProcessingRequest,
    ProcessorRegistry,
    ProcessorResolutionError,
    TargetRegistration,
    WorkbenchHost,
    WorkbenchWriter,
)
from canario.processors.codex import (
    CodexConfigurationError,
    CodexUnavailableError,
    CodexVisualConfig,
    CodexVisualTranscriptionProcessor,
    _CodexRunError,
    _CodexToolchain,
)

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-22T19:00:00.000Z"


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


def _pdf_bytes(pages: list[str | None]) -> bytes:
    objects: list[bytes | None] = [None, None]
    font_obj = 3
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_refs: list[int] = []
    for text in pages:
        content: list[str] = []
        if text:
            escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            content.append(f"BT /F1 12 Tf 72 450 Td ({escaped}) Tj ET")
        stream = "\n".join(content).encode("ascii")
        content_obj = len(objects) + 1
        objects.append(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )
        page_obj = len(objects) + 1
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {content_obj} 0 R >>"
            ).encode("ascii")
        )
        page_refs.append(page_obj)
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{ref} 0 R" for ref in page_refs)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_refs)} >>".encode("ascii")
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        assert obj is not None
        offsets.append(len(payload))
        payload.extend(f"{number} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(payload)


def _toolchain(home: Path) -> _CodexToolchain:
    pdfinfo = shutil.which("pdfinfo") or "/usr/bin/pdfinfo"
    pdftoppm = shutil.which("pdftoppm") or "/usr/bin/pdftoppm"
    return _CodexToolchain(
        "/usr/bin/true",
        pdfinfo,
        pdftoppm,
        "0.149.0",
        "26.07.0",
        home,
    )


class _SimulatedCodex(CodexVisualTranscriptionProcessor):
    def __init__(self, home: Path, *, payload: dict[str, object] | None = None, failure: str | None = None,
                 config: CodexVisualConfig | None = None) -> None:
        super().__init__(_toolchain(home), config=config)
        self.payload = payload
        self.failure = failure
        self.calls = 0
        self.source_absent_at_handoff = False
        self.last_env: dict[str, str] | None = None
        self.last_command: list[str] | None = None
        self.last_image_size = 0

    def _run_codex(self, scratch: Path, image: Path, schema: Path, output: Path, deadline: float) -> None:
        self.calls += 1
        self.source_absent_at_handoff = not (scratch.parent / "render" / "input.pdf").exists()
        self.last_env = self._codex_env(scratch)
        self.last_command = self._codex_command(scratch, image, schema, output)
        self.last_image_size = image.stat().st_size
        if self.failure:
            raise _CodexRunError(self.failure, handed_off=True)
        payload = self.payload
        if payload is None:
            payload = {
                "pages": [{
                    "page_id": image.stem,
                    "transcription": "Texto visible exacto",
                    "uncertain_spans": [],
                    "tables": [],
                }]
            }
        output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class CodexProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.codex_home = self.root / "codex-home"
        self.codex_home.mkdir(mode=0o700)
        self.db = self.root / "canario.sqlite3"
        self.archive = self.root / "archive"
        database._ensure_schema_v1(self.db, NO_RUNTIME_CHECK)
        self.deposit = DepositWriter(self.db, self.archive, connection_factory=local_connection)
        self.writer = WorkbenchWriter(self.db, self.archive, connection_factory=local_connection)
        self.source = SourceRegistration(new_id("src_"), "web", "Municipalidad", True, T)
        self.deposit.register_source(self.source)
        self.locator = SourceLocatorRegistration(
            new_id("sloc_"), self.source.id, "https://example.test/acta.pdf", "http_url", T
        )
        self.deposit.register_source_locator(self.locator)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _capture(self, data: bytes, *, availability: str = "available", language: str | None = "es") -> str:
        rep_id = new_id("rep_")
        artifact = CapturedArtifact(
            new_id("art_"), new_id("aob_"), rep_id, data, "primary", "acta.pdf",
            self.locator.locator, "application/pdf", "verified", availability, language, None, T,
        )
        observation = AcquisitionObservation(
            new_id("acq_"), self.source.id, self.locator.id, T, "success", 200,
            "fixture.codex", "1", None, T,
        )
        self.deposit.record_acquisition(AcquisitionWrite(observation, (artifact,)))
        return rep_id

    def _target(self, rep_id: str, kind: str, payload: dict[str, object]) -> str:
        target_id = new_id("rtgt_")
        self.writer.register_target(
            TargetRegistration(
                target_id, rep_id, kind, "v1",
                json.dumps(payload, sort_keys=True, separators=(",", ":")), T,
            )
        )
        return target_id

    def _auth(self, processor: CodexVisualTranscriptionProcessor) -> EgressAuthorization:
        return EgressAuthorization(
            True,
            "public_civic",
            "chatgpt_personal_operator_enabled",
            processor.request_template_hash,
            processor.config.endpoint_profile,
        )

    def _request(self, processor: CodexVisualTranscriptionProcessor, rep_id: str, target: str,
                 *, run_id: str | None = None) -> ProcessingRequest:
        return ProcessingRequest(
            rep_id,
            (target,),
            "visual_transcribe",
            processor.configuration_hash,
            self._auth(processor),
            run_id or new_id("prun_"),
        )

    def _con(self) -> sqlite3.Connection:
        return local_connection(self.db)

    def test_descriptor_is_page_only_subscription_agent_and_config_hash_is_path_independent(self):
        other_home = self.root / "other-codex-home"
        other_home.mkdir(mode=0o700)
        a = _SimulatedCodex(self.codex_home)
        b = _SimulatedCodex(other_home)
        self.assertEqual(a.configuration_hash, b.configuration_hash)
        self.assertEqual(a.descriptor.key, "codex.visual_transcribe_pdf_page")
        self.assertEqual(a.descriptor.capability_key, "visual_transcribe")
        self.assertEqual(a.descriptor.execution_venue, "subscription_agent")
        self.assertEqual(a.descriptor.scope_kinds, frozenset({"pdf_page"}))
        self.assertTrue(a.descriptor.requires_egress)
        self.assertEqual((a.descriptor.model_provider, a.descriptor.model_name), ("openai", "gpt-5.6-sol"))
        self.assertNotIn(str(self.codex_home), a.configuration_hash)

    def test_material_configuration_changes_hash_and_non_keyring_mode_is_rejected(self):
        base = CodexVisualConfig()
        changed = replace(base, render_dpi=200)
        self.assertNotEqual(base.canonical_hash(), changed.canonical_hash())
        with self.assertRaises(ValueError):
            CodexVisualConfig(auth_store_mode="file")
        with self.assertRaises(ValueError):
            CodexVisualConfig(max_scopes=2)

    def test_isolated_profile_rejects_auth_file_config_and_user_skills(self):
        for relative in ("auth.json", "config.toml"):
            with self.subTest(relative=relative):
                home = self.root / f"profile-{relative.replace('.', '-')}"
                home.mkdir(mode=0o700)
                (home / relative).write_text("x", encoding="utf-8")
                with self.assertRaises(CodexUnavailableError):
                    CodexVisualTranscriptionProcessor(_toolchain(home))
        home = self.root / "profile-skills"
        home.mkdir(mode=0o700)
        (home / "skills" / "personal").mkdir(parents=True)
        with self.assertRaises(CodexUnavailableError):
            CodexVisualTranscriptionProcessor(_toolchain(home))

    @unittest.skipUnless(os.name == "posix", "POSIX permission contract")
    def test_reference_profile_requires_private_directory_permissions(self):
        home = self.root / "profile-public"
        home.mkdir(mode=0o755)
        home.chmod(0o755)
        with self.assertRaises(CodexUnavailableError):
            CodexVisualTranscriptionProcessor(_toolchain(home))

    def test_command_uses_strict_ephemeral_isolation_and_disables_unrelated_tools(self):
        processor = _SimulatedCodex(self.codex_home)
        scratch = self.root / "scratch"
        scratch.mkdir()
        image = scratch / "page_000001.png"
        schema = scratch / "schema.json"
        output = scratch / "out.json"
        command = processor._codex_command(scratch, image, schema, output)
        joined = " ".join(command)
        for required in (
            "--strict-config", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "--sandbox read-only", "--skip-git-repo-check", "--model gpt-5.6-sol",
            "skills.bundled.enabled=false",
            "features.shell_tool=false", "features.unified_exec=false", "features.hooks=false",
            "features.plugins=false",
            "features.apps=false", "features.multi_agent=false", "features.multi_agent_v2.enabled=false",
            'web_search="disabled"', "features.view_image=false",
        ):
            self.assertIn(required, joined)
        self.assertEqual(command[-1], "-")
        self.assertNotIn("--json", command)
        self.assertNotIn("tools.view_image", joined)
        self.assertNotIn("tools.web_search", joined)
        self.assertEqual(command.count("-c"), 21)

    def test_exec_override_policy_is_part_of_configuration_identity(self):
        base = CodexVisualConfig().canonical_hash()
        changed = codex_module._STATIC_CODEX_CONFIG_OVERRIDES + ("features.code_mode=false",)
        with patch.object(codex_module, "_STATIC_CODEX_CONFIG_OVERRIDES", changed):
            self.assertNotEqual(base, CodexVisualConfig().canonical_hash())

    def test_child_environment_excludes_secrets_proxies_and_ambient_codex_configuration(self):
        processor = _SimulatedCodex(self.codex_home)
        scratch = self.root / "scratch-env"
        scratch.mkdir()
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "secret",
            "HTTP_PROXY": "http://secret-proxy",
            "CODEX_FAKE": "ambient",
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/keyring",
            "XDG_RUNTIME_DIR": "/runtime",
        }, clear=False):
            env = processor._codex_env(scratch)
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("HTTP_PROXY", env)
        self.assertNotIn("CODEX_FAKE", env)
        self.assertEqual(env["CODEX_HOME"], str(self.codex_home))
        self.assertEqual(env["DBUS_SESSION_BUS_ADDRESS"], "unix:path=/keyring")
        self.assertEqual(env["XDG_RUNTIME_DIR"], "/runtime")
        self.assertNotEqual(env["HOME"], str(Path.home()))

    def test_success_persists_transcript_table_evidence_model_and_bounded_egress(self):
        processor = _SimulatedCodex(self.codex_home, payload={
            "pages": [{
                "page_id": "page_000001",
                "transcription": "ACTA MUNICIPAL\nA B\n1 2",
                "uncertain_spans": [],
                "tables": [{"rows": [["A", "B"], ["1", "2"]]}],
            }]
        })
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        request = self._request(processor, rep, page)
        receipt = WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(request)
        self.assertEqual(receipt.outcome, "success")
        self.assertEqual(receipt.decisions[0].decision, "accept")
        self.assertEqual(len(receipt.outputs), 2)
        self.assertTrue(processor.source_absent_at_handoff)
        self.assertGreater(processor.last_image_size, 0)

        con = self._con()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT execution_venue,model_provider,model_name,configuration_hash FROM process_runs WHERE id=?",
                    (request.process_run_id,),
                ).fetchone(),
                ("subscription_agent", "openai", "gpt-5.6-sol", processor.configuration_hash),
            )
            egress = con.execute(
                "SELECT bytes_egressed,request_template_hash,endpoint_profile FROM process_run_egress WHERE process_run_id=?",
                (request.process_run_id,),
            ).fetchone()
            self.assertEqual(egress, (processor.last_image_size, processor.request_template_hash, "openai_codex_subscription"))
            evidence = {key: json.loads(value) for key, value in con.execute(
                "SELECT signal_key,payload_json FROM quality_evidence WHERE process_run_id=?",
                (request.process_run_id,),
            )}
            self.assertEqual(evidence["multimodal.schema_valid"], True)
            self.assertEqual(evidence["multimodal.uncertain_span_count"], 0)
            self.assertEqual(
                evidence["multimodal.transcription_character_count"],
                len("ACTA MUNICIPAL\nA B\n1 2"),
            )
            self.assertEqual(evidence["multimodal.table_count"], 1)
            self.assertEqual(evidence["multimodal.table_text_coverage"], 1.0)
            outputs = con.execute(
                "SELECT kind,media_type,language,charset FROM representations WHERE process_run_id=? ORDER BY kind",
                (request.process_run_id,),
            ).fetchall()
            self.assertEqual(outputs, [
                ("table", "application/json", "es", "utf-8"),
                ("transcript", "text/plain", "es", "utf-8"),
            ])
        finally:
            con.close()

    def test_table_text_coverage_preserves_repeated_cell_multiplicity(self):
        value = {
            "pages": [{
                "page_id": "page_000001",
                "transcription": "ALCALDÍA PUSC VICEALCALDÍA",
                "uncertain_spans": [],
                "tables": [{"rows": [["ALCALDÍA", "PUSC"], ["VICEALCALDÍA", "PUSC"]]}],
            }]
        }
        self.assertEqual(
            CodexVisualTranscriptionProcessor._table_text_coverage(value),
            3 / 4,
        )

    def test_prompt_and_schema_require_page_complete_transcription_with_table_duplication(self):
        self.assertIn("including all text inside tables", codex_module._PROMPT)
        self.assertIn("never replace or subtract text from transcription", codex_module._PROMPT)
        schema = CodexVisualConfig().output_schema
        page = schema["properties"]["pages"]["items"]["properties"]
        self.assertIn("Complete visible page transcription", page["transcription"]["description"])
        self.assertIn("never replaces table text", page["tables"]["description"])

    def test_table_text_missing_from_transcription_fails_contract_after_handoff(self):
        processor = _SimulatedCodex(self.codex_home, payload={
            "pages": [{
                "page_id": "page_000001",
                "transcription": "ACTA MUNICIPAL",
                "uncertain_spans": [],
                "tables": [{
                    "rows": [
                        ["ALCALDÍA", "601420299", "BIENVENIDO VENEGAS PORRAS", "PUSC"],
                        ["VICEALCALDÍA PRIMERA", "701450511", "YERLIN DE LOS ANGELES DIAZ VARGAS", "PUSC"],
                    ]
                }],
            }]
        })
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        request = self._request(processor, rep, page)
        receipt = WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(request)
        self.assertEqual(receipt.outcome, "failed")
        self.assertFalse(receipt.outputs)
        self.assertEqual(receipt.decisions[0].decision, "quarantine_review")

        con = self._con()
        try:
            process = con.execute(
                "SELECT error_code FROM process_runs WHERE id=?",
                (request.process_run_id,),
            ).fetchone()
            self.assertEqual(process, ("codex_contract_invalid",))
            evidence = {key: json.loads(value) for key, value in con.execute(
                "SELECT signal_key,payload_json FROM quality_evidence WHERE process_run_id=?",
                (request.process_run_id,),
            )}
            self.assertIs(evidence["multimodal.schema_valid"], True)
            self.assertLess(evidence["multimodal.table_text_coverage"], 1.0)
            self.assertGreater(
                con.execute(
                    "SELECT bytes_egressed FROM process_run_egress WHERE process_run_id=?",
                    (request.process_run_id,),
                ).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_uncertain_span_quarantines_even_with_valid_material_output(self):
        processor = _SimulatedCodex(self.codex_home, payload={
            "pages": [{
                "page_id": "page_000001",
                "transcription": "texto parcial",
                "uncertain_spans": ["firma ilegible"],
                "tables": [],
            }]
        })
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        receipt = WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(
            self._request(processor, rep, page)
        )
        self.assertEqual(receipt.decisions[0].decision, "quarantine_review")

    def test_valid_but_empty_output_is_not_accepted(self):
        processor = _SimulatedCodex(self.codex_home, payload={
            "pages": [{
                "page_id": "page_000001",
                "transcription": "",
                "uncertain_spans": [],
                "tables": [],
            }]
        })
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        receipt = WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(
            self._request(processor, rep, page)
        )
        self.assertEqual(receipt.outcome, "success")
        self.assertFalse(receipt.outputs)
        self.assertEqual(receipt.decisions[0].decision, "quarantine_review")

    def test_schema_invalid_output_fails_with_schema_evidence_and_positive_handoff_bytes(self):
        processor = _SimulatedCodex(self.codex_home, payload={"wrong": []})
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        request = self._request(processor, rep, page)
        receipt = WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(request)
        self.assertEqual(receipt.outcome, "failed")
        self.assertFalse(receipt.outputs)
        con = self._con()
        try:
            self.assertGreater(con.execute(
                "SELECT bytes_egressed FROM process_run_egress WHERE process_run_id=?", (request.process_run_id,)
            ).fetchone()[0], 0)
            self.assertEqual(con.execute(
                "SELECT payload_json FROM quality_evidence WHERE process_run_id=? AND signal_key='multimodal.schema_valid'",
                (request.process_run_id,),
            ).fetchone(), ("false",))
        finally:
            con.close()

    def test_pre_egress_page_range_failure_persists_zero_egress_and_does_not_spawn_codex(self):
        processor = _SimulatedCodex(self.codex_home)
        rep = self._capture(_pdf_bytes(["ONLY ONE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 2})
        request = self._request(processor, rep, page)
        receipt = WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(request)
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(processor.calls, 0)
        con = self._con()
        try:
            self.assertEqual(con.execute(
                "SELECT bytes_egressed FROM process_run_egress WHERE process_run_id=?", (request.process_run_id,)
            ).fetchone(), (0,))
        finally:
            con.close()

    def test_post_handoff_executor_failure_persists_attachment_size(self):
        processor = _SimulatedCodex(self.codex_home, failure="codex_exec_failed")
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        request = self._request(processor, rep, page)
        receipt = WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(request)
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(processor.calls, 1)
        con = self._con()
        try:
            self.assertEqual(con.execute(
                "SELECT bytes_egressed FROM process_run_egress WHERE process_run_id=?", (request.process_run_id,)
            ).fetchone(), (processor.last_image_size,))
        finally:
            con.close()

    def test_executor_unavailable_before_spawn_records_zero_source_egress(self):
        processor = _SimulatedCodex(self.codex_home)
        def fail_before_spawn(*args, **kwargs):
            processor.calls += 1
            raise _CodexRunError("codex_unavailable", handed_off=False)
        processor._run_codex = fail_before_spawn  # type: ignore[method-assign]
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        request = self._request(processor, rep, page)
        receipt = WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(request)
        self.assertEqual(receipt.outcome, "failed")
        con = self._con()
        try:
            self.assertEqual(con.execute(
                "SELECT bytes_egressed FROM process_run_egress WHERE process_run_id=?", (request.process_run_id,)
            ).fetchone(), (0,))
        finally:
            con.close()

    def test_request_requires_exact_endpoint_prompt_and_configuration_identity(self):
        processor = _SimulatedCodex(self.codex_home)
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        bad_hash = ProcessingRequest(rep, (page,), "visual_transcribe", "0" * 64, self._auth(processor))
        with self.assertRaises(CodexConfigurationError):
            WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(bad_hash)
        bad_endpoint = ProcessingRequest(
            rep, (page,), "visual_transcribe", processor.configuration_hash,
            EgressAuthorization(True, "public_civic", "operator_enabled", processor.request_template_hash, "other_endpoint"),
        )
        with self.assertRaises(CodexConfigurationError):
            WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(bad_endpoint)
        bad_prompt = ProcessingRequest(
            rep, (page,), "visual_transcribe", processor.configuration_hash,
            EgressAuthorization(True, "public_civic", "operator_enabled", "e" * 64, processor.config.endpoint_profile),
        )
        with self.assertRaises(CodexConfigurationError):
            WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(bad_prompt)
        self.assertEqual(processor.calls, 0)

    def test_whole_and_multiple_page_requests_are_rejected_before_cloud_invocation(self):
        processor = _SimulatedCodex(self.codex_home)
        rep = self._capture(_pdf_bytes(["ONE", "TWO"]))
        whole = self._target(rep, "whole", {})
        host = WorkbenchHost(self.writer, ProcessorRegistry((processor,)))
        with self.assertRaises(ProcessorResolutionError):
            host.run_attempt(ProcessingRequest(
                rep, (whole,), "visual_transcribe", processor.configuration_hash, self._auth(processor)
            ))
        p1 = self._target(rep, "pdf_page", {"page_ordinal": 1})
        p2 = self._target(rep, "pdf_page", {"page_ordinal": 2})
        with self.assertRaises(ProcessorResolutionError):
            host.run_attempt(ProcessingRequest(
                rep, (p1, p2), "visual_transcribe", processor.configuration_hash, self._auth(processor)
            ))
        self.assertEqual(processor.calls, 0)

    def test_restricted_material_is_rejected_before_codex_invocation(self):
        processor = _SimulatedCodex(self.codex_home)
        rep = self._capture(_pdf_bytes(["RESTRICTED"]), availability="restricted")
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        with self.assertRaises(ProcessorResolutionError):
            WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(
                self._request(processor, rep, page)
            )
        self.assertEqual(processor.calls, 0)

    def test_unauthorized_cloud_is_rejected_before_codex_invocation(self):
        processor = _SimulatedCodex(self.codex_home)
        rep = self._capture(_pdf_bytes(["PUBLIC"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        request = ProcessingRequest(rep, (page,), "visual_transcribe", processor.configuration_hash)
        with self.assertRaises(ProcessorResolutionError):
            WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(request)
        self.assertEqual(processor.calls, 0)

    def test_replay_does_not_invoke_codex_twice_and_survives_adapter_removal(self):
        processor = _SimulatedCodex(self.codex_home)
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        run_id = new_id("prun_")
        request = self._request(processor, rep, page, run_id=run_id)
        host = WorkbenchHost(self.writer, ProcessorRegistry((processor,)))
        first = host.run_attempt(request)
        second = host.run_attempt(request)
        third = WorkbenchHost(self.writer, ProcessorRegistry(())).run_attempt(request)
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertTrue(third.replayed)
        self.assertEqual(processor.calls, 1)

    def test_output_size_and_uncertain_span_contracts_fail_closed(self):
        config = replace(CodexVisualConfig(), max_output_json_bytes=64)
        processor = _SimulatedCodex(self.codex_home, config=config)
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        receipt = WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(
            self._request(processor, rep, page)
        )
        self.assertEqual(receipt.outcome, "failed")
        self.assertEqual(receipt.decisions[0].decision, "quarantine_review")

    def test_model_and_profile_paths_are_not_persisted_as_canonical_metadata(self):
        processor = _SimulatedCodex(self.codex_home)
        rep = self._capture(_pdf_bytes(["SOURCE"]))
        page = self._target(rep, "pdf_page", {"page_ordinal": 1})
        request = self._request(processor, rep, page)
        WorkbenchHost(self.writer, ProcessorRegistry((processor,))).run_attempt(request)
        con = self._con()
        try:
            dump = "\n".join(
                "|".join("" if value is None else str(value) for value in row)
                for table in ("process_runs", "process_run_egress", "quality_evidence")
                for row in con.execute(f"SELECT * FROM {table}")
            )
        finally:
            con.close()
        self.assertNotIn(str(self.codex_home), dump)
        self.assertNotIn("auth.json", dump)
        self.assertNotIn("OPENAI_API_KEY", dump)
        self.assertIn("gpt-5.6-sol", dump)


if __name__ == "__main__":
    unittest.main()
