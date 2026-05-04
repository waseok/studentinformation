"""메인 윈도우: 툴바, 분할 뷰, 탭, OCR 워커."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.data_models import ReviewStatus, StudentRecord
from app.core.excel_exporter import export_master_workbook
from app.core.file_loader import collect_files, is_pdf
from app.core.ocr_engine import check_tesseract
from app.core.roster_matcher import load_roster_df, match_records
from app.core.scan_processor import build_student_records_from_pdf
from app.core.settings_manager import load_app_settings
from app.gui.form_generator_view import FormGeneratorDialog
from app.gui.image_viewer import ImageViewer
from app.gui.result_table import StudentTableModel
from app.gui.review_panel import ReviewPanel
from app.gui.scan_import_view import pick_pdf, pick_roster_excel, pick_template_json
from app.gui.settings_dialog import SettingsDialog
from app.utils.path_utils import ensure_runtime_dirs
from app.workers.ocr_worker import OCRWorker

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("학급 기초자료 조사서 원스캔 OCR 취합 프로그램")
        self.resize(1280, 800)

        self._records: list[StudentRecord] = []
        self._template_path: Path | None = None
        self._form_version: str = ""
        self._roster_df = None
        self._worker: OCRWorker | None = None
        self._errors: list[dict] = []

        dirs = ensure_runtime_dirs()
        self._temp_dir = dirs["temp"]
        self._output_dir = dirs["output"]

        self._build_ui()
        self._refresh_tesseract_hint()

    def _build_ui(self) -> None:
        tb = self.addToolBar("main")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setToolButtonStyle(Qt.ToolButtonTextOnly)
        tb.addAction("배부용 양식 만들기").triggered.connect(self._open_form_dialog)
        tb.addAction("스캔 파일 열기").triggered.connect(self._add_pdf)
        tb.addAction("양식 파일 선택(고급)").triggered.connect(self._pick_template)
        tb.addAction("학교 명단 파일 불러오기(선택)").triggered.connect(self._load_roster)
        self._act_ocr = tb.addAction("다시 인식하기")
        self._act_ocr.triggered.connect(self._run_ocr)
        tb.addAction("결과 저장").triggered.connect(self._save_excel)
        tb.addAction("환경 설정").triggered.connect(self._open_settings)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._lbl_progress = QLabel("")
        self._btn_cancel = QPushButton("OCR 중단")
        self._btn_cancel.setVisible(False)
        self._btn_cancel.clicked.connect(self._cancel_ocr)
        self._btn_cancel.setStyleSheet("background:#b91c1c;color:white;")
        ph = QHBoxLayout()
        ph.addWidget(self._progress, 1)
        ph.addWidget(self._lbl_progress)
        ph.addWidget(self._btn_cancel)
        outer.addLayout(ph)

        split = QSplitter(Qt.Horizontal)
        outer.addWidget(split, 1)

        self._table = QTableView()
        self._model = StudentTableModel(self)
        self._table.setModel(self._model)
        self._table.selectionModel().selectionChanged.connect(self._on_table_sel)
        split.addWidget(self._table)

        mid = QWidget()
        ml = QVBoxLayout(mid)
        self._viewer = ImageViewer()
        ml.addWidget(self._viewer, 1)
        hb = QHBoxLayout()
        self._btn_rot = QPushButton("90° 회전")
        self._btn_rot.clicked.connect(self._viewer.rotate_90)
        self._btn_fit = QPushButton("맞춤")
        self._btn_fit.clicked.connect(self._viewer.reset_view)
        self._btn_rot.setStyleSheet("background:#475569;color:white;")
        self._btn_fit.setStyleSheet("background:#475569;color:white;")
        hb.addWidget(self._btn_rot)
        hb.addWidget(self._btn_fit)
        ml.addLayout(hb)
        split.addWidget(mid)

        self._review = ReviewPanel()
        self._review.changed.connect(self._on_review_changed)
        self._review.next_unreviewed.connect(self._goto_next_unreviewed)
        split.addWidget(self._review)
        split.setSizes([320, 520, 420])

        self._tabs = QTabWidget()
        self._tab_raw = QTextEdit()
        self._tab_norm = QTextEdit()
        self._tab_kw = QTextEdit()
        self._tab_log = QTextEdit()
        self._tabs.addTab(self._tab_raw, "인식 원문")
        self._tabs.addTab(self._tab_norm, "정리된 결과")
        self._tabs.addTab(self._tab_kw, "주의 키워드")
        self._tabs.addTab(QLabel("(상세 표는 결과 엑셀 파일에서 확인하세요)"), "도움말")
        self._tabs.addTab(self._tab_log, "진행 기록")
        outer.addWidget(self._tabs)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dropEvent(self, e: QDropEvent) -> None:
        paths = [Path(u.toLocalFile()) for u in e.mimeData().urls()]
        self._ingest_paths(paths)

    def _append_log(self, msg: str) -> None:
        self._tab_log.append(msg)
        log.info(msg)

    def _refresh_tesseract_hint(self) -> None:
        st = check_tesseract(load_app_settings().get("tesseract_path", ""))
        self._act_ocr.setEnabled(st.available and st.kor_data_present)
        if not st.available:
            self._append_log("문자인식 준비가 필요합니다: '환경 설정'에서 Tesseract 경로를 지정하세요.")
        elif not st.kor_data_present:
            self._append_log("한국어 인식 파일(kor.traineddata)이 없습니다. 설치 후 다시 시도하세요.")

    def _open_form_dialog(self) -> None:
        dlg = FormGeneratorDialog(self)
        dlg.exec_()

    def _open_settings(self) -> None:
        if SettingsDialog(self).exec_():
            self._refresh_tesseract_hint()

    def _pick_template(self) -> None:
        p = pick_template_json(self)
        if p:
            self._template_path = p
            try:
                import json

                with open(p, encoding="utf-8") as f:
                    self._form_version = json.load(f).get("form_version", "")
            except Exception:
                self._form_version = ""
            self._append_log(f"양식 파일 선택됨: {p.name}")

    def _add_pdf(self) -> None:
        paths = pick_pdf(self)
        self._ingest_paths(paths)

    def _ingest_paths(self, paths: list[Path]) -> None:
        files = collect_files(paths)
        if not files:
            QMessageBox.information(self, "안내", "PDF 파일이 없습니다.")
            return
        settings = load_app_settings()
        dpi = int(settings.get("dpi", 300))
        pps = int(settings.get("pages_per_student", 1))
        all_recs: list[StudentRecord] = []
        for f in files:
            if is_pdf(f):
                try:
                    recs = build_student_records_from_pdf(f, self._temp_dir, dpi=dpi, pages_per_student=pps)
                    all_recs.extend(recs)
                except Exception as ex:
                    self._errors.append(
                        {
                            "source_file": f.name,
                            "page_no": "",
                            "field_id": "",
                            "error_type": "pdf_render",
                            "error_message": str(ex),
                            "recommended_action": "PDF 손상 여부 확인",
                        }
                    )
                    self._append_log(f"PDF 로드 실패: {f.name}")
        self._records = all_recs
        self._model.set_records(self._records)
        self._append_log(f"불러온 문서 수: {len(self._records)}명 분량")
        self._auto_start_ocr_if_possible()

    def _load_roster(self) -> None:
        p = pick_roster_excel(self)
        if not p:
            return
        try:
            self._roster_df = load_roster_df(str(p))
            rows = match_records(self._roster_df, self._records)
            self._append_log(f"학교 명단 대조 완료: {len(rows)}건")
        except Exception as e:
            QMessageBox.warning(self, "학교 명단", str(e))

    def _auto_start_ocr_if_possible(self) -> None:
        if not self._records:
            return
        settings = load_app_settings()
        st = check_tesseract(settings.get("tesseract_path", ""))
        if not (st.available and st.kor_data_present):
            self._append_log("자동 인식은 준비 상태가 아닙니다. '환경 설정'을 먼저 확인하세요.")
            return
        self._append_log("스캔 파일을 불러왔습니다. 자동 인식을 시작합니다.")
        self._run_ocr(auto_mode=True)

    def _current_record(self) -> StudentRecord | None:
        idxs = self._table.selectionModel().selectedRows()
        if not idxs:
            return None
        return self._model.record_at(idxs[0].row())

    def _on_table_sel(self) -> None:
        rec = self._current_record()
        self._review.set_record(rec)
        if rec and rec.render_image_paths:
            self._viewer.load_path(rec.render_image_paths[0])
        self._fill_tabs(rec)

    def _fill_tabs(self, rec: StudentRecord | None) -> None:
        if not rec:
            self._tab_raw.clear()
            self._tab_norm.clear()
            self._tab_kw.clear()
            return
        raw_lines = [f"{k}: {v.ocr_text}" for k, v in sorted(rec.fields.items())]
        self._tab_raw.setPlainText("\n".join(raw_lines))
        norm_lines = [f"{k}: {v.normalized_value}" for k, v in sorted(rec.fields.items())]
        self._tab_norm.setPlainText("\n".join(norm_lines))
        self._tab_kw.setPlainText(", ".join(rec.detected_keywords))

    def _run_ocr(self, auto_mode: bool = False) -> None:
        if not self._records:
            QMessageBox.information(self, "안내", "먼저 스캔 파일을 열어주세요.")
            return
        if not self._template_path:
            if not auto_mode:
                ret = QMessageBox.question(
                    self,
                    "양식 파일 없음",
                    "양식 파일 없이도 자동 인식은 가능하지만 정확도가 낮아질 수 있습니다.\n"
                    "계속 진행할까요?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if ret != QMessageBox.Yes:
                    p = pick_template_json(self)
                    if not p:
                        return
                    self._template_path = p
        settings = load_app_settings()
        st = check_tesseract(settings.get("tesseract_path", ""))
        if not (st.available and st.kor_data_present):
            QMessageBox.warning(self, "문자인식", st.message)
            return
        self._worker = OCRWorker(
            self._records,
            self._template_path,
            settings.get("tesseract_path", ""),
            settings.get("ocr_lang", "kor+eng"),
        )
        self._worker.progress.connect(self._on_ocr_progress)
        self._worker.finished_ok.connect(self._on_ocr_done)
        self._worker.failed.connect(self._on_ocr_fail)
        self._progress.setMaximum(len(self._records))
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._btn_cancel.setVisible(True)
        self._worker.start()

    def _cancel_ocr(self) -> None:
        if self._worker:
            self._worker.cancel()

    def _on_ocr_progress(self, cur: int, total: int, name: str) -> None:
        self._progress.setValue(cur)
        self._lbl_progress.setText(f"{cur} / {total} — {name}")

    def _on_review_changed(self) -> None:
        rc = self._model.rowCount()
        cc = self._model.columnCount()
        if rc > 0 and cc > 0:
            self._model.dataChanged.emit(
                self._model.index(0, 0),
                self._model.index(rc - 1, cc - 1),
            )

    def _on_ocr_done(self, records: list[StudentRecord]) -> None:
        self._records = records
        self._model.set_records(self._records)
        self._progress.setVisible(False)
        self._btn_cancel.setVisible(False)
        self._lbl_progress.setText("")
        if self._roster_df is not None:
            match_records(self._roster_df, self._records)
        self._on_review_changed()
        if self._template_path is None:
            self._append_log("자동 인식 완료 (일반 문서 모드)")
        else:
            self._append_log("자동 인식 완료 (양식 기준 모드)")

    def _on_ocr_fail(self, msg: str) -> None:
        self._progress.setVisible(False)
        self._btn_cancel.setVisible(False)
        QMessageBox.critical(self, "인식 오류", msg)
        self._errors.append(
            {
                "source_file": "",
                "page_no": "",
                "field_id": "",
                "error_type": "ocr",
                "error_message": msg,
                "recommended_action": "Tesseract 및 이미지 확인",
            }
        )

    def _goto_next_unreviewed(self) -> None:
        for i, r in enumerate(self._records):
            if r.review_status != ReviewStatus.REVIEWED:
                self._table.selectRow(i)
                return

    def _save_excel(self) -> None:
        if not self._records:
            QMessageBox.information(self, "안내", "저장할 결과가 없습니다.")
            return
        ret = QMessageBox.warning(
            self,
            "개인정보",
            "개인정보 및 민감정보가 포함된 파일입니다. 저장 위치를 확인하세요.",
            QMessageBox.Ok | QMessageBox.Cancel,
        )
        if ret != QMessageBox.Ok:
            return
        settings = load_app_settings()
        grade = "0"
        ban = "0"
        for r in self._records:
            g = r.fields.get("F001")
            if g and g.normalized_value:
                grade = g.normalized_value
                break
        for r in self._records:
            b = r.fields.get("F002")
            if b and b.normalized_value:
                ban = b.normalized_value
                break
        year = settings.get("default_school_name", "") or "출력"
        fname = f"2026_{grade}학년{ban}반_학생기초자료_OCR취합_master.xlsx"
        out = self._output_dir / fname
        roster_rows = None
        if self._roster_df is not None:
            roster_rows = match_records(self._roster_df, self._records)
        else:
            roster_rows = [
                {
                    "roster_grade": "",
                    "roster_class": "",
                    "roster_number": r.extracted_number(),
                    "roster_name": r.extracted_name(),
                    "ocr_page_no": r.page_start,
                    "ocr_number": r.extracted_number(),
                    "ocr_name": r.extracted_name(),
                    "match_status": "auto_from_scan",
                    "review_needed_reason": "학교 명단 파일 미사용",
                }
                for r in self._records
            ]
        try:
            export_master_workbook(
                out,
                self._records,
                form_version=self._form_version or "unknown",
                roster_rows=roster_rows,
                errors=self._errors,
                settings_snapshot=settings,
                minimize_pii=bool(settings.get("minimize_pii_export")),
                health_exclude_address=bool(settings.get("health_sheet_exclude_address", True)),
            )
            QMessageBox.information(self, "완료", str(out))
        except PermissionError:
            QMessageBox.warning(self, "오류", "파일이 열려 있거나 권한이 없습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
