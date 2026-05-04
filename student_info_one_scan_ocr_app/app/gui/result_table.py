"""좌측 학생/페이지 목록 테이블."""

from __future__ import annotations

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QColor, QBrush

from app.core.data_models import ReviewStatus, StudentRecord


class StudentTableModel(QAbstractTableModel):
    HEADERS = ["쪽", "성명", "번호", "명단", "검수", "위험도", "오류"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[StudentRecord] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return str(section + 1)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        r = self._rows[index.row()]
        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0:
                return f"{r.page_start}-{r.page_end}"
            if col == 1:
                return r.extracted_name() or "(이름없음)"
            if col == 2:
                return r.extracted_number() or "(번호없음)"
            if col == 3:
                return r.roster_match or "-"
            if col == 4:
                return r.review_status.value
            if col == 5:
                return r.risk_level.value
            if col == 6:
                return "Y" if r.errors else ""
        if role == Qt.ForegroundRole:
            if r.risk_level.value == "high":
                return QBrush(QColor(180, 0, 0))
            if r.review_status == ReviewStatus.REVIEWED:
                return QBrush(QColor(0, 120, 0))
            if r.review_status == ReviewStatus.NEEDS_REVIEW:
                return QBrush(QColor(160, 120, 0))
        return None

    def set_records(self, rows: list[StudentRecord]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def record_at(self, row: int) -> StudentRecord | None:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None
