"""
Main entry point for Discord-Obsidian Memo Bot
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config import get_secure_settings, settings
    from security.access_logger import (
        SecurityEventType,
        get_access_logger,
        log_security_event,
    )
    from utils import get_logger, setup_logging
except ImportError:
    # Fallback for when running as module
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.config import get_secure_settings, settings
    from src.security.access_logger import (
        SecurityEventType,
        get_access_logger,
        log_security_event,
    )
    from src.utils import get_logger, setup_logging


async def main() -> None:
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = get_logger("main")

    logger.info("Starting Discord-Obsidian Memo Bot", version="0.1.0")

    try:
        # Initialize security systems
        logger.info("Initializing security systems...")
        secure_settings = get_secure_settings()

        # Initialize access logger if enabled
        if settings.enable_access_logging:
            get_access_logger()
            await log_security_event(
                SecurityEventType.LOGIN_ATTEMPT,
                action="Bot startup",
                success=True,
                details={"version": "0.1.0", "mode": settings.environment},
            )
            logger.info("Access logging enabled")

        # Validate critical settings using secure manager
        discord_token = secure_settings.get_discord_token()
        if not discord_token:
            await log_security_event(
                SecurityEventType.LOGIN_ATTEMPT,
                action="Missing Discord token",
                success=False,
            )
            raise ValueError("Discord bot token not available")

        gemini_key = secure_settings.get_gemini_api_key()
        if not gemini_key:
            await log_security_event(
                SecurityEventType.LOGIN_ATTEMPT,
                action="Missing Gemini API key",
                success=False,
            )
            raise ValueError("Gemini API key not available")

        if not settings.obsidian_vault_path.exists():
            logger.warning(
                "Obsidian vault path does not exist, creating directory",
                path=str(settings.obsidian_vault_path),
            )
            settings.obsidian_vault_path.mkdir(parents=True, exist_ok=True)

        logger.info("Configuration validated successfully")
        logger.info("Environment", env=settings.environment)
        logger.info("Obsidian vault path", path=str(settings.obsidian_vault_path))

        # Initialize and start Discord bot
        try:
            from bot import DiscordBot
        except ImportError:
            from src.bot import DiscordBot

        bot = DiscordBot()

        # Start health check server for Cloud Run
        try:
            from monitoring import HealthServer
        except ImportError:
            from src.monitoring import HealthServer

        health_server = HealthServer(bot_instance=bot, port=8080)
        health_server.start()

        logger.info("Starting Discord bot...")
        try:
            await bot.start()
        finally:
            # Cleanup health server on shutdown
            health_server.stop()

    except Exception as e:
        logger.error("Failed to start bot", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
