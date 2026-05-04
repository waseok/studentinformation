"""
학급 기초자료 조사서 원스캔 OCR 취합 프로그램 엔트리포인트.
실행: student_info_one_scan_ocr_app 폴더에서 `python main.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 import 경로에 추가
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    import os

    from PyQt5.QtWidgets import QApplication

    from app.core.logger import setup_logging
    from app.core.settings_manager import ensure_default_config_files
    from app.gui.main_window import MainWindow
    from app.utils.path_utils import ensure_runtime_dirs

    dirs = ensure_runtime_dirs()
    os.chdir(str(dirs["work"]))
    ensure_default_config_files()
    setup_logging(dirs["logs"])

    app = QApplication(sys.argv)
    app.setApplicationName("학급 기초자료 조사서 원스캔 OCR 취합 프로그램")
    app.setStyleSheet(
        """
        QToolBar {
            spacing: 8px;
            padding: 6px;
            border-bottom: 1px solid #d0d7de;
            background: #f8fafc;
        }
        QToolButton {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 8px 12px;
            min-height: 34px;
            font-size: 13px;
            font-weight: 700;
            color: #0f172a;
        }
        QToolButton:hover {
            background: #e2e8f0;
        }
        QToolButton:pressed {
            background: #cbd5e1;
        }
        QPushButton {
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            min-height: 34px;
            font-size: 13px;
            font-weight: 700;
        }
        QPushButton:hover {
            background: #1d4ed8;
        }
        QPushButton:pressed {
            background: #1e40af;
        }
        """
    )
    win = MainWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
