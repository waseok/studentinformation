import pandas as pd

from app.core.data_models import FieldOCRResult, StudentRecord
from app.core.roster_matcher import match_records


def _rec(name: str, num: str, page: int = 1) -> StudentRecord:
    r = StudentRecord(record_id="x", source_path="a.pdf", page_start=page, page_end=page)
    r.fields["F003"] = FieldOCRResult(field_id="F003", ocr_text=num, normalized_value=num)
    r.fields["F004"] = FieldOCRResult(field_id="F004", ocr_text=name, normalized_value=name)
    return r


def test_roster_exact():
    roster = pd.DataFrame(
        {
            "roster_grade": ["3"],
            "roster_class": ["2"],
            "roster_number": ["1"],
            "roster_name": ["홍길동"],
        }
    )
    recs = [_rec("홍길동", "1")]
    rows = match_records(roster, recs)
    assert any(r["match_status"] == "exact" for r in rows)
