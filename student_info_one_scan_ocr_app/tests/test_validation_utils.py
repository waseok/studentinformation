from app.utils.validation_utils import (
    is_plausible_date,
    is_plausible_korean_name,
    is_plausible_phone,
)


def test_plausible_phone():
    assert is_plausible_phone("010-1234-5678") is True
    assert is_plausible_phone("02-123-4567") is False


def test_plausible_date():
    assert is_plausible_date("2026-03-01") is True
    assert is_plausible_date("260301") is True
    assert is_plausible_date("abc") is False


def test_plausible_korean_name():
    assert is_plausible_korean_name("홍길동") is True
    assert is_plausible_korean_name("AB12") is False
