"""Tesseract 래퍼 및 설치 상태 점검."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytesseract
from PIL import Image


@dataclass
class TesseractStatus:
    available: bool
    tesseract_path: str
    kor_data_present: bool
    message: str


def check_tesseract(tesseract_exe: str | Path) -> TesseractStatus:
    exe = Path(tesseract_exe)
    if not exe.is_file():
        return TesseractStatus(False, str(tesseract_exe), False, "Tesseract 실행 파일을 찾을 수 없습니다.")

    pytesseract.pytesseract.tesseract_cmd = str(exe)
    tessdata = exe.parent / "tessdata"
    kor = tessdata / "kor.traineddata"
    kor_ok = kor.is_file()

    try:
        _ = pytesseract.get_tesseract_version()
    except Exception as e:
        return TesseractStatus(False, str(exe), kor_ok, f"Tesseract 실행 실패: {e}")

    msg = "준비됨"
    if not kor_ok:
        msg = "kor.traineddata가 없습니다. TESSDATA_PREFIX 또는 tessdata 폴더에 한국어 데이터를 설치하세요."
    return TesseractStatus(True, str(exe), kor_ok, msg)


def apply_tesseract_env(tesseract_exe: str | Path) -> None:
    """tessdata 상위 경로를 TESSDATA_PREFIX에 설정(필요 시)."""
    exe = Path(tesseract_exe)
    if exe.is_file():
        pytesseract.pytesseract.tesseract_cmd = str(exe)
        tessdata = exe.parent / "tessdata"
        if tessdata.is_dir():
            os.environ.setdefault("TESSDATA_PREFIX", str(tessdata.parent))


def ocr_image(
    image: Image.Image,
    lang: str,
    *,
    psm: int = 6,
    oem: int = 3,
    whitelist: str | None = None,
) -> str:
    cfg = f"--oem {oem} --psm {psm}"
    if whitelist:
        cfg += f' -c tessedit_char_whitelist="{whitelist}"'
    return pytesseract.image_to_string(image, lang=lang, config=cfg).strip()


def ocr_image_data(
    image: Image.Image,
    lang: str,
    *,
    psm: int = 6,
    oem: int = 3,
) -> list[dict[str, Any]]:
    """단어 단위 confidence."""
    cfg = f"--oem {oem} --psm {psm}"
    return pytesseract.image_to_data(image, lang=lang, config=cfg, output_type=pytesseract.Output.DICT)
