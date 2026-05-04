"""표준 양식 생성 대화상자."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.core.form_generator import generate_form
from app.utils.path_utils import get_work_dir


class FormGeneratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("표준 조사서 양식 만들기")
        self._out_dir = str(get_work_dir() / "output")

        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.ed_year = QLineEdit("2026")
        self.ed_school = QLineEdit("")
        self.ed_grade = QLineEdit("3")
        self.ed_class = QLineEdit("2")
        self.ed_teacher = QLineEdit("")
        self.ed_due = QLineEdit("")
        self.cb_notice = QCheckBox("안내문 포함")
        self.cb_notice.setChecked(True)
        self.cb_personal = QCheckBox("개인정보 동의 포함")
        self.cb_personal.setChecked(True)
        self.cb_sensitive = QCheckBox("민감정보 동의 포함")
        self.cb_sensitive.setChecked(True)
        self.cb_sign = QCheckBox("보호자 서명란 포함")
        self.cb_sign.setChecked(True)
        self.cb_qr = QCheckBox("QR(양식 버전 ID)")
        self.cb_qr.setChecked(True)

        form.addRow("학년도", self.ed_year)
        form.addRow("학교명", self.ed_school)
        form.addRow("학년", self.ed_grade)
        form.addRow("반", self.ed_class)
        form.addRow("담임명", self.ed_teacher)
        form.addRow("제출기한", self.ed_due)
        lay.addLayout(form)
        lay.addWidget(self.cb_notice)
        lay.addWidget(self.cb_personal)
        lay.addWidget(self.cb_sensitive)
        lay.addWidget(self.cb_sign)
        lay.addWidget(self.cb_qr)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._run)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _run(self) -> None:
        out = Path(self._out_dir)
        out.mkdir(parents=True, exist_ok=True)
        try:
            res = generate_form(
                output_dir=out,
                school_year=self.ed_year.text().strip(),
                school_name=self.ed_school.text().strip(),
                grade=self.ed_grade.text().strip(),
                class_no=self.ed_class.text().strip(),
                homeroom_teacher=self.ed_teacher.text().strip(),
                due_date=self.ed_due.text().strip(),
                include_notice=self.cb_notice.isChecked(),
                include_personal_consent=self.cb_personal.isChecked(),
                include_sensitive_consent=self.cb_sensitive.isChecked(),
                include_guardian_signature=self.cb_sign.isChecked(),
                use_qr=self.cb_qr.isChecked(),
            )
            QMessageBox.information(
                self,
                "완료",
                f"PDF 및 form_template.json을 생성했습니다.\n{res['pdf']}\n버전: {res['form_version']}",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
