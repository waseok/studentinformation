"""입력값 검증 헬퍼."""

from __future__ import annotations

import re


def is_plausible_phone(s: str) -> bool:
    """정규화 후 010-XXXX-XXXX 형태인지 대략 검사."""
    digits = re.sub(r"\D", "", s)
    return len(digits) in (10, 11) and digits.startswith("010")


def digits_only(s: str) -> str:
    return re.sub(r"\D", "", s)


def is_plausible_date(s: str) -> bool:
    """YYYY-MM-DD / YYYY.MM.DD / YYMMDD 형태를 느슨하게 검사."""
    t = re.sub(r"\s", "", s)
    if re.fullmatch(r"(19|20)?\d{2}[.\-/]?\d{1,2}[.\-/]?\d{1,2}", t):
        return True
    return False


def is_plausible_korean_name(s: str) -> bool:
    """한글 2~5자 중심 이름 검사(느슨)."""
    t = re.sub(r"\s", "", s)
    return bool(re.fullmatch(r"[가-힣]{2,5}", t))
