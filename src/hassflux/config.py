from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MariaDB
    mariadb_host: str = "127.0.0.1"
    mariadb_port: int = 3307
    mariadb_user: str
    mariadb_pass: str
    mariadb_db: str = "ha"

    # InfluxDB
    influx_url: str
    influx_token: str
    influx_org: str
    influx_bucket: str

    # Migration
    batch_size: int = 50000
    progress_file: Path = Path("data/migration_progress.txt")
    friendly_name_file: Path = Path("data/friendly_names.json")
    
    # Logging
    log_dir: Path = Path("logs")

settings = Settings()
