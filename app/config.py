from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "secret_password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "deribit_db"

    DERIBIT_BASE_URL: str = "https://deribit.com/api/v2"

    @property
    def database_url_async(self) -> str:
        """URL для асинхронного подключения FastAPI/Alembic (через asyncpg)"""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_url_sync(self) -> str:
        """URL для синхронного подключения (если понадобится)"""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def celery_broker_url(self) -> str:
        return f"sqla+{self.database_url_sync}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
