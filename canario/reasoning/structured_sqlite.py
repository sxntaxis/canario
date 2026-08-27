"""First production consumer of the frozen Derivation/Verification runtime.

This module intentionally supports one narrow analytical lane:

* one bounded ``canario.structured_table.v1`` input materialization;
* one untrusted SQLite SELECT executed against a disposable in-memory projection;
* deterministic typed result serialization;
* conservative source-lineage reporting (``partial`` when source tables are read,
  ``none`` for source-independent constants);
* one deterministic scalar-result verifier backed by an explicit registered rule.

It does not open the canonical Canario database, does not receive archive write
authority, and does not add a generic operation framework.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import time
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Callable, Mapping

from canario.persistence.runtime import CERTIFIED_SOURCE_IDS, TARGET_VERSION, verify_runtime_contract

from .contracts import (
    DerivationDescriptor,
    DerivationExecutionResult,
    DerivationInvocation,
    DerivationOutput,
    DerivationRequest,
    DerivationResultTargetDraft,
    SourceLineageDraft,
    VerificationDescriptor,
    VerificationEvidenceDraft,
    VerificationExecutionResult,
    VerificationInvocation,
)

STRUCTURED_TABLE_FORMAT = "canario.structured_table.v1"
QUERY_RESULT_FORMAT = "canario.structured_sqlite_query_result.v1"
QUERY_RESULT_SCHEMA_KEY = "canario.structured_sqlite_query_result"
QUERY_RESULT_SCHEMA_VERSION = "v1"

_SQLITE_VERSION = ".".join(str(value) for value in TARGET_VERSION)
_SQLITE_SOURCE_ID = CERTIFIED_SOURCE_IDS[TARGET_VERSION]

_ALLOWED_CELL_TYPES = frozenset(
    {"string", "integer", "number", "boolean", "datetime", "formula", "error"}
)
_ALLOWED_FUNCTIONS = frozenset(
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

RuntimeGuard = Callable[[], None]


class StructuredReasoningError(ValueError):
    """Structured analytical input/result violates the production contract."""


class StructuredQueryRejected(StructuredReasoningError):
    """Untrusted SQL did not satisfy the bounded read-only executor contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class StructuredSQLitePolicy:
    max_rows: int = 1_000
    max_result_bytes: int = 1_000_000
    max_input_bytes: int = 16_000_000
    timeout_ms: int = 2_000
    progress_ops: int = 1_000
    progress_callbacks: int = 10_000

    def __post_init__(self) -> None:
        for field_name in (
            "max_rows",
            "max_result_bytes",
            "max_input_bytes",
            "timeout_ms",
            "progress_ops",
            "progress_callbacks",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{field_name} must be a positive integer")

    @property
    def configuration_hash(self) -> str:
        payload = {
            "format": "canario.structured_sqlite_policy.v1",
            "max_rows": self.max_rows,
            "max_result_bytes": self.max_result_bytes,
            "max_input_bytes": self.max_input_bytes,
            "timeout_ms": self.timeout_ms,
            "progress_ops": self.progress_ops,
            "progress_callbacks": self.progress_callbacks,
        }
        return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


@dataclass(frozen=True, slots=True)
class ScalarVerificationRule:
    """One reproducible scalar proposition/result comparison rule.

    The rule is bound to the exact SQL program and Derivation configuration
    identity. The v1 verifier intentionally authorizes exact integer/string/boolean/null
    equality only; SQLite REAL/float equality is not promoted as civic truth by this lane.
    """

    proposition_text: str
    expected_cell: Mapping[str, object]
    program_sha256: str
    derivation_configuration_hash: str
    authority_scope_kind: str = "dataset_value"

    def __post_init__(self) -> None:
        if not isinstance(self.proposition_text, str) or not self.proposition_text.strip():
            raise ValueError("scalar verification proposition must be non-empty")
        copied = dict(self.expected_cell)
        _validate_result_cell(copied)
        if copied.get("type") not in {"integer", "string", "boolean", "null"}:
            raise ValueError(
                "v1 scalar verification supports exact integer/string/boolean/null cells only"
            )
        object.__setattr__(self, "expected_cell", MappingProxyType(copied))
        _require_sha256(self.program_sha256, "verification rule program SHA")
        _require_sha256(
            self.derivation_configuration_hash, "verification rule Derivation configuration hash"
        )
        if self.authority_scope_kind not in {
            "formal_record",
            "recorded_speech",
            "issuer_statement",
            "reported_statement",
            "dataset_value",
            "visual_record",
            "other",
        }:
            raise ValueError("unknown Source Authority scope kind")

    @property
    def configuration_hash(self) -> str:
        payload = {
            "format": "canario.structured_scalar_verification_rule.v1",
            "proposition_text": self.proposition_text,
            "expected_cell": dict(self.expected_cell),
            "program_sha256": self.program_sha256,
            "derivation_configuration_hash": self.derivation_configuration_hash,
            "authority_scope_kind": self.authority_scope_kind,
        }
        return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()

    @classmethod
    def integer(
        cls,
        proposition_text: str,
        value: int,
        *,
        program_text: str,
        derivation_configuration_hash: str,
        authority_scope_kind: str = "dataset_value",
    ) -> "ScalarVerificationRule":
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("integer verification rule requires int")
        return cls(
            proposition_text,
            {"type": "integer", "value": str(value)},
            hashlib.sha256(program_text.encode("utf-8")).hexdigest(),
            derivation_configuration_hash,
            authority_scope_kind,
        )

    @classmethod
    def string(
        cls,
        proposition_text: str,
        value: str,
        *,
        program_text: str,
        derivation_configuration_hash: str,
        authority_scope_kind: str = "dataset_value",
    ) -> "ScalarVerificationRule":
        return cls(
            proposition_text,
            {"type": "string", "value": value},
            hashlib.sha256(program_text.encode("utf-8")).hexdigest(),
            derivation_configuration_hash,
            authority_scope_kind,
        )


class StructuredSQLiteDerivationBackend:
    """Execute one untrusted SQL SELECT over one bounded structured-table input."""

    def __init__(
        self,
        *,
        policy: StructuredSQLitePolicy | None = None,
        runtime_guard: RuntimeGuard = verify_runtime_contract,
    ) -> None:
        self.policy = policy or StructuredSQLitePolicy()
        self._runtime_guard = runtime_guard
        self._descriptor = DerivationDescriptor(
            key="core.structured_sqlite",
            implementation_version="1",
            execution_venue="local_deterministic",
            executor_key="sqlite_bounded_projection",
            executor_version=_SQLITE_VERSION,
            executor_source_id=_SQLITE_SOURCE_ID,
            sandbox_profile_key="sqlite_disposable_query_only_projection",
            sandbox_profile_version="1",
            operation_kinds=frozenset({"query"}),
            program_kinds=frozenset({"sql"}),
            max_inputs=1,
            max_input_bytes=self.policy.max_input_bytes,
            max_result_bytes=self.policy.max_result_bytes,
        )

    @property
    def descriptor(self) -> DerivationDescriptor:
        return self._descriptor

    def request(self, input_target_ids: tuple[str, ...], sql: str) -> DerivationRequest:
        return DerivationRequest(
            input_target_ids,
            "query",
            "sql",
            sql,
            configuration_hash=self.policy.configuration_hash,
        )

    def derive(self, invocation: DerivationInvocation) -> DerivationExecutionResult:
        if invocation.request.configuration_hash != self.policy.configuration_hash:
            return DerivationExecutionResult("failed", error_code="structured_policy_mismatch")
        if invocation.request.operation_kind != "query" or invocation.request.program_kind != "sql":
            return DerivationExecutionResult("failed", error_code="unsupported_derivation_kind")
        if len(invocation.inputs) != 1:
            return DerivationExecutionResult("failed", error_code="structured_input_count_unsupported")
        source = invocation.inputs[0]
        if len(source.material_bytes) > self.policy.max_input_bytes:
            return DerivationExecutionResult("failed", error_code="structured_input_too_large")
        try:
            self._runtime_guard()
        except Exception:
            return DerivationExecutionResult("failed", error_code="sqlite_runtime_unqualified")
        try:
            projection = _load_structured_table(source.material_bytes)
            result, source_read = _execute_select(
                projection, invocation.request.program_text, self.policy
            )
        except StructuredQueryRejected as exc:
            return DerivationExecutionResult("failed", error_code=exc.code)
        except StructuredReasoningError:
            return DerivationExecutionResult("failed", error_code="structured_input_invalid")

        scalar = result["row_count"] == 1 and len(result["columns"]) == 1
        result_kind = "scalar" if scalar else "table"
        selector_kind = "scalar" if scalar else "whole"
        lineage_state = "partial" if source_read else "none"
        lineage = (
            (SourceLineageDraft(source.ordinal, source.target.id),) if source_read else ()
        )
        return DerivationExecutionResult(
            "success",
            DerivationOutput(
                result_kind,
                QUERY_RESULT_SCHEMA_KEY,
                QUERY_RESULT_SCHEMA_VERSION,
                (
                    DerivationResultTargetDraft(
                        selector_kind,
                        "v1",
                        "{}",
                        lineage_state,
                        lineage,
                    ),
                ),
                inline_payload=result,
            ),
        )


class StructuredScalarVerifierBackend:
    """Verify one registered scalar proposition against one consumed SQL result.

    The rule is code/configuration authority, not source evidence. The persisted
    ``configuration_hash`` must match the exact rule. Source evidence remains the
    explicit Verification scope and the consumed Derivation must itself be
    source-backed.
    """

    def __init__(self, rule: ScalarVerificationRule) -> None:
        self.rule = rule
        self._descriptor = VerificationDescriptor(
            "core.structured_scalar_verifier",
            "1",
            "local_deterministic",
            False,
            None,
            None,
            1,
            16_000_000,
        )

    @property
    def descriptor(self) -> VerificationDescriptor:
        return self._descriptor

    def verify(self, invocation: VerificationInvocation) -> VerificationExecutionResult:
        request = invocation.request
        if request.proposition_text != self.rule.proposition_text:
            return VerificationExecutionResult("failed", error_code="unregistered_proposition")
        if request.configuration_hash != self.rule.configuration_hash:
            return VerificationExecutionResult("failed", error_code="verification_rule_mismatch")
        if len(invocation.scopes) != 1:
            return VerificationExecutionResult("failed", error_code="scalar_verifier_scope_unsupported")

        source_id = invocation.scopes[0].source_id
        if not any(
            scope.source_id == source_id and scope.scope_kind == self.rule.authority_scope_kind
            for scope in invocation.authority_scopes
        ):
            return VerificationExecutionResult("failed", error_code="source_authority_incompatible")

        consumed = [
            step.consumed_result
            for step in invocation.derivations
            if step.use_state == "consumed" and step.consumed_result is not None
        ]
        if len(consumed) != 1:
            return VerificationExecutionResult("failed", error_code="scalar_verifier_requires_one_result")
        consumed_steps = [
            step
            for step in invocation.derivations
            if step.use_state == "consumed" and step.consumed_result is not None
        ]
        step = consumed_steps[0]
        result = consumed[0]
        if (
            step.implementation_key != "core.structured_sqlite"
            or step.executor_key != "sqlite_bounded_projection"
            or step.executor_version != _SQLITE_VERSION
            or step.executor_source_id != _SQLITE_SOURCE_ID
            or step.operation_kind != "query"
            or step.program_kind != "sql"
        ):
            return VerificationExecutionResult(
                "failed", error_code="unsupported_derivation_provenance"
            )
        if step.program_sha256 != self.rule.program_sha256:
            return VerificationExecutionResult("failed", error_code="derivation_program_mismatch")
        if step.configuration_hash != self.rule.derivation_configuration_hash:
            return VerificationExecutionResult(
                "failed", error_code="derivation_configuration_mismatch"
            )
        if (
            result.schema_key != QUERY_RESULT_SCHEMA_KEY
            or result.schema_version != QUERY_RESULT_SCHEMA_VERSION
            or result.result_kind != "scalar"
        ):
            return VerificationExecutionResult("failed", error_code="unsupported_consumed_result")

        if result.lineage_state not in {"exact", "partial"} or not result.source_target_ids:
            return VerificationExecutionResult(
                "completed",
                verdict="insufficient_evidence",
                sufficiency_state="insufficient",
                sufficiency_profile_key="explicit",
                sufficiency_profile_version="v1",
                sufficiency_payload_json="{}",
                abstention_reason_code="derivation_not_source_backed",
            )

        try:
            payload = json.loads(result.material_bytes.decode("utf-8"))
            actual = _single_result_cell(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, StructuredReasoningError):
            return VerificationExecutionResult("failed", error_code="malformed_consumed_result")

        passed = actual == dict(self.rule.expected_cell)
        role = "supports" if passed else "challenges"
        return VerificationExecutionResult(
            "completed",
            verdict="supported" if passed else "contradicted",
            sufficiency_state="sufficient",
            sufficiency_profile_key="explicit",
            sufficiency_profile_version="v1",
            sufficiency_payload_json="{}",
            evidence=(
                VerificationEvidenceDraft(
                    0,
                    invocation.scopes[0].target.id,
                    role,
                ),
            ),
        )


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _require_sha256(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value != value.lower()
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise ValueError(f"{label} must be 64 lowercase SHA-256 hex characters")
    return value


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise StructuredReasoningError("non-finite number")
    text = str(value)
    return "0" if text == "-0" else text


def _load_json_decimal(data: bytes) -> object:
    try:
        return json.loads(data.decode("utf-8"), parse_float=Decimal, parse_int=int)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StructuredReasoningError("structured input must be UTF-8 JSON") from exc


def _normalize_cell(raw: object) -> dict[str, object]:
    if raw is None:
        return {"kind": "blank"}
    if not isinstance(raw, dict):
        raise StructuredReasoningError("structured cell must be null or typed object")
    kind = raw.get("type")
    value = raw.get("value")
    if kind not in _ALLOWED_CELL_TYPES:
        raise StructuredReasoningError("unknown structured cell type")
    if kind in {"string", "datetime", "formula", "error"}:
        if not isinstance(value, str):
            raise StructuredReasoningError("textual structured cell requires string")
        return {"kind": kind, "text": value}
    if kind == "boolean":
        if not isinstance(value, bool):
            raise StructuredReasoningError("boolean structured cell requires bool")
        return {"kind": kind, "value": value}
    if kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise StructuredReasoningError("integer structured cell requires int")
        return {"kind": kind, "decimal": str(value)}
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
            raise StructuredReasoningError("number structured cell requires JSON number")
        return {"kind": kind, "decimal": _canonical_decimal(Decimal(value))}
    raise AssertionError(kind)


def structured_table_schema_summary(data: bytes) -> dict[str, object]:
    """Return deterministic query schema metadata without exposing source cell values."""

    projection = _load_structured_table(data)
    sheets = projection["sheets"]
    assert isinstance(sheets, list)
    records: list[dict[str, object]] = []
    for sheet in sheets:
        assert isinstance(sheet, dict)
        max_column = int(sheet["max_column"])
        columns = ["row_index"]
        for ordinal in range(1, max_column + 1):
            columns.extend(name for name, _kind in _cell_columns(ordinal))
        records.append({
            "table": f"sheet_{int(sheet['ordinal'])}_rows",
            "sheet_ordinal": int(sheet["ordinal"]),
            "sheet_name": str(sheet["name"]),
            "max_row": int(sheet["max_row"]),
            "max_column": max_column,
            "columns": columns,
        })
    return {
        "format": "canario.structured_sqlite_schema.v1",
        "projection_sheets_table": {
            "table": "projection_sheets",
            "columns": ["ordinal", "name", "state", "max_row", "max_column", "merged_ranges_json"],
        },
        "sheet_tables": records,
    }


def _load_structured_table(data: bytes) -> dict[str, object]:
    value = _load_json_decimal(data)
    if not isinstance(value, dict) or value.get("format") != STRUCTURED_TABLE_FORMAT:
        raise StructuredReasoningError("input is not canario.structured_table.v1")
    sheets = value.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        raise StructuredReasoningError("structured table requires sheets")

    normalized_sheets: list[dict[str, object]] = []
    previous = 0
    for sheet in sheets:
        if not isinstance(sheet, dict):
            raise StructuredReasoningError("structured sheet must be object")
        ordinal = sheet.get("ordinal")
        name = sheet.get("name")
        state = sheet.get("state")
        max_row = sheet.get("max_row")
        max_column = sheet.get("max_column")
        rows = sheet.get("rows")
        merged = sheet.get("merged_ranges")
        if not isinstance(ordinal, int) or ordinal <= previous:
            raise StructuredReasoningError("sheet ordinals must be strictly increasing")
        previous = ordinal
        if not isinstance(name, str) or not name or not isinstance(state, str) or not state:
            raise StructuredReasoningError("sheet name/state invalid")
        if (
            not isinstance(max_row, int)
            or max_row < 0
            or not isinstance(max_column, int)
            or max_column < 0
            or not isinstance(rows, list)
            or len(rows) != max_row
            or not isinstance(merged, list)
            or not all(isinstance(item, str) for item in merged)
        ):
            raise StructuredReasoningError("sheet dimensions/rows invalid")
        normalized_rows: list[list[dict[str, object]]] = []
        for row in rows:
            if not isinstance(row, list) or len(row) != max_column:
                raise StructuredReasoningError("structured row width invalid")
            normalized_row: list[dict[str, object]] = []
            for cell in row:
                if not isinstance(cell, dict):
                    raise StructuredReasoningError("structured cell must be object")
                address = cell.get("address")
                data_type = cell.get("data_type")
                number_format = cell.get("number_format")
                if not isinstance(address, str) or not address:
                    raise StructuredReasoningError("cell address invalid")
                if not isinstance(data_type, str) or not isinstance(number_format, str):
                    raise StructuredReasoningError("cell metadata invalid")
                normalized_row.append(
                    {
                        "address": address,
                        "data_type": data_type,
                        "number_format": number_format,
                        "value": _normalize_cell(cell.get("value")),
                    }
                )
            normalized_rows.append(normalized_row)
        normalized_sheets.append(
            {
                "ordinal": ordinal,
                "name": name,
                "state": state,
                "max_row": max_row,
                "max_column": max_column,
                "merged_ranges": list(merged),
                "rows": normalized_rows,
            }
        )
    return {"format": STRUCTURED_TABLE_FORMAT, "sheets": normalized_sheets}


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
    raise StructuredReasoningError("unknown normalized cell")


def _cell_integer(value: Mapping[str, object]) -> int | None:
    if value["kind"] != "integer":
        return None
    integer = int(str(value["decimal"]))
    return integer if -(2**63) <= integer <= (2**63 - 1) else None


def _cell_number(value: Mapping[str, object]) -> float | None:
    if value["kind"] not in {"integer", "number"}:
        return None
    number = float(Decimal(str(value["decimal"])))
    if not math.isfinite(number):
        raise StructuredReasoningError("numeric cell cannot enter SQLite REAL")
    return number


def _cell_columns(column: int) -> list[tuple[str, str]]:
    prefix = f"c{column}"
    return [
        (f"{prefix}_kind", "TEXT"),
        (f"{prefix}_text", "TEXT"),
        (f"{prefix}_integer", "INTEGER"),
        (f"{prefix}_number", "REAL"),
        (f"{prefix}_boolean", "INTEGER"),
        (f"{prefix}_datetime", "TEXT"),
        (f"{prefix}_formula", "TEXT"),
        (f"{prefix}_address", "TEXT"),
        (f"{prefix}_data_type", "TEXT"),
        (f"{prefix}_number_format", "TEXT"),
    ]


def _cell_values(cell: Mapping[str, object]) -> list[object]:
    value = cell["value"]
    assert isinstance(value, dict)
    kind = str(value["kind"])
    return [
        kind,
        _cell_text(value),
        _cell_integer(value),
        _cell_number(value),
        int(bool(value["value"])) if kind == "boolean" else None,
        str(value["text"]) if kind == "datetime" else None,
        str(value["text"]) if kind == "formula" else None,
        str(cell["address"]),
        str(cell["data_type"]),
        str(cell["number_format"]),
    ]


def _create_projection(con: sqlite3.Connection, projection: Mapping[str, object]) -> set[str]:
    allowed_tables = {"projection_sheets"}
    con.execute(
        "CREATE TABLE projection_sheets(ordinal INTEGER PRIMARY KEY,name TEXT NOT NULL,state TEXT NOT NULL,max_row INTEGER NOT NULL,max_column INTEGER NOT NULL,merged_ranges_json TEXT NOT NULL)"
    )
    sheets = projection["sheets"]
    assert isinstance(sheets, list)
    for sheet in sheets:
        assert isinstance(sheet, dict)
        ordinal = int(sheet["ordinal"])
        con.execute(
            "INSERT INTO projection_sheets VALUES(?,?,?,?,?,?)",
            (
                ordinal,
                sheet["name"],
                sheet["state"],
                sheet["max_row"],
                sheet["max_column"],
                json.dumps(sheet["merged_ranges"], separators=(",", ":")),
            ),
        )
        table = f"sheet_{ordinal}_rows"
        allowed_tables.add(table)
        columns: list[tuple[str, str]] = [("row_index", "INTEGER PRIMARY KEY")]
        for column in range(1, int(sheet["max_column"]) + 1):
            columns.extend(_cell_columns(column))
        con.execute(
            f"CREATE TABLE {table}({','.join(f'{name} {kind}' for name, kind in columns)})"
        )
        placeholders = ",".join("?" for _ in columns)
        rows = sheet["rows"]
        assert isinstance(rows, list)
        for row_index, row in enumerate(rows, start=1):
            assert isinstance(row, list)
            values: list[object] = [row_index]
            for cell in row:
                assert isinstance(cell, dict)
                values.extend(_cell_values(cell))
            con.execute(f"INSERT INTO {table} VALUES({placeholders})", values)
    con.commit()
    return allowed_tables


def _result_cell(value: object) -> dict[str, object]:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean", "value": value}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise StructuredQueryRejected("query_result_invalid", "query returned non-finite number")
        return {"type": "number", "value": repr(value)}
    if isinstance(value, str):
        return {"type": "string", "value": value}
    if isinstance(value, bytes):
        return {"type": "bytes", "hex": value.hex()}
    raise StructuredQueryRejected(
        "query_result_invalid", f"unsupported query result type {type(value).__name__}"
    )


def _validate_result_cell(value: dict[str, object]) -> None:
    kind = value.get("type")
    if kind == "null":
        if set(value) != {"type"}:
            raise ValueError("null result cell has extra fields")
        return
    if kind in {"integer", "number", "string"}:
        if set(value) != {"type", "value"} or not isinstance(value.get("value"), str):
            raise ValueError("typed scalar result cell is malformed")
        return
    if kind == "boolean":
        if set(value) != {"type", "value"} or not isinstance(value.get("value"), bool):
            raise ValueError("boolean scalar result cell is malformed")
        return
    if kind == "bytes":
        if set(value) != {"type", "hex"} or not isinstance(value.get("hex"), str):
            raise ValueError("bytes scalar result cell is malformed")
        return
    raise ValueError("unknown scalar result cell type")


def _execute_select(
    projection: Mapping[str, object], sql: str, policy: StructuredSQLitePolicy
) -> tuple[dict[str, object], bool]:
    if not isinstance(sql, str) or not sql.strip():
        raise StructuredQueryRejected("query_empty", "query must be non-empty")
    con = sqlite3.connect(":memory:")
    try:
        allowed_tables = _create_projection(con, projection)
        con.execute("PRAGMA query_only=ON")
        try:
            con.enable_load_extension(False)
        except (AttributeError, sqlite3.DatabaseError):
            pass
        source_read = False

        def authorizer(
            action: int,
            arg1: str | None,
            arg2: str | None,
            _db: str | None,
            _source: str | None,
        ) -> int:
            nonlocal source_read
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ:
                table = arg1 or ""
                if table in allowed_tables:
                    source_read = True
                    return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_FUNCTION:
                function_name = (arg2 or arg1 or "").lower()
                return sqlite3.SQLITE_OK if function_name in _ALLOWED_FUNCTIONS else sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_DENY

        deadline = time.monotonic() + policy.timeout_ms / 1000.0
        callbacks = 0

        def progress() -> int:
            nonlocal callbacks
            callbacks += 1
            return int(
                callbacks > policy.progress_callbacks or time.monotonic() >= deadline
            )

        con.set_progress_handler(progress, policy.progress_ops)
        con.set_authorizer(authorizer)
        try:
            cursor = con.execute(sql)
        except sqlite3.ProgrammingError as exc:
            raise StructuredQueryRejected(
                "query_multiple_statements", "query must contain exactly one statement"
            ) from exc
        except sqlite3.DatabaseError as exc:
            message = str(exc).lower()
            if "not authorized" in message or "authorization denied" in message:
                raise StructuredQueryRejected(
                    "query_forbidden_operation", "query uses a forbidden SQLite operation"
                ) from exc
            if "interrupted" in message:
                raise StructuredQueryRejected(
                    "query_budget_exceeded", "query exceeded SQLite execution budget"
                ) from exc
            raise StructuredQueryRejected("query_invalid", f"SQLite rejected query: {exc}") from exc
        if cursor.description is None:
            raise StructuredQueryRejected("query_not_select", "query did not return a SELECT result")
        columns = [str(item[0]) for item in cursor.description]
        rows: list[list[dict[str, object]]] = []
        while True:
            if time.monotonic() >= deadline:
                raise StructuredQueryRejected(
                    "query_budget_exceeded", "query exceeded wall-clock budget"
                )
            row = cursor.fetchone()
            if row is None:
                break
            if len(rows) >= policy.max_rows:
                raise StructuredQueryRejected("query_result_too_large", "result row limit exceeded")
            rows.append([_result_cell(value) for value in row])
        payload: dict[str, object] = {
            "format": QUERY_RESULT_FORMAT,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": False,
        }
        if len(_canonical_json_bytes(payload)) > policy.max_result_bytes:
            raise StructuredQueryRejected("query_result_too_large", "result byte limit exceeded")
        return payload, source_read
    finally:
        con.close()


def _single_result_cell(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict) or payload.get("format") != QUERY_RESULT_FORMAT:
        raise StructuredReasoningError("consumed result has wrong format")
    columns = payload.get("columns")
    rows = payload.get("rows")
    if not isinstance(columns, list) or len(columns) != 1 or not isinstance(rows, list) or len(rows) != 1:
        raise StructuredReasoningError("scalar verifier requires exactly one row and one column")
    row = rows[0]
    if not isinstance(row, list) or len(row) != 1 or not isinstance(row[0], dict):
        raise StructuredReasoningError("scalar result cell is malformed")
    cell = dict(row[0])
    _validate_result_cell(cell)
    return cell
