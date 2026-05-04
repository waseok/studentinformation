"""OCR 이후 정규화·키워드 분류 일괄 적용."""

from __future__ import annotations

from app.core.data_models import StudentRecord
from app.core.keyword_classifier import apply_to_record, load_dictionary
from app.core.normalizer import normalize_field_value
from app.core.settings_manager import load_json


def apply_post_ocr(record: StudentRecord) -> None:
    rules = load_json("normalization_rules.json")
    for f in record.fields.values():
        f.normalized_value = normalize_field_value(f.field_type, f.ocr_text, rules)

    health_blob = " ".join(
        record.fields[k].normalized_value
        for k in sorted(record.fields)
        if record.fields[k].field_type in ("medical_note", "multiline_text", "text")
    )
    d = load_dictionary()
    if not d.get("categories"):
        d = load_json("keyword_dictionary.json")
    apply_to_record(record, health_blob, d)
