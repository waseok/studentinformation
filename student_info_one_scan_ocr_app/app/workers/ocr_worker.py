"""백그라운드 OCR 작업."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal

from app.core.pipeline import apply_post_ocr
from app.core.template_ocr_extractor import (
    extract_fields_for_record,
    extract_fields_with_label_fallback,
    load_form_template,
)
from app.core.data_models import StudentRecord


class OCRWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished_ok = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(
        self,
        records: list[StudentRecord],
        template_path: Path | None,
        tesseract_path: str,
        ocr_lang: str,
        use_preprocess: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.records = records
        self.template_path = template_path
        self.tesseract_path = tesseract_path
        self.ocr_lang = ocr_lang
        self.use_preprocess = use_preprocess
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        template = None
        if self.template_path is not None:
            try:
                template = load_form_template(self.template_path)
            except Exception as e:
                self.failed.emit(str(e))
                return
        total = len(self.records)
        for i, rec in enumerate(self.records, start=1):
            if self._cancel:
                break
            try:
                if template is not None:
                    extract_fields_for_record(
                        rec,
                        template,
                        tesseract_path=self.tesseract_path,
                        ocr_lang=self.ocr_lang,
                        use_preprocess=self.use_preprocess,
                    )
                else:
                    extract_fields_with_label_fallback(
                        rec,
                        tesseract_path=self.tesseract_path,
                        ocr_lang=self.ocr_lang,
                        use_preprocess=self.use_preprocess,
                    )
                apply_post_ocr(rec)
            except Exception as e:
                self.failed.emit(f"page {rec.page_start}: {e}")
                return
            self.progress.emit(i, total, Path(rec.source_path).name)
        self.finished_ok.emit(self.records)
