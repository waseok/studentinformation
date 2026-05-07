"""PyMuPDF로 PDF 페이지를 이미지로 렌더링."""

from __future__ import annotations

import logging
from pathlib import Path

import fitz

log = logging.getLogger(__name__)

_MAX_PDF_MB = 200


def _check_file_size(path: Path) -> None:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > _MAX_PDF_MB:
        raise ValueError(
            f"PDF 파일이 너무 큽니다 ({size_mb:.1f} MB). "
            f"최대 허용 크기는 {_MAX_PDF_MB} MB입니다."
        )


def pdf_page_count(path: Path) -> int:
    _check_file_size(path)
    try:
        doc = fitz.open(str(path))
    except Exception as e:
        raise ValueError(f"PDF 열기 실패 ({path.name}): {e}") from e
    n = doc.page_count
    doc.close()
    return n


def render_pdf_page(
    pdf_path: Path,
    page_index: int,
    dpi: int,
    out_png: Path,
) -> tuple[int, int]:
    """
    page_index: 0-based
    반환: (width, height) 픽셀
    """
    out_png.parent.mkdir(parents=True, exist_ok=True)
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        raise ValueError(f"PDF 열기 실패 ({pdf_path.name}): {e}") from e
    try:
        page = doc.load_page(page_index)
        mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(str(out_png))
        return pix.width, pix.height
    except Exception as e:
        log.error("PDF 페이지 렌더링 실패 (%s, page=%d): %s", pdf_path.name, page_index, e)
        raise
    finally:
        doc.close()


def warn_low_resolution(width_px: float, height_px: float, dpi: int, page_short_mm: float = 297.0) -> bool:
    """A4 세로 기준으로 해상도가 지나치게 낮은지."""
    expected_h = dpi / 25.4 * page_short_mm
    return height_px < expected_h * 0.7
