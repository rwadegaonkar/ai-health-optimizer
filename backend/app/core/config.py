from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "AI Health Optimizer"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://health_ai:changeme@db:5432/health_ai"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Auth
    JWT_SECRET: str = "change-this-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Nutritionix
    NUTRITIONIX_APP_ID: str = ""
    NUTRITIONIX_API_KEY: str = ""

    # Fitbit
    FITBIT_CLIENT_ID: str = ""
    FITBIT_CLIENT_SECRET: str = ""
    FITBIT_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/fitbit/callback"

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]


settings = Settings()
