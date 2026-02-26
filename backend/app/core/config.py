from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Flow Capacity Monitor"
    environment: str = "dev"
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/flow_monitor"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_minutes: int = 60 * 24 * 14
    timezone_display_default: str = "America/New_York"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
