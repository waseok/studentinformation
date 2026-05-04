"""Tesseract 및 OCR 설정."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.ocr_engine import check_tesseract
from app.core.settings_manager import load_app_settings, save_json


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("환경 설정(쉬운 설정)")
        self._settings = load_app_settings()

        lay = QVBoxLayout(self)
        lay.addWidget(
            QLabel(
                "어려운 건 최소화했습니다.\n"
                "보통은 1) Tesseract 경로만 지정하고 2) 저장을 누르면 됩니다."
            )
        )
        form = QFormLayout()
        self.ed_tesseract = QLineEdit(self._settings.get("tesseract_path", ""))
        row = QWidget()
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.ed_tesseract)
        btn_find = QPushButton("찾기...")
        btn_find.clicked.connect(self._browse_tesseract)
        hl.addWidget(btn_find)
        form.addRow("문자인식 프로그램 위치", row)

        self.sp_dpi = QSpinBox()
        self.sp_dpi.setRange(150, 600)
        self.sp_dpi.setValue(int(self._settings.get("dpi", 300)))
        form.addRow("스캔 선명도(기본 300)", self.sp_dpi)

        self.ed_lang = QLineEdit(self._settings.get("ocr_lang", "kor+eng"))
        form.addRow("인식 언어", self.ed_lang)

        lay.addLayout(form)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _browse_tesseract(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "tesseract.exe 선택",
            "C:/Program Files/Tesseract-OCR",
            "Executable (tesseract.exe)",
        )
        if path:
            self.ed_tesseract.setText(path)

    def _save(self) -> None:
        st = check_tesseract(self.ed_tesseract.text())
        if not st.available:
            QMessageBox.warning(self, "문자인식 준비", st.message)
        elif not st.kor_data_present:
            QMessageBox.warning(self, "문자인식 준비", st.message)
        # 기존 설정 전체를 유지한 채 일부만 갱신
        full = load_app_settings()
        full["tesseract_path"] = self.ed_tesseract.text()
        full["dpi"] = self.sp_dpi.value()
        full["ocr_lang"] = self.ed_lang.text()
        save_json("app_settings.json", full)
        self.accept()
