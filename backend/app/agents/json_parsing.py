import json
import re
from collections.abc import Callable
from typing import Any

_MISSING = object()


def clean_json_text(text: str) -> str:
    return text.strip().replace("```json", "").replace("```", "")


def normalize_json_trailing_commas(text: str) -> str:
    return re.sub(r",(\s*[\]}])", r"\1", text)


def _decode_json_candidate(
    decoder: json.JSONDecoder,
    candidate: str,
    *,
    normalize_trailing_commas: bool,
) -> Any:
    try:
        parsed, _ = decoder.raw_decode(candidate)
        return parsed
    except json.JSONDecodeError:
        if not normalize_trailing_commas:
            return _MISSING

    try:
        parsed, _ = decoder.raw_decode(normalize_json_trailing_commas(candidate))
        return parsed
    except json.JSONDecodeError:
        return _MISSING


def find_first_json_value(
    text: str,
    *,
    start_chars: str,
    accept: Callable[[Any], bool],
    normalize_trailing_commas: bool = False,
) -> Any:
    cleaned_text = clean_json_text(text)
    decoder = json.JSONDecoder()

    for index, char in enumerate(cleaned_text):
        if char not in start_chars:
            continue

        candidate = cleaned_text[index:]
        parsed = _decode_json_candidate(
            decoder,
            candidate,
            normalize_trailing_commas=normalize_trailing_commas,
        )
        if parsed is not _MISSING and accept(parsed):
            return parsed

    raise ValueError("No matching JSON value found in model response")
