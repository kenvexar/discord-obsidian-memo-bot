"""Refactored Discord command modules."""

from typing import Any
import structlog

from ..channel_config import ChannelConfig
from .basic_commands import BasicCommands
from .config_commands import ConfigCommands
from .stats_commands import StatsCommands

__all__ = ["BasicCommands", "ConfigCommands", "StatsCommands", "setup_commands"]


async def setup_commands(bot: Any, channel_config: ChannelConfig) -> None:
    """Setup refactored bot commands."""
    logger = structlog.get_logger(__name__)
    try:
        await bot.add_cog(BasicCommands(bot))
        logger.info("BasicCommands loaded successfully")

        await bot.add_cog(ConfigCommands(bot, channel_config))
        logger.info("ConfigCommands loaded successfully")

        await bot.add_cog(StatsCommands(bot))
        logger.info("StatsCommands loaded successfully")

        logger.info("All command cogs loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load command cogs: {e}", exc_info=True)
