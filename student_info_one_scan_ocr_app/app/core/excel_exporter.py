"""master.xlsx 멀티 시트 출력."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.core.data_models import StudentRecord
from app.utils.privacy_utils import mask_address_export, mask_name_export, mask_phone_export


def _field(rec: StudentRecord, *candidates: str) -> str:
    for c in candidates:
        f = rec.fields.get(c)
        if f and f.normalized_value:
            return f.normalized_value
    for f in rec.fields.values():
        if f.standard_name in candidates and f.normalized_value:
            return f.normalized_value
    return ""


def build_normalized_rows(records: list[StudentRecord], form_version: str) -> pd.DataFrame:
    rows = []
    for rec in records:
        rows.append(
            {
                "source_file": Path(rec.source_path).name,
                "page_no": rec.page_start,
                "form_version": form_version,
                "review_status": rec.review_status.value,
                "성명": _field(rec, "F004", "학생 성명"),
                "학년": _field(rec, "F001"),
                "반": _field(rec, "F002"),
                "번호": _field(rec, "F003"),
                "생년월일": _field(rec, "F005"),
                "성별": _field(rec, "F006"),
                "주소": _field(rec, "F007"),
                "보호자1성명": _field(rec, "F010"),
                "보호자1관계": _field(rec, "F011"),
                "보호자1연락처": _field(rec, "F012"),
                "보호자2성명": _field(rec, "F013"),
                "보호자2관계": _field(rec, "F014"),
                "보호자2연락처": _field(rec, "F015"),
                "긴급연락우선순위": _field(rec, "F016"),
                "하교방법": " ".join(
                    filter(
                        None,
                        [
                            _field(rec, "F009a"),
                            _field(rec, "F009b"),
                            _field(rec, "F009c"),
                            _field(rec, "F009d"),
                            _field(rec, "F009e"),
                            _field(rec, "F009f"),
                        ],
                    )
                ).strip(),
                "돌봄여부": _field(rec, "F009d"),
                "알레르기여부": _field(rec, "F021"),
                "알레르기내용": _field(rec, "F023"),
                "아나필락시스경험": _field(rec, "F024b"),
                "응급약보유": _field(rec, "F025b"),
                "천식여부": _field(rec, "F026b"),
                "흡입기보유": _field(rec, "F027b"),
                "당뇨여부": _field(rec, "F028b"),
                "혈당관리필요": _field(rec, "F029b"),
                "복용약": _field(rec, "F030"),
                "응급약": _field(rec, "F025b"),
                "주이용병원": _field(rec, "F032"),
                "건강상특이사항": _field(rec, "F033"),
                "생활지도참고사항": _field(rec, "F040"),
                "보호자요청사항": _field(rec, "F044"),
                "개인정보동의": _field(rec, "F050", "F051"),
                "민감정보동의": _field(rec, "F053", "F054"),
                # 학교생활기록부 기초자료 양식 전용 필드 (없으면 빈 문자열)
                "학생전화번호": _field(rec, "F060"),
                "통학방법": " ".join(
                    filter(
                        None,
                        [
                            _field(rec, "F061a"),
                            _field(rec, "F061b"),
                            _field(rec, "F061c"),
                            _field(rec, "F061d"),
                            _field(rec, "F061e"),
                        ],
                    )
                ).strip() or _field(rec, "F009a", "F009b", "F009c", "F009d", "F009e"),
                "맞벌이여부": _field(rec, "F062a") or ("아니오" if _field(rec, "F062b") else ""),
                "방과후_보호자유무": _field(rec, "F063"),
                "방과후_주활동": _field(rec, "F064"),
                "선생님알림": _field(rec, "F065"),
                "학습지도메모": _field(rec, "F066"),
                "건강상태메모": _field(rec, "F067"),
                "기타중요사항": _field(rec, "F068"),
                "risk_level": rec.risk_level.value,
                "detected_keywords": ",".join(rec.detected_keywords),
                "health_teacher_review_needed": rec.health_teacher_review_needed,
            }
        )
    return pd.DataFrame(rows)


def export_master_workbook(
    out_path: Path,
    records: list[StudentRecord],
    *,
    form_version: str,
    roster_rows: list[dict[str, Any]] | None,
    errors: list[dict[str, Any]],
    settings_snapshot: dict[str, Any],
    minimize_pii: bool = False,
    health_exclude_address: bool = True,
    mask_phone: bool = False,
    mask_address: bool = False,
    mask_names: bool = False,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    norm = build_normalized_rows(records, form_version)
    if minimize_pii:
        for col in ("주소", "보호자1연락처", "보호자2연락처"):
            if col in norm.columns:
                norm[col] = ""
    if mask_phone:
        for col in ("보호자1연락처", "보호자2연락처", "학생전화번호"):
            if col in norm.columns:
                norm[col] = norm[col].apply(mask_phone_export)
    if mask_address:
        if "주소" in norm.columns:
            norm["주소"] = norm["주소"].apply(mask_address_export)
    if mask_names:
        for col in ("성명", "보호자1성명", "보호자2성명"):
            if col in norm.columns:
                norm[col] = norm[col].apply(mask_name_export)

    health = norm[norm["risk_level"].isin(["high", "medium"])].copy()
    if health_exclude_address and "주소" in health.columns:
        health.drop(columns=["주소"], inplace=True, errors="ignore")

    page_status = pd.DataFrame(
        [
            {
                "page_no": r.page_start,
                "extracted_name": r.extracted_name(),
                "extracted_number": r.extracted_number(),
                "matched_roster_name": "",
                "review_status": r.review_status.value,
                "risk_level": r.risk_level.value,
                "warning_message": ";".join(e.get("error_message", "") for e in r.errors),
            }
            for r in records
        ]
    )

    roster_df = pd.DataFrame(roster_rows or [])
    raw_rows = []
    for r in records:
        for fid, f in r.fields.items():
            raw_rows.append(
                {
                    "source_file": Path(r.source_path).name,
                    "page_no": r.page_start,
                    "field_id": fid,
                    "field_name": f.standard_name,
                    "ocr_text": f.ocr_text,
                    "confidence": f.confidence,
                    "crop_image_path_optional": f.crop_path or "",
                }
            )
    raw_ocr = pd.DataFrame(raw_rows)

    kw_rows = []
    for r in records:
        for kw in r.detected_keywords:
            kw_rows.append(
                {
                    "성명": r.extracted_name(),
                    "학년": _field(r, "F001"),
                    "반": _field(r, "F002"),
                    "번호": _field(r, "F003"),
                    "category": "",
                    "detected_keyword": kw,
                    "risk_level": r.risk_level.value,
                    "source_text": "",
                    "review_needed": True,
                }
            )
    keyword_flags = pd.DataFrame(kw_rows)

    errors_df = pd.DataFrame(errors)
    settings_df = pd.DataFrame([settings_snapshot])

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        norm.to_excel(writer, sheet_name="normalized", index=False)
        health.to_excel(writer, sheet_name="health_review", index=False)
        page_status.to_excel(writer, sheet_name="page_review_status", index=False)
        roster_df.to_excel(writer, sheet_name="roster_compare", index=False)
        raw_ocr.to_excel(writer, sheet_name="raw_ocr", index=False)
        keyword_flags.to_excel(writer, sheet_name="keyword_flags", index=False)
        errors_df.to_excel(writer, sheet_name="errors", index=False)
        settings_df.to_excel(writer, sheet_name="settings_snapshot", index=False)
