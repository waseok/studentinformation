"""학급 명단과 OCR 결과 대조(자동 확정 없음)."""

from __future__ import annotations

from dataclasses import dataclass
import difflib
from typing import Any

import pandas as pd

from app.core.data_models import StudentRecord


@dataclass
class RosterRow:
    grade: str
    class_no: str
    number: str
    name: str


def load_roster_df(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    cols = {c.lower().strip(): c for c in df.columns}
    def pick(*names: str) -> str | None:
        for n in names:
            for k, v in cols.items():
                if n in k:
                    return v
        return None
    g = pick("학년")
    cl = pick("반")
    num = pick("번호")
    nm = pick("성명", "이름")
    if not all([g, cl, num, nm]):
        raise ValueError("명단에 학년, 반, 번호, 성명 열이 필요합니다.")
    out = pd.DataFrame(
        {
            "roster_grade": df[g].astype(str),
            "roster_class": df[cl].astype(str),
            "roster_number": df[num].astype(str),
            "roster_name": df[nm].astype(str),
        }
    )
    return out


def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def match_records(
    roster: pd.DataFrame,
    records: list[StudentRecord],
) -> list[dict[str, Any]]:
    """
    각 record에 대해 ocr 이름/번호와 명단 비교.
    match_status: exact / number_mismatch / name_mismatch / not_in_roster / roster_missing / review
    """
    rows: list[dict[str, Any]] = []
    used_roster_idx: set[int] = set()

    for rec in records:
        on = rec.extracted_number().strip()
        o_name = rec.extracted_name().strip()
        best: tuple[float, int | None] = (0.0, None)
        for i, r in roster.iterrows():
            rn = str(r["roster_number"]).strip()
            rname = str(r["roster_name"]).strip()
            if on and rn and on == rn and o_name and rname:
                if o_name == rname:
                    best = (1.0, int(i))
                    break
                sim = _similar(o_name, rname)
                if sim > best[0]:
                    best = (sim, int(i))
            elif on and rn and on == rn:
                sim = _similar(o_name, rname) if o_name else 0.0
                if sim > best[0]:
                    best = (sim, int(i))

        status = "review"
        reason = ""
        matched_name = ""
        rrow: pd.Series | None = None
        if best[1] is not None:
            used_roster_idx.add(best[1])
            rrow = roster.loc[best[1]]
            matched_name = str(rrow["roster_name"])
            rn = str(rrow["roster_number"]).strip()
            if on == rn and o_name == matched_name:
                status = "exact"
            elif on == rn and o_name != matched_name:
                status = "name_mismatch"
                reason = "번호는 일치하나 성명이 다릅니다."
            else:
                status = "review"
                reason = "유사 매칭만 가능합니다. 검수 필요."
        else:
            if o_name or on:
                status = "not_in_roster"
                reason = "명단에서 매칭되는 학생을 찾지 못했습니다."
        rec.roster_match = status
        rows.append(
            {
                "roster_grade": str(rrow["roster_grade"]) if rrow is not None else "",
                "roster_class": str(rrow["roster_class"]) if rrow is not None else "",
                "roster_number": str(rrow["roster_number"]) if rrow is not None else "",
                "roster_name": matched_name,
                "ocr_page_no": rec.page_start,
                "ocr_number": on,
                "ocr_name": o_name,
                "match_status": status,
                "review_needed_reason": reason,
            }
        )

    # 명단에만 있고 PDF에 없음
    for i, r in roster.iterrows():
        if int(i) not in used_roster_idx:
            rows.append(
                {
                    "roster_grade": r["roster_grade"],
                    "roster_class": r["roster_class"],
                    "roster_number": r["roster_number"],
                    "roster_name": r["roster_name"],
                    "ocr_page_no": "",
                    "ocr_number": "",
                    "ocr_name": "",
                    "match_status": "missing_in_pdf",
                    "review_needed_reason": "PDF에 해당 학생이 없습니다.",
                }
            )
    return rows
