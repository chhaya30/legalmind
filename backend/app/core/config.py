from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    APP_NAME: str = "LegalMind API"
    API_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "postgresql+psycopg://legalmind:legalmind@localhost:5432/legalmind"
    FRONTEND_ORIGIN: str = "http://localhost:5173,http://127.0.0.1:5173"
    MAX_UPLOAD_MB: int = 15
    UPLOAD_DIR: str = "../data/uploads"
    PROCESSED_DIR: str = "../data/processed"
    LOG_LEVEL: str = "INFO"
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    EMBEDDING_FALLBACK_MODEL: str = "sentence-transformers/all-distilroberta-v1"
    EMBEDDING_DIMENSION: int = 768
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    RETRIEVAL_CANDIDATES: int = 50
    RETRIEVAL_TOP_K: int = 10
    RRF_K: int = 60
    ENABLE_EMBEDDINGS: bool = True
    LLM_PROVIDER: str = "openai-compatible"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_TIMEOUT_SECONDS: int = 60
    MIN_EVIDENCE_COVERAGE: float = 0.35
    SUMMARY_MAP_LIMIT: int = 8
    ENABLE_FAITHFULNESS_JUDGE: bool = True
    FAITHFULNESS_JUDGE_MODEL: str = "gpt-4o-mini"
    LEGAL_NER_MODEL: str = "hf-tuner/BERT-Indian-legal-NER"
    LEGAL_NER_MAX_CHARS: int = 12000
    ENABLE_LEGAL_TRANSFORMER_NLP: bool = True
    LEGAL_NLP_VERSION: str = "legal-transformer-ner-v1"
    JURISDICTION: str = "India - Supreme Court judgments"
    OCR_SUPPORTED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    ADMIN_API_KEY: str = ""
    EVALUATOR_API_KEY: str = ""
    AUTH_SECRET: str = "change-me-auth-secret"
    AUTH_SESSION_TTL_SECONDS: int = 28800
    RETENTION_DAYS: int = 0
    REDIS_URL: str = "redis://redis:6379/0"
    USE_WORKER: bool = True
    WORKER_QUEUE: str = "legalmind"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def upload_path(self) -> Path:
        return (BASE_DIR / self.UPLOAD_DIR).resolve()

    @property
    def processed_path(self) -> Path:
        return (BASE_DIR / self.PROCESSED_DIR).resolve()

    @property
    def frontend_origins(self) -> list[str]:
        value = (self.FRONTEND_ORIGIN or "").strip()
        origins = [part.strip() for part in value.split(",") if part.strip()]
        if not origins:
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        return origins

settings = Settings()
settings.upload_path.mkdir(parents=True, exist_ok=True)
settings.processed_path.mkdir(parents=True, exist_ok=True)
