"""Environment-based application configuration.

Settings are selected with the APP_ENV environment variable so that the same
code runs unchanged in development, testing and production. No secrets are
stored in source control — values are read from the environment (or a local
git-ignored .env file loaded by python-dotenv).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-not-a-secret-change-me")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "dunbar_vet.sqlite3")
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))

    @property
    def database_file(self) -> Path:
        db = Path(self.DATABASE_PATH)
        return db if db.is_absolute() else INSTANCE_DIR / db


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = "test_dunbar_vet.sqlite3"


class ProductionConfig(Config):
    DEBUG = False


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> Config:
    """Return a config instance for the named environment (default: APP_ENV)."""
    name = (name or os.environ.get("APP_ENV") or "development").lower()
    config_cls = _CONFIGS.get(name, DevelopmentConfig)
    return config_cls()
