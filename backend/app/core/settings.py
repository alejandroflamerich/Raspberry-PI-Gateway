from pydantic_settings import BaseSettings
from pydantic.networks import AnyHttpUrl
from typing import List


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    jwt_secret: str = "CHANGEME_IN_PROD"
    jwt_algo: str = "HS256"
    api_prefix: str = "/api/v1"
    cors_origins: List[AnyHttpUrl] = ["http://localhost:5173"]
    hw_mode: str = "mock"  # 'mock' or 'raspberry'
    # Modbus TCP configuration
    modbus_host: str = "localhost"
    modbus_port: int = 502
    modbus_unit: int = 1
    modbus_timeout: float = 3.0
    modbus_retries: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
