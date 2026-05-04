from app.core.keyword_classifier import classify_text


def test_keyword_risk():
    d = {
        "categories": {"allergy": ["알레르기"], "anaphylaxis": ["에피펜"]},
        "risk_high": ["에피펜"],
        "risk_medium": ["알레르기"],
    }
    r = classify_text("학생은 알레르기가 있고 에피펜을 보유", d)
    assert r["risk_score"] >= 3
    assert r["flags"]["allergy_flag"] is True
