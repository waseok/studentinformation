"""config/*.json 로드 및 기본값 자동 생성."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.utils.path_utils import get_work_dir, resource_path

DEFAULT_APP_SETTINGS: dict[str, Any] = {
    "tesseract_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "default_output_dir": "",
    "ocr_lang": "kor+eng",
    "dpi": 300,
    "save_raw_ocr": True,
    "delete_temp_files": False,
    "use_qr_form_id": True,
    "default_school_name": "",
    "default_retention_period": "학년도 종료 후 1년",
    "pages_per_student": 1,
    "default_sort_mode": "pdf_order",
    "minimize_pii_export": False,
    "health_sheet_exclude_address": True,
}


def _config_dir() -> Path:
    return get_work_dir() / "config"


def _write_if_missing(path: Path, data: dict[str, Any] | list[Any]) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_default_config_files() -> None:
    """없는 설정 파일만 기본 템플릿으로 생성."""
    cfg = _config_dir()
    _write_if_missing(cfg / "app_settings.json", DEFAULT_APP_SETTINGS.copy())

    bundled = resource_path("config")
    if bundled.is_dir():
        for src in bundled.glob("*.json"):
            if src.name == "app_settings.json":
                continue
            dst = cfg / src.name
            if not dst.exists():
                shutil.copy2(src, dst)

    bundled_tpl = resource_path("templates")
    work_tpl = get_work_dir() / "templates"
    work_tpl.mkdir(parents=True, exist_ok=True)
    if bundled_tpl.is_dir():
        for src in bundled_tpl.glob("*.json"):
            dst = work_tpl / src.name
            if not dst.exists():
                shutil.copy2(src, dst)


def load_json(name: str) -> dict[str, Any]:
    path = _config_dir() / name
    if not path.exists():
        ensure_default_config_files()
    with open(_config_dir() / name, encoding="utf-8") as f:
        return json.load(f)


def save_json(name: str, data: dict[str, Any]) -> None:
    path = _config_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_app_settings() -> dict[str, Any]:
    ensure_default_config_files()
    data = load_json("app_settings.json")
    merged = DEFAULT_APP_SETTINGS.copy()
    merged.update(data)
    return merged
