"""체크박스 영역의 채움 여부 휴리스틱."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image


@dataclass
class CheckboxResult:
    checked: bool
    confidence: float
    needs_review: bool


def detect_checkbox(crop: Image.Image, *, thresh: float = 0.12) -> CheckboxResult:
    """
    검은/진한 잉크 비율이 thresh 이상이면 체크된 것으로 간주.
    confidence는 0~1 (휴리스틱).
    """
    gray = np.array(crop.convert("L"))
    if gray.size == 0:
        return CheckboxResult(False, 0.0, True)
    # 이진화 후 검은 픽셀 비율
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    dark_ratio = float(np.mean(bw == 255))
    checked = dark_ratio >= thresh
    # 경계 근처면 검토
    margin = 0.04
    needs = abs(dark_ratio - thresh) < margin
    conf = min(1.0, abs(dark_ratio - thresh) / max(thresh, 1 - thresh))
    return CheckboxResult(checked=checked, confidence=conf, needs_review=needs)
