"""
Secure settings loader with Google Cloud Secret Manager integration
"""

import structlog

from ..security.secret_manager import SecureConfigManager
from .settings import get_settings


class SecureSettingsManager:
    """Settings manager with secure credential loading"""

    def __init__(self) -> None:
        self.logger = structlog.get_logger("secure_settings")
        self.base_settings = get_settings()
        self.secure_config = None
        self._secrets_cache: dict[str, str] = {}

    def get_secure_setting(self, key: str, default: str | None = None) -> str | None:
        """Get a setting securely from Secret Manager or environment"""
        if not self.base_settings.should_use_secret_manager:
            return getattr(self.base_settings, key, default)

        if key in self._secrets_cache:
            return self._secrets_cache[key]

        if self.secure_config is None:
            try:
                self.secure_config = SecureConfigManager(
                    project_id=self.base_settings.google_cloud_project
                )
            except Exception as e:
                self.logger.warning(
                    "Failed to initialize secure config manager",
                    error=str(e),
                    key=key,
                )
                return getattr(self.base_settings, key, default)

        try:
            value = self.secure_config.get_secret(key)
            if value:
                self._secrets_cache[key] = value
                return value
        except Exception as e:
            self.logger.warning(
                "Failed to get secret from Secret Manager",
                error=str(e),
                key=key,
            )

        return getattr(self.base_settings, key, default)

    def get_discord_token(self) -> str:
        """Get Discord bot token securely"""
        token = self.get_secure_setting("discord_bot_token")
        if not token:
            raise ValueError("Discord bot token not found")
        return token if isinstance(token, str) else token.get_secret_value()

    def get_gemini_api_key(self) -> str:
        """Get Gemini API key securely"""
        key = self.get_secure_setting("gemini_api_key")
        if not key:
            raise ValueError("Gemini API key not found")
        return key if isinstance(key, str) else key.get_secret_value()


# Global instance for easy access
_secure_settings_manager: SecureSettingsManager | None = None


def get_secure_settings() -> SecureSettingsManager:
    """Get the global secure settings manager instance"""
    global _secure_settings_manager
    if _secure_settings_manager is None:
        _secure_settings_manager = SecureSettingsManager()
    return _secure_settings_manager
