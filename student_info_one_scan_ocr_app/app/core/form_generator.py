"""표준 양식 생성 진입점."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.pdf_form_exporter import FormMeta, generate_student_form_bundle


def generate_form(
    *,
    output_dir: Path,
    school_year: str,
    school_name: str,
    grade: str,
    class_no: str,
    homeroom_teacher: str,
    due_date: str,
    include_notice: bool = True,
    include_personal_consent: bool = True,
    include_sensitive_consent: bool = True,
    include_guardian_signature: bool = True,
    use_qr: bool = True,
    dpi_base: int = 300,
) -> dict[str, Any]:
    meta = FormMeta(
        school_year=school_year,
        school_name=school_name,
        grade=grade,
        class_no=class_no,
        homeroom_teacher=homeroom_teacher,
        due_date=due_date,
        include_notice=include_notice,
        include_personal_consent=include_personal_consent,
        include_sensitive_consent=include_sensitive_consent,
        include_guardian_signature=include_guardian_signature,
        use_qr=use_qr,
    )
    paths = generate_student_form_bundle(output_dir, meta, dpi_base=dpi_base)
    return {
        "pdf": str(paths["pdf"]),
        "template_json": str(paths["template_json"]),
        "preview_png": str(paths["preview_png"]),
        "form_version": paths["form_version"],
    }
