from app.services.normalization import normalize_text


def test_normalize_title_removes_video_noise():
    assert normalize_text("Bien - Lifestyle (Official Music Video) [4K]") == "bien lifestyle"
