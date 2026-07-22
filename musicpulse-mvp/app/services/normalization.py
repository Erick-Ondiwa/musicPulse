import re
import unicodedata


NOISE = (
    "official music video",
    "official video",
    "official audio",
    "official lyric video",
    "lyrics video",
    "lyric video",
    "visualizer",
    "official",
    "audio",
    "video",
    "lyrics",
    "4k",
    "hd",
)


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    for phrase in NOISE:
        value = value.replace(phrase, " ")
    value = re.sub(r"[\(\)\[\]\{\}\|:_\-–—]+", " ", value)
    value = re.sub(r"[^a-z0-9\s]", "", value)
    return re.sub(r"\s+", " ", value).strip()
