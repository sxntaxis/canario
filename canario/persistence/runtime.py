"""Fail-closed SQLite runtime contract for the canonical Canario store."""

from __future__ import annotations

import sqlite3
from functools import lru_cache

TARGET_VERSION = (3, 53, 4)
CERTIFIED_SOURCE_IDS: dict[tuple[int, int, int], str] = {
    (3, 53, 4): (
        "2026-07-24 19:02:57 "
        "bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc"
    ),
}


class RuntimeContractError(RuntimeError):
    """The loaded SQLite library is not a certified Canario runtime."""


def _version_tuple() -> tuple[int, int, int]:
    pieces = sqlite3.sqlite_version.split(".")
    return tuple(int(piece) for piece in pieces[:3])  # type: ignore[return-value]


@lru_cache(maxsize=1)
def verify_runtime_contract() -> None:
    """Reject SQLite builds not explicitly certified for canonical writes.

    Version ordering alone is insufficient: a later SQLite release must be run
    through Canario's durability/projection proofs before it enters the registry.
    """

    version = _version_tuple()
    if version < TARGET_VERSION:
        raise RuntimeContractError(
            f"SQLite {sqlite3.sqlite_version} is below the Canario floor 3.53.4"
        )

    expected_source_id = CERTIFIED_SOURCE_IDS.get(version)
    if expected_source_id is None:
        raise RuntimeContractError(
            f"SQLite {sqlite3.sqlite_version} is not in the certified runtime registry"
        )

    con = sqlite3.connect(":memory:")
    try:
        source_id = con.execute("select sqlite_source_id()").fetchone()[0]
        if source_id != expected_source_id:
            raise RuntimeContractError(
                "SQLite source ID does not match the certified build for "
                f"{sqlite3.sqlite_version}: {source_id!r}"
            )

        options = {row[0] for row in con.execute("pragma compile_options")}
    finally:
        con.close()

    if "ENABLE_FTS5" not in options:
        raise RuntimeContractError("SQLite was built without ENABLE_FTS5")

    thread_options = [option for option in options if option.startswith("THREADSAFE=")]
    if not thread_options or thread_options[0] == "THREADSAFE=0":
        raise RuntimeContractError(
            f"SQLite thread-safety contract failed: {thread_options or ['missing THREADSAFE']}"
        )

    forbidden = {"OMIT_WAL", "OMIT_FOREIGN_KEY", "OMIT_TRIGGER"}
    present = sorted(forbidden & options)
    if present:
        raise RuntimeContractError(
            "SQLite build omits required capabilities: " + ", ".join(present)
        )
