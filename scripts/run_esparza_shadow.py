#!/usr/bin/env python3
"""Run the Esparza Source Connector into an isolated Canario shadow Depósito.

This is a host/integration harness, not part of the SourceConnector SPI itself.
It intentionally does not write the legacy scraper output, Markdown inbox, Hilos,
or any semantic Fichero rows.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from canario.connectors.esparza import (
    DEFAULT_SECTIONS,
    EsparzaCmsConfig,
    EsparzaCmsConnector,
)
from canario.deposit import DepositWriter, SourceRegistration, new_id, utc_now
from canario.ingress import DepositInbox, run_connector
from canario.persistence import ensure_schema_v1


SOURCE_BINDING_VERSION = 1
SOURCE_KIND = "web"
SOURCE_NAME = "Municipalidad de Esparza — CMS"


def load_or_create_source_binding(path: Path) -> SourceRegistration:
    """Persist the host-owned Source identity outside the repository/database.

    Source identity is stable across shadow runs.  This is not a connector
    checkpoint and contains no discovery cursor or source-specific page state.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise RuntimeError(f"refusing symlink source-binding path: {path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        source = SourceRegistration(
            new_id("src_"), SOURCE_KIND, SOURCE_NAME, True, utc_now()
        )
        payload = {
            "version": SOURCE_BINDING_VERSION,
            "source": {
                "id": source.id,
                "kind": source.kind,
                "name": source.name,
                "active": source.active,
                "created_at": source.created_at,
            },
        }
        data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags, 0o600)
        except FileExistsError:
            return load_or_create_source_binding(path)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        return source

    try:
        payload = json.loads(raw)
        if payload.get("version") != SOURCE_BINDING_VERSION:
            raise ValueError("unsupported source-binding version")
        item = payload["source"]
        source = SourceRegistration(
            item["id"],
            item["kind"],
            item["name"],
            item["active"],
            item["created_at"],
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid Esparza shadow source binding: {path}") from exc

    if source.kind != SOURCE_KIND or source.name != SOURCE_NAME or not source.active:
        raise RuntimeError(
            "Esparza shadow source binding does not match the expected active CMS Source"
        )
    return source


def _selected_sections(names: list[str] | None):
    if not names:
        return DEFAULT_SECTIONS
    by_key = {section.key: section for section in DEFAULT_SECTIONS}
    unknown = sorted(set(names) - set(by_key))
    if unknown:
        raise ValueError(f"unknown Esparza sections: {unknown!r}")
    return tuple(section for section in DEFAULT_SECTIONS if section.key in names)


def assert_source_binding_continuity(database_path: Path, binding_path: Path) -> None:
    """Fail closed if a known shadow DB lost its host-owned Source binding."""

    if database_path.exists() and not binding_path.exists():
        raise RuntimeError(
            "shadow database exists but source-binding.json is missing; "
            "restore/reconcile the binding instead of minting a new Source"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Shadow-ingest Esparza CMS material through INGRESS-001"
    )
    parser.add_argument(
        "--shadow-root",
        required=True,
        type=Path,
        help="Isolated Canario shadow state root (never the legacy vault)",
    )
    parser.add_argument(
        "--base-url",
        default="https://muniesparza.go.cr",
        help="Esparza CMS base URL",
    )
    parser.add_argument(
        "--section",
        action="append",
        choices=[section.key for section in DEFAULT_SECTIONS],
        help="Limit to one or more sections; makes coverage unknown",
    )
    parser.add_argument(
        "--year",
        action="append",
        help="Limit to one or more listing years; makes coverage unknown",
    )
    parser.add_argument(
        "--max-documents",
        type=int,
        default=None,
        help="Bound document downloads for dogfood; makes coverage unknown",
    )
    parser.add_argument(
        "--rate-limit-seconds",
        type=float,
        default=1.0,
        help="Delay between top-level source fetches",
    )
    parser.add_argument(
        "--max-payload-mib",
        type=int,
        default=64,
        help="Maximum decompressed response size accepted per fetch",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    shadow_root = args.shadow_root
    shadow_root.mkdir(parents=True, exist_ok=True)

    database_path = shadow_root / "canario.sqlite3"
    archive_root = shadow_root / "archive"
    binding_path = shadow_root / "source-binding.json"

    # Source identity is host-owned and must remain stable.  Losing only the
    # sidecar while keeping a populated/known database is an operator recovery
    # event, not permission to mint a second canonical Source silently.
    assert_source_binding_continuity(database_path, binding_path)
    source = load_or_create_source_binding(binding_path)
    # The production runtime guard remains active.  No shadow-only bypass exists.
    ensure_schema_v1(database_path)

    writer = DepositWriter(database_path, archive_root)
    config = EsparzaCmsConfig(
        base_url=args.base_url,
        sections=_selected_sections(args.section),
        years=frozenset(args.year) if args.year else None,
        max_documents=args.max_documents,
        rate_limit_seconds=args.rate_limit_seconds,
        max_payload_bytes=args.max_payload_mib * 1024 * 1024,
    )
    connector = EsparzaCmsConnector(config)
    inbox = DepositInbox(writer, source, connector.descriptor)

    result = run_connector(connector, inbox)
    print(
        "ESPARZA_SHADOW_RUN=PASS "
        f"coverage={result.coverage} emitted={result.emitted} "
        f"database={database_path} archive={archive_root}"
    )
    print("legacy_scraper_hilo_behavior=UNCHANGED")
    print("canonical_cutover=NOT_AUTHORIZED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
