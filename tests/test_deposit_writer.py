from __future__ import annotations

import sqlite3
import tempfile
import unittest
import uuid
from dataclasses import replace
from pathlib import Path
from unittest import mock

from actakit.deposit import (
    AcquisitionObservation,
    AcquisitionWrite,
    ArchiveIntegrityError,
    CapturedArtifact,
    DepositInvariantError,
    DepositWriter,
    IdentityCollisionError,
    SourceLocatorRegistration,
    SourceRegistration,
    new_id,
)
from actakit.persistence import database

NO_RUNTIME_CHECK = lambda: None
T = "2026-08-21T12:34:56.789Z"


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


class DepositWriterTests(unittest.TestCase):
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
        self.source = SourceRegistration(new_id("src_"), "web", "Municipalidad", True, T)
        self.writer.register_source(self.source)
        self.locator = SourceLocatorRegistration(
            new_id("sloc_"), self.source.id, "https://example.test/actas/1", "http_url", T
        )
        self.locator_id = self.writer.register_source_locator(self.locator)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _operation(
        self,
        data: bytes = b"acta uno",
        *,
        acquisition_id: str | None = None,
        artifact: CapturedArtifact | None = None,
        outcome: str = "success",
    ) -> AcquisitionWrite:
        observation = AcquisitionObservation(
            acquisition_id or new_id("acq_"),
            self.source.id,
            self.locator_id,
            T,
            outcome,
            200 if outcome == "success" else 500,
            "test_adapter",
            "1",
            None if outcome == "success" else "fetch_failed",
            T,
        )
        payload = artifact or CapturedArtifact(
            new_id("art_"),
            new_id("aob_"),
            new_id("rep_"),
            data,
            "primary",
            "acta.pdf",
            "https://example.test/actas/1",
            "application/pdf",
            "pending",
            "available",
            "es",
            None,
            T,
        )
        return AcquisitionWrite(observation, (payload,))

    def test_generated_ids_are_prefixed_uuidv7(self):
        value = new_id("clm_")
        parsed = uuid.UUID(value[len("clm_") :])
        self.assertEqual(parsed.version, 7)
        self.assertEqual(parsed.variant, uuid.RFC_4122)

    def test_source_exact_retry_and_collision_fail_closed(self):
        self.assertEqual(self.writer.register_source(self.source), self.source.id)
        with self.assertRaises(IdentityCollisionError):
            self.writer.register_source(replace(self.source, name="Otra fuente"))

    def test_locator_same_address_reuses_existing_identity(self):
        second = SourceLocatorRegistration(
            new_id("sloc_"), self.source.id, self.locator.locator, "http_url", T
        )
        self.assertEqual(self.writer.register_source_locator(second), self.locator.id)
        with self.assertRaises(DepositInvariantError):
            self.writer.register_source_locator(replace(second, locator_kind="filesystem_path"))

    def test_successful_capture_materializes_full_custody_graph(self):
        operation = self._operation()
        receipt = self.writer.record_acquisition(operation)
        self.assertFalse(receipt.replayed)
        self.assertEqual(len(receipt.artifacts), 1)
        stored = receipt.artifacts[0]
        path = self.archive / stored.storage_key
        self.assertEqual(path.read_bytes(), b"acta uno")

        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM acquisitions WHERE id=?", (receipt.acquisition_id,)).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute("SELECT count(*) FROM acquisition_artifacts WHERE acquisition_id=?", (receipt.acquisition_id,)).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM representations WHERE artifact_id=? AND kind='original'",
                    (stored.artifact_id,),
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT validation_state FROM artifacts WHERE id=?",
                    (stored.artifact_id,),
                ).fetchone()[0],
                "pending",
            )
        finally:
            con.close()

    def test_failed_observation_without_bytes_is_durable_and_non_destructive(self):
        first = self.writer.record_acquisition(self._operation())
        failed = AcquisitionWrite(
            AcquisitionObservation(
                new_id("acq_"), self.source.id, self.locator_id, T, "failed", 503,
                "test_adapter", "1", "upstream_unavailable", T
            ),
            (),
        )
        receipt = self.writer.record_acquisition(failed)
        self.assertEqual(receipt.artifacts, ())
        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT outcome FROM acquisitions WHERE id=?", (receipt.acquisition_id,)).fetchone()[0], "failed")
            self.assertEqual(con.execute("SELECT count(*) FROM artifacts WHERE id=?", (first.artifacts[0].artifact_id,)).fetchone()[0], 1)
        finally:
            con.close()

    def test_identical_bytes_keep_distinct_artifacts_and_share_archive_object(self):
        first_operation = self._operation(b"same bytes")
        second_operation = self._operation(b"same bytes")
        first = self.writer.record_acquisition(first_operation)
        second = self.writer.record_acquisition(second_operation)
        second_retry = self.writer.record_acquisition(second_operation)
        self.assertNotEqual(first.acquisition_id, second.acquisition_id)
        self.assertNotEqual(first.artifacts[0].artifact_id, second.artifacts[0].artifact_id)
        self.assertEqual(first.artifacts[0].archive_object_id, second.artifacts[0].archive_object_id)
        self.assertEqual(first.artifacts[0].storage_key, second.artifacts[0].storage_key)
        self.assertTrue(second_retry.replayed)
        self.assertEqual(second_retry.artifacts, second.artifacts)

        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM archive_objects").fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT count(*) FROM artifacts").fetchone()[0], 2)
        finally:
            con.close()

    def test_same_locator_changed_bytes_get_new_archive_identity(self):
        first = self.writer.record_acquisition(self._operation(b"version A"))
        second = self.writer.record_acquisition(self._operation(b"version B"))
        self.assertNotEqual(first.artifacts[0].archive_object_id, second.artifacts[0].archive_object_id)
        self.assertNotEqual(first.artifacts[0].content_sha256, second.artifacts[0].content_sha256)

    def test_exact_operation_retry_is_idempotent_but_changed_payload_collides(self):
        operation = self._operation(b"retry payload")
        first = self.writer.record_acquisition(operation)
        second = self.writer.record_acquisition(operation)
        self.assertTrue(second.replayed)
        self.assertEqual(first.artifacts, second.artifacts)

        changed_payload = replace(operation.artifacts[0], data=b"changed on retry")
        changed = AcquisitionWrite(operation.observation, (changed_payload,))
        with self.assertRaises(IdentityCollisionError):
            self.writer.record_acquisition(changed)

        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM acquisitions WHERE id=?", (operation.observation.id,)).fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT count(*) FROM acquisition_artifacts WHERE acquisition_id=?", (operation.observation.id,)).fetchone()[0], 1)
        finally:
            con.close()

    def test_corrupt_existing_archive_object_fails_closed(self):
        first = self.writer.record_acquisition(self._operation(b"immutable evidence"))
        path = self.archive / first.artifacts[0].storage_key
        path.write_bytes(b"tampered")
        with self.assertRaises(ArchiveIntegrityError):
            self.writer.record_acquisition(self._operation(b"immutable evidence"))

    def test_transaction_failure_rolls_back_rows_and_cleans_new_file(self):
        operation = self._operation(b"must rollback")
        digest = self.writer.archive.digest(operation.artifacts[0].data)
        key = self.writer.archive.key_for_digest(digest)
        path = self.archive / key

        with mock.patch.object(
            self.writer,
            "_validate_custody",
            side_effect=RuntimeError("injected before commit"),
        ):
            with self.assertRaisesRegex(RuntimeError, "injected before commit"):
                self.writer.record_acquisition(operation)

        self.assertFalse(path.exists())
        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM acquisitions WHERE id=?", (operation.observation.id,)).fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT count(*) FROM artifacts WHERE id=?", (operation.artifacts[0].artifact_id,)).fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT count(*) FROM archive_objects WHERE content_sha256=?", (digest,)).fetchone()[0], 0)
        finally:
            con.close()

    def test_transaction_failure_never_deletes_preexisting_shared_bytes(self):
        first = self.writer.record_acquisition(self._operation(b"shared survives"))
        shared_path = self.archive / first.artifacts[0].storage_key
        operation = self._operation(b"shared survives")
        with mock.patch.object(
            self.writer,
            "_validate_custody",
            side_effect=RuntimeError("injected before commit"),
        ):
            with self.assertRaises(RuntimeError):
                self.writer.record_acquisition(operation)
        self.assertTrue(shared_path.exists())
        self.assertEqual(shared_path.read_bytes(), b"shared survives")

    def test_one_acquisition_can_commit_multiple_payloads_with_intra_operation_dedup(self):
        first_payload = CapturedArtifact(
            new_id("art_"), new_id("aob_"), new_id("rep_"), b"same attachment",
            "primary", "a.pdf", self.locator.locator, "application/pdf",
            "pending", "available", "es", None, T
        )
        second_payload = CapturedArtifact(
            new_id("art_"), new_id("aob_"), new_id("rep_"), b"same attachment",
            "attachment", "copy.pdf", self.locator.locator, "application/pdf",
            "pending", "restricted", "es", None, T
        )
        observation = AcquisitionObservation(
            new_id("acq_"), self.source.id, self.locator_id, T, "success", 200,
            "test_adapter", "1", None, T
        )
        receipt = self.writer.record_acquisition(
            AcquisitionWrite(observation, (first_payload, second_payload))
        )
        self.assertEqual(len(receipt.artifacts), 2)
        self.assertEqual(
            receipt.artifacts[0].archive_object_id,
            receipt.artifacts[1].archive_object_id,
        )
        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute("SELECT count(*) FROM acquisition_artifacts WHERE acquisition_id=?", (observation.id,)).fetchone()[0],
                2,
            )
            self.assertEqual(con.execute("SELECT count(*) FROM archive_objects").fetchone()[0], 1)
            states = dict(con.execute("SELECT id,availability FROM artifacts"))
            self.assertEqual(states[first_payload.artifact_id], "available")
            self.assertEqual(states[second_payload.artifact_id], "restricted")
        finally:
            con.close()

    def test_locator_from_another_source_is_rejected_before_archive_write(self):
        other_source = SourceRegistration(new_id("src_"), "web", "Otra fuente", True, T)
        self.writer.register_source(other_source)
        other_locator = SourceLocatorRegistration(
            new_id("sloc_"), other_source.id, "https://other.test/item", "http_url", T
        )
        other_locator_id = self.writer.register_source_locator(other_locator)
        operation = self._operation(b"must never be archived")
        bad_observation = replace(
            operation.observation, source_locator_id=other_locator_id
        )
        with self.assertRaises(DepositInvariantError):
            self.writer.record_acquisition(
                AcquisitionWrite(bad_observation, operation.artifacts)
            )
        self.assertEqual(list(self.archive.rglob("*.bin")), [])

    def test_crash_orphan_bytes_are_verified_and_adopted_by_later_capture(self):
        data = b"orphan before database commit"
        orphan = self.writer.archive.materialize(data)
        self.assertTrue(orphan.created)

        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM archive_objects WHERE content_sha256=?",
                    (orphan.content_sha256,),
                ).fetchone()[0],
                0,
            )
        finally:
            con.close()

        receipt = self.writer.record_acquisition(self._operation(data))
        stored = receipt.artifacts[0]
        self.assertEqual(stored.content_sha256, orphan.content_sha256)
        self.assertEqual(stored.storage_key, orphan.storage_key)
        self.assertEqual((self.archive / orphan.storage_key).read_bytes(), data)

    def test_failed_observation_may_preserve_response_body_bytes(self):
        observation = AcquisitionObservation(
            new_id("acq_"), self.source.id, self.locator_id, T, "failed", 503,
            "test_adapter", "1", "upstream_unavailable", T
        )
        payload = CapturedArtifact(
            new_id("art_"), new_id("aob_"), new_id("rep_"), b"service unavailable",
            "response_body", None, self.locator.locator, "text/plain",
            "pending", "available", "en", "utf-8", T
        )
        receipt = self.writer.record_acquisition(
            AcquisitionWrite(observation, (payload,))
        )
        self.assertEqual(len(receipt.artifacts), 1)
        self.assertEqual(
            (self.archive / receipt.artifacts[0].storage_key).read_bytes(),
            b"service unavailable",
        )

    def test_content_address_target_symlink_is_rejected(self):
        data = b"symlink target safety"
        digest = self.writer.archive.digest(data)
        key = self.writer.archive.key_for_digest(digest)
        final_path = self.archive / key
        final_path.parent.mkdir(parents=True, exist_ok=True)
        outside = self.root / "outside.bin"
        outside.write_bytes(data)
        final_path.symlink_to(outside)

        with self.assertRaises(ArchiveIntegrityError):
            self.writer.record_acquisition(self._operation(data))
        self.assertEqual(outside.read_bytes(), data)
        self.assertTrue(final_path.is_symlink())


if __name__ == "__main__":
    unittest.main()
