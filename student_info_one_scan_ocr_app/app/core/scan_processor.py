"""
스캔 PDF를 페이지 단위 이미지로 만들고 StudentRecord 묶음을 생성.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from app.core.data_models import ReviewStatus, StudentRecord
from app.core.pdf_renderer import pdf_page_count, render_pdf_page, warn_low_resolution

log = logging.getLogger(__name__)


def build_student_records_from_pdf(
    pdf_path: Path,
    temp_dir: Path,
    *,
    dpi: int,
    pages_per_student: int,
) -> list[StudentRecord]:
    """
    pages_per_student: 1이면 페이지당 1명, 2이면 2페이지를 한 학생으로 묶음.
    """
    n = pdf_page_count(pdf_path)
    records: list[StudentRecord] = []
    if pages_per_student < 1:
        pages_per_student = 1

    idx = 0
    group = 0
    while idx < n:
        end = min(idx + pages_per_student, n)
        paths: list[str] = []
        for p in range(idx, end):
            out = temp_dir / f"{pdf_path.stem}_p{p+1:04d}.png"
            w, h = render_pdf_page(pdf_path, p, dpi, out)
            if warn_low_resolution(w, h, dpi):
                log.warning("low_resolution page=%s file=%s", p + 1, pdf_path.name)
            paths.append(str(out))
        rec = StudentRecord(
            record_id=str(uuid.uuid4()),
            source_path=str(pdf_path.resolve()),
            page_start=idx + 1,
            page_end=end,
            page_group_id=f"G{group:04d}",
            render_image_paths=paths,
            review_status=ReviewStatus.OCR_DONE,
        )
        records.append(rec)
        idx = end
        group += 1
    return records
