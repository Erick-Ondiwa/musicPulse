"""Embedding tests cover local fallback and injected BGE-compatible encoders."""

from app.core.config import Settings
from app.services.embeddings import EmbeddingService


class FakeEncoder:
    """Return a known vector without downloading a model during unit tests."""

    def encode(self, sentences, **kwargs):
        return [[1.0, 0.0, 0.0, 0.0] for _ in sentences]


def test_local_embeddings_are_deterministic_and_normalized():
    service = EmbeddingService(Settings(bge_enabled=False, rag_embedding_dimensions=64))
    first = service.embed("Kenyan afro pop music")
    second = service.embed("Kenyan afro pop music")
    assert first == second
    assert len(first) == 64
    assert round(sum(value * value for value in first), 6) == 1.0


def test_bge_encoder_is_used_when_enabled():
    service = EmbeddingService(
        Settings(bge_enabled=True, rag_embedding_dimensions=4),
        encoder=FakeEncoder(),
    )
    assert service.embed("music intelligence") == [1.0, 0.0, 0.0, 0.0]
    assert service.provider_name == "BAAI/bge-small-en-v1.5"


def test_cosine_similarity_prefers_related_text():
    service = EmbeddingService(Settings(bge_enabled=False, rag_embedding_dimensions=128))
    query = service.embed("song artist views")
    related = service.embed("artist song views and likes")
    unrelated = service.embed("database container network")
    assert service.cosine_similarity(query, related) > service.cosine_similarity(query, unrelated)
