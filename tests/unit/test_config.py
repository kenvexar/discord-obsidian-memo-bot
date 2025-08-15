"""Test configuration module"""

import os
from pathlib import Path


def test_config_import():
    """Test that configuration can be imported without error"""
    # Set required environment variables for testing
    os.environ["DISCORD_BOT_TOKEN"] = "test_token"
    os.environ["DISCORD_GUILD_ID"] = "123456789"
    os.environ["GEMINI_API_KEY"] = "test_api_key"
    os.environ["OBSIDIAN_VAULT_PATH"] = "/tmp/test_vault"
    os.environ["CHANNEL_INBOX"] = "111111111"
    os.environ["CHANNEL_VOICE"] = "222222222"
    os.environ["CHANNEL_FILES"] = "333333333"
    os.environ["CHANNEL_MONEY"] = "444444444"
    os.environ["CHANNEL_FINANCE_REPORTS"] = "555555555"
    os.environ["CHANNEL_TASKS"] = "666666666"
    os.environ["CHANNEL_PRODUCTIVITY_REVIEWS"] = "777777777"
    os.environ["CHANNEL_NOTIFICATIONS"] = "888888888"
    os.environ["CHANNEL_COMMANDS"] = "999999999"

    try:
        from src.config import settings

        assert settings.discord_bot_token.get_secret_value() == "test_token"
        assert settings.discord_guild_id == 123456789
        assert settings.gemini_api_key.get_secret_value() == "test_api_key"
        assert settings.obsidian_vault_path == Path("/tmp/test_vault")

    finally:
        # Clean up environment variables
        for key in [
            "DISCORD_BOT_TOKEN",
            "DISCORD_GUILD_ID",
            "GEMINI_API_KEY",
            "OBSIDIAN_VAULT_PATH",
            "CHANNEL_INBOX",
            "CHANNEL_VOICE",
            "CHANNEL_FILES",
            "CHANNEL_MONEY",
            "CHANNEL_FINANCE_REPORTS",
            "CHANNEL_TASKS",
            "CHANNEL_PRODUCTIVITY_REVIEWS",
            "CHANNEL_NOTIFICATIONS",
            "CHANNEL_COMMANDS",
        ]:
            if key in os.environ:
                del os.environ[key]
