"""form_template.json 좌표 기반 필드 OCR."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from PIL import Image

from app.core.checkbox_detector import detect_checkbox
from app.core.data_models import FieldOCRResult, ReviewStatus, StudentRecord
from app.core.form_schema import template_dict_to_field
from app.core.image_preprocessor import preprocess
from app.core.ocr_engine import apply_tesseract_env, ocr_image, ocr_image_data
from app.core.label_text_extractor import augment_with_aliases, extract_with_anchor_regions
from app.core.settings_manager import load_json
from app.utils.path_utils import get_work_dir
from app.utils.validation_utils import is_plausible_date, is_plausible_korean_name, is_plausible_phone

log = logging.getLogger(__name__)


def load_form_template(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _pixels_from_ratio(bbox_ratio: list[float], w: int, h: int) -> tuple[int, int, int, int]:
    x0 = max(0, int(bbox_ratio[0] * w))
    y0 = max(0, int(bbox_ratio[1] * h))
    x1 = min(w, int(bbox_ratio[2] * w))
    y1 = min(h, int(bbox_ratio[3] * h))
    if x1 <= x0 or y1 <= y0:
        return 0, 0, max(1, w // 2), max(1, h // 2)
    return x0, y0, x1, y1


def _mean_confidence(data: dict[str, Any]) -> float:
    confs = [int(c) for c in data.get("conf", []) if str(c).isdigit() and int(c) >= 0]
    if not confs:
        return 0.0
    return sum(confs) / (len(confs) * 100.0)


def _field_text_score(field_type: str, text: str, conf: float) -> float:
    """
    OCR 후보 텍스트를 타입별 유효성으로 재점수화.
    conf(0~1)에 패턴 가산점을 더해 최종 점수를 만든다.
    """
    t = text.strip()
    if not t:
        return conf - 0.2
    score = conf + min(len(t), 30) / 300.0
    if field_type == "phone":
        if is_plausible_phone(t):
            score += 0.45
        if re.search(r"\d{2,4}[-\s.]?\d{3,4}[-\s.]?\d{4}", t):
            score += 0.2
    elif field_type == "number":
        digits = re.sub(r"\D", "", t)
        if 1 <= len(digits) <= 4:
            score += 0.35
    elif field_type == "date":
        if is_plausible_date(t):
            score += 0.35
    elif field_type in ("text", "multiline_text"):
        if is_plausible_korean_name(t):
            score += 0.2
    return score


def _ocr_best_for_crop(
    crop: Image.Image,
    *,
    field_type: str,
    ocr_lang: str,
    psm: int,
    oem: int,
    whitelist: str | None,
) -> tuple[str, float]:
    """
    동일 crop에 대해 다중 전처리 + 다중 psm으로 OCR을 시도하고
    타입별 점수가 가장 높은 결과를 반환한다.
    """
    variants: list[Image.Image] = [
        crop,
        preprocess(crop, grayscale=True, denoise=True, adaptive_thresh=False, deskew=False),
        preprocess(crop, grayscale=True, denoise=True, adaptive_thresh=True, deskew=False),
        preprocess(crop, grayscale=True, denoise=False, adaptive_thresh=True, deskew=False),
    ]
    psm_candidates = [psm, 6, 7, 11]
    # 순서 보존 중복 제거
    seen_psm: set[int] = set()
    psm_list: list[int] = []
    for p in psm_candidates:
        if p not in seen_psm:
            seen_psm.add(p)
            psm_list.append(p)

    best_text = ""
    best_score = -999.0
    best_conf = 0.0
    for var in variants:
        for p in psm_list:
            txt = ocr_image(var, ocr_lang, psm=p, oem=oem, whitelist=whitelist)
            data = ocr_image_data(var, ocr_lang, psm=p, oem=oem)
            conf = _mean_confidence(data)
            score = _field_text_score(field_type, txt, conf)
            if score > best_score:
                best_score = score
                best_text = txt
                best_conf = conf
    return best_text, best_conf


def extract_fields_for_record(
    record: StudentRecord,
    template: dict[str, Any],
    *,
    tesseract_path: str,
    ocr_lang: str,
    use_preprocess: bool = False,
    temp_dir: Path | None = None,
) -> None:
    """
    record.render_image_paths 순서 = 양식 1쪽, 2쪽, ...
    template fields의 page_no는 1-based 양식 페이지 번호.
    """
    apply_tesseract_env(tesseract_path)
    temp_dir = temp_dir or (get_work_dir() / "temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    ocr_profiles = load_json("ocr_profiles.json")

    fields_def = [template_dict_to_field(d) for d in template.get("fields", [])]

    for fd in fields_def:
        page_idx = fd.page_no - 1
        if page_idx < 0 or page_idx >= len(record.render_image_paths):
            log.warning("field %s page %s out of range", fd.field_id, fd.page_no)
            continue
        img_path = record.render_image_paths[page_idx]
        base = Image.open(img_path)
        img = preprocess(base) if use_preprocess else base.convert("RGB")
        w, h = img.size
        x0, y0, x1, y1 = _pixels_from_ratio(fd.bbox_ratio, w, h)
        crop = img.crop((x0, y0, x1, y1))
        crop_path = temp_dir / f"{record.record_id}_{fd.field_id}.png"
        crop.save(crop_path)

        profile = ocr_profiles.get(fd.ocr_profile, ocr_profiles.get("default", {}))
        psm = int(profile.get("psm", 6))
        oem = int(profile.get("oem", 3))
        whitelist = profile.get("whitelist")

        if fd.field_type == "checkbox":
            chk = detect_checkbox(crop)
            if fd.checkbox_options:
                text = fd.checkbox_options[0] if chk.checked else ""
            else:
                text = "예" if chk.checked else "아니오"
            conf = chk.confidence
            needs = chk.needs_review
        else:
            text, conf = _ocr_best_for_crop(
                crop,
                field_type=fd.field_type,
                ocr_lang=ocr_lang,
                psm=psm,
                oem=oem,
                whitelist=whitelist,
            )
            needs = conf < 0.45 or len(text.strip()) == 0

        if fd.required and not text.strip():
            needs = True

        record.fields[fd.field_id] = FieldOCRResult(
            field_id=fd.field_id,
            standard_name=fd.standard_name,
            ocr_text=text,
            confidence=float(conf),
            crop_path=str(crop_path),
            needs_review=needs,
            field_type=fd.field_type,
            normalized_value=text,
        )

    record.review_status = ReviewStatus.NEEDS_REVIEW if any(
        f.needs_review for f in record.fields.values()
    ) else ReviewStatus.OCR_DONE


_STD_TO_FID = {
    "학년": "F001",
    "반": "F002",
    "번호": "F003",
    "학생 성명": "F004",
    "성명": "F004",
    "생년월일": "F005",
    "성별": "F006",
    "주소": "F007",
    "보호자1 성명": "F010",
    "보호자1 연락처": "F012",
    "보호자2 성명": "F013",
    "보호자2 연락처": "F015",
    "긴급연락 우선순위": "F016",
    "알레르기 내용": "F023",
    "현재 복용 약": "F030",
    "응급 유의사항": "F031",
    "주 이용 병원": "F032",
    "기타 건강 특이사항": "F033",
    "생활지도 참고": "F040",
    "보호자 요청": "F044",
    # 학교생활기록부 기초자료 양식 전용
    "학생전화번호": "F060",
    "통학방법_도보": "F061a",
    "통학방법_자가용": "F061b",
    "통학방법_등교버스": "F061c",
    "통학방법_학원차": "F061d",
    "통학방법_기타": "F061e",
    "맞벌이_예": "F062a",
    "맞벌이_아니오": "F062b",
    "방과후_보호자유무": "F063",
    "방과후_주활동": "F064",
    "선생님알림": "F065",
    "학습지도메모": "F066",
    "건강상태메모": "F067",
    "기타중요사항": "F068",
}


def extract_fields_with_label_fallback(
    record: StudentRecord,
    *,
    tesseract_path: str,
    ocr_lang: str,
    use_preprocess: bool = False,
) -> None:
    """
    비표준 양식 폴백:
    1) 페이지 전체 OCR 텍스트를 얻고
    2) field_aliases.json 기준 라벨-값 추정
    3) 표준 field_id(Fxxx)가 알려진 항목은 매핑 저장
    """
    apply_tesseract_env(tesseract_path)
    aliases = load_json("field_aliases.json")

    def _try_one_image(img: Image.Image) -> tuple[str, dict[str, dict[str, Any]], float]:
        txt = ocr_image(img, ocr_lang, psm=6, oem=3)
        by_anchor = extract_with_anchor_regions(img, aliases, ocr_lang=ocr_lang)
        # 텍스트 품질 점수: 핵심 패턴이 많을수록 가점
        quality = 0.0
        quality += len(re.findall(r"\d{2,4}[-\s.]?\d{3,4}[-\s.]?\d{4}", txt)) * 0.8
        quality += len(re.findall(r"(19|20)?\d{2}[.\-/]\d{1,2}[.\-/]\d{1,2}", txt)) * 0.6
        quality += len(re.findall(r"[가-힣]{2,4}", txt[:600])) * 0.03
        return txt, by_anchor, quality

    all_text_parts: list[str] = []
    anchor_merged: dict[str, dict[str, Any]] = {}
    for img_path in record.render_image_paths:
        base = Image.open(img_path)
        img0 = preprocess(base) if use_preprocess else base.convert("RGB")
        page_variants = [
            img0,
            preprocess(img0, grayscale=True, denoise=True, adaptive_thresh=True, deskew=False),
            preprocess(img0, grayscale=True, denoise=False, adaptive_thresh=True, deskew=False),
        ]

        # 회전 자동 재시도: 라벨 앵커 인식 점수가 가장 높은 각도를 선택
        best_txt = ""
        best_anchor: dict[str, dict[str, Any]] = {}
        best_score = -1.0
        for var in page_variants:
            for angle in (0, 90, 180, 270):
                cand = var if angle == 0 else var.rotate(angle, expand=True)
                txt, by_anchor, quality = _try_one_image(cand)
                conf_sum = sum(float(v.get("confidence", 0.0)) for v in by_anchor.values())
                score = len(by_anchor) * 12.0 + conf_sum * 2.0 + min(len(txt), 500) / 350.0 + quality
                if score > best_score:
                    best_score = score
                    best_txt = txt
                    best_anchor = by_anchor

        all_text_parts.append(best_txt)
        for std_name, payload in best_anchor.items():
            prev = anchor_merged.get(std_name)
            if prev is None:
                anchor_merged[std_name] = payload
            else:
                if payload.get("confidence", 0.0) > prev.get("confidence", 0.0) or len(
                    payload.get("value", "")
                ) > len(prev.get("value", "")):
                    anchor_merged[std_name] = payload

    full_text = "\n".join(all_text_parts).strip()
    record.full_page_ocr_text = full_text

    inferred = augment_with_aliases(full_text, aliases)
    # 앵커 기반 추정이 있으면 우선, 없으면 텍스트 alias 추정을 사용
    merged: dict[str, tuple[str, float]] = {}
    for std_name, payload in anchor_merged.items():
        merged[std_name] = (str(payload.get("value", "")), float(payload.get("confidence", 0.0)))
    for std_name, val in inferred.items():
        if std_name not in merged and val.strip():
            merged[std_name] = (val, 0.35)

    for std_name, tup in merged.items():
        val, conf = tup
        fid = _STD_TO_FID.get(std_name, f"LABEL_{std_name}")
        record.fields[fid] = FieldOCRResult(
            field_id=fid,
            standard_name=std_name,
            ocr_text=val,
            confidence=conf if conf > 0 else 0.35,
            crop_path=None,
            needs_review=True,
            field_type="text",
            normalized_value=val,
            raw_ocr_lines=full_text[:1000],
        )

    # 최소한 이름/번호/학년/반이 하나도 없으면 전체 OCR 일부를 남겨 검수 가능하게 함
    if not record.fields:
        record.fields["LABEL_FULLTEXT"] = FieldOCRResult(
            field_id="LABEL_FULLTEXT",
            standard_name="전체 OCR 텍스트",
            ocr_text=full_text[:2000],
            confidence=0.2,
            crop_path=None,
            needs_review=True,
            field_type="multiline_text",
            normalized_value=full_text[:2000],
            raw_ocr_lines=full_text[:2000],
        )

    record.review_status = ReviewStatus.NEEDS_REVIEW
