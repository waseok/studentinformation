"""보건 키워드 탐지 및 위험도."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.data_models import RiskLevel, StudentRecord


def load_dictionary(path: Path | None = None) -> dict[str, Any]:
    if path and path.is_file():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    from app.core.settings_manager import load_json

    return load_json("keyword_dictionary.json")


def classify_text(text: str, d: dict[str, Any]) -> dict[str, Any]:
    """텍스트에서 키워드 매칭 및 위험도 산정."""
    found: list[str] = []
    cats_hit: set[str] = set()
    t = text
    for cat, kws in d.get("categories", {}).items():
        for kw in kws:
            if kw and kw in t:
                found.append(kw)
                cats_hit.add(cat)
    risk_score = 0
    level = RiskLevel.LOW
    high = set(d.get("risk_high", []))
    med = set(d.get("risk_medium", []))
    for kw in found:
        if kw in high:
            risk_score += 3
        elif kw in med:
            risk_score += 2
        else:
            risk_score += 1
    if risk_score >= 5:
        level = RiskLevel.HIGH
    elif risk_score >= 2:
        level = RiskLevel.MEDIUM

    flags = {
        "allergy_flag": "allergy" in cats_hit,
        "anaphylaxis_flag": "anaphylaxis" in cats_hit,
        "asthma_flag": "asthma" in cats_hit,
        "diabetes_flag": "diabetes" in cats_hit,
        "emergency_flag": "emergency_other" in cats_hit,
        "medication_flag": "medication" in cats_hit,
    }
    return {
        "detected_keywords": sorted(set(found)),
        "risk_level": level,
        "risk_score": risk_score,
        "flags": flags,
        "health_teacher_review_needed": level != RiskLevel.LOW,
    }


def apply_to_record(record: StudentRecord, health_text: str, d: dict[str, Any]) -> None:
    r = classify_text(health_text, d)
    record.detected_keywords = r["detected_keywords"]
    record.risk_level = r["risk_level"]
    record.risk_score = r["risk_score"]
    record.health_teacher_review_needed = r["health_teacher_review_needed"]
    for k, v in r["flags"].items():
        setattr(record, k, v)
