"""검수 입력 폼."""

from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.data_models import ReviewStatus, StudentRecord


class ReviewPanel(QWidget):
    """선택된 StudentRecord 필드 편집."""

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._record: StudentRecord | None = None
        self._edits: dict[str, QLineEdit] = {}

        root = QVBoxLayout(self)
        self._keywords = QLabel("")
        root.addWidget(self._keywords)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        self._form = QFormLayout(inner)
        scroll.setWidget(inner)
        root.addWidget(scroll)

        btns = QHBoxLayout()
        self.btn_done = QPushButton("검수완료")
        self.btn_next = QPushButton("다음 미검수")
        btns.addWidget(self.btn_done)
        btns.addWidget(self.btn_next)
        root.addLayout(btns)

        self.btn_done.clicked.connect(self._mark_done)
        self.btn_next.clicked.connect(self._emit_next_unreviewed)

    next_unreviewed = pyqtSignal()

    def set_record(self, rec: StudentRecord | None) -> None:
        self._clear_form()
        self._record = rec
        if not rec:
            return
        self._keywords.setText(
            f"위험도: {rec.risk_level.value} | 키워드: {', '.join(rec.detected_keywords[:12])}"
        )
        for fid in sorted(rec.fields.keys()):
            f = rec.fields[fid]
            le = QLineEdit(f.normalized_value or f.ocr_text)
            le.setPlaceholderText(f"{f.standard_name} (conf {f.confidence:.2f})")
            self._edits[fid] = le
            self._form.addRow(QLabel(f"{fid}"), le)

    def _clear_form(self) -> None:
        while self._form.count():
            item = self._form.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._edits.clear()

    def _mark_done(self) -> None:
        if not self._record:
            return
        for fid, le in self._edits.items():
            if fid in self._record.fields:
                self._record.fields[fid].normalized_value = le.text()
                self._record.fields[fid].ocr_text = le.text()
        self._record.review_status = ReviewStatus.REVIEWED
        self.changed.emit()

    def _emit_next_unreviewed(self) -> None:
        self.next_unreviewed.emit()
