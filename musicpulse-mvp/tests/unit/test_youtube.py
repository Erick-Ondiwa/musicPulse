from app.connectors.youtube import YouTubeClient


def test_parse_iso_duration():
    assert YouTubeClient._parse_duration_seconds("PT3M45S") == 225
    assert YouTubeClient._parse_duration_seconds("PT1H2M3S") == 3723
