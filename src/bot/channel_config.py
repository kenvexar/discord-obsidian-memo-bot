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
    """Simplified channel categories"""

    CAPTURE = "capture"  # memo, voice, files
    SYSTEM = "system"  # notifications, commands


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

        # Simplified channel names for auto-discovery (5 channels only)
        self.standard_channel_names = {
            "memo": ChannelCategory.CAPTURE,  # 統合メイン入力チャンネル
            "voice": ChannelCategory.CAPTURE,  # 音声メモ（維持）
            "files": ChannelCategory.CAPTURE,  # ファイル共有（維持）
            "notifications": ChannelCategory.SYSTEM,  # システム通知（維持）
            "commands": ChannelCategory.SYSTEM,  # ボットコマンド（維持）
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
        required_channels = ["memo", "notifications", "commands"]
        found_required = 0

        for channel in self.guild.text_channels:
            channel_name = channel.name.lower().replace("-", "").replace("_", "")

            # Check for exact matches only
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
                f"Successfully discovered {len(discovered_channels)} channels "
                f"(required: {found_required}/{len(required_channels)})"
            )
        else:
            self.logger.warning(
                f"Only found {found_required}/{len(required_channels)} required channels. "
                f"Please create channels: {', '.join(f'#{name}' for name in required_channels)}"
            )

        return success

    def get_channel_info(self, channel_id: int) -> ChannelInfo:
        """Get channel information by ID"""
        return self.channels.get(
            channel_id,
            ChannelInfo(
                id=channel_id,
                name="unknown",
                category=ChannelCategory.CAPTURE,  # Default to CAPTURE
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

    def get_memo_channel(self) -> int | None:
        """Get unified memo channel ID"""
        return self.get_channel_by_name("memo")

    def get_capture_channels(self) -> set[int]:
        """Get capture category channel IDs"""
        return self.get_channels_by_category(ChannelCategory.CAPTURE)

    def get_system_channels(self) -> set[int]:
        """Get system category channel IDs"""
        return self.get_channels_by_category(ChannelCategory.SYSTEM)

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
