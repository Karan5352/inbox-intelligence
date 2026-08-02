"""Text embedding with a graceful fallback.

Primary: local ``sentence-transformers`` MiniLM (installed via the ``[ml]`` extra).
Nothing leaves the machine - the model runs on CPU locally, which is the whole
privacy premise.

Fallback: a deterministic hashing embedder (numpy only). It is dependency-free,
reproducible, and good enough for the kNN classifier and the test suite, so CI and
first-run demos work without downloading ~80 MB of model weights. The active
backend is reported via :func:`backend_name` and surfaced in ``/health``.
"""

from __future__ import annotations

import hashlib
import re
from functools import lru_cache

import numpy as np

from app.config import get_settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class _HashingEmbedder:
    """Bag-of-hashed-tokens (unigrams + bigrams) projected to a fixed dim, L2-normalized.

    Deterministic across runs and machines - the same text always yields the same
    vector - which keeps benchmarks and tests stable.
    """

    name = "hashing-fallback"

    def __init__(self, dim: int) -> None:
        self.dim = dim

    def _tokens(self, text: str) -> list[str]:
        words = _TOKEN_RE.findall(text.lower())
        bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:], strict=False)]
        return words + bigrams

    def _bucket(self, token: str) -> int:
        h = hashlib.md5(token.encode("utf-8")).digest()  # noqa: S324 (non-crypto use)
        return int.from_bytes(h[:4], "little") % self.dim

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            for tok in self._tokens(text):
                out[i, self._bucket(tok)] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return out / norms


class _SentenceTransformerEmbedder:
    def __init__(self, model_id: str) -> None:
        from sentence_transformers import SentenceTransformer  # local import: optional dep

        self.name = model_id
        self._model = SentenceTransformer(model_id)

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = self._model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
        )
        return np.asarray(vecs, dtype=np.float32)


@lru_cache(maxsize=1)
def get_embedder() -> _SentenceTransformerEmbedder | _HashingEmbedder:
    """Return the process-wide embedder, loaded lazily on first use."""
    settings = get_settings()
    try:
        return _SentenceTransformerEmbedder(settings.embedding_model)
    except Exception:  # noqa: BLE001 - any import/load failure falls back cleanly
        return _HashingEmbedder(settings.embedding_dim)


def embed(texts: list[str]) -> np.ndarray:
    return get_embedder().encode(texts)


def backend_name() -> str:
    return get_embedder().name
