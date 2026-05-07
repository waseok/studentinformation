"""
ReportLab으로 OCR 친화적 표준 양식 PDF를 그리고,
동일 레이아웃의 form_template.json(bbox_ratio 포함)을 생성합니다.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.core.form_schema import FieldDefinition, field_to_template_dict

import logging

log = logging.getLogger(__name__)

PAGE_W, PAGE_H = A4


def _bbox_ratio_from_rl(x: float, y_ll: float, w: float, h: float) -> list[float]:
    """ReportLab 하단 기준 사각형 → 이미지 좌상단 기준 정규화 bbox."""
    y_img0 = PAGE_H - y_ll - h
    return [x / PAGE_W, y_img0 / PAGE_H, (x + w) / PAGE_W, (y_img0 + h) / PAGE_H]


def _try_register_korean_font() -> str:
    """가능하면 맑은 고딕, 실패 시 CID 한글 폰트."""
    candidates = [
        (r"C:\Windows\Fonts\malgun.ttf", "Malgun"),
        (r"C:\Windows\Fonts\malgunsl.ttf", "MalgunSL"),
    ]
    for path, name in candidates:
        p = Path(path)
        if p.is_file():
            try:
                pdfmetrics.registerFont(TTFont(name, str(p)))
                return name
            except Exception as e:
                log.debug("폰트 등록 실패 (%s): %s", name, e)
                continue
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
        return "HYSMyeongJo-Medium"
    except Exception as e:
        log.debug("CID 한글 폰트 등록 실패, Helvetica로 대체: %s", e)
        return "Helvetica"


def _draw_field_box(c: canvas.Canvas, font: str, item: dict[str, Any]) -> None:
    """라벨/코드를 칸 내부에 고정 배치해 겹침을 방지."""
    x, y_ll, w, h = item["x"], item["y_ll"], item["w"], item["h"]
    label = item["label"]
    field_id = item["field_id"]
    ftype = item["field_type"]

    if ftype == "checkbox":
        c.setLineWidth(0.9)
        c.rect(x, y_ll, w, h, stroke=1, fill=0)
        c.setFont(font, 8)
        c.setFillColor(colors.black)
        c.drawString(x + w + 2.5, y_ll + 0.4 * h, label)
        c.setFont("Helvetica", 5)
        c.setFillColor(colors.grey)
        c.drawRightString(x + w, y_ll + h + 2, field_id)
        c.setFillColor(colors.black)
        return

    # 칸 위 텍스트를 없애고, 칸 내부 상단에 라벨을 연하게 배치
    c.setFont(font, 6.2)
    c.setFillColor(colors.grey)
    c.drawString(x + 2, y_ll + h - 7.0, label)

    c.setFont("Helvetica", 4.8)
    c.setFillColor(colors.lightgrey)
    c.drawRightString(x + w - 1.5, y_ll + 1.4, field_id)

    c.setFillColor(colors.black)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.0)
    c.rect(x, y_ll, w, h, stroke=1, fill=0)


@dataclass
class FormMeta:
    school_year: str
    school_name: str
    grade: str
    class_no: str
    homeroom_teacher: str
    due_date: str
    include_notice: bool
    include_personal_consent: bool
    include_sensitive_consent: bool
    include_guardian_signature: bool
    use_qr: bool


def _layout_fields(meta: FormMeta) -> list[dict[str, Any]]:
    """
    필드 배치 정의. 좌표는 페이지 좌상단 기준 y_top(pt), 너비·높이 pt.
    """
    fields: list[dict[str, Any]] = []

    def add(
        fid: str,
        standard_name: str,
        label: str,
        page: int,
        x: float,
        y_top: float,
        w: float,
        h: float,
        field_type: str,
        *,
        required: bool = False,
        ocr_profile: str = "default",
        norm: str = "default",
        aliases: list[str] | None = None,
        review_priority: int = 0,
        health_related: bool = False,
        sensitive_info: bool = False,
        checkbox_options: list[str] | None = None,
    ) -> None:
        y_ll = PAGE_H - y_top - h
        fields.append(
            {
                "field_id": fid,
                "standard_name": standard_name,
                "label": label,
                "page": page,
                "x": x,
                "y_ll": y_ll,
                "w": w,
                "h": h,
                "field_type": field_type,
                "required": required,
                "ocr_profile": ocr_profile,
                "normalization_rule": norm,
                "aliases": aliases or [],
                "review_priority": review_priority,
                "health_related": health_related,
                "sensitive_info": sensitive_info,
                "checkbox_options": checkbox_options or [],
            }
        )

    # ----- Page 1: 헤더/안내문 아래부터 시작 (겹침 방지) -----
    y = 78 * mm
    add("F001", "학년", "학년", 1, 22 * mm, y, 22 * mm, 7 * mm, "number", required=True, ocr_profile="number")
    add("F002", "반", "반", 1, 48 * mm, y, 18 * mm, 7 * mm, "number", required=True, ocr_profile="number")
    add("F003", "번호", "번호", 1, 70 * mm, y, 22 * mm, 7 * mm, "number", required=True, ocr_profile="number")
    add("F004", "성명", "학생 성명", 1, 100 * mm, y, 55 * mm, 7 * mm, "text", required=True, ocr_profile="korean_name")
    y += 10 * mm
    add(
        "F005",
        "생년월일",
        "생년월일",
        1,
        22 * mm,
        y,
        45 * mm,
        7 * mm,
        "date",
        required=True,
        ocr_profile="date",
    )
    add("F006", "성별", "성별", 1, 72 * mm, y, 35 * mm, 7 * mm, "text", ocr_profile="default")
    y += 10 * mm
    add(
        "F007",
        "주소",
        "주소",
        1,
        22 * mm,
        y,
        168 * mm,
        14 * mm,
        "address",
        ocr_profile="multiline",
        norm="address",
    )
    y += 18 * mm
    add("F008", "형제자매 재학", "형제자매 재학 여부", 1, 22 * mm, y, 168 * mm, 8 * mm, "multiline_text")
    y += 11 * mm
    # 하교 방법 체크박스
    cx = 22 * mm
    for i, (txt, fid) in enumerate(
        [
            ("도보", "F009a"),
            ("보호자 동행", "F009b"),
            ("학원 차량", "F009c"),
            ("돌봄", "F009d"),
            ("기타", "F009e"),
        ]
    ):
        add(fid, "하교방법", txt, 1, cx + i * 34 * mm, y, 6 * mm, 6 * mm, "checkbox", checkbox_options=[txt])
    add("F009f", "하교방법 기타", "기타 상세", 1, 22 * mm, y + 8 * mm, 168 * mm, 7 * mm, "text")
    y += 22 * mm

    add("F010", "보호자1 성명", "보호자1 성명", 1, 22 * mm, y, 55 * mm, 7 * mm, "text", required=True)
    add("F011", "보호자1 관계", "관계", 1, 82 * mm, y, 30 * mm, 7 * mm, "text", required=True)
    add("F012", "보호자1 연락처", "보호자1 연락처", 1, 118 * mm, y, 72 * mm, 7 * mm, "phone", ocr_profile="phone", norm="phone")
    y += 10 * mm
    add("F013", "보호자2 성명", "보호자2 성명", 1, 22 * mm, y, 55 * mm, 7 * mm, "text")
    add("F014", "보호자2 관계", "관계", 1, 82 * mm, y, 30 * mm, 7 * mm, "text")
    add("F015", "보호자2 연락처", "보호자2 연락처", 1, 118 * mm, y, 72 * mm, 7 * mm, "phone", ocr_profile="phone", norm="phone")
    y += 10 * mm
    add("F016", "긴급연락 우선순위", "긴급연락 우선순위", 1, 22 * mm, y, 168 * mm, 7 * mm, "text")
    y += 10 * mm
    add("F017", "비상 추가 연락처", "비상 시 추가 연락처", 1, 22 * mm, y, 168 * mm, 8 * mm, "phone", ocr_profile="phone", norm="phone")
    y += 11 * mm
    add("F018", "비상 인계 보호자", "비상 시 인계 가능 보호자", 1, 22 * mm, y, 168 * mm, 8 * mm, "text")

    # ----- Page 2: 페이지 제목 아래부터 시작 (겹침 방지) -----
    y2 = 46 * mm
    add("F020", "알레르기 여부 없음", "알레르기 없음", 2, 22 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F021", "알레르기 여부 있음", "알레르기 있음", 2, 40 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    y2 += 9 * mm
    add("F022a", "알레르기 원인 식품", "식품", 2, 22 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F022b", "알레르기 원인 약물", "약물", 2, 40 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F022c", "알레르기 원인 곤충", "곤충", 2, 58 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F022d", "알레르기 원인 기타", "기타", 2, 76 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    y2 += 10 * mm
    add(
        "F023",
        "알레르기 내용",
        "구체적 알레르기 내용",
        2,
        22 * mm,
        y2,
        168 * mm,
        12 * mm,
        "medical_note",
        health_related=True,
        sensitive_info=True,
        ocr_profile="medical",
    )
    y2 += 15 * mm
    add("F024a", "아나필락시스 없음", "아나필락시스 없음", 2, 22 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F024b", "아나필락시스 있음", "아나필락시스 있음", 2, 45 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F025a", "응급약 없음", "에피펜/응급약 없음", 2, 70 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F025b", "응급약 있음", "에피펜/응급약 있음", 2, 100 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    y2 += 10 * mm
    add("F026a", "천식 없음", "천식 없음", 2, 22 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F026b", "천식 있음", "천식 있음", 2, 45 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F027a", "흡입기 없음", "흡입기 없음", 2, 70 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F027b", "흡입기 있음", "흡입기 있음", 2, 100 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    y2 += 10 * mm
    add("F028a", "당뇨 없음", "당뇨 없음", 2, 22 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F028b", "당뇨 있음", "당뇨 있음", 2, 45 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F029a", "혈당관리 없음", "혈당관리 불필요", 2, 70 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    add("F029b", "혈당관리 필요", "혈당관리 필요", 2, 100 * mm, y2, 7 * mm, 7 * mm, "checkbox", health_related=True)
    y2 += 10 * mm
    add(
        "F030",
        "현재 복용 약",
        "현재 복용 중인 약",
        2,
        22 * mm,
        y2,
        168 * mm,
        10 * mm,
        "medical_note",
        health_related=True,
        sensitive_info=True,
        ocr_profile="medical",
    )
    y2 += 13 * mm
    add(
        "F031",
        "응급 유의사항",
        "응급 상황 시 유의사항",
        2,
        22 * mm,
        y2,
        168 * mm,
        12 * mm,
        "medical_note",
        health_related=True,
        sensitive_info=True,
        ocr_profile="medical",
    )
    y2 += 15 * mm
    add("F032", "주 이용 병원", "주 이용 병원", 2, 22 * mm, y2, 168 * mm, 8 * mm, "text", health_related=True)
    y2 += 11 * mm
    add(
        "F033",
        "기타 건강 특이사항",
        "기타 건강상 특이사항",
        2,
        22 * mm,
        y2,
        168 * mm,
        14 * mm,
        "medical_note",
        health_related=True,
        sensitive_info=True,
        ocr_profile="medical",
    )
    y2 += 17 * mm
    add("F040", "생활지도 참고", "학교생활 참고사항", 2, 22 * mm, y2, 168 * mm, 10 * mm, "multiline_text")
    y2 += 12 * mm
    add("F041", "친구관계", "친구관계 참고", 2, 22 * mm, y2, 168 * mm, 9 * mm, "multiline_text")
    y2 += 11 * mm
    add("F042", "정서행동", "정서·행동 참고", 2, 22 * mm, y2, 168 * mm, 9 * mm, "multiline_text")
    y2 += 11 * mm
    add("F043", "학습", "학습 참고", 2, 22 * mm, y2, 168 * mm, 9 * mm, "multiline_text")
    y2 += 11 * mm
    add("F044", "보호자 요청", "보호자 요청사항", 2, 22 * mm, y2, 168 * mm, 10 * mm, "multiline_text")

    if meta.include_personal_consent and meta.include_guardian_signature:
        y2 += 13 * mm
        add("F050", "개인정보 동의 성명", "보호자 성명(개인정보)", 2, 22 * mm, y2, 60 * mm, 7 * mm, "text", sensitive_info=True)
        add("F051", "개인정보 동의 서명", "보호자 서명", 2, 90 * mm, y2, 50 * mm, 10 * mm, "signature", sensitive_info=True)
        add("F052", "개인정보 동의 일자", "작성일", 2, 150 * mm, y2, 40 * mm, 7 * mm, "date", ocr_profile="date")
    if meta.include_sensitive_consent and meta.include_guardian_signature:
        y2 += 14 * mm
        add("F053", "민감정보 동의 성명", "보호자 성명(민감)", 2, 22 * mm, y2, 60 * mm, 7 * mm, "text", sensitive_info=True)
        add("F054", "민감정보 동의 서명", "보호자 서명(민감)", 2, 90 * mm, y2, 50 * mm, 10 * mm, "signature", sensitive_info=True)
        add("F055", "민감정보 동의 일자", "작성일(민감)", 2, 150 * mm, y2, 40 * mm, 7 * mm, "date", ocr_profile="date")

    return fields


def _draw_header(c: canvas.Canvas, font: str, meta: FormMeta) -> None:
    c.setFont(font, 15)
    c.drawString(22 * mm, PAGE_H - 18 * mm, "학생 기초자료 조사서 (표준 OCR 양식)")
    c.setFont(font, 9.5)
    line = f"학년도 {meta.school_year}  |  {meta.school_name}  {meta.grade}학년 {meta.class_no}반  |  담임 {meta.homeroom_teacher}  |  제출기한 {meta.due_date}"
    c.drawString(22 * mm, PAGE_H - 26 * mm, line)


def _draw_notice(c: canvas.Canvas, font: str, meta: FormMeta) -> None:
    if not meta.include_notice:
        return
    consent_path = Path(__file__).resolve().parents[2] / "templates" / "consent_text.json"
    notice: list[str] = []
    if consent_path.is_file():
        with open(consent_path, encoding="utf-8") as f:
            data = json.load(f)
            notice = list(data.get("notice_intro", []))
    y = PAGE_H - 34 * mm
    c.setFont(font, 8.5)
    for t in notice[:6]:
        c.drawString(22 * mm, y, "· " + t)
        y -= 4 * mm


def generate_student_form_bundle(
    output_dir: Path,
    meta: FormMeta,
    *,
    dpi_base: int = 300,
) -> dict[str, Path]:
    """
    PDF, form_template.json, preview PNG를 동시에 생성.
    반환: 키 pdf, template_json, preview_png, form_version
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    form_version = f"STD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    pdf_path = output_dir / "학생기초자료조사서_양식.pdf"
    json_path = output_dir / "form_template.json"
    preview_path = output_dir / "printable_form_preview.png"

    layout = _layout_fields(meta)
    font = _try_register_korean_font()

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    c.setTitle("학생 기초자료 조사서")

    def draw_page1() -> None:
        _draw_header(c, font, meta)
        _draw_notice(c, font, meta)
        c.setStrokeColor(colors.black)
        c.setFont(font, 10)
        c.drawString(22 * mm, PAGE_H - 63 * mm, "1. 학생 기본 정보 / 보호자 연락")
        for item in layout:
            if item["page"] != 1:
                continue
            _draw_field_box(c, font, item)
        if meta.use_qr:
            try:
                import qrcode

                qr = qrcode.QRCode(box_size=3, border=1)
                qr.add_data(json.dumps({"form_version": form_version}, ensure_ascii=False))
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                tmp_qr = output_dir / "_form_qr.png"
                img.save(tmp_qr)
                c.drawImage(
                    str(tmp_qr),
                    PAGE_W - 32 * mm,
                    PAGE_H - 32 * mm,
                    width=28 * mm,
                    height=28 * mm,
                    mask="auto",
                )
                tmp_qr.unlink(missing_ok=True)
            except Exception:
                pass

    def draw_page2() -> None:
        c.showPage()
        c.setFont(font, 12)
        c.drawString(22 * mm, PAGE_H - 15 * mm, "[2쪽] 건강·생활지도·동의")
        c.setFont(font, 10)
        c.drawString(22 * mm, PAGE_H - 22 * mm, "2. 건강 및 생활 참고사항")
        for item in layout:
            if item["page"] != 2:
                continue
            _draw_field_box(c, font, item)

    draw_page1()
    draw_page2()
    c.save()

    # form_template.json
    fields_out: list[dict[str, Any]] = []
    for item in layout:
        br = _bbox_ratio_from_rl(item["x"], item["y_ll"], item["w"], item["h"])
        fd = FieldDefinition(
            field_id=item["field_id"],
            standard_name=item["standard_name"],
            label=item["label"],
            page_no=item["page"],
            bbox_ratio=br,
            field_type=item["field_type"],
            required=item.get("required", False),
            ocr_profile=item.get("ocr_profile", "default"),
            normalization_rule=item.get("normalization_rule", "default"),
            aliases=item.get("aliases", []),
            review_priority=item.get("review_priority", 0),
            health_related=item.get("health_related", False),
            sensitive_info=item.get("sensitive_info", False),
            checkbox_options=item.get("checkbox_options", []),
        )
        fd.validate()
        fields_out.append(field_to_template_dict(fd))

    template_doc = {
        "form_version": form_version,
        "school_year": meta.school_year,
        "page_size": {"width_pt": PAGE_W, "height_pt": PAGE_H},
        "dpi_base": dpi_base,
        "anchor_points": [],
        "fields": fields_out,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(template_doc, f, ensure_ascii=False, indent=2)

    # preview: PyMuPDF로 1페이지 렌더
    try:
        import fitz

        doc = fitz.open(str(pdf_path))
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72))
        pix.save(str(preview_path))
        doc.close()
    except Exception:
        if preview_path.exists():
            preview_path.unlink(missing_ok=True)

    return {"pdf": pdf_path, "template_json": json_path, "preview_png": preview_path, "form_version": form_version}
