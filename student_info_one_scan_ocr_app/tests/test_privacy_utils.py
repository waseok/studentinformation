from app.utils.privacy_utils import mask_phone, sanitize_log_message


def test_mask_phone():
    s = mask_phone("call 010-1234-5678 end")
    assert "[PHONE]" in s
    assert "010" not in s


def test_sanitize_log():
    assert "010" not in sanitize_log_message("error 010-1111-2222")
