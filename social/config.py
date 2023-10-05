from typing import Optional

from pydantic import BaseSettings


class BaseConfig(BaseSettings):
    env_file: str = ".env"


class GlobalConfig(BaseSettings):
    DATABASE_URL: Optional[str] = None
    DB_FORCE_ROLLBACK: bool = False


class DevConfig(GlobalConfig):
    class Config:
        env_prefix = "DEV_"


class ProdConfig(GlobalConfig):
    class Config:
        env_prefix = "PROD_"


class TestConfig(GlobalConfig):
    DATABASE_URL: Optional[str] = "sqlite:///test.db"
    DB_FORCE_ROLLBACK: bool = True

    class Config:
        env_prefix = "TEST_"
