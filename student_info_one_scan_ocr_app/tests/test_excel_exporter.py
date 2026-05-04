from pathlib import Path

import pandas as pd

from app.core.data_models import FieldOCRResult, StudentRecord
from app.core.excel_exporter import export_master_workbook


def test_export_workbook(tmp_path: Path):
    r = StudentRecord(record_id="1", source_path="t.pdf", page_start=1, page_end=1)
    r.fields["F004"] = FieldOCRResult(
        field_id="F004",
        standard_name="성명",
        ocr_text="테스트",
        normalized_value="테스트",
    )
    out = tmp_path / "out.xlsx"
    export_master_workbook(
        out,
        [r],
        form_version="v1",
        roster_rows=[],
        errors=[],
        settings_snapshot={"dpi": 300},
    )
    assert out.is_file()
    xl = pd.ExcelFile(out)
    assert "normalized" in xl.sheet_names
    assert "errors" in xl.sheet_names
