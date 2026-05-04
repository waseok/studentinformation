"""
로그 등에 출력하기 전 개인정보 패턴 마스킹.
원문 이름·전화·주소 전체를 로그에 남기지 않도록 합니다.
"""

from __future__ import annotations

import re


# 휴대전화 형태 (간단한 국내 패턴)
_PHONE_RE = re.compile(
    r"(?:\+?82[-.\s]?)?0?(?:1[0-9]|2|[3579][0-9]|[46][0-9])(?:[-.\s]?\d{3,4}){2}\d{4}"
)
# 연속 숫자 10~11자리 (전화 후보)
_DIGITS_RE = re.compile(r"\b\d{10,11}\b")
# 한글 이름 2~4자 (문맥 없이 보수적으로 마스킹하지 않음 — 별도 API 사용)


def mask_phone(text: str) -> str:
    """전화번호 패턴을 [PHONE]으로 치환."""
    s = _PHONE_RE.sub("[PHONE]", text)
    # 흔한 국내 휴대전화 패턴(하이픈/공백 변형 포함)
    s = re.sub(r"0?1[0-9]\D*\d{3,4}\D*\d{4}", "[PHONE]", s)
    s = _DIGITS_RE.sub(lambda m: "[PHONE]" if len(m.group()) >= 10 else m.group(), s)
    return s


def mask_korean_name_token(text: str) -> str:
    """로그용: '성명: 홍길동' 같은 짧은 토큰만 마스킹할 때는 호출부에서 길이 제한 권장."""
    # 2~4자 연속 한글을 [NAME]으로 (과마스킹 방지를 위해 앞뒤 구분자가 있을 때만 쓰도록 호출부에서 처리)
    return re.sub(r"(?<![가-힣])([가-힣]{2,4})(?![가-힣])", "[NAME]", text)


def sanitize_log_message(message: str, *, mask_names: bool = False) -> str:
    """
    로그 한 줄을 안전하게 가공.
    - 전화번호 마스킹
    - mask_names=True 시 고립된 2~4자 한글 토큰 마스킹 (일반 문장은 훼손될 수 있어 기본 False)
    """
    s = mask_phone(message)
    if mask_names:
        s = mask_korean_name_token(s)
    return s


def truncate(text: str, max_len: int = 20) -> str:
    """주소 등 긴 문자열의 앞부분만 표시."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
