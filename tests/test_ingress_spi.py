from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

from actakit.deposit import DepositWriter, SourceRegistration, new_id
from actakit.ingress import (
    CaptureEnvelope,
    CapturePayload,
    ConnectorContractError,
    ConnectorDescriptor,
    ConnectorRunResult,
    DepositInbox,
    InboxPolicy,
    ObservedLocator,
    run_connector,
)
from actakit.persistence import database

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-21T12:34:56.789Z"


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


class HtmlInventoryConnector:
    descriptor = ConnectorDescriptor(
        "fixture.html_inventory", "1", frozenset({"pull", "inventory"})
    )

    def run(self, context):
        # The connector may have arbitrary terrain-specific machinery internally.
        # Only the envelope crosses the Inbox boundary.
        html = '<a href="/files/acta-1.pdf">Acta 1</a>'
        self.assert_terrain = "href" in html
        context.inbox.accept(
            CaptureEnvelope(
                observed_at=T,
                outcome="success",
                locator=ObservedLocator(
                    "https://municipio.test/files/acta-1.pdf", "http_url"
                ),
                http_status=200,
                payloads=(
                    CapturePayload(
                        b"%PDF-fixture-html",
                        observed_filename="acta-1.pdf",
                        observed_url="https://municipio.test/files/acta-1.pdf",
                        media_type="application/pdf",
                        language="es",
                    ),
                ),
            )
        )
        return ConnectorRunResult("complete_inventory", 1)


class JsonApiConnector:
    descriptor = ConnectorDescriptor(
        "fixture.json_api",
        "2026.08",
        frozenset({"pull", "incremental", "checkpointing"}),
    )

    def run(self, context):
        if context.checkpoint != b"cursor:41":
            raise AssertionError("opaque checkpoint was interpreted/changed by host")
        item = json.loads('{"id": 42, "download": "/objects/42"}')
        context.inbox.accept(
            CaptureEnvelope(
                observed_at=T,
                outcome="success",
                locator=ObservedLocator(
                    f"https://api.test{item['download']}", "http_url"
                ),
                http_status=200,
                payloads=(
                    CapturePayload(
                        b"api-object-42",
                        observed_filename="42.bin",
                        observed_url=f"https://api.test{item['download']}",
                        media_type="application/octet-stream",
                    ),
                ),
            )
        )
        return ConnectorRunResult("incremental", 1, b"cursor:42")


class ManualDropConnector:
    descriptor = ConnectorDescriptor(
        "fixture.manual_drop", "1", frozenset({"push"})
    )

    def run(self, context):
        context.inbox.accept(
            CaptureEnvelope(
                observed_at=T,
                outcome="success",
                locator=ObservedLocator("drop/meeting-notes.txt", "local_path"),
                payloads=(
                    CapturePayload(
                        b"manual notes",
                        observed_filename="meeting-notes.txt",
                        media_type="text/plain",
                        language="es",
                        charset="utf-8",
                    ),
                ),
            )
        )
        return ConnectorRunResult("unknown", 1)


class IngressSpiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "actakit.sqlite3"
        self.archive = self.root / "archive"
        database._ensure_schema_v1(self.db, NO_RUNTIME_CHECK)
        self.writer = DepositWriter(
            self.db,
            self.archive,
            connection_factory=local_connection,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _inbox(
        self,
        descriptor: ConnectorDescriptor,
        *,
        source_kind: str,
        source_name: str,
        policy: InboxPolicy | None = None,
    ) -> DepositInbox:
        source = SourceRegistration(
            new_id("src_"), source_kind, source_name, True, T
        )
        return DepositInbox(self.writer, source, descriptor, policy=policy)

    def test_three_incompatible_terrains_use_one_socket_shape(self):
        html = HtmlInventoryConnector()
        api = JsonApiConnector()
        manual = ManualDropConnector()

        html_result = run_connector(
            html,
            self._inbox(html.descriptor, source_kind="web", source_name="Web fixture"),
        )
        api_result = run_connector(
            api,
            self._inbox(api.descriptor, source_kind="api", source_name="API fixture"),
            checkpoint=b"cursor:41",
        )
        manual_result = run_connector(
            manual,
            self._inbox(
                manual.descriptor, source_kind="manual", source_name="Manual fixture"
            ),
        )

        self.assertEqual(html_result.coverage, "complete_inventory")
        self.assertEqual(api_result.next_checkpoint, b"cursor:42")
        self.assertEqual(manual_result.coverage, "unknown")

        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM acquisitions").fetchone()[0], 3)
            self.assertEqual(con.execute("SELECT count(*) FROM artifacts").fetchone()[0], 3)
            self.assertEqual(con.execute("SELECT count(*) FROM representations").fetchone()[0], 3)
            self.assertEqual(
                set(con.execute("SELECT adapter_key FROM acquisitions")),
                {
                    ("fixture.html_inventory",),
                    ("fixture.json_api",),
                    ("fixture.manual_drop",),
                },
            )
            self.assertEqual(
                set(con.execute("SELECT locator_kind FROM source_locators")),
                {("http_url",), ("local_path",)},
            )
            # The connector cannot self-promote incoming bytes to verified.
            self.assertEqual(
                set(con.execute("SELECT validation_state FROM artifacts")),
                {("pending",)},
            )
        finally:
            con.close()

    def test_exact_envelope_retry_is_deposito_idempotent(self):
        descriptor = ConnectorDescriptor("fixture.retry", "1", frozenset({"pull"}))
        inbox = self._inbox(descriptor, source_kind="web", source_name="Retry source")
        envelope = CaptureEnvelope(
            observed_at=T,
            outcome="success",
            locator=ObservedLocator("https://retry.test/file", "http_url"),
            http_status=200,
            payloads=(
                CapturePayload(
                    b"same delivery",
                    observed_filename="file.bin",
                    observed_url="https://retry.test/file",
                ),
            ),
        )

        first = inbox.accept(envelope)
        second = inbox.accept(envelope)
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.acquisition_ref, second.acquisition_ref)

        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM acquisitions").fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT count(*) FROM source_locators").fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT count(*) FROM artifacts").fetchone()[0], 1)
        finally:
            con.close()

    def test_inbox_rejects_inactive_source_binding(self):
        descriptor = ConnectorDescriptor("fixture.inactive", "1", frozenset({"pull"}))
        inactive = SourceRegistration(
            new_id("src_"), "web", "Disabled source", False, T
        )
        with self.assertRaisesRegex(ValueError, "inactive Source"):
            DepositInbox(self.writer, inactive, descriptor)

    def test_inbox_owns_adapter_attribution_and_custody_policy(self):
        descriptor = ConnectorDescriptor("fixture.policy", "v3", frozenset({"push"}))
        inbox = self._inbox(
            descriptor,
            source_kind="manual",
            source_name="Restricted drop",
            policy=InboxPolicy("restricted", "quarantined"),
        )
        receipt = inbox.accept(
            CaptureEnvelope(
                observed_at=T,
                outcome="failed",
                locator=ObservedLocator("drop/error.html", "local_path"),
                error_code="operator_rejected_transport",
                payloads=(
                    CapturePayload(
                        b"captured failure body",
                        role="response_body",
                        media_type="text/html",
                    ),
                ),
            )
        )
        self.assertEqual(receipt.artifact_count, 1)

        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT adapter_key,adapter_version,outcome FROM acquisitions"
                ).fetchone(),
                ("fixture.policy", "v3", "failed"),
            )
            self.assertEqual(
                con.execute(
                    "SELECT validation_state,availability FROM artifacts"
                ).fetchone(),
                ("quarantined", "restricted"),
            )
        finally:
            con.close()

    def test_connector_failures_propagate_after_preserving_accepted_custody(self):
        descriptor = ConnectorDescriptor("fixture.fail_loud", "1", frozenset({"pull"}))
        inbox = self._inbox(descriptor, source_kind="web", source_name="Fail-loud")

        class FailLoudConnector:
            @property
            def descriptor(self):
                return descriptor

            def run(self, context):
                context.inbox.accept(
                    CaptureEnvelope(
                        observed_at=T,
                        outcome="success",
                        payloads=(CapturePayload(b"preserved before failure"),),
                    )
                )
                raise RuntimeError("unexpected source structure")

        with self.assertRaisesRegex(RuntimeError, "unexpected source structure"):
            run_connector(FailLoudConnector(), inbox)

        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM acquisitions").fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT count(*) FROM artifacts").fetchone()[0], 1)
        finally:
            con.close()

    def test_spi_rejects_coverage_checkpoint_and_binding_lies(self):
        inventoryless = ConnectorDescriptor("fixture.no_inventory", "1", frozenset({"pull"}))
        inbox = self._inbox(
            inventoryless, source_kind="web", source_name="No inventory"
        )

        class BadCoverage:
            descriptor = inventoryless

            def run(self, context):
                return ConnectorRunResult("complete_inventory", 0)

        with self.assertRaisesRegex(ConnectorContractError, "inventory capability"):
            run_connector(BadCoverage(), inbox)

        checkpointless = ConnectorDescriptor("fixture.no_checkpoint", "1", frozenset({"pull"}))
        checkpoint_inbox = self._inbox(
            checkpointless, source_kind="web", source_name="No checkpoint"
        )

        class BadCheckpoint:
            descriptor = checkpointless

            def run(self, context):
                return ConnectorRunResult("unknown", 0, b"opaque")

        with self.assertRaisesRegex(ConnectorContractError, "checkpointing capability"):
            run_connector(BadCheckpoint(), checkpoint_inbox)

        other = ConnectorDescriptor("fixture.other", "1", frozenset({"pull"}))

        class WrongBinding:
            descriptor = other

            def run(self, context):
                raise AssertionError("must not run")

        with self.assertRaisesRegex(ConnectorContractError, "does not match"):
            run_connector(WrongBinding(), inbox)

        with self.assertRaisesRegex(ConnectorContractError, "without checkpointing"):
            run_connector(BadCoverage(), inbox, checkpoint=b"not-allowed")

        counting = ConnectorDescriptor("fixture.bad_count", "1", frozenset({"pull"}))
        counting_inbox = self._inbox(
            counting, source_kind="web", source_name="Bad count"
        )

        class BadCount:
            descriptor = counting

            def run(self, context):
                context.inbox.accept(
                    CaptureEnvelope(observed_at=T, outcome="not_found")
                )
                return ConnectorRunResult("unknown", 0)

        with self.assertRaisesRegex(ConnectorContractError, "reported=0, accepted=1"):
            run_connector(BadCount(), counting_inbox)

    def test_connectors_cannot_inject_canonical_persistence_ids(self):
        with self.assertRaises(TypeError):
            CaptureEnvelope(
                observed_at=T,
                outcome="not_found",
                _acquisition_id=new_id("acq_"),
            )
        with self.assertRaises(TypeError):
            CapturePayload(
                b"bytes",
                _artifact_id=new_id("art_"),
            )

    def test_inbox_dto_has_no_esparza_or_transport_topology_fields(self):
        names = {item.name for item in fields(CaptureEnvelope)} | {
            item.name for item in fields(CapturePayload)
        }
        forbidden_fragments = {
            "esparza",
            "municipio",
            "acta",
            "html",
            "api",
            "selector",
            "playwright",
            "pagination",
            "article",
            "session",
        }
        for fragment in forbidden_fragments:
            self.assertFalse(
                any(fragment in name.lower() for name in names),
                (fragment, sorted(names)),
            )


if __name__ == "__main__":
    unittest.main()
