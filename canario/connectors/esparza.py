"""Municipalidad de Esparza CMS Source Connector.

This module is intentionally source-specific.  It may know about Esparza's CMS,
``fileTree`` markup and ``openDocumentArticle`` JavaScript hooks, but it stops at
INGRESS-001 and never imports Depósito or SQLite writers.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol
from urllib.parse import quote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from canario.ingress import (
    CaptureEnvelope,
    CapturePayload,
    ConnectorDescriptor,
    ConnectorRunResult,
    ObservedLocator,
)
from canario.ingress.spi import ConnectorContext


ESPARZA_CONNECTOR_DESCRIPTOR = ConnectorDescriptor(
    "cr.muniesparza.cms",
    "1",
    frozenset({"pull", "inventory"}),
)


@dataclass(frozen=True, slots=True)
class EsparzaSection:
    key: str
    path: str

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise ValueError("Esparza section key must be non-empty")
        if not self.path.startswith("/"):
            raise ValueError("Esparza section path must be absolute within the site")


DEFAULT_SECTIONS = (
    EsparzaSection("concejo", "/articulo/230/actas-concejo-municipal"),
    EsparzaSection("comisiones", "/articulo/609/actas-de-comisiones"),
    EsparzaSection("junta_vial", "/articulo/231/actas-junta-vial"),
)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-CR,es;q=0.9",
}

_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


@dataclass(frozen=True, slots=True)
class EsparzaCmsConfig:
    """Private terrain configuration for the Esparza CMS connector."""

    base_url: str = "https://muniesparza.go.cr"
    sections: tuple[EsparzaSection, ...] = DEFAULT_SECTIONS
    years: frozenset[str] | None = None
    max_documents: int | None = None
    rate_limit_seconds: float = 1.0
    timeout_seconds: float = 60.0
    max_payload_bytes: int = 64 * 1024 * 1024
    max_redirects: int = 5
    headers: tuple[tuple[str, str], ...] = tuple(_DEFAULT_HEADERS.items())

    def __post_init__(self) -> None:
        parts = urlsplit(self.base_url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("Esparza base_url must be an absolute HTTP(S) URL")
        if parts.query or parts.fragment:
            raise ValueError("Esparza base_url must not contain query/fragment")
        if not self.sections:
            raise ValueError("Esparza connector requires at least one section")
        if len({section.key for section in self.sections}) != len(self.sections):
            raise ValueError("Esparza section keys must be unique")
        if self.years is not None:
            for year in self.years:
                if not re.fullmatch(r"\d{4}", year):
                    raise ValueError(f"invalid Esparza year filter: {year!r}")
        if self.max_documents is not None and self.max_documents < 0:
            raise ValueError("max_documents cannot be negative")
        if self.rate_limit_seconds < 0:
            raise ValueError("rate_limit_seconds cannot be negative")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_payload_bytes <= 0:
            raise ValueError("max_payload_bytes must be positive")
        if self.max_redirects < 0:
            raise ValueError("max_redirects cannot be negative")
        if not all(k and v for k, v in self.headers):
            raise ValueError("Esparza HTTP headers must have non-empty keys/values")

    @property
    def claims_complete_inventory(self) -> bool:
        return (
            self.sections == DEFAULT_SECTIONS
            and self.years is None
            and self.max_documents is None
        )

    @property
    def files_url(self) -> str:
        return self.base_url.rstrip("/") + "/files/folder/"

    @property
    def allowed_hosts(self) -> frozenset[str]:
        host = urlsplit(self.base_url).hostname
        assert host is not None
        host = host.lower()
        bare = host[4:] if host.startswith("www.") else host
        return frozenset({bare, f"www.{bare}"})


@dataclass(frozen=True, slots=True)
class EsparzaHttpResponse:
    attempted_url: str
    final_url: str
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class EsparzaHttpClient(Protocol):
    def get(self, url: str) -> EsparzaHttpResponse:
        ...


class EsparzaConnectorError(RuntimeError):
    """Base error for source-specific acquisition failures."""


class EsparzaSourceStructureError(EsparzaConnectorError):
    """The source returned material that no longer matches the known CMS shape."""


class EsparzaFetchError(EsparzaConnectorError):
    """A transport outcome could not be represented as an ordinary HTTP response."""

    def __init__(self, code: str, url: str, message: str) -> None:
        super().__init__(f"{code}: {message} ({url})")
        self.code = code
        self.url = url


class EsparzaRedirectPolicyError(EsparzaFetchError):
    """A redirect attempted to leave the configured source host boundary."""


class RequestsEsparzaHttpClient:
    """Bounded HTTP transport used privately by the Esparza connector."""

    def __init__(
        self,
        config: EsparzaCmsConfig,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self._config = config
        self._session = session or requests.Session()

    def get(self, url: str) -> EsparzaHttpResponse:
        attempted = url
        current = url
        for redirect_no in range(self._config.max_redirects + 1):
            self._validate_url(current)
            try:
                response = self._session.get(
                    current,
                    headers=dict(self._config.headers),
                    timeout=self._config.timeout_seconds,
                    stream=True,
                    allow_redirects=False,
                )
            except requests.Timeout as exc:
                raise EsparzaFetchError("timeout", current, str(exc)) from exc
            except requests.RequestException as exc:
                raise EsparzaFetchError("transport_error", current, str(exc)) from exc

            try:
                status = int(response.status_code)
                if status in _REDIRECT_STATUSES:
                    location = response.headers.get("Location")
                    if not location:
                        raise EsparzaFetchError(
                            "redirect_without_location",
                            current,
                            f"HTTP {status} had no Location header",
                        )
                    if redirect_no >= self._config.max_redirects:
                        raise EsparzaFetchError(
                            "too_many_redirects",
                            current,
                            "redirect limit exceeded",
                        )
                    next_url = urljoin(current, location)
                    self._validate_url(next_url, redirect=True)
                    current = next_url
                    continue

                body = self._read_bounded(response, current)
                return EsparzaHttpResponse(
                    attempted,
                    current,
                    status,
                    dict(response.headers),
                    body,
                )
            finally:
                response.close()

        raise AssertionError("redirect loop exhausted without terminal response")

    def _validate_url(self, url: str, *, redirect: bool = False) -> None:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if parts.scheme not in {"http", "https"} or not host:
            cls = EsparzaRedirectPolicyError if redirect else EsparzaFetchError
            raise cls("invalid_url", url, "URL must be absolute HTTP(S)")
        if host not in self._config.allowed_hosts:
            cls = EsparzaRedirectPolicyError if redirect else EsparzaFetchError
            raise cls(
                "disallowed_host",
                url,
                f"host {host!r} is outside Esparza connector policy",
            )

    def _read_bounded(self, response: requests.Response, url: str) -> bytes:
        chunks: list[bytes] = []
        total = 0
        try:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > self._config.max_payload_bytes:
                    raise EsparzaFetchError(
                        "payload_too_large",
                        url,
                        f"response exceeded {self._config.max_payload_bytes} bytes",
                    )
                chunks.append(chunk)
        except requests.RequestException as exc:
            raise EsparzaFetchError("body_read_error", url, str(exc)) from exc
        return b"".join(chunks)


@dataclass(frozen=True, slots=True)
class _Candidate:
    section: str
    year: str
    title: str
    filename: str
    source_class: str


class EsparzaCmsConnector:
    """First real SourceConnector consumer of INGRESS-001.

    Source-specific labels (year/title/CSS class) never cross the Inbox socket.
    They remain preserved in the captured listing HTML.
    """

    descriptor = ESPARZA_CONNECTOR_DESCRIPTOR

    def __init__(
        self,
        config: EsparzaCmsConfig | None = None,
        *,
        http: EsparzaHttpClient | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config or EsparzaCmsConfig()
        self._http = http or RequestsEsparzaHttpClient(self.config)
        self._sleep = sleeper

    def run(self, context: ConnectorContext) -> ConnectorRunResult:
        emitted = 0
        remaining = self.config.max_documents

        for section in self.config.sections:
            listing_url = self.config.base_url.rstrip("/") + section.path
            try:
                listing = self._fetch(listing_url)
            except EsparzaFetchError as exc:
                context.inbox.accept(
                    CaptureEnvelope.now(
                        outcome="failed",
                        locator=ObservedLocator(listing_url, "http_url"),
                        error_code=exc.code,
                    )
                )
                emitted += 1
                raise EsparzaConnectorError(
                    f"cannot enumerate Esparza section {section.key!r}"
                ) from exc

            listing_envelope = self._listing_envelope(listing)
            context.inbox.accept(listing_envelope)
            emitted += 1

            if not 200 <= listing.status_code < 300:
                raise EsparzaConnectorError(
                    f"cannot enumerate Esparza section {section.key!r}: "
                    f"HTTP {listing.status_code}"
                )

            try:
                candidates = self._parse_listing(listing.body, section.key)
            except EsparzaSourceStructureError:
                # The raw listing was committed above before we refuse to make a
                # plausible-but-wrong inventory claim.
                raise

            for candidate in candidates:
                if self.config.years is not None and candidate.year not in self.config.years:
                    continue
                if remaining is not None and remaining <= 0:
                    break

                context.inbox.accept(self._capture_candidate(candidate))
                emitted += 1
                if remaining is not None:
                    remaining -= 1

            if remaining is not None and remaining <= 0:
                break

        coverage = (
            "complete_inventory"
            if self.config.claims_complete_inventory
            else "unknown"
        )
        return ConnectorRunResult(coverage, emitted)

    def _fetch(self, url: str) -> EsparzaHttpResponse:
        try:
            return self._http.get(url)
        finally:
            if self.config.rate_limit_seconds:
                self._sleep(self.config.rate_limit_seconds)

    def _listing_envelope(self, response: EsparzaHttpResponse) -> CaptureEnvelope:
        outcome, error_code = _http_outcome(response.status_code)
        payloads = ()
        if response.body:
            payloads = (
                CapturePayload(
                    response.body,
                    role="response_body",
                    observed_url=response.final_url,
                    media_type=_media_type(response.headers, response.body),
                ),
            )
        return CaptureEnvelope.now(
            outcome=outcome,
            locator=ObservedLocator(response.attempted_url, "http_url"),
            http_status=response.status_code,
            error_code=error_code,
            payloads=payloads,
        )

    def _capture_candidate(self, candidate: _Candidate) -> CaptureEnvelope:
        url = self.config.files_url + quote(candidate.filename, safe="")
        try:
            response = self._fetch(url)
        except EsparzaFetchError as exc:
            return CaptureEnvelope.now(
                outcome="failed",
                locator=ObservedLocator(url, "http_url"),
                error_code=exc.code,
            )

        outcome, error_code = _http_outcome(response.status_code)
        role = "primary" if outcome == "success" else "response_body"
        media_type = _media_type(response.headers, response.body)

        if outcome == "success" and _looks_like_html(response.body, media_type):
            outcome = "failed"
            error_code = "unexpected_html_payload"
            role = "response_body"
        elif outcome == "success" and not response.body:
            outcome = "failed"
            error_code = "empty_response_body"
            role = "response_body"

        payloads = ()
        if response.body or outcome == "success":
            payloads = (
                CapturePayload(
                    response.body,
                    role=role,
                    observed_filename=candidate.filename,
                    observed_url=response.final_url,
                    media_type=media_type,
                ),
            )

        return CaptureEnvelope.now(
            outcome=outcome,
            locator=ObservedLocator(response.attempted_url, "http_url"),
            http_status=response.status_code,
            error_code=error_code,
            payloads=payloads,
        )

    @staticmethod
    def _parse_listing(body: bytes, section: str) -> list[_Candidate]:
        soup = BeautifulSoup(body, "html.parser")
        file_tree = soup.find("ul", class_="fileTree")
        if file_tree is None:
            raise EsparzaSourceStructureError(
                f"Esparza section {section!r} no longer contains ul.fileTree"
            )

        candidates: list[_Candidate] = []
        current_year = ""
        for li in file_tree.find_all("li", recursive=True):
            year_link = li.find("a", href="#")
            if year_link:
                label = year_link.get_text(strip=True)
                if re.fullmatch(r"\d{4}", label):
                    current_year = label
                    continue

            anchor = li.find("a", onclick=True)
            if anchor is None:
                continue
            match = re.search(
                r"openDocumentArticle\('([^']+)'\)",
                anchor.get("onclick", ""),
            )
            if match is None:
                continue
            filename = match.group(1)
            if not filename.strip():
                continue
            candidates.append(
                _Candidate(
                    section=section,
                    year=current_year,
                    title=anchor.get_text(strip=True),
                    filename=filename,
                    source_class=" ".join(li.get("class", [])),
                )
            )

        if not candidates:
            raise EsparzaSourceStructureError(
                f"Esparza section {section!r} produced zero known document hooks"
            )
        return candidates


def _http_outcome(status: int) -> tuple[str, str | None]:
    if 200 <= status < 300:
        return "success", None
    if status in {404, 410}:
        return "not_found", f"http_{status}"
    return "failed", f"http_{status}"


def _media_type(headers: Mapping[str, str], body: bytes) -> str:
    raw = ""
    for key, value in headers.items():
        if key.lower() == "content-type":
            raw = value.split(";", 1)[0].strip().lower()
            break
    if raw:
        return raw
    if body.startswith(b"%PDF"):
        return "application/pdf"
    if body.startswith(b"PK"):
        # ZIP containers include DOCX/XLSX/ODT and arbitrary archives.  The
        # connector must not promote transport bytes to a semantic document
        # type merely because the legacy site mostly served DOCX here.
        return "application/zip"
    if _looks_like_html(body, None):
        return "text/html"
    return "application/octet-stream"


def _looks_like_html(body: bytes, media_type: str | None) -> bool:
    if media_type in {"text/html", "application/xhtml+xml"}:
        return True
    prefix = body.lstrip()[:256].lower()
    return prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html")
