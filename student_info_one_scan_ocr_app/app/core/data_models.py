"""도메인 데이터 모델."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReviewStatus(str, Enum):
    OCR_DONE = "OCR완료"
    NEEDS_REVIEW = "검토필요"
    EDITED = "수정됨"
    REVIEWED = "검수완료"
    ERROR = "오류"


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FieldOCRResult:
    field_id: str
    standard_name: str = ""
    ocr_text: str = ""
    confidence: float = 0.0
    crop_path: str | None = None
    needs_review: bool = False
    field_type: str = "text"
    normalized_value: str = ""
    raw_ocr_lines: str = ""


@dataclass
class StudentRecord:
    """학생 1명(1~N페이지 묶음) 단위."""

    record_id: str
    source_path: str
    page_start: int  # 1-based
    page_end: int
    page_group_id: str = ""
    render_image_paths: list[str] = field(default_factory=list)
    fields: dict[str, FieldOCRResult] = field(default_factory=dict)
    review_status: ReviewStatus = ReviewStatus.OCR_DONE
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: int = 0
    roster_match: str = ""
    roster_name_expected: str | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    full_page_ocr_text: str = ""
    # 플래그 컬럼 (엑셀용)
    allergy_flag: bool = False
    anaphylaxis_flag: bool = False
    asthma_flag: bool = False
    diabetes_flag: bool = False
    emergency_flag: bool = False
    medication_flag: bool = False
    detected_keywords: list[str] = field(default_factory=list)
    health_teacher_review_needed: bool = False

    def extracted_name(self) -> str:
        for key in ("F004", "student_name", "성명"):
            f = self.fields.get(key)
            if f and f.normalized_value:
                return f.normalized_value
        for f in self.fields.values():
            if f.standard_name in ("학생 성명", "성명") and f.normalized_value:
                return f.normalized_value
        return ""

    def extracted_number(self) -> str:
        for key in ("F003", "student_number", "번호"):
            f = self.fields.get(key)
            if f and f.normalized_value:
                return f.normalized_value
        for f in self.fields.values():
            if f.standard_name == "번호" and f.normalized_value:
                return f.normalized_value
        return ""
