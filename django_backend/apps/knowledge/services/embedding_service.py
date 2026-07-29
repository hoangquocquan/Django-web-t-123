"""Deterministic local embedding service for the learning platform."""

from __future__ import annotations

import hashlib
import math
import re


TOKEN_PATTERN = re.compile(r"[\w\-]+", re.UNICODE)


class LocalEmbeddingService:
    """Create small hash embeddings without calling external AI providers."""

    dimensions = 32
    model_name = "local-hash-embedding"

    def embed(self, text):
        """Convert text into a normalized numeric vector."""
        vector = [0.0 for _ in range(self.dimensions)]
        tokens = TOKEN_PATTERN.findall(str(text or "").lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = digest[0] % self.dimensions
            weight = 1.0 + (digest[1] % 5) / 10.0
            vector[index] += weight
        return self._normalize(vector)

    def similarity(self, left, right):
        """Return cosine similarity for two vectors."""
        return sum(float(a) * float(b) for a, b in zip(left, right))

    def _normalize(self, vector):
        """Normalize one vector so dot product behaves like cosine similarity."""
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [round(value / magnitude, 6) for value in vector]

