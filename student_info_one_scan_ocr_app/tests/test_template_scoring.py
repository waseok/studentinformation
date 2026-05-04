from app.core.template_ocr_extractor import _field_text_score


def test_field_text_score_phone_bonus():
    base = _field_text_score("phone", "abc", 0.3)
    good = _field_text_score("phone", "010-1234-5678", 0.3)
    assert good > base


def test_field_text_score_date_bonus():
    bad = _field_text_score("date", "메모", 0.4)
    good = _field_text_score("date", "2026.03.01", 0.4)
    assert good > bad
