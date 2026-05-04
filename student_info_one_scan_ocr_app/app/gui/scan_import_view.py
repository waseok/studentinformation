"""스캔 가져오기 헬퍼(메인 윈도우에서 호출)."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import QFileDialog


def pick_pdf(parent) -> list[Path]:
    paths, _ = QFileDialog.getOpenFileNames(parent, "학급 스캔 PDF", "", "PDF (*.pdf)")
    return [Path(p) for p in paths]


def pick_template_json(parent) -> Path | None:
    path, _ = QFileDialog.getOpenFileName(parent, "form_template.json 선택", "", "JSON (*.json)")
    return Path(path) if path else None


def pick_roster_excel(parent) -> Path | None:
    path, _ = QFileDialog.getOpenFileName(parent, "학급 명단 Excel", "", "Excel (*.xlsx *.xls)")
    return Path(path) if path else None
