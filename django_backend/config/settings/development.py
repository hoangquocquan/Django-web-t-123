"""Development settings for the Django migration backend."""

from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403


DEBUG = True
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")  # noqa: F405

for origin in CORS_ALLOWED_ORIGINS:  # noqa: F405
    parsed = urlparse(origin)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or not parsed.port
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ImproperlyConfigured(
            "Development CORS_ALLOWED_ORIGINS must contain explicit loopback HTTP origins."
        )

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Match the current local demo workstation: this model was observed in Ollama
# during the AI demo. Operators can still override these values through env.
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")  # noqa: F405
OLLAMA_GENERATION_MODELS = tuple(
    item.strip()
    for item in os.getenv("OLLAMA_GENERATION_MODELS", OLLAMA_MODEL).split(",")  # noqa: F405
    if item.strip()
)
OLLAMA_NUM_PREDICT = env_int("OLLAMA_NUM_PREDICT", 512)  # noqa: F405
OLLAMA_TIMEOUT_SECONDS = env_int("OLLAMA_TIMEOUT_SECONDS", 60)  # noqa: F405

# Local demo knowledge is seeded with deterministic hash embeddings, so
# development search must query with the same provider family.
KNOWLEDGE_EMBEDDING_PROVIDER = os.getenv("KNOWLEDGE_EMBEDDING_PROVIDER", "development-hash")  # noqa: F405
KNOWLEDGE_MIN_RELEVANCE_SCORE = env_float("KNOWLEDGE_MIN_RELEVANCE_SCORE", 0.33)  # noqa: F405

# Explicit localhost-only public UI demo; production inherits the disabled base flag.
PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED = env_bool("PUBLIC_SYNTHETIC_RAG_DEMO_ENABLED", True)  # noqa: F405
