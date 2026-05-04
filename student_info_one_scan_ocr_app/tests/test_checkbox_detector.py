from PIL import Image

from app.core.checkbox_detector import detect_checkbox


def test_checkbox_empty():
    img = Image.new("RGB", (10, 10), (255, 255, 255))
    r = detect_checkbox(img, thresh=0.99)
    assert r.checked is False
