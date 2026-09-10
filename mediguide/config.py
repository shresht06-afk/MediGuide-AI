import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    model: str = os.getenv("MEDIGUIDE_MODEL", "openrouter/free")
    database: str = os.getenv("MEDIGUIDE_DATABASE", "mediguide.db")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("MEDIGUIDE_CORS_ORIGINS", "http://localhost:8000,http://localhost:3000").split(",")
        if origin.strip()
    )


settings = Settings()
