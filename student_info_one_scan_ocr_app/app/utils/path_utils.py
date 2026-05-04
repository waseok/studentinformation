"""
실행 경로 및 작업 디렉터리 유틸리티.
PyInstaller 번들(sys._MEIPASS)과 개발 모드를 구분합니다.
"""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """PyInstaller 등으로 패키징된 실행 파일인지 여부."""
    return getattr(sys, "frozen", False)


def get_bundle_dir() -> Path:
    """번들된 리소스가 있는 디렉터리(읽기 전용일 수 있음)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]


def get_work_dir() -> Path:
    """
    사용자 데이터·출력·로그·임시 파일을 둘 쓰기 가능한 기준 디렉터리.
    - frozen: 실행 파일이 있는 폴더
    - 개발: 프로젝트 루트 (student_info_one_scan_ocr_app/)
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def subdir(name: str) -> Path:
    """작업 디렉터리 하위 폴더 경로."""
    return get_work_dir() / name


def ensure_runtime_dirs() -> dict[str, Path]:
    """
    config, templates, output, logs, temp 폴더를 생성하고 경로 dict를 반환.
    templates는 번들에서 복사할 소스가 있으면 워크 디렉터리에 없을 때만 복사하지 않고,
    앱은 워크 디렉터리의 templates를 우선 사용합니다.
    """
    paths = {
        "work": get_work_dir(),
        "config": subdir("config"),
        "templates": subdir("templates"),
        "output": subdir("output"),
        "logs": subdir("logs"),
        "temp": subdir("temp"),
    }
    for key in ("config", "templates", "output", "logs", "temp"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def resource_path(relative: str) -> Path:
    """번들 내 기본 리소스 파일 경로(패키지 옆 samples 등)."""
    return get_bundle_dir() / relative
