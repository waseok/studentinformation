"""스캔 이미지 전처리."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def pil_to_cv(img: Image.Image) -> np.ndarray:
    rgb = np.array(img.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def cv_to_pil(arr: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def preprocess(
    img: Image.Image,
    *,
    grayscale: bool = True,
    denoise: bool = True,
    adaptive_thresh: bool = False,
    deskew: bool = False,
) -> Image.Image:
    bgr = pil_to_cv(img)
    if grayscale:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    if deskew:
        gray = _deskew_gray(gray)

    if denoise:
        gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    if adaptive_thresh:
        gray = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 10
        )

    return Image.fromarray(gray)


def _deskew_gray(gray: np.ndarray) -> np.ndarray:
    """간단한 최소외접사각형 기울기 보정."""
    thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thr > 0))
    if coords.size < 10:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.1:
        return gray
    (h, w) = gray.shape[:2]
    m = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(gray, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
