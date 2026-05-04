"""애플리케이션 로깅 설정. PII는 sanitize 후 기록."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from app.utils.privacy_utils import sanitize_log_message


class PrivacyFilter(logging.Filter):
    """LogRecord.getMessage() 결과에 sanitize 적용."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            raw = record.getMessage()
            record.msg = sanitize_log_message(raw)
            record.args = ()
        except Exception:
            pass
        return True


def setup_logging(log_dir: Path, level: int = logging.INFO) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)
    fh.addFilter(PrivacyFilter())

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(fmt)
    sh.addFilter(PrivacyFilter())

    root.addHandler(fh)
    root.addHandler(sh)

    return logging.getLogger("student_info_ocr")
