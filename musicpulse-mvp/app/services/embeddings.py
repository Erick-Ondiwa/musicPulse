
"""Local semantic embeddings for Retrieval-Augmented Generation.

The primary embedding provider is BAAI/bge-small-en-v1.5 through
sentence-transformers. It runs locally, requires no paid API key, and produces
384-dimensional normalized vectors.

A deterministic hash-based fallback keeps the application functional during
tests, offline startup, model download failures, or environments where
sentence-transformers cannot be loaded.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
import threading
from collections.abc import Iterable, Sequence
from typing import Any, Protocol

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class Encoder(Protocol):
    """Minimal interface required from a sentence-transformers model."""

    def encode(
        self,
        sentences: Sequence[str],
        **kwargs: Any,
    ) -> Any:
        """Encode one or more text values into vectors."""
        ...


class EmbeddingService:
    """Create normalized embeddings and calculate vector similarity."""

    # SentenceTransformer models are expensive to load. Reuse one instance for
    # every service object using the same model and device.
    _shared_models: dict[tuple[str, str], Encoder] = {}

    # Prevent two simultaneous requests from loading the same model twice.
    _model_load_lock = threading.Lock()

    def __init__(
        self,
        settings: Settings | None = None,
        encoder: Encoder | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._encoder = encoder

    @property
    def provider_name(self) -> str:
        """Return the embedding provider recorded with knowledge documents."""
        if self.settings.bge_enabled:
            return self.settings.bge_embedding_model

        return "local-hash"

    @property
    def dimensions(self) -> int:
        """Return the configured embedding vector dimensions."""
        return max(int(self.settings.rag_embedding_dimensions), 32)

    def warm_up(self) -> None:
        """Load the configured BGE model before the first user request.

        This method should be called from FastAPI's startup lifespan. It avoids
        making the first assistant or ingestion request wait while model weights
        are downloaded and loaded.

        Raises:
            RuntimeError: If BGE is enabled but the model cannot be loaded.
        """
        if not self.settings.bge_enabled:
            logger.info(
                "BGE embeddings are disabled. "
                "The local hash embedding provider will be used."
            )
            return

        logger.info(
            "Loading embedding model '%s' on device '%s'.",
            self.settings.bge_embedding_model,
            self.settings.bge_device,
        )

        try:
            self._get_encoder()
        except Exception as exc:
            raise RuntimeError(
                "Unable to load the configured BGE embedding model "
                f"'{self.settings.bge_embedding_model}'."
            ) from exc

        logger.info(
            "Embedding model '%s' is ready.",
            self.settings.bge_embedding_model,
        )

    def embed(self, text: str) -> list[float]:
        """Create an embedding for a single text value.

        BGE is used when enabled and available. If BGE cannot be loaded or
        encoding fails, a deterministic local vector is returned so the
        application remains operational.
        """
        cleaned_text = self._clean_text(text)

        if self.settings.bge_enabled:
            try:
                return self._bge_embedding(cleaned_text)
            except Exception as exc:
                logger.warning(
                    "BGE embedding failed. Falling back to local hash "
                    "embeddings. Error: %s",
                    exc,
                    exc_info=True,
                )

        return self._local_embedding(cleaned_text)

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        """Create embeddings for multiple text values efficiently.

        The BGE model encodes the complete batch in one call. If batch encoding
        fails, every input is encoded using the deterministic local fallback.

        Args:
            texts: Sequence of strings to embed.

        Returns:
            One normalized vector for every supplied text.
        """
        if not texts:
            return []

        cleaned_texts = [self._clean_text(text) for text in texts]

        if self.settings.bge_enabled:
            try:
                return self._bge_embeddings(cleaned_texts)
            except Exception as exc:
                logger.warning(
                    "BGE batch embedding failed. Falling back to local hash "
                    "embeddings. Error: %s",
                    exc,
                    exc_info=True,
                )

        return [self._local_embedding(text) for text in cleaned_texts]

    def _get_encoder(self) -> Encoder:
        """Lazily load and cache the configured sentence-transformers model."""
        if self._encoder is not None:
            return self._encoder

        model_name = self.settings.bge_embedding_model.strip()
        device = self.settings.bge_device.strip() or "cpu"

        if not model_name:
            raise ValueError("BGE_EMBEDDING_MODEL cannot be empty.")

        cache_key = (model_name, device)

        cached_model = self._shared_models.get(cache_key)
        if cached_model is not None:
            self._encoder = cached_model
            return cached_model

        with self._model_load_lock:
            # Recheck after obtaining the lock because another request may have
            # loaded the model while this request was waiting.
            cached_model = self._shared_models.get(cache_key)

            if cached_model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as exc:
                    raise ImportError(
                        "sentence-transformers is not installed. Run "
                        "'pip install sentence-transformers'."
                    ) from exc

                logger.info(
                    "Initializing SentenceTransformer model '%s' on '%s'.",
                    model_name,
                    device,
                )

                cached_model = SentenceTransformer(
                    model_name,
                    device=device,
                )

                self._shared_models[cache_key] = cached_model

            self._encoder = cached_model

        return self._encoder

    def _bge_embedding(self, text: str) -> list[float]:
        """Generate one normalized BGE embedding."""
        vectors = self._bge_embeddings([text])

        if not vectors:
            raise ValueError("The embedding model returned no vectors.")

        return vectors[0]

    def _bge_embeddings(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate normalized BGE embeddings for a batch of texts."""
        if not texts:
            return []

        model = self._get_encoder()

        encoded = model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        vectors: list[list[float]] = []

        for index, encoded_vector in enumerate(encoded):
            if hasattr(encoded_vector, "tolist"):
                raw_values = encoded_vector.tolist()
            else:
                raw_values = list(encoded_vector)

            values = [float(value) for value in raw_values]

            self._validate_vector(
                values,
                source=f"BGE output at batch index {index}",
            )

            # Sentence Transformers should already normalize these because
            # normalize_embeddings=True, but normalizing again protects against
            # injected test encoders and alternative model implementations.
            vectors.append(self._normalize(values))

        if len(vectors) != len(texts):
            raise ValueError(
                "Embedding count mismatch: "
                f"expected {len(texts)}, received {len(vectors)}."
            )

        return vectors

    def _local_embedding(self, text: str) -> list[float]:
        """Create a deterministic normalized fallback embedding.

        The fallback hashes tokens into a fixed-size signed vector. It is not a
        semantic replacement for BGE, but it allows tests and degraded operation
        to continue without an external model.
        """
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9']+", text.lower())

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()

            index = int.from_bytes(digest[:4], byteorder="big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0

            # Add a small deterministic token weight to reduce collisions among
            # repeated terms while keeping the fallback reproducible.
            weight = 1.0 + (digest[5] / 255.0)
            vector[index] += sign * weight

        return self._normalize(vector)

    def _validate_vector(
        self,
        vector: Sequence[float],
        *,
        source: str,
    ) -> None:
        """Validate embedding dimensions and numeric values."""
        if len(vector) != self.dimensions:
            raise ValueError(
                f"{source} dimension mismatch: expected {self.dimensions}, "
                f"received {len(vector)}."
            )

        if any(not math.isfinite(value) for value in vector):
            raise ValueError(f"{source} contains non-finite numeric values.")

    @staticmethod
    def _clean_text(text: str | None) -> str:
        """Normalize text before embedding."""
        if text is None:
            return ""

        if not isinstance(text, str):
            text = str(text)

        # Collapse repeated whitespace while retaining the original words and
        # punctuation used by the semantic model.
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _normalize(vector: Iterable[float]) -> list[float]:
        """Return a unit-length copy of a vector."""
        values = [float(value) for value in vector]
        magnitude = math.sqrt(sum(value * value for value in values))

        if magnitude == 0.0:
            return values

        return [value / magnitude for value in values]

    @staticmethod
    def cosine_similarity(
        left: Sequence[float],
        right: Sequence[float],
    ) -> float:
        """Calculate cosine similarity between two vectors.

        Although BGE vectors are normally already normalized, this method also
        handles non-normalized vectors safely.

        Returns:
            A similarity score between -1.0 and 1.0. Returns 0.0 for empty,
            incompatible, zero-length, or invalid vectors.
        """
        if not left or not right or len(left) != len(right):
            return 0.0

        try:
            left_values = [float(value) for value in left]
            right_values = [float(value) for value in right]
        except (TypeError, ValueError):
            return 0.0

        if any(
            not math.isfinite(value)
            for value in (*left_values, *right_values)
        ):
            return 0.0

        dot_product = sum(
            left_value * right_value
            for left_value, right_value in zip(
                left_values,
                right_values,
                strict=True,
            )
        )

        left_magnitude = math.sqrt(
            sum(value * value for value in left_values)
        )
        right_magnitude = math.sqrt(
            sum(value * value for value in right_values)
        )

        denominator = left_magnitude * right_magnitude

        if denominator == 0.0:
            return 0.0

        similarity = dot_product / denominator

        # Guard against tiny floating-point overshoots such as 1.0000000002.
        return max(-1.0, min(1.0, similarity))

