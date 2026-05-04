"""양식 필드 정의 및 JSON 직렬화."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

VALID_FIELD_TYPES = frozenset(
    {
        "text",
        "number",
        "phone",
        "date",
        "checkbox",
        "checkbox_group",
        "multiline_text",
        "medical_note",
        "address",
        "signature",
    }
)


@dataclass
class FieldDefinition:
    field_id: str
    standard_name: str
    label: str
    page_no: int
    bbox_ratio: list[float]  # [x0,y0,x1,y1] top-left origin, normalized 0-1
    field_type: str
    required: bool = False
    ocr_profile: str = "default"
    normalization_rule: str = "default"
    aliases: list[str] = field(default_factory=list)
    review_priority: int = 0
    health_related: bool = False
    sensitive_info: bool = False
    checkbox_options: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.field_type not in VALID_FIELD_TYPES:
            raise ValueError(f"Invalid field_type: {self.field_type}")
        if len(self.bbox_ratio) != 4:
            raise ValueError("bbox_ratio must have 4 floats")
        for v in self.bbox_ratio:
            if not (-0.001 <= v <= 1.001):
                raise ValueError(f"bbox_ratio out of range: {self.bbox_ratio}")


def field_to_template_dict(f: FieldDefinition) -> dict[str, Any]:
    d = asdict(f)
    return d


def template_dict_to_field(d: dict[str, Any]) -> FieldDefinition:
    return FieldDefinition(
        field_id=d["field_id"],
        standard_name=d["standard_name"],
        label=d["label"],
        page_no=int(d["page_no"]),
        bbox_ratio=[float(x) for x in d["bbox_ratio"]],
        field_type=d["field_type"],
        required=bool(d.get("required", False)),
        ocr_profile=d.get("ocr_profile", "default"),
        normalization_rule=d.get("normalization_rule", "default"),
        aliases=list(d.get("aliases") or []),
        review_priority=int(d.get("review_priority", 0)),
        health_related=bool(d.get("health_related", False)),
        sensitive_info=bool(d.get("sensitive_info", False)),
        checkbox_options=list(d.get("checkbox_options") or []),
    )
