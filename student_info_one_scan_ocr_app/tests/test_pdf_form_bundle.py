from pathlib import Path

from app.core.pdf_form_exporter import FormMeta, generate_student_form_bundle


def test_generate_pdf_and_template(tmp_path: Path):
    meta = FormMeta(
        school_year="2026",
        school_name="테스트초",
        grade="3",
        class_no="2",
        homeroom_teacher="김교사",
        due_date="2026-03-01",
        include_notice=True,
        include_personal_consent=True,
        include_sensitive_consent=True,
        include_guardian_signature=True,
        use_qr=False,
    )
    res = generate_student_form_bundle(tmp_path, meta)
    assert res["pdf"].is_file()
    assert res["template_json"].is_file()
    import json

    data = json.loads(res["template_json"].read_text(encoding="utf-8"))
    assert "fields" in data and len(data["fields"]) > 5
