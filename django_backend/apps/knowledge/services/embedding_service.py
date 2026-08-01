"""Các embedding provider cục bộ dùng cho hệ thống Knowledge/RAG."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
from abc import ABC, abstractmethod
from urllib import error, request

from django.conf import settings


logger = logging.getLogger(__name__)
TOKEN_PATTERN = re.compile(r"[\w\-]+", re.UNICODE)


class EmbeddingProviderError(RuntimeError):
    """Lỗi an toàn khi provider không thể tạo vector hợp lệ."""


class EmbeddingProvider(ABC):
    """Hợp đồng chung để thay model hoặc backend mà không đổi business flow."""

    provider_name = "unknown"
    model_name = "unknown"
    dimensions = 0
    embedding_version = "v1"

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Biến một đoạn văn bản thành vector số."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Tạo vector cho một nhóm văn bản trong một lần gọi."""

    @abstractmethod
    def health_check(self) -> dict:
        """Trả trạng thái endpoint, model và kích thước vector."""

    def embed(self, text: str) -> list[float]:
        """Giữ tương thích với service cũ trong quá trình migration."""
        return self.embed_text(text)

    @staticmethod
    def similarity(left, right):
        """Tính cosine similarity và từ chối vector khác chiều."""
        if len(left) != len(right):
            raise EmbeddingProviderError("Embedding dimensions do not match.")
        left_magnitude = math.sqrt(sum(float(value) ** 2 for value in left))
        right_magnitude = math.sqrt(sum(float(value) ** 2 for value in right))
        if not left_magnitude or not right_magnitude:
            return 0.0
        dot_product = sum(float(a) * float(b) for a, b in zip(left, right))
        return dot_product / (left_magnitude * right_magnitude)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Gọi `/api/embed` của Ollama local, có timeout và retry giới hạn."""

    provider_name = "ollama-local"

    def __init__(self, base_url=None, model=None, timeout=None, retries=None, dimensions=None, opener=None):
        self.base_url = (base_url or getattr(settings, "OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.model_name = model or getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        self.timeout = int(timeout or getattr(settings, "OLLAMA_EMBEDDING_TIMEOUT_SECONDS", 30))
        self.retries = max(0, int(retries if retries is not None else getattr(settings, "OLLAMA_EMBEDDING_RETRIES", 1)))
        self.dimensions = int(dimensions or getattr(settings, "OLLAMA_EMBEDDING_DIMENSIONS", 768))
        self.opener = opener or request.urlopen

    def embed_text(self, text: str) -> list[float]:
        vectors = self.embed_batch([text])
        return vectors[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        normalized = [str(text or "").strip() for text in texts]
        if not normalized or any(not text for text in normalized):
            raise EmbeddingProviderError("Embedding input must not be empty.")

        payload = {"model": self.model_name, "input": normalized}
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                data = self._json_request("POST", "/api/embed", payload)
                vectors = data.get("embeddings") or []
                self._validate_vectors(vectors, expected_count=len(normalized))
                return [[float(value) for value in vector] for vector in vectors]
            except EmbeddingProviderError as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.1 * (attempt + 1))

        logger.warning("Ollama embedding failed without logging document content: %s", last_error)
        raise last_error or EmbeddingProviderError("Ollama embedding failed.")

    def health_check(self) -> dict:
        try:
            data = self._json_request("GET", "/api/tags")
            models = [item.get("name", "") for item in data.get("models", []) if item.get("name")]
            model_available = any(
                name == self.model_name or name.split(":", 1)[0] == self.model_name.split(":", 1)[0]
                for name in models
            )
            return {
                "available": True,
                "provider": self.provider_name,
                "endpoint": self.base_url,
                "model": self.model_name,
                "model_available": model_available,
                "dimensions": self.dimensions,
                "models": models,
            }
        except EmbeddingProviderError as exc:
            return {
                "available": False,
                "provider": self.provider_name,
                "endpoint": self.base_url,
                "model": self.model_name,
                "model_available": False,
                "dimensions": self.dimensions,
                "models": [],
                "error": str(exc),
            }

    def _json_request(self, method, path, payload=None):
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = request.Request(f"{self.base_url}{path}", data=body, headers=headers, method=method)
        try:
            with self.opener(req, timeout=self.timeout) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise EmbeddingProviderError(f"Ollama embedding API returned HTTP {exc.code}.") from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            raise EmbeddingProviderError("Ollama embedding API is not available.") from exc
        try:
            return json.loads(raw_body or "{}")
        except json.JSONDecodeError as exc:
            raise EmbeddingProviderError("Ollama embedding API returned invalid JSON.") from exc

    def _validate_vectors(self, vectors, expected_count):
        if len(vectors) != expected_count:
            raise EmbeddingProviderError("Ollama returned an incomplete embedding batch.")
        for vector in vectors:
            if not vector:
                raise EmbeddingProviderError("Ollama returned an empty embedding vector.")
            if self.dimensions and len(vector) != self.dimensions:
                raise EmbeddingProviderError(
                    f"Embedding dimension mismatch: expected {self.dimensions}, received {len(vector)}."
                )


class DevelopmentHashEmbeddingProvider(EmbeddingProvider):
    """Fallback xác định được chỉ dành cho test/phát triển, không phải semantic search production."""

    provider_name = "development-hash-fallback"
    dimensions = 32
    model_name = "local-hash-embedding"

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        tokens = TOKEN_PATTERN.findall(str(text or "").lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = digest[0] % self.dimensions
            vector[index] += 1.0 + (digest[1] % 5) / 10.0
        magnitude = math.sqrt(sum(value * value for value in vector))
        return vector if magnitude == 0 else [round(value / magnitude, 6) for value in vector]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def health_check(self) -> dict:
        return {
            "available": True,
            "provider": self.provider_name,
            "model": self.model_name,
            "dimensions": self.dimensions,
            "warning": "Development fallback is not production semantic vector search.",
        }


class LocalEmbeddingService(DevelopmentHashEmbeddingProvider):
    """Tên tương thích tạm thời cho test cũ; code mới nên dùng provider factory."""


def get_embedding_provider():
    """Chọn provider bằng settings; production mặc định dùng Ollama local."""
    provider_name = getattr(settings, "KNOWLEDGE_EMBEDDING_PROVIDER", "ollama").strip().lower()
    if provider_name in {"development-hash", "local-fallback", "test"}:
        logger.warning("Using development hash embedding fallback; semantic retrieval is disabled.")
        return DevelopmentHashEmbeddingProvider()
    return OllamaEmbeddingProvider()
