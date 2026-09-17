from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = (
        "postgresql+psycopg2://inventory_app:inventory_app_dev_pw@localhost:5432/spoorthi_inventory_db"
    )
    jwt_secret: str = "dev-only-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12

    consumption_file: Path = DATA_RAW_DIR / "Raw Material Consumption data from April 2025 to August 2026.xlsx"
    procurement_file: Path = DATA_RAW_DIR / "Format - Raw Material Received Details for IO.xlsx"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
