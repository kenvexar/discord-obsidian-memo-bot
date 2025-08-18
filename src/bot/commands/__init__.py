"""Refactored Discord command modules."""

from typing import Any

from ..channel_config import ChannelConfig
from .basic_commands import BasicCommands
from .config_commands import ConfigCommands
from .stats_commands import StatsCommands

__all__ = ["BasicCommands", "ConfigCommands", "StatsCommands", "setup_commands"]


async def setup_commands(bot: Any, channel_config: ChannelConfig) -> None:
    """Setup refactored bot commands."""
    await bot.add_cog(BasicCommands(bot))
    await bot.add_cog(ConfigCommands(bot, channel_config))
    await bot.add_cog(StatsCommands(bot))
