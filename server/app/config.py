from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://biotest:biotest@127.0.0.1:5432/biotest"
    telemetry_dir: str = str(ROOT / "data" / "telemetry")
    demo_speed: float = 12.0
    max_concurrent_runs: int = 12
    max_runtime_minutes: int = 30
    rows_per_file: int = 60
    seed: int = 42
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def telemetry_path(self) -> Path:
        path = Path(self.telemetry_dir)
        if not path.is_absolute():
            path = (ROOT / path).resolve()
        return path

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def tick_interval_seconds(self) -> float:
        """Wall-clock seconds between simulated seconds."""
        speed = max(self.demo_speed, 0.1)
        return 1.0 / speed


settings = Settings()