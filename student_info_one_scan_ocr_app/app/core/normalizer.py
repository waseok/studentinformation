"""OCR 텍스트 정규화."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_rules(path: Path | None = None) -> dict[str, Any]:
    if path and path.is_file():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def collapse_whitespace(s: str) -> str:
    s = re.sub(r"[\u00a0\u200b]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_phone(raw: str, fixes: dict[str, str] | None = None) -> str:
    s = raw
    for a, b in (fixes or {}).items():
        s = s.replace(a, b)
    digits = re.sub(r"\D", "", s)
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    if len(digits) == 10 and digits.startswith("10"):
        digits = "0" + digits
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return collapse_whitespace(raw)


def normalize_yes_no(s: str, rules: dict[str, Any]) -> str:
    t = collapse_whitespace(s)
    low = t.lower()
    for tok in rules.get("yes_tokens", []):
        if tok.lower() == low or tok == t:
            return "예"
    for tok in rules.get("no_tokens", []):
        if tok.lower() == low or tok == t:
            return "아니오"
    return t


def digits_only_field(s: str) -> str:
    return re.sub(r"\D", "", s)


def warn_name_has_digit(name: str) -> bool:
    return bool(re.search(r"[0-9]", name))


def normalize_field_value(field_type: str, text: str, rules: dict[str, Any]) -> str:
    if field_type == "phone":
        return normalize_phone(text, rules.get("phone_ocr_fixes"))
    if field_type in ("number",):
        return digits_only_field(text)
    if field_type == "checkbox":
        return normalize_yes_no(text, rules)
    if field_type in ("multiline_text", "medical_note", "address", "text", "date", "signature"):
        return collapse_whitespace(text)
    return collapse_whitespace(text)
