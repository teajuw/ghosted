from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Ghosted"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # API Keys
    sapling_api_key: str = ""
    hf_api_token: str = ""

    # Limits
    max_text_length_scan: int = 50_000
    max_text_length_detect: int = 10_000
    rate_limit_rpm: int = 10

    # Sapling quota tracking (chars per day)
    sapling_daily_limit: int = 50_000

    model_config = {"env_file": ".env", "env_prefix": "AIDET_"}


settings = Settings()
