from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./cloudpulse.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str
    access_token_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    demo_base_url: str = "http://localhost:8000"
    check_tick_seconds: int = 15
    seed_admin_password: str | None = None
    seed_viewer_password: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
