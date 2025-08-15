"""
Secure settings loader with Google Cloud Secret Manager integration
"""

from ..security import SecureConfigManager
from ..utils import get_logger
from .settings import Settings, get_settings


class SecureSettingsManager:
    """Settings manager with secure credential loading"""

    def __init__(self):
        self.logger = get_logger("secure_settings")
        self.base_settings = get_settings()
        self.secure_config = None
        self._secrets_cache = {}

        if self.base_settings.should_use_secret_manager:
            self.secure_config = SecureConfigManager(
                project_id=self.base_settings.google_cloud_project
            )
            self.logger.info("Secure config manager initialized with Secret Manager")
        else:
            self.logger.info("Using environment variables for credential management")

    async def get_secure_token(self, key: str) -> str | None:
        """Get secure token (bot token, API key, etc.) from secure storage"""

        # Check cache first
        if key in self._secrets_cache:
            return self._secrets_cache[key]

        if self.secure_config:
            # Use Secret Manager
            value = await self.secure_config.get_config_value(key)
        else:
            # Fallback to environment variables
            value = getattr(self.base_settings, key, None)
            if hasattr(value, "get_secret_value"):
                value = value.get_secret_value()

        # Cache the value
        if value:
            self._secrets_cache[key] = value

        return value

    async def validate_all_credentials(self) -> dict[str, bool]:
        """Validate all required credentials are accessible"""
        results = {}

        # Required credentials
        required_secrets = ["discord_bot_token", "gemini_api_key"]

        # Optional credentials
        optional_secrets = [
            "google_cloud_speech_api_key",
            "garmin_username",
            "garmin_password",
        ]

        # Check required credentials
        for secret in required_secrets:
            value = await self.get_secure_token(secret)
            results[secret] = {
                "available": value is not None and len(value) > 0,
                "required": True,
            }

        # Check optional credentials
        for secret in optional_secrets:
            value = await self.get_secure_token(secret)
            results[secret] = {
                "available": value is not None and len(value) > 0,
                "required": False,
            }

        return results

    async def get_discord_token(self) -> str:
        """Get Discord bot token"""
        token = await self.get_secure_token("discord_bot_token")
        if not token:
            raise ValueError("Discord bot token not available")
        return token

    async def get_gemini_api_key(self) -> str:
        """Get Gemini API key"""
        key = await self.get_secure_token("gemini_api_key")
        if not key:
            raise ValueError("Gemini API key not available")
        return key

    async def get_speech_api_key(self) -> str | None:
        """Get Google Cloud Speech API key"""
        return await self.get_secure_token("google_cloud_speech_api_key")

    async def get_garmin_credentials(self) -> tuple[str, str] | None:
        """Get Garmin username and password"""
        username = await self.get_secure_token("garmin_username")
        password = await self.get_secure_token("garmin_password")

        if username and password:
            return username, password
        return None

    async def refresh_secret(self, key: str) -> bool:
        """Refresh a cached secret"""
        if key in self._secrets_cache:
            del self._secrets_cache[key]

        value = await self.get_secure_token(key)
        return value is not None

    async def clear_cache(self) -> None:
        """Clear the secrets cache"""
        self._secrets_cache.clear()
        if self.secure_config:
            self.secure_config.secret_manager.clear_cache()

        self.logger.info("Secrets cache cleared")

    def get_base_settings(self) -> Settings:
        """Get base settings (non-sensitive configuration)"""
        return self.base_settings


# Global secure settings manager
_secure_settings_manager = None


def get_secure_settings() -> SecureSettingsManager:
    """Get the global secure settings manager instance"""
    global _secure_settings_manager
    if _secure_settings_manager is None:
        _secure_settings_manager = SecureSettingsManager()
    return _secure_settings_manager


async def initialize_secure_settings() -> SecureSettingsManager:
    """Initialize and validate secure settings"""
    manager = get_secure_settings()

    # Validate all credentials
    validation_results = await manager.validate_all_credentials()

    # Check for missing required credentials
    missing_required = [
        key
        for key, result in validation_results.items()
        if result["required"] and not result["available"]
    ]

    if missing_required:
        raise ValueError(f"Missing required credentials: {', '.join(missing_required)}")

    # Log validation results
    logger = get_logger("secure_settings")
    logger.info("Credential validation completed", results=validation_results)

    return manager
