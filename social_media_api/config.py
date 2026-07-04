from typing import Optional
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None

    class Config:
        env_file = str(ENV_FILE)
        extra = "ignore"

class GlobalConfig(BaseConfig):
    DATABASE_URL: Optional[str] = None
    DB_FORCE_ROLL_BACK: bool = False
    LOGTAIL_API_KEY: Optional[str] = None

class DevConfig(GlobalConfig):
    class Config:
        env_prefix: str = "DEV_"

class TestConfig(GlobalConfig): 
    # run the values from the test config when running tests not from .env file
    DATABASE_URL: Optional[str] = "sqlite:///test.db"
    DB_FORCE_ROLL_BACK: bool = True # database will be cleared when the connection is closed
    
    class Config:
        env_prefix: str = "TEST_"

class ProdConfig(GlobalConfig):
    class Config:
        env_prefix: str = "PROD_"

@lru_cache()
def get_config(env_state: str):
    configs = {"dev": DevConfig, "test": TestConfig, "prod": ProdConfig}
    return configs.get(env_state, DevConfig)()

config = get_config(BaseConfig().ENV_STATE)