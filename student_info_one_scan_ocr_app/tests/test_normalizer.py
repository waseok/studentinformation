import pytest

from app.core.normalizer import (
    collapse_whitespace,
    digits_only_field,
    normalize_phone,
    normalize_yes_no,
    warn_name_has_digit,
)


def test_collapse_whitespace():
    assert collapse_whitespace("  a  \n b  ") == "a b"


def test_normalize_phone_ocr_fix():
    fixes = {"O": "0"}
    # OCR에서 O(영문)이 0으로 잘못 인식된 경우: 자리 수는 11자리로 유지되는 형태
    assert normalize_phone("010-12O4-5678", fixes) == "010-1204-5678"


def test_normalize_phone_basic():
    assert normalize_phone("01012345678", {}) == "010-1234-5678"


def test_yes_no():
    rules = {"yes_tokens": ["예"], "no_tokens": ["아니오"]}
    assert normalize_yes_no("예", rules) == "예"
    assert normalize_yes_no("아니오", rules) == "아니오"


def test_digits_only():
    assert digits_only_field("3학년") == "3"


def test_name_warn():
    assert warn_name_has_digit("김1동") is True
    assert warn_name_has_digit("김철수") is False
