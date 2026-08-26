#!/usr/bin/env python3
"""Deterministic structured-reasoning fit bench for Canario.

This module is deliberately outside ``canario/``.  It is a bench implementation,
not product authority.  It consumes retained ``canario.structured_table.v1`` bytes,
materializes a neutral deterministic projection, and lets bounded SQL executors
query disposable copies of that projection.  The original XLSX is never an engine
input.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import shutil
import sqlite3
import subprocess
import tempfile
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

STRUCTURED_TABLE_FORMAT = "canario.structured_table.v1"
PROJECTION_FORMAT = "canario.structured_projection.v1"
EXTERNAL_CSV_SPEC_FORMAT = "canario.external_csv_projection_spec.v1"
QUERY_CORPUS_FORMAT = "canario.structured_query_corpus.v1"
PLANNER_CASES_FORMAT = "canario.planner_verifier_cases.v1"
RESULT_FORMAT = "canario.structured_query_result.v1"

SQLITE_EXPECTED_VERSION = "3.53.4"
SQLITE_EXPECTED_SOURCE_ID = (
    "2026-07-24 19:02:57 "
    "bf7c7f30031888f4e796e429ab3978879485813aaca6f641c7b33e4e09459bcc"
)

DEFAULT_MAX_ROWS = 1_000
DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_TIMEOUT_MS = 2_000
DEFAULT_DUCKDB_BOOTSTRAP_GRACE_MS = 30_000
DEFAULT_DUCKDB_PROCESS_OVERHEAD_MS = 5_000
DEFAULT_SQLITE_PROGRESS_OPS = 1_000
DEFAULT_SQLITE_PROGRESS_CALLBACKS = 10_000

_ALLOWED_CELL_TYPES = {
    "string",
    "integer",
    "number",
    "boolean",
    "datetime",
    "formula",
    "error",
}


class FitBenchError(ValueError):
    """Bench input violates a deterministic or security invariant."""


class QueryRejected(FitBenchError):
    """An untrusted query was rejected before successful execution."""


@dataclass(frozen=True, slots=True)
class QueryLimits:
    max_rows: int = DEFAULT_MAX_ROWS
    max_bytes: int = DEFAULT_MAX_BYTES
    timeout_ms: int = DEFAULT_TIMEOUT_MS
    duckdb_bootstrap_grace_ms: int = DEFAULT_DUCKDB_BOOTSTRAP_GRACE_MS
    duckdb_process_overhead_ms: int = DEFAULT_DUCKDB_PROCESS_OVERHEAD_MS
    sqlite_progress_ops: int = DEFAULT_SQLITE_PROGRESS_OPS
    sqlite_progress_callbacks: int = DEFAULT_SQLITE_PROGRESS_CALLBACKS

    def __post_init__(self) -> None:
        for name in (
            "max_rows",
            "max_bytes",
            "timeout_ms",
            "duckdb_bootstrap_grace_ms",
            "duckdb_process_overhead_ms",
            "sqlite_progress_ops",
            "sqlite_progress_callbacks",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class ExternalCsvColumn:
    name: str
    source_index: int
    kind: str = "string"

    def __post_init__(self) -> None:
        if not self.name or not self.name.replace("_", "").isalnum():
            raise ValueError("external CSV column name must be a simple identifier")
        if self.source_index < 0:
            raise ValueError("external CSV source_index must be non-negative")
        if self.kind not in {"string", "integer", "number", "boolean", "datetime"}:
            raise ValueError(f"unsupported external CSV kind {self.kind!r}")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise FitBenchError("non-finite numeric values are not supported")
    # The canonical structured-table derivative already lost Excel display-only
    # trailing zeroes when it serialized Python floats.  Preserve the exact JSON
    # numeric value represented by Decimal without adding binary-float noise.
    text = str(value)
    if text == "-0":
        return "0"
    return text


def _load_json_decimal(data: bytes) -> object:
    try:
        return json.loads(data.decode("utf-8"), parse_float=Decimal, parse_int=int)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FitBenchError("input must be UTF-8 JSON") from exc


def _validate_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise FitBenchError(f"{label} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise FitBenchError(f"{label} must be a SHA-256 hex digest") from exc
    return value


def _normalize_cell_value(raw: object) -> dict[str, object]:
    if raw is None:
        return {"kind": "blank"}
    if not isinstance(raw, dict):
        raise FitBenchError("structured-table cell value must be null or typed object")
    kind = raw.get("type")
    value = raw.get("value")
    if kind not in _ALLOWED_CELL_TYPES:
        raise FitBenchError(f"unsupported structured-table cell type {kind!r}")
    if kind in {"string", "datetime", "formula", "error"}:
        if not isinstance(value, str):
            raise FitBenchError(f"{kind} cell requires string value")
        return {"kind": kind, "text": value}
    if kind == "boolean":
        if not isinstance(value, bool):
            raise FitBenchError("boolean cell requires boolean value")
        return {"kind": kind, "value": value}
    if kind == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise FitBenchError("integer cell requires integer value")
        return {"kind": kind, "decimal": str(value)}
    if kind == "number":
        if isinstance(value, int) and not isinstance(value, bool):
            decimal_value = Decimal(value)
        elif isinstance(value, Decimal):
            decimal_value = value
        else:
            raise FitBenchError("number cell requires JSON number value")
        return {"kind": kind, "decimal": _canonical_decimal(decimal_value)}
    raise AssertionError(kind)


def _cell_text(value: Mapping[str, object]) -> str | None:
    kind = value["kind"]
    if kind == "blank":
        return None
    if kind in {"string", "datetime", "formula", "error"}:
        return str(value["text"])
    if kind in {"integer", "number"}:
        return str(value["decimal"])
    if kind == "boolean":
        return "true" if value["value"] else "false"
    raise AssertionError(kind)


def _cell_integer(value: Mapping[str, object]) -> int | None:
    if value["kind"] != "integer":
        return None
    integer = int(str(value["decimal"]))
    if -(2**63) <= integer <= (2**63 - 1):
        return integer
    return None


def _cell_number(value: Mapping[str, object]) -> float | None:
    if value["kind"] == "integer":
        integer = int(str(value["decimal"]))
        return float(integer)
    if value["kind"] == "number":
        decimal_value = Decimal(str(value["decimal"]))
        number = float(decimal_value)
        if not math.isfinite(number):
            raise FitBenchError("numeric value cannot be represented by engine REAL")
        return number
    return None


def build_projection(source_bytes: bytes) -> tuple[bytes, dict[str, object]]:
    """Build the neutral projection from canonical typed Representation bytes."""

    value = _load_json_decimal(source_bytes)
    if not isinstance(value, dict) or value.get("format") != STRUCTURED_TABLE_FORMAT:
        raise FitBenchError(f"source must be {STRUCTURED_TABLE_FORMAT}")
    declared_source_sha = _validate_sha256(value.get("source_sha256"), "declared source SHA")
    sheets = value.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        raise FitBenchError("structured-table source requires non-empty sheets")

    projection_sheets: list[dict[str, object]] = []
    cells: list[dict[str, object]] = []
    previous_ordinal = 0
    for sheet in sheets:
        if not isinstance(sheet, dict):
            raise FitBenchError("sheet entry must be an object")
        ordinal = sheet.get("ordinal")
        name = sheet.get("name")
        state = sheet.get("state")
        max_row = sheet.get("max_row")
        max_column = sheet.get("max_column")
        merged_ranges = sheet.get("merged_ranges")
        rows = sheet.get("rows")
        if not isinstance(ordinal, int) or ordinal <= previous_ordinal:
            raise FitBenchError("sheet ordinals must be positive and strictly increasing")
        previous_ordinal = ordinal
        if not isinstance(name, str) or not name:
            raise FitBenchError("sheet name must be non-empty")
        if not isinstance(state, str) or not state:
            raise FitBenchError("sheet state must be non-empty")
        if not isinstance(max_row, int) or max_row < 0:
            raise FitBenchError("sheet max_row must be non-negative integer")
        if not isinstance(max_column, int) or max_column < 0:
            raise FitBenchError("sheet max_column must be non-negative integer")
        if not isinstance(merged_ranges, list) or not all(isinstance(x, str) for x in merged_ranges):
            raise FitBenchError("sheet merged_ranges must be a string list")
        if not isinstance(rows, list) or len(rows) != max_row:
            raise FitBenchError("sheet row count disagrees with max_row")
        projection_sheets.append(
            {
                "ordinal": ordinal,
                "name": name,
                "state": state,
                "max_row": max_row,
                "max_column": max_column,
                "merged_ranges": list(merged_ranges),
            }
        )
        for row_index, row in enumerate(rows, start=1):
            if not isinstance(row, list) or len(row) != max_column:
                raise FitBenchError("sheet row width disagrees with max_column")
            for column_index, cell in enumerate(row, start=1):
                if not isinstance(cell, dict):
                    raise FitBenchError("cell entry must be an object")
                address = cell.get("address")
                data_type = cell.get("data_type")
                number_format = cell.get("number_format")
                if not isinstance(address, str) or not address:
                    raise FitBenchError("cell address must be non-empty")
                if not isinstance(data_type, str):
                    raise FitBenchError("cell data_type must be a string")
                if not isinstance(number_format, str):
                    raise FitBenchError("cell number_format must be a string")
                cells.append(
                    {
                        "sheet_ordinal": ordinal,
                        "sheet_name": name,
                        "row": row_index,
                        "column": column_index,
                        "address": address,
                        "data_type": data_type,
                        "number_format": number_format,
                        "value": _normalize_cell_value(cell.get("value")),
                    }
                )

    projection = {
        "format": PROJECTION_FORMAT,
        "source_representation_sha256": _sha256_bytes(source_bytes),
        "source_representation_format": STRUCTURED_TABLE_FORMAT,
        "declared_original_source_sha256": declared_source_sha,
        "sheets": projection_sheets,
        "cells": cells,
    }
    projection_bytes = _canonical_json_bytes(projection)
    manifest = {
        "format": PROJECTION_FORMAT,
        "source_representation_sha256": projection["source_representation_sha256"],
        "declared_original_source_sha256": declared_source_sha,
        "projection_sha256": _sha256_bytes(projection_bytes),
        "projection_bytes": len(projection_bytes),
        "sheet_count": len(projection_sheets),
        "row_count": sum(int(sheet["max_row"]) for sheet in projection_sheets),
        "cell_count": len(cells),
        "non_empty_cell_count": sum(cell["value"]["kind"] != "blank" for cell in cells),
        "formula_count": sum(cell["value"]["kind"] == "formula" for cell in cells),
        "merged_range_count": sum(len(sheet["merged_ranges"]) for sheet in projection_sheets),
        "value_kinds": sorted({str(cell["value"]["kind"]) for cell in cells}),
    }
    return projection_bytes, manifest


def load_projection(projection_bytes: bytes, *, expected_sha256: str | None = None) -> dict[str, object]:
    if expected_sha256 is not None and _sha256_bytes(projection_bytes) != expected_sha256:
        raise FitBenchError("projection SHA-256 mismatch")
    value = _load_json_decimal(projection_bytes)
    if not isinstance(value, dict) or value.get("format") != PROJECTION_FORMAT:
        raise FitBenchError(f"projection must be {PROJECTION_FORMAT}")
    source_sha = value.get("source_representation_sha256")
    _validate_sha256(source_sha, "projection source Representation SHA")
    sheets = value.get("sheets")
    cells = value.get("cells")
    if not isinstance(sheets, list) or not isinstance(cells, list):
        raise FitBenchError("projection requires sheets and cells")
    return value


def projection_manifest(projection_bytes: bytes) -> dict[str, object]:
    projection = load_projection(projection_bytes)
    cells = projection["cells"]
    sheets = projection["sheets"]
    assert isinstance(cells, list) and isinstance(sheets, list)
    return {
        "format": PROJECTION_FORMAT,
        "source_representation_sha256": projection["source_representation_sha256"],
        "declared_original_source_sha256": projection.get("declared_original_source_sha256"),
        "projection_sha256": _sha256_bytes(projection_bytes),
        "projection_bytes": len(projection_bytes),
        "sheet_count": len(sheets),
        "row_count": sum(int(sheet["max_row"]) for sheet in sheets if isinstance(sheet, dict)),
        "cell_count": len(cells),
        "non_empty_cell_count": sum(
            isinstance(cell, dict)
            and isinstance(cell.get("value"), dict)
            and cell["value"].get("kind") != "blank"
            for cell in cells
        ),
        "formula_count": sum(
            isinstance(cell, dict)
            and isinstance(cell.get("value"), dict)
            and cell["value"].get("kind") == "formula"
            for cell in cells
        ),
    }


def _sql_identifier(value: str) -> str:
    if not value or not value.replace("_", "").isalnum() or value[0].isdigit():
        raise FitBenchError(f"unsafe SQL identifier {value!r}")
    return value


def _sql_string_literal(value: str) -> str:
    """Return a portable single-quoted SQL literal for frozen bench metadata only."""

    return "'" + value.replace("'", "''") + "'"


def _sheet_table_name(ordinal: int) -> str:
    return f"sheet_{ordinal}_rows"


def _projection_sheet_map(projection: Mapping[str, object]) -> dict[int, dict[str, object]]:
    sheets = projection.get("sheets")
    if not isinstance(sheets, list):
        raise FitBenchError("projection sheets missing")
    result: dict[int, dict[str, object]] = {}
    for sheet in sheets:
        if not isinstance(sheet, dict) or not isinstance(sheet.get("ordinal"), int):
            raise FitBenchError("projection sheet malformed")
        result[int(sheet["ordinal"])] = sheet
    return result


def _projection_cells_by_sheet_row(
    projection: Mapping[str, object],
) -> dict[tuple[int, int], dict[int, dict[str, object]]]:
    cells = projection.get("cells")
    if not isinstance(cells, list):
        raise FitBenchError("projection cells missing")
    result: dict[tuple[int, int], dict[int, dict[str, object]]] = {}
    for cell in cells:
        if not isinstance(cell, dict):
            raise FitBenchError("projection cell malformed")
        sheet = int(cell["sheet_ordinal"])
        row = int(cell["row"])
        column = int(cell["column"])
        result.setdefault((sheet, row), {})[column] = cell
    return result


def _engine_cell_columns(column: int) -> list[tuple[str, str]]:
    prefix = f"c{column}"
    return [
        (f"{prefix}_kind", "TEXT"),
        (f"{prefix}_text", "TEXT"),
        (f"{prefix}_integer", "BIGINT"),
        (f"{prefix}_number", "DOUBLE"),
        (f"{prefix}_boolean", "BOOLEAN"),
        (f"{prefix}_datetime", "TEXT"),
        (f"{prefix}_formula", "TEXT"),
        (f"{prefix}_address", "TEXT"),
        (f"{prefix}_data_type", "TEXT"),
        (f"{prefix}_number_format", "TEXT"),
    ]


def _engine_cell_values(cell: Mapping[str, object]) -> list[object]:
    value = cell.get("value")
    if not isinstance(value, dict):
        raise FitBenchError("projection cell has no normalized value")
    kind = str(value["kind"])
    text = _cell_text(value)
    integer = _cell_integer(value)
    number = _cell_number(value)
    boolean = bool(value["value"]) if kind == "boolean" else None
    datetime = str(value["text"]) if kind == "datetime" else None
    formula = str(value["text"]) if kind == "formula" else None
    return [
        kind,
        text,
        integer,
        number,
        boolean,
        datetime,
        formula,
        str(cell["address"]),
        str(cell["data_type"]),
        str(cell["number_format"]),
    ]


def _sqlite_create_projection(connection: sqlite3.Connection, projection: Mapping[str, object]) -> None:
    sheets = _projection_sheet_map(projection)
    cells_by_row = _projection_cells_by_sheet_row(projection)
    connection.execute(
        "CREATE TABLE projection_sheets(ordinal INTEGER PRIMARY KEY,name TEXT NOT NULL,state TEXT NOT NULL,max_row INTEGER NOT NULL,max_column INTEGER NOT NULL,merged_ranges_json TEXT NOT NULL)"
    )
    for ordinal in sorted(sheets):
        sheet = sheets[ordinal]
        connection.execute(
            "INSERT INTO projection_sheets VALUES(?,?,?,?,?,?)",
            (
                ordinal,
                str(sheet["name"]),
                str(sheet["state"]),
                int(sheet["max_row"]),
                int(sheet["max_column"]),
                json.dumps(sheet.get("merged_ranges", []), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            ),
        )
        max_column = int(sheet["max_column"])
        columns = [("row_index", "INTEGER PRIMARY KEY")]
        for column in range(1, max_column + 1):
            columns.extend(_engine_cell_columns(column))
        table = _sheet_table_name(ordinal)
        connection.execute(
            f"CREATE TABLE {table}({','.join(f'{name} {kind}' for name, kind in columns)})"
        )
        placeholders = ",".join("?" for _ in columns)
        for row_index in range(1, int(sheet["max_row"]) + 1):
            row_values: list[object] = [row_index]
            row_cells = cells_by_row.get((ordinal, row_index), {})
            for column in range(1, max_column + 1):
                cell = row_cells.get(column)
                if cell is None:
                    raise FitBenchError("projection row is missing an in-extent cell")
                row_values.extend(_engine_cell_values(cell))
            connection.execute(f"INSERT INTO {table} VALUES({placeholders})", row_values)
    connection.commit()


def sqlite_runtime_identity() -> dict[str, object]:
    connection = sqlite3.connect(":memory:")
    try:
        version, source_id = connection.execute("SELECT sqlite_version(),sqlite_source_id()").fetchone()
    finally:
        connection.close()
    return {
        "version": version,
        "source_id": source_id,
        "registered_runtime": version == SQLITE_EXPECTED_VERSION and source_id == SQLITE_EXPECTED_SOURCE_ID,
        "expected_version": SQLITE_EXPECTED_VERSION,
        "expected_source_id": SQLITE_EXPECTED_SOURCE_ID,
    }


_SQLITE_ALLOWED_FUNCTIONS = frozenset(
    {
        "abs",
        "avg",
        "coalesce",
        "count",
        "dense_rank",
        "first_value",
        "ifnull",
        "lag",
        "last_value",
        "lead",
        "length",
        "lower",
        "max",
        "min",
        "nth_value",
        "nullif",
        "printf",
        "rank",
        "replace",
        "round",
        "row_number",
        "substr",
        "substring",
        "sum",
        "total",
        "upper",
    }
)


def _sqlite_authorizer(action: int, arg1: str | None, arg2: str | None, _db: str | None, _source: str | None) -> int:
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        table = arg1 or ""
        if table == "projection_sheets" or table.startswith("sheet_"):
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION:
        function_name = (arg2 or arg1 or "").lower()
        return sqlite3.SQLITE_OK if function_name in _SQLITE_ALLOWED_FUNCTIONS else sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_DENY


def _canonical_result_value(value: object) -> dict[str, object]:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean", "value": value}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, Decimal):
        return {"type": "number", "value": _canonical_decimal(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise FitBenchError("query result contains non-finite float")
        return {"type": "number", "value": repr(value)}
    if isinstance(value, str):
        return {"type": "string", "value": value}
    if isinstance(value, bytes):
        return {"type": "bytes", "hex": value.hex()}
    # DuckDB may return date/time objects without this bench importing its package.
    if hasattr(value, "isoformat"):
        return {"type": "datetime", "value": str(value.isoformat())}
    raise FitBenchError(f"unsupported query result type {type(value).__name__}")


def _result_payload(
    *,
    engine: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[object]],
    truncated: bool,
) -> dict[str, object]:
    typed_rows = [[_canonical_result_value(value) for value in row] for row in rows]
    deterministic = {
        "format": RESULT_FORMAT,
        "columns": list(columns),
        "rows": typed_rows,
        "row_count": len(rows),
        "truncated": truncated,
    }
    return {
        **deterministic,
        "engine": engine,
        "result_sha256": _sha256_bytes(_canonical_json_bytes(deterministic)),
    }


def _enforce_result_bounds(payload: Mapping[str, object], limits: QueryLimits) -> None:
    if int(payload["row_count"]) > limits.max_rows:
        raise QueryRejected("result row limit exceeded")
    encoded = _canonical_json_bytes({
        "format": payload["format"],
        "columns": payload["columns"],
        "rows": payload["rows"],
        "row_count": payload["row_count"],
        "truncated": payload["truncated"],
    })
    if len(encoded) > limits.max_bytes:
        raise QueryRejected("result byte limit exceeded")


def execute_sqlite(
    projection_bytes: bytes,
    sql: str,
    *,
    limits: QueryLimits | None = None,
) -> dict[str, object]:
    """Run one untrusted SELECT against a disposable in-memory SQLite projection."""

    limits = limits or QueryLimits()
    if not isinstance(sql, str) or not sql.strip():
        raise QueryRejected("query must be non-empty")
    projection = load_projection(projection_bytes)
    connection = sqlite3.connect(":memory:")
    try:
        _sqlite_create_projection(connection, projection)
        connection.execute("PRAGMA query_only=ON")
        try:
            connection.enable_load_extension(False)
        except (AttributeError, sqlite3.DatabaseError):
            pass
        deadline = time.monotonic() + limits.timeout_ms / 1000.0
        callbacks = 0

        def progress() -> int:
            nonlocal callbacks
            callbacks += 1
            if callbacks > limits.sqlite_progress_callbacks:
                return 1
            if time.monotonic() >= deadline:
                return 1
            return 0

        connection.set_progress_handler(progress, limits.sqlite_progress_ops)
        connection.set_authorizer(_sqlite_authorizer)
        started = time.monotonic()
        try:
            cursor = connection.execute(sql)
        except sqlite3.ProgrammingError as exc:
            raise QueryRejected("query must contain exactly one statement") from exc
        except sqlite3.DatabaseError as exc:
            message = str(exc).lower()
            if "not authorized" in message or "authorization denied" in message:
                raise QueryRejected("query uses a forbidden SQLite operation") from exc
            if "interrupted" in message:
                raise QueryRejected("query exceeded SQLite execution budget") from exc
            raise QueryRejected(f"SQLite rejected query: {exc}") from exc
        if cursor.description is None:
            raise QueryRejected("query did not return a SELECT result")
        columns = [str(item[0]) for item in cursor.description]
        rows: list[tuple[object, ...]] = []
        truncated = False
        while True:
            if time.monotonic() >= deadline:
                raise QueryRejected("query exceeded wall-clock budget")
            row = cursor.fetchone()
            if row is None:
                break
            if len(rows) >= limits.max_rows:
                truncated = True
                raise QueryRejected("result row limit exceeded")
            rows.append(tuple(row))
        payload = _result_payload(engine="sqlite", columns=columns, rows=rows, truncated=truncated)
        _enforce_result_bounds(payload, limits)
        payload["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
        payload["runtime"] = sqlite_runtime_identity()
        payload["security"] = {
            "disposable_database": True,
            "query_only": True,
            "authorizer": "explicit_select_read_function_allowlist",
            "extensions_enabled": False,
            "canonical_database_opened": False,
            "filesystem_authority": "none_from_sql_surface",
            "network_authority": "none_from_sql_surface",
        }
        return payload
    finally:
        connection.close()


def duckdb_worker_path() -> Path:
    return Path(__file__).with_name("structured_reasoning_duckdb_worker.py")


def _required_runtime_mounts() -> list[tuple[Path, str]]:
    result: list[tuple[Path, str]] = []
    for source, dest in (
        (Path("/usr"), "/usr"),
        (Path("/bin"), "/bin"),
        (Path("/lib"), "/lib"),
        (Path("/lib64"), "/lib64"),
    ):
        if source.exists():
            result.append((source, dest))
    return result


def duckdb_process_timeout_ms(limits: QueryLimits, *, query_count: int = 1) -> int:
    """Return the hard sandbox-process bound for one materialization + bounded queries.

    The untrusted SQL budget remains ``limits.timeout_ms`` **per query** inside the
    worker.  The parent process separately allows bounded trusted startup/materialization
    time and a small fixed teardown/serialization allowance.  Corpus runs therefore
    materialize the neutral projection once and execute all frozen queries in the same
    disposable sandbox session instead of rebuilding it for every query.
    """

    if not isinstance(query_count, int) or query_count <= 0 or query_count > 128:
        raise ValueError("query_count must be between 1 and 128")
    return (
        limits.duckdb_bootstrap_grace_ms
        + limits.duckdb_process_overhead_ms
        + limits.timeout_ms * query_count
    )


def _duckdb_request_limits(limits: QueryLimits) -> dict[str, object]:
    return {
        "max_rows": limits.max_rows,
        "max_bytes": limits.max_bytes,
        "query_timeout_ms": limits.timeout_ms,
        "memory_limit": "256MB",
        "threads": 1,
    }


def _run_duckdb_worker_sandboxed(
    projection_bytes: bytes,
    request: Mapping[str, object],
    *,
    duckdb_python: Path,
    process_timeout_ms: int,
    bwrap: Path,
    query_count: int,
    limits: QueryLimits,
) -> dict[str, object]:
    if not bwrap.exists():
        raise FitBenchError("bubblewrap is required for the DuckDB lane")
    worker = duckdb_worker_path()
    if not worker.is_file():
        raise FitBenchError("DuckDB worker file is missing")
    if not duckdb_python.is_file():
        raise FitBenchError("DuckDB Python interpreter does not exist")
    venv_root = duckdb_python.parent.parent
    if not (venv_root / "pyvenv.cfg").exists():
        raise FitBenchError("DuckDB interpreter must come from a dedicated virtual environment")

    with tempfile.TemporaryDirectory(prefix="canario-duckdb-bench-") as tmp:
        scratch = Path(tmp)
        (scratch / "projection.json").write_bytes(projection_bytes)
        request_payload = {**dict(request), "limits": _duckdb_request_limits(limits)}
        (scratch / "request.json").write_bytes(_canonical_json_bytes(request_payload))
        (scratch / "tmp").mkdir()

        command = [
            str(bwrap),
            "--die-with-parent",
            "--new-session",
            "--unshare-all",
            "--clearenv",
            "--dir",
            "/opt",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--ro-bind",
            str(worker),
            "/worker.py",
            "--ro-bind",
            str(venv_root),
            "/opt/duckdb-venv",
            "--bind",
            str(scratch),
            "/work",
            "--setenv",
            "HOME",
            "/nonexistent",
            "--setenv",
            "XDG_CACHE_HOME",
            "/work/cache",
            "--setenv",
            "PYTHONNOUSERSITE",
            "1",
            "--setenv",
            "PATH",
            "/opt/duckdb-venv/bin:/usr/bin:/bin",
            "--chdir",
            "/work",
        ]
        for source, dest in _required_runtime_mounts():
            command.extend(["--ro-bind", str(source), dest])
        command.extend(
            [
                "/opt/duckdb-venv/bin/python",
                "/worker.py",
                "/work/projection.json",
                "/work/request.json",
            ]
        )
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=process_timeout_ms / 1000.0,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise QueryRejected("DuckDB worker exceeded bounded process wall-clock budget") from exc
        duration_ms = round((time.monotonic() - started) * 1000, 3)
        if completed.returncode != 0:
            detail = completed.stderr.strip()[-2_000:]
            raise QueryRejected(f"DuckDB sandbox rejected query: {detail or 'worker failed'}")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise FitBenchError("DuckDB worker returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise FitBenchError("DuckDB worker returned invalid result")
        payload["duration_ms"] = duration_ms
        payload["security"] = {
            **dict(payload.get("security") or {}),
            "process_isolation": True,
            "os_sandbox": "bubblewrap --unshare-all",
            "network_namespace": "unshared",
            "repo_mounted": False,
            "canonical_database_mounted": False,
            "home_mounted": False,
            "worker_only_code_mount": True,
            "query_timeout_ms": limits.timeout_ms,
            "bootstrap_grace_ms": limits.duckdb_bootstrap_grace_ms,
            "process_overhead_ms": limits.duckdb_process_overhead_ms,
            "query_count": query_count,
            "process_timeout_ms": process_timeout_ms,
        }
        return payload


def execute_duckdb_sandboxed(
    projection_bytes: bytes,
    sql: str,
    *,
    duckdb_python: Path,
    limits: QueryLimits | None = None,
    bwrap: Path = Path("/usr/bin/bwrap"),
) -> dict[str, object]:
    """Run one untrusted SELECT in a separate bubblewrap sandbox."""

    limits = limits or QueryLimits()
    if not isinstance(sql, str) or not sql.strip():
        raise QueryRejected("query must be a non-empty string")
    process_timeout_ms = duckdb_process_timeout_ms(limits, query_count=1)
    payload = _run_duckdb_worker_sandboxed(
        projection_bytes,
        {"sql": sql},
        duckdb_python=duckdb_python,
        process_timeout_ms=process_timeout_ms,
        bwrap=bwrap,
        query_count=1,
        limits=limits,
    )
    if payload.get("format") != RESULT_FORMAT or payload.get("engine") != "duckdb":
        raise FitBenchError("DuckDB worker returned unexpected single-query format")
    return payload


def execute_duckdb_batch_sandboxed(
    projection_bytes: bytes,
    queries: Sequence[tuple[str, str]],
    *,
    duckdb_python: Path,
    limits: QueryLimits | None = None,
    bwrap: Path = Path("/usr/bin/bwrap"),
) -> dict[str, object]:
    """Run a frozen query corpus with one trusted projection materialization.

    Each SQL statement is independently AST-gated and independently interrupted after the
    same untrusted per-query timeout.  Only the deterministic projection materialization is
    shared across the batch.
    """

    limits = limits or QueryLimits()
    if not queries or len(queries) > 128:
        raise FitBenchError("DuckDB batch must contain 1..128 queries")
    seen: set[str] = set()
    request_queries: list[dict[str, str]] = []
    for query_id, sql in queries:
        if not isinstance(query_id, str) or not query_id or query_id in seen:
            raise FitBenchError("DuckDB batch query IDs must be unique non-empty strings")
        if not isinstance(sql, str) or not sql.strip():
            raise QueryRejected("DuckDB batch SQL must be non-empty")
        seen.add(query_id)
        request_queries.append({"query_id": query_id, "sql": sql})
    process_timeout_ms = duckdb_process_timeout_ms(limits, query_count=len(request_queries))
    payload = _run_duckdb_worker_sandboxed(
        projection_bytes,
        {"queries": request_queries},
        duckdb_python=duckdb_python,
        process_timeout_ms=process_timeout_ms,
        bwrap=bwrap,
        query_count=len(request_queries),
        limits=limits,
    )
    if payload.get("format") != "canario.duckdb_query_batch_result.v1" or payload.get("engine") != "duckdb":
        raise FitBenchError("DuckDB worker returned unexpected batch format")
    raw_results = payload.get("queries")
    if not isinstance(raw_results, list) or len(raw_results) != len(request_queries):
        raise FitBenchError("DuckDB worker returned incomplete batch")
    returned_ids: list[str] = []
    for raw in raw_results:
        if not isinstance(raw, dict) or not isinstance(raw.get("query_id"), str):
            raise FitBenchError("DuckDB worker returned malformed batch entry")
        result = raw.get("result")
        if not isinstance(result, dict) or result.get("format") != RESULT_FORMAT:
            raise FitBenchError("DuckDB worker returned malformed batch query result")
        returned_ids.append(str(raw["query_id"]))
    if returned_ids != [item["query_id"] for item in request_queries]:
        raise FitBenchError("DuckDB worker changed batch query order/identity")
    return payload

def compare_results(left: Mapping[str, object], right: Mapping[str, object]) -> dict[str, object]:
    """Compare deterministic engine results without conflating engine timing/runtime."""

    left_columns = left.get("columns")
    right_columns = right.get("columns")
    left_rows = left.get("rows")
    right_rows = right.get("rows")
    if left_columns != right_columns:
        return {"agree": False, "reason": "columns", "left": left_columns, "right": right_columns}
    if not isinstance(left_rows, list) or not isinstance(right_rows, list):
        raise FitBenchError("query result rows missing")
    if len(left_rows) != len(right_rows):
        return {"agree": False, "reason": "row_count", "left": len(left_rows), "right": len(right_rows)}
    divergences: list[dict[str, object]] = []
    for row_index, (left_row, right_row) in enumerate(zip(left_rows, right_rows, strict=True)):
        if not isinstance(left_row, list) or not isinstance(right_row, list) or len(left_row) != len(right_row):
            divergences.append({"row": row_index, "reason": "row_shape"})
            continue
        for column_index, (left_value, right_value) in enumerate(zip(left_row, right_row, strict=True)):
            if left_value == right_value:
                continue
            if isinstance(left_value, dict) and isinstance(right_value, dict):
                if left_value.get("type") in {"integer", "number"} and right_value.get("type") in {"integer", "number"}:
                    try:
                        left_decimal = Decimal(str(left_value.get("value")))
                        right_decimal = Decimal(str(right_value.get("value")))
                    except InvalidOperation:
                        pass
                    else:
                        tolerance = max(Decimal("1e-9"), abs(left_decimal) * Decimal("1e-12"))
                        if abs(left_decimal - right_decimal) <= tolerance:
                            continue
            divergences.append(
                {
                    "row": row_index,
                    "column": column_index,
                    "left": left_value,
                    "right": right_value,
                }
            )
    return {"agree": not divergences, "divergences": divergences}


def evaluate_case_result(case: Mapping[str, object], result: Mapping[str, object]) -> dict[str, object]:
    """Evaluate one executable deterministic corpus case against its independent oracle.

    This compares only the deterministic columns/typed rows. Engine timing, process
    identity and other runtime observations are deliberately excluded from correctness.
    """

    case_id = case.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        raise FitBenchError("query case requires case_id")
    sql = case.get("portable_sql")
    if not isinstance(sql, str) or not sql.strip():
        raise FitBenchError(f"query case {case_id} is not executable")
    expected = case.get("expected")
    if not isinstance(expected, dict):
        raise FitBenchError(f"query case {case_id} lacks independent expected result")
    expected_columns = expected.get("columns")
    expected_rows = expected.get("rows")
    if not isinstance(expected_columns, list) or not isinstance(expected_rows, list):
        raise FitBenchError(f"query case {case_id} expected result is malformed")
    if expected.get("row_count") != len(expected_rows):
        raise FitBenchError(f"query case {case_id} expected row_count is inconsistent")
    comparison = compare_results(expected, result)
    passed = bool(comparison.get("agree"))
    return {
        "case_id": case_id,
        "kind": case.get("kind"),
        "passed": passed,
        "comparison": comparison,
        "expected_row_count": len(expected_rows),
        "actual_row_count": result.get("row_count"),
        "actual_result_sha256": result.get("result_sha256"),
    }


def run_query_corpus(
    corpus: Mapping[str, object],
    projection_bytes: bytes,
    *,
    engine: str,
    limits: QueryLimits | None = None,
    duckdb_python: Path | None = None,
    bwrap: Path = Path("/usr/bin/bwrap"),
) -> dict[str, object]:
    """Execute every deterministic SQL case without using engine output as oracle.

    SQLite keeps its per-query disposable executor. DuckDB intentionally runs the frozen
    executable corpus in one sandbox process so the trusted neutral projection is
    materialized once; every SQL statement still receives an independent AST gate and
    independent ``timeout_ms`` watchdog inside that isolated worker.
    """

    validation = validate_query_corpus(corpus, projection_bytes)
    if engine not in {"sqlite", "duckdb"}:
        raise FitBenchError("engine must be sqlite or duckdb")
    if engine == "duckdb" and duckdb_python is None:
        raise FitBenchError("DuckDB corpus run requires dedicated duckdb_python")
    limits = limits or QueryLimits()
    raw_cases = corpus.get("cases")
    assert isinstance(raw_cases, list)

    duckdb_results: dict[str, dict[str, object]] = {}
    engine_session: dict[str, object] | None = None
    if engine == "duckdb":
        executable_queries: list[tuple[str, str]] = []
        for raw_case in raw_cases:
            assert isinstance(raw_case, dict)
            sql = raw_case.get("portable_sql")
            if isinstance(sql, str) and sql.strip():
                executable_queries.append((str(raw_case["case_id"]), sql))
        if executable_queries:
            assert duckdb_python is not None
            try:
                batch = execute_duckdb_batch_sandboxed(
                    projection_bytes,
                    executable_queries,
                    duckdb_python=duckdb_python,
                    limits=limits,
                    bwrap=bwrap,
                )
            except (FitBenchError, QueryRejected) as exc:
                duckdb_results = {
                    case_id: {
                        "_execution_error_type": type(exc).__name__,
                        "_execution_error": str(exc),
                    }
                    for case_id, _sql in executable_queries
                }
                engine_session = {
                    "status": "failed_before_complete_batch",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "query_count": len(executable_queries),
                }
            else:
                raw_batch_results = batch.get("queries")
                assert isinstance(raw_batch_results, list)
                for item in raw_batch_results:
                    assert isinstance(item, dict)
                    query_id = str(item["query_id"])
                    result = item.get("result")
                    assert isinstance(result, dict)
                    duckdb_results[query_id] = result
                engine_session = {
                    "status": "completed",
                    "runtime": batch.get("runtime"),
                    "security": batch.get("security"),
                    "bootstrap_duration_ms": batch.get("bootstrap_duration_ms"),
                    "projection_materializations": batch.get("projection_materializations"),
                    "duration_ms": batch.get("duration_ms"),
                    "query_count": batch.get("query_count"),
                }

    records: list[dict[str, object]] = []
    passed = 0
    failed = 0
    semantic_only = 0
    for raw_case in raw_cases:
        assert isinstance(raw_case, dict)
        case_id = str(raw_case["case_id"])
        sql = raw_case.get("portable_sql")
        if not isinstance(sql, str) or not sql.strip():
            semantic_only += 1
            records.append(
                {
                    "case_id": case_id,
                    "kind": raw_case.get("kind"),
                    "status": "not_executed_by_design",
                    "expected_semantics": raw_case.get("expected_semantics"),
                    "execution_failure_expected": raw_case.get("execution_failure_expected"),
                    "reason": raw_case.get("reason"),
                }
            )
            continue
        try:
            if engine == "sqlite":
                result = execute_sqlite(projection_bytes, sql, limits=limits)
            else:
                result = duckdb_results.get(case_id)
                if not isinstance(result, dict):
                    raise FitBenchError("DuckDB batch omitted executable case")
                if "_execution_error" in result:
                    raise QueryRejected(str(result["_execution_error"]))
            evaluation = evaluate_case_result(raw_case, result)
        except (FitBenchError, QueryRejected) as exc:
            failed += 1
            records.append(
                {
                    "case_id": case_id,
                    "kind": raw_case.get("kind"),
                    "status": "execution_failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue
        if evaluation["passed"]:
            passed += 1
            status = "passed"
        else:
            failed += 1
            status = "oracle_mismatch"
        records.append(
            {
                "case_id": case_id,
                "kind": raw_case.get("kind"),
                "status": status,
                "evaluation": evaluation,
                "result": result,
            }
        )
    executable = passed + failed
    payload = {
        "format": "canario.structured_query_corpus_run.v1",
        "engine": engine,
        "projection_sha256": _sha256_bytes(projection_bytes),
        "query_corpus_projection_sha256": corpus.get("projection_sha256"),
        "case_family": corpus.get("case_family"),
        "validation": validation,
        "summary": {
            "total_cases": len(raw_cases),
            "executable_cases": executable,
            "passed": passed,
            "failed": failed,
            "semantic_only": semantic_only,
            "all_executable_passed": failed == 0,
        },
        "cases": records,
    }
    if engine_session is not None:
        payload["engine_session"] = engine_session
    return payload

def compare_corpus_runs(left: Mapping[str, object], right: Mapping[str, object]) -> dict[str, object]:
    """Compare matching successful cases from two engine run reports."""

    if left.get("format") != "canario.structured_query_corpus_run.v1" or right.get("format") != "canario.structured_query_corpus_run.v1":
        raise FitBenchError("corpus run format mismatch")
    if left.get("projection_sha256") != right.get("projection_sha256"):
        raise FitBenchError("cannot compare corpus runs from different projections")
    left_cases = left.get("cases")
    right_cases = right.get("cases")
    if not isinstance(left_cases, list) or not isinstance(right_cases, list):
        raise FitBenchError("corpus run cases missing")
    left_by_id = {
        str(item.get("case_id")): item
        for item in left_cases
        if isinstance(item, dict) and item.get("case_id") is not None
    }
    right_by_id = {
        str(item.get("case_id")): item
        for item in right_cases
        if isinstance(item, dict) and item.get("case_id") is not None
    }
    if set(left_by_id) != set(right_by_id):
        raise FitBenchError("corpus runs have different case IDs")
    comparisons: list[dict[str, object]] = []
    disagreements = 0
    jointly_executed = 0
    for case_id in sorted(left_by_id):
        lcase = left_by_id[case_id]
        rcase = right_by_id[case_id]
        lresult = lcase.get("result")
        rresult = rcase.get("result")
        if isinstance(lresult, dict) and isinstance(rresult, dict):
            jointly_executed += 1
            comparison = compare_results(lresult, rresult)
            agree = bool(comparison.get("agree"))
            if not agree:
                disagreements += 1
            comparisons.append(
                {
                    "case_id": case_id,
                    "status": "compared",
                    "agree": agree,
                    "comparison": comparison,
                }
            )
        else:
            comparisons.append(
                {
                    "case_id": case_id,
                    "status": "not_jointly_executed",
                    "left_status": lcase.get("status"),
                    "right_status": rcase.get("status"),
                }
            )
    return {
        "format": "canario.structured_query_cross_engine_comparison.v1",
        "projection_sha256": left.get("projection_sha256"),
        "left_engine": left.get("engine"),
        "right_engine": right.get("engine"),
        "jointly_executed": jointly_executed,
        "disagreements": disagreements,
        "all_joint_results_agree": disagreements == 0,
        "cases": comparisons,
    }


def _external_value(raw: str, kind: str) -> dict[str, object]:
    if raw == "":
        return {"kind": "blank"}
    if kind in {"string", "datetime"}:
        return {"kind": kind, "text": raw}
    if kind == "integer":
        try:
            return {"kind": kind, "decimal": str(int(raw))}
        except ValueError as exc:
            raise FitBenchError(f"invalid integer external value {raw!r}") from exc
    if kind == "number":
        try:
            return {"kind": kind, "decimal": _canonical_decimal(Decimal(raw))}
        except InvalidOperation as exc:
            raise FitBenchError(f"invalid decimal external value {raw!r}") from exc
    if kind == "boolean":
        lowered = raw.strip().lower()
        if lowered not in {"true", "false", "1", "0"}:
            raise FitBenchError(f"invalid boolean external value {raw!r}")
        return {"kind": kind, "value": lowered in {"true", "1"}}
    raise FitBenchError(f"unsupported external kind {kind!r}")


def build_external_csv_projection(source_bytes: bytes, spec: Mapping[str, object]) -> tuple[bytes, dict[str, object]]:
    """Normalize an external CSV lane using an explicit, versioned source spec.

    This is benchmark-only normalization.  It is not a Canario Representation contract.
    """

    if spec.get("format") != EXTERNAL_CSV_SPEC_FORMAT:
        raise FitBenchError(f"external CSV spec must be {EXTERNAL_CSV_SPEC_FORMAT}")
    dataset_id = spec.get("dataset_id")
    expected_source_sha256 = spec.get("expected_source_sha256")
    expected_row_count = spec.get("expected_row_count")
    encoding = spec.get("encoding")
    delimiter = spec.get("delimiter", ",")
    has_header = spec.get("has_header")
    raw_columns = spec.get("columns")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise FitBenchError("external CSV spec requires dataset_id")
    if expected_source_sha256 is not None:
        if not isinstance(expected_source_sha256, str) or len(expected_source_sha256) != 64:
            raise FitBenchError("external CSV expected_source_sha256 must be a SHA-256 hex string")
        if _sha256_bytes(source_bytes) != expected_source_sha256:
            raise FitBenchError("external CSV source SHA-256 does not match frozen source spec")
    if expected_row_count is not None and (not isinstance(expected_row_count, int) or expected_row_count < 0):
        raise FitBenchError("external CSV expected_row_count must be a non-negative integer")
    if not isinstance(encoding, str) or not encoding:
        raise FitBenchError("external CSV spec requires explicit encoding")
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise FitBenchError("external CSV spec delimiter must be one character")
    if not isinstance(has_header, bool):
        raise FitBenchError("external CSV spec requires boolean has_header")
    if not isinstance(raw_columns, list) or not raw_columns:
        raise FitBenchError("external CSV spec requires columns")
    columns = [
        ExternalCsvColumn(str(item["name"]), int(item["source_index"]), str(item.get("kind", "string")))
        for item in raw_columns
        if isinstance(item, dict)
    ]
    if len(columns) != len(raw_columns):
        raise FitBenchError("external CSV spec columns malformed")
    try:
        text = source_bytes.decode(encoding)
    except (UnicodeDecodeError, LookupError) as exc:
        raise FitBenchError("external CSV does not match explicit encoding") from exc
    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))
    if not rows:
        raise FitBenchError("external CSV is empty")
    header: list[str] | None = rows[0] if has_header else None
    expected_header = spec.get("expected_header")
    if expected_header is not None:
        if not isinstance(expected_header, list) or not all(isinstance(item, str) for item in expected_header):
            raise FitBenchError("external CSV expected_header must be a string list")
        if header != expected_header:
            raise FitBenchError("external CSV header does not match frozen source spec")
    data_rows = rows[1:] if has_header else rows
    if expected_row_count is not None and len(data_rows) != expected_row_count:
        raise FitBenchError("external CSV row count does not match frozen source spec")
    max_source_index = max(column.source_index for column in columns)
    normalized_cells: list[dict[str, object]] = []
    for row_index, row in enumerate(data_rows, start=1):
        if len(row) <= max_source_index:
            raise FitBenchError(f"external CSV row {row_index} is too short")
        for projected_column, column in enumerate(columns, start=1):
            normalized_cells.append(
                {
                    "sheet_ordinal": 1,
                    "sheet_name": dataset_id,
                    "row": row_index,
                    "column": projected_column,
                    "address": f"R{row_index}C{projected_column}",
                    "data_type": f"external:{column.kind}",
                    "number_format": "external",
                    "value": _external_value(row[column.source_index], column.kind),
                }
            )
    transform_spec = {
        "format": spec.get("format"),
        "dataset_id": dataset_id,
        "encoding": encoding,
        "delimiter": delimiter,
        "has_header": has_header,
        "columns": [
            {"name": column.name, "source_index": column.source_index, "kind": column.kind}
            for column in columns
        ],
    }
    validation_spec = {
        "expected_header": expected_header,
        "expected_source_sha256": expected_source_sha256,
        "expected_row_count": expected_row_count,
    }
    transform_spec_sha256 = _sha256_bytes(_canonical_json_bytes(transform_spec))
    validation_spec_sha256 = _sha256_bytes(_canonical_json_bytes(validation_spec))

    projection = {
        "format": PROJECTION_FORMAT,
        "source_representation_sha256": _sha256_bytes(source_bytes),
        "source_representation_format": "external_csv",
        "external_dataset_id": dataset_id,
        "external_transform_spec_sha256": transform_spec_sha256,
        "external_header": header,
        "external_columns": [
            {"projected_column": index, "name": column.name, "kind": column.kind, "source_index": column.source_index}
            for index, column in enumerate(columns, start=1)
        ],
        "sheets": [
            {
                "ordinal": 1,
                "name": dataset_id,
                "state": "visible",
                "max_row": len(data_rows),
                "max_column": len(columns),
                "merged_ranges": [],
            }
        ],
        "cells": normalized_cells,
    }
    projection_bytes = _canonical_json_bytes(projection)
    manifest = projection_manifest(projection_bytes)
    manifest["external_transform_spec_sha256"] = transform_spec_sha256
    manifest["external_validation_spec_sha256"] = validation_spec_sha256
    manifest["external_expected_source_sha256"] = expected_source_sha256
    manifest["external_expected_row_count"] = expected_row_count
    return projection_bytes, manifest


def oracle_rows(projection_bytes: bytes, *, sheet_ordinal: int) -> list[list[dict[str, object]]]:
    """Return exact normalized rows for an independent Python/Decimal oracle."""

    projection = load_projection(projection_bytes)
    sheets = _projection_sheet_map(projection)
    if sheet_ordinal not in sheets:
        raise FitBenchError("unknown oracle sheet")
    sheet = sheets[sheet_ordinal]
    cells_by_row = _projection_cells_by_sheet_row(projection)
    result: list[list[dict[str, object]]] = []
    for row in range(1, int(sheet["max_row"]) + 1):
        row_cells = cells_by_row[(sheet_ordinal, row)]
        result.append([dict(row_cells[column]) for column in range(1, int(sheet["max_column"]) + 1)])
    return result


def oracle_decimal_sum(cells: Iterable[Mapping[str, object]]) -> Decimal:
    total = Decimal(0)
    for cell in cells:
        value = cell.get("value")
        if not isinstance(value, dict):
            raise FitBenchError("oracle cell lacks normalized value")
        kind = value.get("kind")
        if kind == "integer" or kind == "number":
            total += Decimal(str(value["decimal"]))
    return total


def _result_value_from_oracle(value: object) -> dict[str, object]:
    return _canonical_result_value(value)


def _oracle_expected(columns: Sequence[str], rows: Sequence[Sequence[object]]) -> dict[str, object]:
    return {
        "columns": list(columns),
        "rows": [[_result_value_from_oracle(value) for value in row] for row in rows],
        "row_count": len(rows),
    }


def _numeric_cells_for_sheet(
    projection: Mapping[str, object], sheet_ordinal: int
) -> dict[int, list[dict[str, object]]]:
    cells = projection.get("cells")
    if not isinstance(cells, list):
        raise FitBenchError("projection cells missing")
    by_column: dict[int, list[dict[str, object]]] = {}
    for cell in cells:
        if not isinstance(cell, dict) or int(cell["sheet_ordinal"]) != sheet_ordinal:
            continue
        value = cell.get("value")
        if isinstance(value, dict) and value.get("kind") in {"integer", "number"}:
            by_column.setdefault(int(cell["column"]), []).append(cell)
    return by_column


def _string_cells_for_sheet(
    projection: Mapping[str, object], sheet_ordinal: int
) -> dict[int, list[dict[str, object]]]:
    cells = projection.get("cells")
    if not isinstance(cells, list):
        raise FitBenchError("projection cells missing")
    by_column: dict[int, list[dict[str, object]]] = {}
    for cell in cells:
        if not isinstance(cell, dict) or int(cell["sheet_ordinal"]) != sheet_ordinal:
            continue
        value = cell.get("value")
        if isinstance(value, dict) and value.get("kind") == "string" and str(value.get("text", "")):
            by_column.setdefault(int(cell["column"]), []).append(cell)
    return by_column


def _cell_decimal(cell: Mapping[str, object]) -> Decimal:
    value = cell.get("value")
    if not isinstance(value, dict) or value.get("kind") not in {"integer", "number"}:
        raise FitBenchError("cell is not numeric")
    return Decimal(str(value["decimal"]))


def _lineage(cell: Mapping[str, object]) -> dict[str, object]:
    return {
        "sheet_ordinal": int(cell["sheet_ordinal"]),
        "sheet_name": str(cell["sheet_name"]),
        "row": int(cell["row"]),
        "column": int(cell["column"]),
        "address": str(cell["address"]),
    }


def build_esparza_query_corpus(projection_bytes: bytes) -> dict[str, object]:
    """Create a deterministic, engine-independent query corpus for the civic workbook.

    The generator chooses structural/numeric axes mechanically from the exact projection.
    It does not classify municipal semantics or use engine output as the oracle.
    """

    projection = load_projection(projection_bytes)
    sheets = _projection_sheet_map(projection)
    if not sheets:
        raise FitBenchError("Esparza corpus requires sheets")

    # Choose the sheet/column with the largest numeric population.  This is deterministic
    # and keeps the bench useful if the fixture is regenerated without hard-coding labels.
    numeric_candidates: list[tuple[int, int, int, list[dict[str, object]]]] = []
    for sheet_ordinal in sorted(sheets):
        for column, cells in _numeric_cells_for_sheet(projection, sheet_ordinal).items():
            numeric_candidates.append((len(cells), -sheet_ordinal, -column, cells))
    if not numeric_candidates:
        raise FitBenchError("Esparza projection contains no numeric cells")
    _, neg_sheet, neg_numeric_column, numeric_cells = max(numeric_candidates, key=lambda item: item[:3])
    sheet_ordinal = -neg_sheet
    numeric_column = -neg_numeric_column
    numeric_cells = sorted(numeric_cells, key=lambda cell: int(cell["row"]))
    table = _sheet_table_name(sheet_ordinal)
    numeric_prefix = f"c{numeric_column}"

    string_candidates = _string_cells_for_sheet(projection, sheet_ordinal)
    if not string_candidates:
        raise FitBenchError("Esparza projection contains no string cells on numeric analysis sheet")
    # Prefer the string column with the most repeated nonblank values; repeated prefixes and
    # labels exercise grouping without declaring what a column means.
    string_scores: list[tuple[int, int, int, list[dict[str, object]]]] = []
    for column, cells in string_candidates.items():
        texts = [str(cell["value"]["text"]) for cell in cells]
        repeats = len(texts) - len(set(texts))
        string_scores.append((repeats, len(cells), -column, cells))
    _, _, neg_string_column, string_cells = max(string_scores, key=lambda item: item[:3])
    string_column = -neg_string_column
    string_prefix = f"c{string_column}"

    first_numeric = numeric_cells[0]
    first_row = int(first_numeric["row"])
    first_value = _cell_decimal(first_numeric)
    numeric_values = [_cell_decimal(cell) for cell in numeric_cells]
    sorted_values = sorted(numeric_values)
    threshold = sorted_values[len(sorted_values) // 2]
    exact_sum = sum(numeric_values, Decimal(0))
    absolute_sum = sum((abs(value) for value in numeric_values), Decimal(0))
    composition = absolute_sum - abs(exact_sum)

    row_map = _projection_cells_by_sheet_row(projection)
    lookup_row = row_map[(sheet_ordinal, first_row)]
    lookup_text = _cell_text(lookup_row[string_column]["value"])

    # Oracle for Q2 filter.
    filtered = [
        (int(cell["row"]), _cell_decimal(cell))
        for cell in numeric_cells
        if _cell_decimal(cell) <= threshold
    ]

    # Oracle for Q4 grouping by first code/label character.  This is structural exercise,
    # not a semantic claim about the category system.
    group_counts: dict[str, int] = {}
    for cell in string_cells:
        text = str(cell["value"]["text"])
        if text:
            group_counts[text[0]] = group_counts.get(text[0], 0) + 1
    grouped = sorted(group_counts.items(), key=lambda item: item[0])

    top_rows = sorted(
        ((int(cell["row"]), _cell_decimal(cell)) for cell in numeric_cells),
        key=lambda item: (-item[1], item[0]),
    )[:3]
    ranked_rows = sorted(
        ((int(cell["row"]), _cell_decimal(cell)) for cell in numeric_cells),
        key=lambda item: (-item[1], item[0]),
    )[:5]
    rank_output: list[tuple[int, Decimal, int]] = []
    previous: Decimal | None = None
    rank = 0
    for index, (row, value) in enumerate(ranked_rows, start=1):
        if previous is None or value != previous:
            rank = index
        rank_output.append((row, value, rank))
        previous = value

    # Find a real cross-sheet overlapping string key, preferring low ordinals/columns.
    cross: tuple[int, int, int, int, str] | None = None
    string_sets: dict[tuple[int, int], set[str]] = {}
    for candidate_sheet in sorted(sheets):
        for column, cells in _string_cells_for_sheet(projection, candidate_sheet).items():
            string_sets[(candidate_sheet, column)] = {str(cell["value"]["text"]) for cell in cells}
    keys = sorted(string_sets)
    for left_index, (left_sheet, left_column) in enumerate(keys):
        for right_sheet, right_column in keys[left_index + 1 :]:
            if left_sheet == right_sheet:
                continue
            overlap = sorted(string_sets[(left_sheet, left_column)] & string_sets[(right_sheet, right_column)])
            if overlap:
                cross = (left_sheet, left_column, right_sheet, right_column, overlap[0])
                break
        if cross is not None:
            break

    cases: list[dict[str, object]] = [
        {
            "case_id": "ESP-Q1-LOOKUP",
            "kind": "explicit_lookup",
            "question": "Return the selected row's string-axis value and exact numeric value.",
            "portable_sql": (
                f"SELECT {string_prefix}_text AS label,{numeric_prefix}_number AS value "
                f"FROM {table} WHERE row_index={first_row}"
            ),
            "expected": _oracle_expected(["label", "value"], [[lookup_text, first_value]]),
            "required_evidence": [_lineage(lookup_row[string_column]), _lineage(first_numeric)],
            "expected_semantics": "query_only",
            "execution_failure_expected": False,
        },
        {
            "case_id": "ESP-Q2-FILTER",
            "kind": "filter",
            "question": "Return rows on the numeric axis at or below the independently computed median threshold.",
            "portable_sql": (
                f"SELECT row_index,{numeric_prefix}_number AS value FROM {table} "
                f"WHERE {numeric_prefix}_number IS NOT NULL AND {numeric_prefix}_number<={threshold} "
                "ORDER BY row_index"
            ),
            "expected": _oracle_expected(["row_index", "value"], [[row, value] for row, value in filtered]),
            "required_evidence": [_lineage(cell) for cell in numeric_cells],
            "expected_semantics": "query_only",
            "execution_failure_expected": False,
        },
        {
            "case_id": "ESP-Q3-AGGREGATE",
            "kind": "aggregation",
            "question": "Sum the numeric axis over the bounded sheet.",
            "portable_sql": f"SELECT SUM({numeric_prefix}_number) AS total FROM {table}",
            "expected": _oracle_expected(["total"], [[exact_sum]]),
            "required_evidence": [_lineage(cell) for cell in numeric_cells],
            "expected_semantics": "query_only",
            "execution_failure_expected": False,
        },
        {
            "case_id": "ESP-Q4-GROUP",
            "kind": "grouping",
            "question": "Group nonblank string-axis rows by their first character.",
            "portable_sql": (
                f"SELECT substr({string_prefix}_text,1,1) AS prefix,COUNT(*) AS n FROM {table} "
                f"WHERE {string_prefix}_text IS NOT NULL AND {string_prefix}_text<>'' "
                "GROUP BY prefix ORDER BY prefix"
            ),
            "expected": _oracle_expected(["prefix", "n"], [[prefix, count] for prefix, count in grouped]),
            "required_evidence": [_lineage(cell) for cell in string_cells],
            "expected_semantics": "query_only",
            "execution_failure_expected": False,
        },
        {
            "case_id": "ESP-Q5-TOPK",
            "kind": "ordering_top_k",
            "question": "Return the three greatest numeric-axis rows with deterministic tie breaking.",
            "portable_sql": (
                f"SELECT row_index,{numeric_prefix}_number AS value FROM {table} "
                f"WHERE {numeric_prefix}_number IS NOT NULL ORDER BY value DESC,row_index ASC LIMIT 3"
            ),
            "expected": _oracle_expected(["row_index", "value"], [[row, value] for row, value in top_rows]),
            "required_evidence": [_lineage(cell) for cell in numeric_cells],
            "expected_semantics": "query_only",
            "execution_failure_expected": False,
        },
        {
            "case_id": "ESP-Q6-WINDOW",
            "kind": "window_rank",
            "question": "Rank numeric rows using a window function and return the top five.",
            "portable_sql": (
                f"SELECT row_index,value,rnk FROM (SELECT row_index,{numeric_prefix}_number AS value,"
                f"RANK() OVER (ORDER BY {numeric_prefix}_number DESC) AS rnk FROM {table} "
                f"WHERE {numeric_prefix}_number IS NOT NULL) ORDER BY value DESC,row_index ASC LIMIT 5"
            ),
            "expected": _oracle_expected(
                ["row_index", "value", "rnk"],
                [[row, value, rank_value] for row, value, rank_value in rank_output],
            ),
            "required_evidence": [_lineage(cell) for cell in numeric_cells],
            "expected_semantics": "query_only",
            "execution_failure_expected": False,
        },
        {
            "case_id": "ESP-Q7-COMPOSITION",
            "kind": "numerical_composition",
            "question": "Compute absolute gross movement minus absolute net movement on the numeric axis.",
            "portable_sql": (
                f"SELECT SUM(ABS({numeric_prefix}_number))-ABS(SUM({numeric_prefix}_number)) AS cancellation "
                f"FROM {table}"
            ),
            "expected": _oracle_expected(["cancellation"], [[composition]]),
            "required_evidence": [_lineage(cell) for cell in numeric_cells],
            "expected_semantics": "query_only",
            "execution_failure_expected": False,
        },
    ]
    if cross is not None:
        left_sheet, left_column, right_sheet, right_column, overlap_value = cross
        left_table = _sheet_table_name(left_sheet)
        right_table = _sheet_table_name(right_sheet)
        left_prefix = f"c{left_column}"
        right_prefix = f"c{right_column}"
        left_matching_cells = [
            cell
            for cell in _string_cells_for_sheet(projection, left_sheet)[left_column]
            if str(cell["value"]["text"]) == overlap_value
        ]
        right_matching_cells = [
            cell
            for cell in _string_cells_for_sheet(projection, right_sheet)[right_column]
            if str(cell["value"]["text"]) == overlap_value
        ]
        left_rows = [int(cell["row"]) for cell in left_matching_cells]
        right_rows = [int(cell["row"]) for cell in right_matching_cells]
        joined = [[left_row, right_row, overlap_value] for left_row in left_rows for right_row in right_rows]
        join_evidence = [
            *(_lineage(cell) for cell in left_matching_cells),
            *(_lineage(cell) for cell in right_matching_cells),
        ]
        cases.append(
            {
                "case_id": "ESP-Q8-CROSS-SHEET",
                "kind": "cross_sheet_join",
                "question": "Join two sheets on an exact overlapping represented string value.",
                "portable_sql": (
                    f"SELECT l.row_index AS left_row,r.row_index AS right_row,l.{left_prefix}_text AS key "
                    f"FROM {left_table} l JOIN {right_table} r ON l.{left_prefix}_text=r.{right_prefix}_text "
                    f"WHERE l.{left_prefix}_text={_sql_string_literal(overlap_value)} ORDER BY left_row,right_row"
                ),
                "expected": _oracle_expected(["left_row", "right_row", "key"], joined),
                "required_evidence": join_evidence,
                "expected_semantics": "query_only",
                "execution_failure_expected": False,
            }
        )
    else:
        cases.append(
            {
                "case_id": "ESP-Q8-CROSS-SHEET",
                "kind": "cross_sheet_join",
                "question": "No exact cross-sheet string overlap exists in this projection; cross-sheet composition must be exercised in an external lane.",
                "portable_sql": None,
                "expected": None,
                "required_evidence": [],
                "expected_semantics": "insufficient_evidence",
                "execution_failure_expected": False,
                "reason": "fixture_has_no_mechanical_cross_sheet_join_key",
            }
        )

    sentinel = f"__CANARIO_ABSENT_{str(projection['source_representation_sha256'])[:12]}__"
    union_parts = []
    for candidate_sheet, sheet in sorted(sheets.items()):
        for column in range(1, int(sheet["max_column"]) + 1):
            union_parts.append(
                f"SELECT c{column}_text AS value FROM {_sheet_table_name(candidate_sheet)}"
            )
    cases.extend(
        [
            {
                "case_id": "ESP-Q9-BOUNDED-ABSENCE",
                "kind": "bounded_absence",
                "question": "Is the deterministic sentinel absent from every represented cell in this complete workbook projection?",
                "portable_sql": (
                    "SELECT COUNT(*) AS matches FROM ("
                    + " UNION ALL ".join(union_parts)
                    + f") q WHERE value={_sql_string_literal(sentinel)}"
                ),
                "expected": _oracle_expected(["matches"], [[0]]),
                "required_evidence": [],
                "bounded_scope": {
                    "scope": "complete retained structured-table Representation",
                    "claim_strength": "not_found_in_bounded_scope",
                    "does_not_exist_in_reality": False,
                },
                "expected_semantics": "supported",
                "execution_failure_expected": False,
            },
            {
                "case_id": "ESP-Q10-INSUFFICIENT",
                "kind": "insufficient_evidence",
                "question": "Does this workbook prove that no other municipal budget modification exists outside this retained workbook?",
                "portable_sql": None,
                "expected": None,
                "required_evidence": [],
                "bounded_scope": {
                    "scope": "one retained workbook",
                    "inventory_completeness": "not_established",
                },
                "expected_semantics": "insufficient_evidence",
                "execution_failure_expected": False,
                "reason": "one workbook has no authority to prove global absence",
            },
        ]
    )
    return {
        "format": QUERY_CORPUS_FORMAT,
        "case_family": "CR-ESPARZA-BUDGET-STRUCTURED-FIT",
        "projection_sha256": _sha256_bytes(projection_bytes),
        "source_representation_sha256": projection["source_representation_sha256"],
        "oracle": "independent_python_projection_oracle",
        "engine_outputs_used_as_oracle": False,
        "analysis_axis": {
            "sheet_ordinal": sheet_ordinal,
            "numeric_column": numeric_column,
            "string_column": string_column,
        },
        "cases": cases,
    }


def planner_verifier_cases_from_corpus(corpus: Mapping[str, object]) -> dict[str, object]:
    cases = corpus.get("cases")
    if not isinstance(cases, list):
        raise FitBenchError("query corpus cases missing")
    handoff: list[dict[str, object]] = []
    for case in cases:
        if not isinstance(case, dict):
            raise FitBenchError("query corpus case malformed")
        handoff.append(
            {
                "case_id": case["case_id"],
                "question": case["question"],
                "projection_sha256": corpus["projection_sha256"],
                "source_authority": case.get("bounded_scope", {"scope": "retained_projection"}),
                "expected_semantics": case["expected_semantics"],
                "expected": case.get("expected"),
                "expected_decimal": case.get("expected_decimal"),
                "required_evidence": case.get("required_evidence", []),
                "resource_budget": {
                    "max_rows": DEFAULT_MAX_ROWS,
                    "max_bytes": DEFAULT_MAX_BYTES,
                    "timeout_ms": DEFAULT_TIMEOUT_MS,
                },
            }
        )
    return {
        "format": PLANNER_CASES_FORMAT,
        "source_query_corpus_format": corpus.get("format"),
        "projection_sha256": corpus.get("projection_sha256"),
        "cases": handoff,
    }


def validate_query_corpus(corpus: Mapping[str, object], projection_bytes: bytes) -> dict[str, object]:
    if corpus.get("format") != QUERY_CORPUS_FORMAT:
        raise FitBenchError(f"query corpus must be {QUERY_CORPUS_FORMAT}")
    projection_sha = _sha256_bytes(projection_bytes)
    if corpus.get("projection_sha256") != projection_sha:
        raise FitBenchError("query corpus projection identity mismatch")
    projection = load_projection(projection_bytes)
    raw_projection_cells = projection.get("cells")
    if not isinstance(raw_projection_cells, list):
        raise FitBenchError("projection cells missing")
    evidence_index: dict[tuple[int, int, int], Mapping[str, object]] = {}
    for raw_cell in raw_projection_cells:
        if not isinstance(raw_cell, dict):
            raise FitBenchError("projection cell malformed")
        evidence_index[(int(raw_cell["sheet_ordinal"]), int(raw_cell["row"]), int(raw_cell["column"]))] = raw_cell

    cases = corpus.get("cases")
    if not isinstance(cases, list) or not cases:
        raise FitBenchError("query corpus requires cases")
    ids: set[str] = set()
    executable_count = 0
    semantic_only_count = 0
    evidence_ref_count = 0
    for case in cases:
        if not isinstance(case, dict):
            raise FitBenchError("query corpus case must be object")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise FitBenchError("query corpus case IDs must be non-empty and unique")
        ids.add(case_id)
        expected_semantics = case.get("expected_semantics")
        if expected_semantics not in {"supported", "contradicted", "insufficient_evidence", "query_only"}:
            raise FitBenchError(f"case {case_id} has invalid expected_semantics")
        if expected_semantics == "insufficient_evidence" and case.get("execution_failure_expected") is True:
            raise FitBenchError("insufficient evidence cannot be encoded as execution failure")

        sql = case.get("portable_sql")
        if isinstance(sql, str) and sql.strip():
            executable_count += 1
            expected = case.get("expected")
            if not isinstance(expected, dict):
                raise FitBenchError(f"executable case {case_id} lacks independent expected result")
            expected_columns = expected.get("columns")
            expected_rows = expected.get("rows")
            if not isinstance(expected_columns, list) or not all(isinstance(item, str) for item in expected_columns):
                raise FitBenchError(f"case {case_id} expected columns malformed")
            if not isinstance(expected_rows, list) or expected.get("row_count") != len(expected_rows):
                raise FitBenchError(f"case {case_id} expected rows malformed")
        else:
            semantic_only_count += 1
            if expected_semantics != "insufficient_evidence":
                raise FitBenchError(f"non-executable case {case_id} must be explicit insufficient_evidence")
            if case.get("expected") is not None:
                raise FitBenchError(f"non-executable case {case_id} must not carry query result oracle")

        lineage = case.get("required_evidence")
        if not isinstance(lineage, list):
            raise FitBenchError(f"case {case_id} required_evidence must be a list")
        for ref in lineage:
            if not isinstance(ref, dict):
                raise FitBenchError(f"case {case_id} evidence ref must be object")
            try:
                key = (int(ref["sheet_ordinal"]), int(ref["row"]), int(ref["column"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise FitBenchError(f"case {case_id} evidence ref identity malformed") from exc
            cell = evidence_index.get(key)
            if cell is None:
                raise FitBenchError(f"case {case_id} evidence ref does not reopen in projection")
            if ref.get("address") != cell.get("address") or ref.get("sheet_name") != cell.get("sheet_name"):
                raise FitBenchError(f"case {case_id} evidence ref metadata does not reopen exactly")
            evidence_ref_count += 1
    return {
        "case_count": len(cases),
        "executable_count": executable_count,
        "semantic_only_count": semantic_only_count,
        "evidence_ref_count": evidence_ref_count,
        "case_ids": sorted(ids),
        "projection_sha256": projection_sha,
    }


def deterministic_prior_art_case_ids(dataset_bytes: bytes, *, count: int = 5) -> list[str]:
    """Choose prior-art cases mechanically without semantic cherry-picking.

    Supports JSON arrays of objects with common ID fields.  The exact dataset bytes
    bind the selection; ranking is SHA-256(dataset_sha || case_id).
    """

    value = _load_json_decimal(dataset_bytes)
    if not isinstance(value, list):
        raise FitBenchError("prior-art dataset must be a JSON array")
    candidates: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            continue
        raw_id = next((item.get(key) for key in ("id", "example_id", "claim_id", "uid") if item.get(key) is not None), index)
        candidates.append(str(raw_id))
    if len(candidates) < count:
        raise FitBenchError("prior-art dataset has too few identifiable cases")
    dataset_sha = bytes.fromhex(_sha256_bytes(dataset_bytes))
    ranked = sorted(candidates, key=lambda item: hashlib.sha256(dataset_sha + item.encode("utf-8")).hexdigest())
    return ranked[:count]


def _projection_from_rows(
    *,
    source_bytes: bytes,
    source_format: str,
    sheet_name: str,
    rows: Sequence[Sequence[dict[str, object]]],
    metadata: Mapping[str, object] | None = None,
) -> tuple[bytes, dict[str, object]]:
    max_column = max((len(row) for row in rows), default=0)
    normalized_cells: list[dict[str, object]] = []
    for row_index, row in enumerate(rows, start=1):
        if len(row) != max_column:
            raise FitBenchError("projection row width must be rectangular")
        for column_index, normalized_value in enumerate(row, start=1):
            normalized_cells.append(
                {
                    "sheet_ordinal": 1,
                    "sheet_name": sheet_name,
                    "row": row_index,
                    "column": column_index,
                    "address": f"R{row_index}C{column_index}",
                    "data_type": f"external:{normalized_value.get('kind', 'unknown')}",
                    "number_format": "external",
                    "value": dict(normalized_value),
                }
            )
    projection = {
        "format": PROJECTION_FORMAT,
        "source_representation_sha256": _sha256_bytes(source_bytes),
        "source_representation_format": source_format,
        "sheets": [
            {
                "ordinal": 1,
                "name": sheet_name,
                "state": "visible",
                "max_row": len(rows),
                "max_column": max_column,
                "merged_ranges": [],
            }
        ],
        "cells": normalized_cells,
    }
    if metadata:
        projection["external_metadata"] = dict(metadata)
    projection_bytes = _canonical_json_bytes(projection)
    return projection_bytes, projection_manifest(projection_bytes)


def prepare_scitab_lane(dataset_bytes: bytes, *, count: int = 5) -> dict[str, object]:
    """Prepare mechanically selected SciTab cases without importing its ontology into core."""

    value = _load_json_decimal(dataset_bytes)
    if not isinstance(value, list):
        raise FitBenchError("SciTab dataset must be a JSON array")
    selected_ids = deterministic_prior_art_case_ids(dataset_bytes, count=count)
    by_id = {str(item.get("id")): item for item in value if isinstance(item, dict) and item.get("id") is not None}
    cases: list[dict[str, object]] = []
    for case_id in selected_ids:
        item = by_id.get(case_id)
        if not isinstance(item, dict):
            raise FitBenchError(f"selected SciTab case {case_id!r} not found")
        claim = item.get("claim")
        label = item.get("label")
        columns = item.get("table_column_names")
        content = item.get("table_content_values")
        if not isinstance(claim, str) or not claim:
            raise FitBenchError(f"SciTab case {case_id} lacks claim")
        if label not in {"supports", "refutes", "not enough info"}:
            raise FitBenchError(f"SciTab case {case_id} has unsupported label {label!r}")
        if not isinstance(columns, list) or not all(isinstance(column, str) for column in columns):
            raise FitBenchError(f"SciTab case {case_id} table columns malformed")
        if not isinstance(content, list) or not all(isinstance(row, list) for row in content):
            raise FitBenchError(f"SciTab case {case_id} table content malformed")
        rows: list[list[dict[str, object]]] = [
            [{"kind": "string", "text": str(column)} for column in columns]
        ]
        for raw_row in content:
            if len(raw_row) != len(columns):
                raise FitBenchError(f"SciTab case {case_id} table is non-rectangular")
            rows.append(
                [
                    {"kind": "blank"} if raw is None else {"kind": "string", "text": str(raw)}
                    for raw in raw_row
                ]
            )
        # Bind the projection source identity to the exact selected case bytes rather than
        # pretending the table is a Canario Representation.
        case_bytes = _canonical_json_bytes(item)
        projection_bytes, manifest = _projection_from_rows(
            source_bytes=case_bytes,
            source_format="external_scitab_case",
            sheet_name=f"scitab_{case_id}",
            rows=rows,
            metadata={
                "project": "SciTab",
                "case_id": case_id,
                "claim": claim,
                "label": label,
                "table_id": item.get("table_id"),
                "paper_id": item.get("paper_id"),
            },
        )
        cases.append(
            {
                "case_id": case_id,
                "claim": claim,
                "label": label,
                "projection_sha256": manifest["projection_sha256"],
                "projection_bytes": projection_bytes.decode("utf-8"),
                "table_rows": manifest["row_count"],
                "table_cells": manifest["cell_count"],
            }
        )
    return {
        "project": "SciTab",
        "dataset_sha256": _sha256_bytes(dataset_bytes),
        "selection_policy": "sha256(dataset_bytes || case_id) rank",
        "selected_case_ids": selected_ids,
        "cases": cases,
    }


def build_inec_scale_corpus(projection_bytes: bytes) -> dict[str, object]:
    """Build a fixed scale-oriented query corpus for the frozen INEC purchases schema."""

    projection = load_projection(projection_bytes)
    metadata = projection.get("external_columns")
    if not isinstance(metadata, list):
        raise FitBenchError("INEC scale corpus requires external column metadata")
    names = {str(item.get("name")): int(item.get("projected_column")) for item in metadata if isinstance(item, dict)}
    required = {
        "numero_procedimiento",
        "linea",
        "encargado_proveduria",
        "proveedor_adju",
        "numero_contrato",
    }
    if not required.issubset(names):
        raise FitBenchError("INEC projection does not match frozen purchases schema")
    table = "sheet_1_rows"
    procedure = f"c{names['numero_procedimiento']}_text"
    line = f"c{names['linea']}_integer"
    officer = f"c{names['encargado_proveduria']}_text"
    provider = f"c{names['proveedor_adju']}_text"
    contract = f"c{names['numero_contrato']}_text"

    # Independent oracle material.
    rows = oracle_rows(projection_bytes, sheet_ordinal=1)
    provider_counts: dict[str, int] = {}
    officer_counts: dict[str, int] = {}
    procedure_lines: dict[str, int] = {}
    contracts: set[str] = set()
    for row in rows:
        def text_at(name: str) -> str | None:
            value = row[names[name] - 1]["value"]
            assert isinstance(value, dict)
            return _cell_text(value)

        provider_value = text_at("proveedor_adju")
        officer_value = text_at("encargado_proveduria")
        procedure_value = text_at("numero_procedimiento")
        contract_value = text_at("numero_contrato")
        if provider_value:
            provider_counts[provider_value] = provider_counts.get(provider_value, 0) + 1
        if officer_value:
            officer_counts[officer_value] = officer_counts.get(officer_value, 0) + 1
        if procedure_value:
            procedure_lines[procedure_value] = procedure_lines.get(procedure_value, 0) + 1
        if contract_value:
            contracts.add(contract_value)
    top_providers = sorted(provider_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    all_procedures = sorted(procedure_lines.items(), key=lambda item: (-item[1], item[0]))
    top_procedures = all_procedures[:10]
    ranked_procedures: list[list[object]] = []
    previous_count: int | None = None
    current_rank = 0
    for index, (procedure_key, line_count) in enumerate(all_procedures, start=1):
        if previous_count is None or line_count != previous_count:
            current_rank = index
        if len(ranked_procedures) < 10:
            ranked_procedures.append([procedure_key, line_count, current_rank])
        previous_count = line_count
    cases = [
        {
            "case_id": "INEC-Q1-ROWCOUNT",
            "kind": "scale_count",
            "portable_sql": f"SELECT COUNT(*) AS n FROM {table}",
            "expected": _oracle_expected(["n"], [[len(rows)]]),
        },
        {
            "case_id": "INEC-Q2-PROVIDER-GROUP",
            "kind": "scale_group",
            "portable_sql": (
                f"SELECT {provider} AS provider,COUNT(*) AS n FROM {table} WHERE {provider} IS NOT NULL "
                "GROUP BY provider ORDER BY n DESC,provider ASC LIMIT 10"
            ),
            "expected": _oracle_expected(["provider", "n"], [[key, value] for key, value in top_providers]),
        },
        {
            "case_id": "INEC-Q3-OFFICER-GROUP",
            "kind": "scale_group",
            "portable_sql": (
                f"SELECT {officer} AS officer,COUNT(*) AS n FROM {table} WHERE {officer} IS NOT NULL "
                "GROUP BY officer ORDER BY n DESC,officer ASC"
            ),
            "expected": _oracle_expected(
                ["officer", "n"],
                [[key, value] for key, value in sorted(officer_counts.items(), key=lambda item: (-item[1], item[0]))],
            ),
        },
        {
            "case_id": "INEC-Q4-PROCEDURE-TOPK",
            "kind": "scale_top_k",
            "portable_sql": (
                f"SELECT {procedure} AS procedure,COUNT(*) AS lines FROM {table} WHERE {procedure} IS NOT NULL "
                "GROUP BY procedure ORDER BY lines DESC,procedure ASC LIMIT 10"
            ),
            "expected": _oracle_expected(["procedure", "lines"], [[key, value] for key, value in top_procedures]),
        },
        {
            "case_id": "INEC-Q5-PROCEDURE-WINDOW",
            "kind": "scale_window",
            "portable_sql": (
                "SELECT procedure,lines,RANK() OVER (ORDER BY lines DESC) AS rnk FROM ("
                f"SELECT {procedure} AS procedure,COUNT(*) AS lines FROM {table} WHERE {procedure} IS NOT NULL GROUP BY procedure"
                ") q ORDER BY lines DESC,procedure ASC LIMIT 10"
            ),
            "expected": _oracle_expected(["procedure", "lines", "rnk"], ranked_procedures),
        },
        {
            "case_id": "INEC-Q6-DISTINCT-CONTRACTS",
            "kind": "scale_distinct",
            "portable_sql": f"SELECT COUNT(DISTINCT {contract}) AS n FROM {table} WHERE {contract} IS NOT NULL",
            "expected": _oracle_expected(["n"], [[len(contracts)]]),
        },
        {
            "case_id": "INEC-Q7-LINE-RANGE",
            "kind": "scale_filter",
            "portable_sql": f"SELECT COUNT(*) AS n FROM {table} WHERE {line}>=5",
            "expected": _oracle_expected(
                ["n"],
                [[sum(1 for row in rows if _cell_integer(row[names['linea'] - 1]["value"]) is not None and _cell_integer(row[names['linea'] - 1]["value"]) >= 5)]],
            ),
        },
    ]
    for case in cases:
        case.setdefault("required_evidence", [])
        case.setdefault("expected_semantics", "query_only")
        case.setdefault("execution_failure_expected", False)
    return {
        "format": QUERY_CORPUS_FORMAT,
        "case_family": "CR-INEC-PURCHASES-SCALE-FIT",
        "projection_sha256": _sha256_bytes(projection_bytes),
        "oracle": "independent_python_projection_oracle",
        "engine_outputs_used_as_oracle": False,
        "cases": cases,
    }


def write_json(path: Path, value: object) -> str:
    data = _canonical_json_bytes(value)
    path.write_bytes(data)
    return _sha256_bytes(data)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    project = sub.add_parser("project-table", help="build neutral projection from canonical structured-table JSON")
    project.add_argument("--source", type=Path, required=True)
    project.add_argument("--output", type=Path, required=True)
    project.add_argument("--manifest", type=Path, required=True)
    project.add_argument("--expected-source-sha256")

    sqlite_query = sub.add_parser("query-sqlite", help="execute one bounded SELECT using disposable SQLite projection")
    sqlite_query.add_argument("--projection", type=Path, required=True)
    sqlite_query.add_argument("--sql", required=True)

    duck_query = sub.add_parser("query-duckdb", help="execute one bounded SELECT in sandboxed DuckDB")
    duck_query.add_argument("--projection", type=Path, required=True)
    duck_query.add_argument("--sql", required=True)
    duck_query.add_argument("--duckdb-python", type=Path, required=True)

    runtime = sub.add_parser("sqlite-runtime", help="report linked SQLite runtime identity")

    csv_project = sub.add_parser("project-external-csv", help="normalize an explicit external CSV bench lane")
    csv_project.add_argument("--source", type=Path, required=True)
    csv_project.add_argument("--spec", type=Path, required=True)
    csv_project.add_argument("--output", type=Path, required=True)
    csv_project.add_argument("--manifest", type=Path, required=True)

    prior = sub.add_parser("select-prior-art", help="deterministically select prior-art case IDs")
    prior.add_argument("--dataset", type=Path, required=True)
    prior.add_argument("--count", type=int, default=5)

    corpus = sub.add_parser("build-esparza-corpus", help="build independent deterministic query corpus from projection")
    corpus.add_argument("--projection", type=Path, required=True)
    corpus.add_argument("--output", type=Path, required=True)
    corpus.add_argument("--planner-output", type=Path, required=True)

    inec = sub.add_parser("build-inec-corpus", help="build independent scale corpus for frozen INEC purchases projection")
    inec.add_argument("--projection", type=Path, required=True)
    inec.add_argument("--output", type=Path, required=True)

    scitab = sub.add_parser("prepare-scitab-lane", help="prepare deterministic external SciTab representability lane")
    scitab.add_argument("--dataset", type=Path, required=True)
    scitab.add_argument("--output", type=Path, required=True)
    scitab.add_argument("--count", type=int, default=5)

    run_corpus = sub.add_parser("run-corpus", help="execute deterministic query corpus against one bounded engine")
    run_corpus.add_argument("--projection", type=Path, required=True)
    run_corpus.add_argument("--corpus", type=Path, required=True)
    run_corpus.add_argument("--engine", choices=("sqlite", "duckdb"), required=True)
    run_corpus.add_argument("--duckdb-python", type=Path)
    run_corpus.add_argument("--output", type=Path, required=True)

    compare_runs = sub.add_parser("compare-corpus-runs", help="compare successful deterministic results from two engines")
    compare_runs.add_argument("--left", type=Path, required=True)
    compare_runs.add_argument("--right", type=Path, required=True)
    compare_runs.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "project-table":
        source_bytes = args.source.read_bytes()
        if args.expected_source_sha256 and _sha256_bytes(source_bytes) != args.expected_source_sha256:
            raise FitBenchError("source Representation SHA-256 mismatch")
        projection_bytes, manifest = build_projection(source_bytes)
        args.output.write_bytes(projection_bytes)
        write_json(args.manifest, manifest)
        result = manifest
    elif args.command == "query-sqlite":
        result = execute_sqlite(args.projection.read_bytes(), args.sql)
    elif args.command == "query-duckdb":
        result = execute_duckdb_sandboxed(
            args.projection.read_bytes(), args.sql, duckdb_python=args.duckdb_python
        )
    elif args.command == "sqlite-runtime":
        result = sqlite_runtime_identity()
    elif args.command == "project-external-csv":
        spec_value = _load_json_decimal(args.spec.read_bytes())
        if not isinstance(spec_value, dict):
            raise FitBenchError("external CSV spec must be JSON object")
        projection_bytes, manifest = build_external_csv_projection(args.source.read_bytes(), spec_value)
        args.output.write_bytes(projection_bytes)
        write_json(args.manifest, manifest)
        result = manifest
    elif args.command == "select-prior-art":
        selected = deterministic_prior_art_case_ids(args.dataset.read_bytes(), count=args.count)
        result = {"dataset_sha256": _sha256_bytes(args.dataset.read_bytes()), "selected_case_ids": selected}
    elif args.command == "build-esparza-corpus":
        projection_bytes = args.projection.read_bytes()
        corpus = build_esparza_query_corpus(projection_bytes)
        validate_query_corpus(corpus, projection_bytes)
        corpus_sha = write_json(args.output, corpus)
        planner = planner_verifier_cases_from_corpus(corpus)
        planner_sha = write_json(args.planner_output, planner)
        result = {
            "query_corpus_sha256": corpus_sha,
            "planner_verifier_cases_sha256": planner_sha,
            "case_count": len(corpus["cases"]),
        }
    elif args.command == "build-inec-corpus":
        projection_bytes = args.projection.read_bytes()
        corpus = build_inec_scale_corpus(projection_bytes)
        validate_query_corpus(corpus, projection_bytes)
        corpus_sha = write_json(args.output, corpus)
        result = {"query_corpus_sha256": corpus_sha, "case_count": len(corpus["cases"])}
    elif args.command == "prepare-scitab-lane":
        lane = prepare_scitab_lane(args.dataset.read_bytes(), count=args.count)
        lane_sha = write_json(args.output, lane)
        result = {
            "lane_sha256": lane_sha,
            "dataset_sha256": lane["dataset_sha256"],
            "selected_case_ids": lane["selected_case_ids"],
        }
    elif args.command == "run-corpus":
        projection_bytes = args.projection.read_bytes()
        corpus_value = _load_json_decimal(args.corpus.read_bytes())
        if not isinstance(corpus_value, dict):
            raise FitBenchError("query corpus must be JSON object")
        run = run_query_corpus(
            corpus_value,
            projection_bytes,
            engine=args.engine,
            duckdb_python=args.duckdb_python,
        )
        report_sha = write_json(args.output, run)
        result = {"run_sha256": report_sha, "engine": args.engine, "summary": run["summary"]}
        if not bool(run["summary"]["all_executable_passed"]):
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 1
    elif args.command == "compare-corpus-runs":
        left_value = _load_json_decimal(args.left.read_bytes())
        right_value = _load_json_decimal(args.right.read_bytes())
        if not isinstance(left_value, dict) or not isinstance(right_value, dict):
            raise FitBenchError("corpus run inputs must be JSON objects")
        comparison = compare_corpus_runs(left_value, right_value)
        comparison_sha = write_json(args.output, comparison)
        result = {
            "comparison_sha256": comparison_sha,
            "jointly_executed": comparison["jointly_executed"],
            "disagreements": comparison["disagreements"],
        }
        if not bool(comparison["all_joint_results_agree"]):
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 1
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
