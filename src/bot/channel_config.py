"""
Channel configuration and categorization for Discord bot
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import discord
    from discord.ext.commands import Bot as DiscordBot

from ..utils.mixins import LoggerMixin


class ChannelCategory(Enum):
    """Channel categories for organizing different types of content"""

    CAPTURE = "capture"
    FINANCE = "finance"
    PRODUCTIVITY = "productivity"
    HEALTH = "health"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ChannelInfo:
    """Information about a Discord channel"""

    id: int
    name: str
    category: ChannelCategory
    description: str


class ChannelConfig(LoggerMixin):
    """Manages Discord channel configuration and categorization"""

    def __init__(self) -> None:
        """Initialize with empty channel config - will be populated when bot is set"""
        super().__init__()
        self.channels: dict[int, ChannelInfo] = {}
        self.bot: DiscordBot | None = None
        self.guild: discord.Guild | None = None

        # Standard channel names for auto-discovery
        self.standard_channel_names = {
            "inbox": ChannelCategory.CAPTURE,
            "voice": ChannelCategory.CAPTURE,
            "files": ChannelCategory.CAPTURE,
            "money": ChannelCategory.FINANCE,
            "finance-reports": ChannelCategory.FINANCE,
            "income": ChannelCategory.FINANCE,
            "subscriptions": ChannelCategory.FINANCE,
            "tasks": ChannelCategory.PRODUCTIVITY,
            "productivity-reviews": ChannelCategory.PRODUCTIVITY,
            "projects": ChannelCategory.PRODUCTIVITY,
            "health-activities": ChannelCategory.HEALTH,
            "health-sleep": ChannelCategory.HEALTH,
            "health-wellness": ChannelCategory.HEALTH,
            "health-analytics": ChannelCategory.HEALTH,
            "notifications": ChannelCategory.SYSTEM,
            "commands": ChannelCategory.SYSTEM,
            "logs": ChannelCategory.SYSTEM,
        }

    async def set_bot(self, bot: "DiscordBot") -> None:
        """Set the bot instance and discover channels"""
        self.bot = bot
        self.guild = bot.get_guild(bot.guilds[0].id) if bot.guilds else None

        if self._discover_channels_by_names():
            self.logger.info("Successfully initialized channels using channel names")
        else:
            self.logger.warning("Failed to discover required channels by name")

    def _load_channel_config(self) -> dict[int, ChannelInfo]:
        """Load channel configuration from standard channel names"""
        # Return empty dict - channels will be discovered by name when bot is set
        return {}

    def _discover_channels_by_names(self) -> bool:
        """Discover channels by their standard names"""
        if not self.guild:
            self.logger.warning("No guild available for channel discovery")
            return False

        discovered_channels = {}
        required_channels = ["inbox", "notifications", "commands"]
        found_required = 0

        for channel in self.guild.text_channels:
            channel_name = channel.name.lower().replace("-", "").replace("_", "")

            # Check for exact matches first
            if channel_name in self.standard_channel_names:
                category = self.standard_channel_names[channel_name]
                discovered_channels[channel.id] = ChannelInfo(
                    id=channel.id,
                    name=channel.name,
                    category=category,
                    description=f"Auto-discovered {category.value} channel",
                )
                self.logger.info(
                    f"Discovered channel: #{channel.name} (ID: {channel.id})"
                )

                if channel_name in required_channels:
                    found_required += 1

        # Update the channels dict
        self.channels.update(discovered_channels)

        # Check if we found the minimum required channels
        success = found_required >= len(required_channels)
        if success:
            self.logger.info(
                f"Successfully discovered {len(discovered_channels)} channels"
            )
        else:
            self.logger.warning(
                f"Only found {found_required}/{len(required_channels)} required channels"
            )

        return success

    def get_channel_info(self, channel_id: int) -> ChannelInfo:
        """Get channel information by ID"""
        return self.channels.get(
            channel_id,
            ChannelInfo(
                id=channel_id,
                name="unknown",
                category=ChannelCategory.UNKNOWN,
                description="Unknown channel",
            ),
        )

    def is_monitored_channel(self, channel_id: int) -> bool:
        """Check if a channel is being monitored by the bot"""
        return channel_id in self.channels

    def get_channels_by_category(self, category: ChannelCategory) -> set[int]:
        """Get all channel IDs for a specific category"""
        return {
            channel_id
            for channel_id, info in self.channels.items()
            if info.category == category
        }

    def get_channel_by_name(self, name: str) -> int | None:
        """Get channel ID by standard name"""
        name_lower = name.lower().replace("-", "").replace("_", "")
        for channel_id, info in self.channels.items():
            channel_name = info.name.lower().replace("-", "").replace("_", "")
            if channel_name == name_lower:
                return channel_id
        return None

    def get_all_monitored_channel_names(self) -> list[str]:
        """Get list of all monitored channel names"""
        return [info.name for info in self.channels.values()]

    def get_channel_purpose(self, channel_id: int) -> str:
        """Get human-readable purpose of a channel"""
        info = self.get_channel_info(channel_id)
        return f"{info.category.value.title()}: {info.description}"

    # Legacy API compatibility methods
    def get_channel(self, channel_id: int) -> int | None:
        """Legacy method for compatibility - returns channel ID if it exists"""
        return channel_id if channel_id in self.channels else None

    def get_capture_channels(self) -> set[int]:
        """Get capture category channel IDs"""
        return self.get_channels_by_category(ChannelCategory.CAPTURE)

    def get_finance_channels(self) -> set[int]:
        """Get finance category channel IDs"""
        return self.get_channels_by_category(ChannelCategory.FINANCE)

    def get_productivity_channels(self) -> set[int]:
        """Get productivity category channel IDs"""
        return self.get_channels_by_category(ChannelCategory.PRODUCTIVITY)

    def get_finance_expenses_channel(self) -> int | None:
        """Get expenses channel ID"""
        return self.get_channel_by_name("money")

    def get_finance_money_channel(self) -> int | None:
        """Get money channel ID"""
        return self.get_channel_by_name("money")

    def get_finance_income_channel(self) -> int | None:
        """Get income channel ID"""
        return self.get_channel_by_name("income")

    def __str__(self) -> str:
        """String representation of channel configuration"""
        return f"ChannelConfig({len(self.channels)} channels configured)"

    def __repr__(self) -> str:
        """Detailed representation of channel configuration"""
        channels_by_category: dict[ChannelCategory, list[str]] = {}
        for info in self.channels.values():
            if info.category not in channels_by_category:
                channels_by_category[info.category] = []
            channels_by_category[info.category].append(info.name)

        return f"ChannelConfig({channels_by_category})"
