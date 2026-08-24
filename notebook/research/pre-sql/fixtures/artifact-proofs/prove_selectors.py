#!/usr/bin/env python3
"""Artifact-backed reopening proof for the initial RepresentationTarget selectors.

This is research/candidate proof, not production parser code. It deliberately uses
one preserved official civic PDF and derives text/table Representations locally so
selector semantics are exercised against real material rather than synthetic JSON.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import fitz
import pdfplumber

HERE = Path(__file__).resolve().parent
PDF = HERE / "alcaldias_pu.pdf"
EXPECTED_PDF_SHA256 = "192da0e99878aa310a906f381f3bb25c9678934743b1b7563df747e05a8eb4f3"
PAGE_ORDINAL = 2
PDF_EXACT = "ALCALDÍA 601420299 BIENVENIDO VENEGAS PORRAS PUSC"
TEXT_EXACT = "ALCALDÍA\n601420299\nBIENVENIDO VENEGAS PORRAS\nPUSC"
TABLE_ROW = ["ALCALDÍA", "601420299", "BIENVENIDO VENEGAS PORRAS", "PUSC", ""]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_quote_v1_normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text, flags=re.UNICODE).strip()


def main() -> None:
    source_bytes = PDF.read_bytes()
    assert sha256(source_bytes) == EXPECTED_PDF_SHA256

    # pdf_page_quote:v1 — 1-based physical page + narrow quote normalization.
    doc = fitz.open(stream=source_bytes, filetype="pdf")
    assert PAGE_ORDINAL <= doc.page_count
    page_text = doc[PAGE_ORDINAL - 1].get_text("text")
    normalized_page = pdf_quote_v1_normalize(page_text)
    pdf_selector = {"page_ordinal": PAGE_ORDINAL, "exact": PDF_EXACT}
    assert pdf_quote_v1_normalize(pdf_selector["exact"]) in normalized_page

    # text_quote:v1 — offsets address the exact decoded derivative: 0-based,
    # start inclusive/end exclusive, with no fuzzy matching.
    start = page_text.index(TEXT_EXACT)
    end = start + len(TEXT_EXACT)
    text_selector = {
        "exact": TEXT_EXACT,
        "start_char": start,
        "end_char": end,
    }
    assert page_text[text_selector["start_char"] : text_selector["end_char"]] == text_selector["exact"]

    # table_range:v1 — the extracted table is itself the represented table, so
    # row ordinals are 1-based/inclusive within that Representation.
    with pdfplumber.open(PDF) as pdf:
        tables = pdf.pages[PAGE_ORDINAL - 1].extract_tables()
    assert len(tables) == 1
    table = tables[0]
    row_start = row_end = 6
    table_selector = {
        "row_start": row_start,
        "row_end": row_end,
        "observed_values": [TABLE_ROW],
    }
    selected = table[row_start - 1 : row_end]
    assert selected == table_selector["observed_values"]

    # Keep hashes of the exact derived representation bytes used in this proof.
    text_bytes = page_text.encode("utf-8")
    table_bytes = json.dumps(table, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    print("SELECTOR_ARTIFACT_PROOF=PASS")
    print(f"source_pdf_sha256={sha256(source_bytes)}")
    print(f"pdf_page_ordinal={PAGE_ORDINAL}")
    print(f"text_representation_sha256={sha256(text_bytes)}")
    print(f"text_offsets={start}:{end}")
    print(f"table_representation_sha256={sha256(table_bytes)}")
    print(f"table_rows={row_start}:{row_end}")


if __name__ == "__main__":
    main()
