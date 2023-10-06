from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env")


class GlobalConfig(BaseConfig):
    DATABASE_URL: Optional[str] = None
    DB_FORCE_ROLLBACK: bool = False


class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_")


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_")


class TestConfig(GlobalConfig):
    DATABASE_URL: Optional[str] = "sqlite:///test.db"
    DB_FORCE_ROLLBACK: bool = True

    model_config = SettingsConfigDict(env_prefix="TEST_")


@lru_cache()
def get_config(env_state: str) -> BaseConfig:
    configs = {
        "dev": DevConfig,
        "prod": ProdConfig,
        "test": TestConfig,
    }
    return configs[env_state]()


config = get_config(BaseConfig().ENV_STATE)
