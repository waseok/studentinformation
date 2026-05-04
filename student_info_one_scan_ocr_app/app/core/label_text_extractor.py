"""전체 OCR 텍스트에서 라벨 alias 기반 보조 추출(검수 대기 전용)."""

from __future__ import annotations

import re
from typing import Any

from PIL import Image

from app.core.ocr_engine import ocr_image, ocr_image_data

def extract_after_label(full_text: str, labels: list[str]) -> str | None:
    """첫 매칭 라벨 뒤의 한 줄 또는 공백까지 토큰."""
    lines = full_text.splitlines()
    joined = "\n".join(lines)
    for lab in labels:
        for i, line in enumerate(lines):
            if lab in line:
                after = line.split(lab, 1)[-1].strip(" :：\t")
                if after:
                    return after[:200]
                if i + 1 < len(lines):
                    nxt = lines[i + 1].strip()
                    if nxt:
                        return nxt[:200]
        m = re.search(re.escape(lab) + r"\s*[:：]?\s*(.+)", joined)
        if m:
            return m.group(1).strip()[:200]
    return None


def augment_with_aliases(
    full_text: str,
    field_aliases: dict[str, list[str]],
) -> dict[str, str]:
    """standard_name -> 추정값."""
    out: dict[str, str] = {}
    for std, aliases in field_aliases.items():
        val = extract_after_label(full_text, [std, *aliases])
        if val:
            out[std] = val
    return out


def _norm_token(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", s).lower()


def extract_with_anchor_regions(
    image: Image.Image,
    field_aliases: dict[str, list[str]],
    *,
    ocr_lang: str,
) -> dict[str, dict[str, Any]]:
    """
    라벨(앵커) 텍스트 위치를 먼저 찾고, 라벨 오른쪽/아래의 동적 bbox를 OCR해 값을 추정한다.
    반환: standard_name -> {"value": str, "confidence": float}
    """
    data = ocr_image_data(image, ocr_lang, psm=6, oem=3)
    words = data.get("text", [])
    lefts = data.get("left", [])
    tops = data.get("top", [])
    widths = data.get("width", [])
    heights = data.get("height", [])
    img_w, img_h = image.size

    out: dict[str, dict[str, Any]] = {}

    for std_name, aliases in field_aliases.items():
        labels = [_norm_token(std_name)] + [_norm_token(a) for a in aliases]
        labels = [x for x in labels if x]
        if not labels:
            continue

        best_val = ""
        best_conf = 0.0

        for i, wtxt in enumerate(words):
            tok = _norm_token(str(wtxt))
            if not tok:
                continue
            if not any((lab in tok) or (tok in lab) for lab in labels):
                continue

            try:
                lx = int(lefts[i])
                ly = int(tops[i])
                lw = int(widths[i])
                lh = int(heights[i])
            except Exception:
                continue

            # 1차: 라벨 오른쪽 영역
            rx0 = min(img_w - 1, lx + lw + 6)
            rx1 = min(img_w, lx + int(img_w * 0.55))
            ry0 = max(0, ly - 2)
            ry1 = min(img_h, ly + max(24, int(lh * 1.8)))
            if rx1 > rx0 and ry1 > ry0:
                crop_r = image.crop((rx0, ry0, rx1, ry1))
                val_r = ocr_image(crop_r, ocr_lang, psm=7, oem=3).strip()
                data_r = ocr_image_data(crop_r, ocr_lang, psm=7, oem=3)
                cands = [int(c) for c in data_r.get("conf", []) if str(c).isdigit() and int(c) >= 0]
                conf_r = (sum(cands) / (len(cands) * 100.0)) if cands else 0.0
                if len(val_r) > len(best_val) or conf_r > best_conf:
                    best_val, best_conf = val_r, conf_r

            # 2차: 라벨 아래 줄(오른쪽이 비는 경우 대비)
            by0 = min(img_h - 1, ly + lh + 2)
            by1 = min(img_h, by0 + max(24, int(lh * 2.2)))
            bx0 = max(0, lx)
            bx1 = min(img_w, lx + int(img_w * 0.6))
            if bx1 > bx0 and by1 > by0:
                crop_b = image.crop((bx0, by0, bx1, by1))
                val_b = ocr_image(crop_b, ocr_lang, psm=6, oem=3).strip()
                data_b = ocr_image_data(crop_b, ocr_lang, psm=6, oem=3)
                cands_b = [int(c) for c in data_b.get("conf", []) if str(c).isdigit() and int(c) >= 0]
                conf_b = (sum(cands_b) / (len(cands_b) * 100.0)) if cands_b else 0.0
                if len(val_b) > len(best_val) or conf_b > best_conf:
                    best_val, best_conf = val_b, conf_b

        if best_val.strip():
            out[std_name] = {"value": best_val.strip()[:200], "confidence": float(best_conf)}

    return out


def load_field_aliases(path: Any) -> dict[str, list[str]]:
    import json
    from pathlib import Path

    p = Path(path)
    if not p.is_file():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)
