from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = value.replace("\u00ad", "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _distance(a: Sequence[str] | str, b: Sequence[str] | str) -> int:
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, item_a in enumerate(a, 1):
        current = [i]
        for j, item_b in enumerate(b, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (item_a != item_b),
                )
            )
        previous = current
    return previous[-1]


def char_error_rate(truth: str, observed: str) -> float:
    truth_n = normalize_text(truth)
    observed_n = normalize_text(observed)
    if not truth_n:
        return 0.0 if not observed_n else 1.0
    return _distance(truth_n, observed_n) / len(truth_n)


def word_error_rate(truth: str, observed: str) -> float:
    truth_words = normalize_text(truth).split()
    observed_words = normalize_text(observed).split()
    if not truth_words:
        return 0.0 if not observed_words else 1.0
    return _distance(truth_words, observed_words) / len(truth_words)


def token_prf(truth: str, observed: str) -> dict[str, float | int]:
    truth_tokens = Counter(normalize_text(truth).split())
    observed_tokens = Counter(normalize_text(observed).split())
    true_positive = sum((truth_tokens & observed_tokens).values())
    predicted = sum(observed_tokens.values())
    actual = sum(truth_tokens.values())
    precision = true_positive / predicted if predicted else (1.0 if actual == 0 else 0.0)
    recall = true_positive / actual if actual else 1.0
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {
        "token_precision": precision,
        "token_recall": recall,
        "token_f1": f1,
        "unexpected_token_count": max(0, predicted - true_positive),
        "missing_token_count": max(0, actual - true_positive),
    }


def required_span_recall(required_spans: Iterable[str], observed: str) -> dict[str, object]:
    observed_n = normalize_text(observed).casefold()
    spans = list(required_spans)
    hits = [span for span in spans if normalize_text(span).casefold() in observed_n]
    misses = [span for span in spans if span not in hits]
    return {
        "required_span_recall": len(hits) / len(spans) if spans else 1.0,
        "required_span_hits": hits,
        "required_span_misses": misses,
    }


def text_metrics(truth: str, observed: str, required_spans: Iterable[str]) -> dict[str, object]:
    result: dict[str, object] = {
        "truth_chars": len(normalize_text(truth)),
        "observed_chars": len(normalize_text(observed)),
        "cer": char_error_rate(truth, observed),
        "wer": word_error_rate(truth, observed),
    }
    result.update(token_prf(truth, observed))
    result.update(required_span_recall(required_spans, observed))
    return result


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")
