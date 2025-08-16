"""
Configuration settings for Discord-Obsidian Memo Bot
"""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Discord Configuration
    discord_bot_token: SecretStr
    discord_guild_id: int

    # Google API Configuration
    gemini_api_key: SecretStr
    google_application_credentials: str | None = None
    google_cloud_speech_api_key: SecretStr | None = None

    # Garmin Configuration
    garmin_username: str | None = None
    garmin_password: SecretStr | None = None

    # Obsidian Configuration
    obsidian_vault_path: Path

    # Discord Channel Configuration
    channel_inbox: int
    channel_voice: int
    channel_files: int
    channel_money: int
    channel_finance_reports: int
    channel_tasks: int
    channel_productivity_reviews: int
    channel_notifications: int
    channel_commands: int
    channel_activity_log: int | None = None
    channel_daily_tasks: int | None = None

    # Garmin Connect Integration (Optional)
    garmin_email: SecretStr | None = None
    garmin_cache_dir: Path | None = None
    garmin_cache_hours: float = 24.0

    # API Rate Limiting
    gemini_api_daily_limit: int = 1500
    gemini_api_minute_limit: int = 15
    speech_api_monthly_limit_minutes: int = 60

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"

    # Environment
    environment: str = "development"

    # Security Configuration
    google_cloud_project: str | None = None
    use_secret_manager: bool = False
    enable_access_logging: bool = True
    security_log_path: Path | None = None

    # Mock Mode Configuration (for development/testing)
    enable_mock_mode: bool = False
    mock_discord_enabled: bool = False
    mock_gemini_enabled: bool = False
    mock_garmin_enabled: bool = False
    mock_speech_enabled: bool = False

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() == "production"

    @property
    def is_mock_mode(self) -> bool:
        """Check if mock mode is enabled"""
        return self.enable_mock_mode or self.is_development

    @property
    def should_use_secret_manager(self) -> bool:
        """Check if Secret Manager should be used"""
        return self.use_secret_manager and self.google_cloud_project is not None


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()
