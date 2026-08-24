from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from canario.connectors.esparza import (
    DEFAULT_SECTIONS,
    EsparzaCmsConfig,
    EsparzaCmsConnector,
    EsparzaConnectorError,
    EsparzaFetchError,
    EsparzaHttpResponse,
    EsparzaRedirectPolicyError,
    EsparzaSection,
    EsparzaSourceStructureError,
    RequestsEsparzaHttpClient,
)
from canario.deposit import DepositWriter, SourceRegistration, new_id
from canario.ingress import DepositInbox, run_connector
from canario.persistence import database


T = "2026-08-21T12:34:56.789Z"
NO_RUNTIME_CHECK = lambda: None


def local_connection(path: Path) -> sqlite3.Connection:
    return database._open_writable_v1(path, NO_RUNTIME_CHECK)


class FakeHttp:
    def __init__(self, responses):
        self.responses = {key: list(value) for key, value in responses.items()}
        self.calls: list[str] = []

    def get(self, url: str) -> EsparzaHttpResponse:
        self.calls.append(url)
        queue = self.responses.get(url)
        if not queue:
            raise AssertionError(f"unexpected HTTP fetch: {url}")
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def response(
    url: str,
    body: bytes,
    *,
    status: int = 200,
    final_url: str | None = None,
    content_type: str = "text/html; charset=utf-8",
) -> EsparzaHttpResponse:
    return EsparzaHttpResponse(
        url,
        final_url or url,
        status,
        {"Content-Type": content_type},
        body,
    )


def listing(*rows: tuple[str, str, str]) -> bytes:
    """Build minimal Esparza fileTree rows as (year, filename, title)."""

    chunks = ["<html><body><ul class='fileTree'>"]
    current = None
    for year, filename, title in rows:
        if year != current:
            chunks.append(f"<li><a href='#'>{year}</a></li>")
            current = year
        chunks.append(
            "<li class='file ext_pdf'><a onclick=\"openDocumentArticle('"
            + filename
            + "')\">"
            + title
            + "</a></li>"
        )
    chunks.append("</ul></body></html>")
    return "".join(chunks).encode()


class EsparzaConnectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.db = root / "canario.sqlite3"
        self.archive = root / "archive"
        database._ensure_schema_v1(self.db, NO_RUNTIME_CHECK)
        self.writer = DepositWriter(
            self.db,
            self.archive,
            connection_factory=local_connection,
        )
        self.source = SourceRegistration(
            new_id("src_"), "web", "Municipalidad de Esparza CMS fixture", True, T
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _connector(self, http, **config_kwargs):
        config = EsparzaCmsConfig(
            base_url="https://muniesparza.test",
            sections=(EsparzaSection("concejo", "/listing"),),
            rate_limit_seconds=0,
            **config_kwargs,
        )
        connector = EsparzaCmsConnector(config, http=http, sleeper=lambda _: None)
        inbox = DepositInbox(self.writer, self.source, connector.descriptor)
        return connector, inbox

    def test_listing_and_document_enter_same_inbox_without_source_metadata_fields(self):
        listing_url = "https://muniesparza.test/listing"
        doc_url = "https://muniesparza.test/files/folder/abc.pdf"
        http = FakeHttp(
            {
                listing_url: [response(listing_url, listing(("2026", "abc.pdf", "Acta 1")))],
                doc_url: [
                    response(
                        doc_url,
                        b"%PDF-real-document",
                        content_type="application/pdf",
                    )
                ],
            }
        )
        connector, inbox = self._connector(http)

        result = run_connector(connector, inbox)
        self.assertEqual(result.coverage, "unknown")
        self.assertEqual(result.emitted, 2)

        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM acquisitions").fetchone()[0], 2)
            self.assertEqual(con.execute("SELECT count(*) FROM artifacts").fetchone()[0], 2)
            self.assertEqual(con.execute("SELECT count(*) FROM archive_objects").fetchone()[0], 2)
            self.assertEqual(
                con.execute(
                    """
                    SELECT aa.role,aa.observed_filename,aa.observed_url,a.media_type
                    FROM acquisition_artifacts aa
                    JOIN artifacts a ON a.id=aa.artifact_id
                    WHERE aa.observed_filename='abc.pdf'
                    """
                ).fetchone(),
                ("primary", "abc.pdf", doc_url, "application/pdf"),
            )
            # year/title/section remain in the preserved listing HTML, not columns.
            listing_role = con.execute(
                "SELECT role FROM acquisition_artifacts WHERE observed_filename IS NULL"
            ).fetchone()[0]
            self.assertEqual(listing_role, "response_body")
        finally:
            con.close()

    def test_structure_change_preserves_listing_then_fails_loud(self):
        listing_url = "https://muniesparza.test/listing"
        html = b"<html><body>CMS redesigned</body></html>"
        http = FakeHttp({listing_url: [response(listing_url, html)]})
        connector, inbox = self._connector(http)

        with self.assertRaisesRegex(EsparzaSourceStructureError, "ul.fileTree"):
            run_connector(connector, inbox)

        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM acquisitions").fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT count(*) FROM artifacts").fetchone()[0], 1)
            self.assertEqual(
                con.execute("SELECT adapter_key FROM acquisitions").fetchone()[0],
                "cr.muniesparza.cms",
            )
        finally:
            con.close()

    def test_same_locator_with_changed_bytes_keeps_distinct_artifacts_and_shared_listing_bytes(self):
        listing_url = "https://muniesparza.test/listing"
        doc_url = "https://muniesparza.test/files/folder/abc.pdf"
        page = listing(("2026", "abc.pdf", "Acta 1"))
        http = FakeHttp(
            {
                listing_url: [response(listing_url, page), response(listing_url, page)],
                doc_url: [
                    response(doc_url, b"%PDF-version-one", content_type="application/pdf"),
                    response(doc_url, b"%PDF-version-two", content_type="application/pdf"),
                ],
            }
        )
        connector, inbox = self._connector(http)

        run_connector(connector, inbox)
        run_connector(connector, inbox)

        con = local_connection(self.db)
        try:
            self.assertEqual(con.execute("SELECT count(*) FROM acquisitions").fetchone()[0], 4)
            self.assertEqual(con.execute("SELECT count(*) FROM artifacts").fetchone()[0], 4)
            # listing bytes deduplicate physically; the two document versions do not.
            self.assertEqual(con.execute("SELECT count(*) FROM archive_objects").fetchone()[0], 3)
            self.assertEqual(con.execute("SELECT count(*) FROM source_locators").fetchone()[0], 2)
        finally:
            con.close()

    def test_duplicate_source_entry_preserves_distinct_provenance_but_deduplicates_bytes(self):
        config = EsparzaCmsConfig(
            base_url="https://muniesparza.test",
            sections=(
                EsparzaSection("concejo", "/concejo"),
                EsparzaSection("comisiones", "/comisiones"),
            ),
            rate_limit_seconds=0,
        )
        shared_name = "shared.pdf"
        doc_url = "https://muniesparza.test/files/folder/shared.pdf"
        http = FakeHttp(
            {
                "https://muniesparza.test/concejo": [
                    response(
                        "https://muniesparza.test/concejo",
                        listing(("2026", shared_name, "Acta compartida")),
                    )
                ],
                "https://muniesparza.test/comisiones": [
                    response(
                        "https://muniesparza.test/comisiones",
                        listing(("2026", shared_name, "Mismo recurso listado otra vez")),
                    )
                ],
                doc_url: [
                    response(doc_url, b"%PDF-shared", content_type="application/pdf"),
                    response(doc_url, b"%PDF-shared", content_type="application/pdf"),
                ],
            }
        )
        connector = EsparzaCmsConnector(config, http=http, sleeper=lambda _: None)
        inbox = DepositInbox(self.writer, self.source, connector.descriptor)

        result = run_connector(connector, inbox)
        self.assertEqual(result.coverage, "unknown")

        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM acquisition_artifacts WHERE observed_filename=?",
                    (shared_name,),
                ).fetchone()[0],
                2,
            )
            # Two listings + one shared document body.
            self.assertEqual(con.execute("SELECT count(*) FROM archive_objects").fetchone()[0], 3)
        finally:
            con.close()

    def test_not_found_and_html_instead_of_document_are_recorded_honestly(self):
        listing_url = "https://muniesparza.test/listing"
        a_url = "https://muniesparza.test/files/folder/missing.pdf"
        b_url = "https://muniesparza.test/files/folder/login.pdf"
        http = FakeHttp(
            {
                listing_url: [
                    response(
                        listing_url,
                        listing(
                            ("2026", "missing.pdf", "Missing"),
                            ("2026", "login.pdf", "Login wall"),
                        ),
                    )
                ],
                a_url: [response(a_url, b"not found", status=404)],
                b_url: [response(b_url, b"<html>please login</html>", content_type="text/html")],
            }
        )
        connector, inbox = self._connector(http)

        result = run_connector(connector, inbox)
        self.assertEqual(result.emitted, 3)

        con = local_connection(self.db)
        try:
            outcomes = set(
                con.execute(
                    "SELECT outcome,error_code,http_status FROM acquisitions WHERE http_status IS NOT NULL"
                )
            )
            self.assertIn(("not_found", "http_404", 404), outcomes)
            self.assertIn(("failed", "unexpected_html_payload", 200), outcomes)
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM acquisition_artifacts WHERE role='response_body'"
                ).fetchone()[0],
                3,  # listing + 404 body + login body
            )
        finally:
            con.close()

    def test_year_filter_is_not_allowed_to_claim_complete_inventory(self):
        listing_url = "https://muniesparza.test/listing"
        keep_url = "https://muniesparza.test/files/folder/keep.pdf"
        http = FakeHttp(
            {
                listing_url: [
                    response(
                        listing_url,
                        listing(
                            ("2026", "keep.pdf", "Keep"),
                            ("2025", "skip.pdf", "Skip"),
                        ),
                    )
                ],
                keep_url: [response(keep_url, b"%PDF-keep", content_type="application/pdf")],
            }
        )
        connector, inbox = self._connector(http, years=frozenset({"2026"}))

        result = run_connector(connector, inbox)
        self.assertEqual(result.coverage, "unknown")
        self.assertEqual(result.emitted, 2)
        self.assertNotIn("https://muniesparza.test/files/folder/skip.pdf", http.calls)

    def test_default_unfiltered_scope_may_claim_complete_inventory(self):
        responses = {}
        for index, section in enumerate(DEFAULT_SECTIONS, start=1):
            listing_url = "https://muniesparza.test" + section.path
            filename = f"doc-{index}.pdf"
            doc_url = "https://muniesparza.test/files/folder/" + filename
            responses[listing_url] = [
                response(listing_url, listing(("2026", filename, f"Doc {index}")))
            ]
            responses[doc_url] = [
                response(doc_url, f"%PDF-{index}".encode(), content_type="application/pdf")
            ]
        config = EsparzaCmsConfig(
            base_url="https://muniesparza.test",
            rate_limit_seconds=0,
        )
        connector = EsparzaCmsConnector(config, http=FakeHttp(responses), sleeper=lambda _: None)
        inbox = DepositInbox(self.writer, self.source, connector.descriptor)

        result = run_connector(connector, inbox)
        self.assertEqual(result.coverage, "complete_inventory")
        self.assertEqual(result.emitted, 6)

    def test_unknown_zip_container_is_not_assumed_to_be_docx(self):
        listing_url = "https://muniesparza.test/listing"
        doc_url = "https://muniesparza.test/files/folder/mystery.bin"
        http = FakeHttp(
            {
                listing_url: [response(listing_url, listing(("2026", "mystery.bin", "Mystery")))],
                doc_url: [
                    EsparzaHttpResponse(
                        doc_url, doc_url, 200, {}, b"PK\x03\x04opaque-zip-container"
                    )
                ],
            }
        )
        connector, inbox = self._connector(http)
        run_connector(connector, inbox)

        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    """
                    SELECT a.media_type
                    FROM artifacts a
                    JOIN acquisition_artifacts aa ON aa.artifact_id=a.id
                    WHERE aa.observed_filename='mystery.bin'
                    """
                ).fetchone()[0],
                "application/zip",
            )
        finally:
            con.close()

    def test_document_transport_failure_becomes_failed_acquisition_and_run_continues(self):
        listing_url = "https://muniesparza.test/listing"
        doc_url = "https://muniesparza.test/files/folder/huge.pdf"
        http = FakeHttp(
            {
                listing_url: [response(listing_url, listing(("2026", "huge.pdf", "Huge")))],
                doc_url: [EsparzaFetchError("payload_too_large", doc_url, "too large")],
            }
        )
        connector, inbox = self._connector(http)

        result = run_connector(connector, inbox)
        self.assertEqual(result.emitted, 2)
        con = local_connection(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT outcome,error_code FROM acquisitions WHERE error_code='payload_too_large'"
                ).fetchone(),
                ("failed", "payload_too_large"),
            )
        finally:
            con.close()


class _RedirectResponse:
    def __init__(self, status_code: int, headers: dict[str, str], body: bytes = b""):
        self.status_code = status_code
        self.headers = headers
        self._body = body
        self.closed = False

    def iter_content(self, chunk_size: int):
        del chunk_size
        if self._body:
            yield self._body

    def close(self):
        self.closed = True


class _RedirectSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[str] = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        self.kwargs = kwargs
        return self.responses.pop(0)


class EsparzaArchitectureBoundaryTests(unittest.TestCase):
    def test_source_connector_module_stops_at_ingress_boundary(self):
        source = Path("canario/connectors/esparza.py").read_text(encoding="utf-8")
        forbidden = (
            "canario.deposit",
            "canario.persistence",
            "sqlite3",
            "DepositWriter",
            "CivicDocument",
            "ClaimRevision",
            "EntityReconciliation",
        )
        for token in forbidden:
            self.assertNotIn(token, source)


class EsparzaTransportPolicyTests(unittest.TestCase):
    def test_cross_host_redirect_is_rejected_before_following(self):
        session = _RedirectSession(
            [_RedirectResponse(302, {"Location": "https://evil.test/file.pdf"})]
        )
        config = EsparzaCmsConfig(
            base_url="https://muniesparza.test",
            rate_limit_seconds=0,
        )
        client = RequestsEsparzaHttpClient(config, session=session)

        with self.assertRaisesRegex(EsparzaRedirectPolicyError, "outside Esparza"):
            client.get("https://muniesparza.test/file.pdf")
        self.assertEqual(session.calls, ["https://muniesparza.test/file.pdf"])

    def test_same_source_redirect_is_followed_and_final_url_is_retained(self):
        session = _RedirectSession(
            [
                _RedirectResponse(302, {"Location": "/new/file.pdf"}),
                _RedirectResponse(200, {"Content-Type": "application/pdf"}, b"%PDF-ok"),
            ]
        )
        config = EsparzaCmsConfig(
            base_url="https://muniesparza.test",
            rate_limit_seconds=0,
        )
        client = RequestsEsparzaHttpClient(config, session=session)

        result = client.get("https://muniesparza.test/old/file.pdf")
        self.assertEqual(result.attempted_url, "https://muniesparza.test/old/file.pdf")
        self.assertEqual(result.final_url, "https://muniesparza.test/new/file.pdf")
        self.assertEqual(result.body, b"%PDF-ok")
        self.assertFalse(session.kwargs["allow_redirects"])


if __name__ == "__main__":
    unittest.main()
