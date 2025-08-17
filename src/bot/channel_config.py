"""
Channel configuration and categorization for Discord bot
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import discord

from ..utils.mixins import LoggerMixin


class ChannelCategory(Enum):
    """Channel categories for organizing different types of content"""

    CAPTURE = "capture"
    FINANCE = "finance"
    PRODUCTIVITY = "productivity"
    HEALTH = "health"  # 新規追加：健康管理カテゴリ
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
    """Configuration and utilities for Discord channel management"""

    def __init__(self) -> None:
        self.channels = self._load_channel_config()
        self.bot: discord.Client | None = None
        self.logger.info(
            "Channel configuration loaded", channel_count=len(self.channels)
        )

    def set_bot(self, bot: discord.Client) -> None:
        """Set the Discord bot instance and discover channels by name."""
        self.bot = bot

        # Always use name-based discovery
        if self._discover_channels_by_names():
            self.logger.info("Successfully initialized channels using channel names")
        else:
            self.logger.warning("Failed to discover required channels by name")

    def _load_channel_config(self) -> dict[int, ChannelInfo]:
        """Load channel configuration from standard channel names"""
        # Return empty dict - channels will be discovered by name when bot is set
        return {}

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

    def get_capture_channels(self) -> set[int]:
        """Get all capture channel IDs"""
        return self.get_channels_by_category(ChannelCategory.CAPTURE)

    def get_finance_channels(self) -> set[int]:
        """Get all finance channel IDs"""
        return self.get_channels_by_category(ChannelCategory.FINANCE)

    def get_productivity_channels(self) -> set[int]:
        """Get all productivity channel IDs"""
        return self.get_channels_by_category(ChannelCategory.PRODUCTIVITY)

    def get_system_channels(self) -> set[int]:
        """Get all system channel IDs"""
        return self.get_channels_by_category(ChannelCategory.SYSTEM)

    def get_health_channels(self) -> set[int]:
        """Get all health channel IDs"""
        return self.get_channels_by_category(ChannelCategory.HEALTH)

    def get_finance_money_channel(self) -> discord.TextChannel | None:
        """Get finance money channel if exists."""
        if not self.bot:
            return None

        return self.get_channel_by_name("money")

    def get_finance_expenses_channel(self) -> discord.TextChannel | None:
        """Get finance expenses channel if exists."""
        if not self.bot:
            return None
        from ..config import get_settings

        settings = get_settings()
        channel_id = getattr(settings, "channel_expenses", None)
        if not isinstance(channel_id, int):
            return None
        channel = self.bot.get_channel(channel_id)
        return channel if isinstance(channel, discord.TextChannel) else None

    def get_finance_income_channel(self) -> discord.TextChannel | None:
        """Get finance income channel if exists."""
        if not self.bot:
            return None
        from ..config import get_settings

        settings = get_settings()
        channel_id = getattr(settings, "channel_income", None)
        if not isinstance(channel_id, int):
            return None
        channel = self.bot.get_channel(channel_id)
        return channel if isinstance(channel, discord.TextChannel) else None

    def get_channel_by_name(self, name: str) -> discord.TextChannel | None:
        """Get Discord channel by name"""
        if not self.bot:
            return None

        from ..config import get_settings

        settings = get_settings()

        # Search in the configured guild
        guild = self.bot.get_guild(settings.discord_guild_id)
        if not guild:
            # Fall back to first available guild
            guild = self.bot.guilds[0] if self.bot.guilds else None

        if not guild:
            return None

        # Find channel by name (exact match)
        for channel in guild.text_channels:
            if channel.name == name:
                return channel

        return None

    def get_channel(self, name: str) -> discord.TextChannel | None:
        """Get Discord channel by name (alias for get_channel_by_name)"""
        return self.get_channel_by_name(name)

    def get_channel_id_by_name(self, name: str) -> int | None:
        """Get channel ID by name"""
        channel = self.get_channel_by_name(name)
        return channel.id if channel else None

    def find_channels_by_name_pattern(self, pattern: str) -> list[discord.TextChannel]:
        """Find channels matching a name pattern"""
        if not self.bot:
            return []

        import re

        from ..config import get_settings

        settings = get_settings()

        guild = self.bot.get_guild(settings.discord_guild_id)
        if not guild:
            guild = self.bot.guilds[0] if self.bot.guilds else None

        if not guild:
            return []

        matches = []
        regex = re.compile(pattern, re.IGNORECASE)

        for channel in guild.text_channels:
            if regex.search(channel.name):
                matches.append(channel)

        return matches

    def get_channel_info_by_name(self, name: str) -> ChannelInfo | None:
        """Get channel info by searching for channel name"""
        # First check if we have it in our configured channels
        for channel_info in self.channels.values():
            if channel_info.name == name:
                return channel_info

        # If not found in config, try to find the actual Discord channel
        channel = self.get_channel_by_name(name)
        if channel:
            return ChannelInfo(
                id=channel.id,
                name=channel.name,
                category=ChannelCategory.UNKNOWN,
                description=f"Found channel: {channel.name}",
            )

        return None

    def _find_channel_by_name(self, guild, name: str):
        """Find channel by exact name match"""
        for channel in guild.text_channels:
            if channel.name == name:
                return channel
        return None

    def _get_category_for_config_name(self, config_name: str) -> ChannelCategory:
        """Determine channel category based on configuration name"""
        if config_name in ["inbox", "voice", "files", "quick_notes"]:
            return ChannelCategory.CAPTURE
        elif config_name in ["money", "finance_reports", "income", "subscriptions"]:
            return ChannelCategory.FINANCE
        elif config_name in [
            "tasks",
            "productivity_reviews",
            "activity_log",
            "daily_tasks",
            "projects",
            "weekly_reviews",
            "goal_tracking",
        ]:
            return ChannelCategory.PRODUCTIVITY
        elif config_name in [
            "health_activities",
            "health_sleep",
            "health_wellness",
            "health_analytics",
        ]:
            return ChannelCategory.HEALTH
        elif config_name in ["notifications", "commands", "logs"]:
            return ChannelCategory.SYSTEM
        else:
            return ChannelCategory.UNKNOWN

    # Enhanced channel access methods
    def get_inbox_channel(self) -> discord.TextChannel | None:
        """Get inbox channel by name"""
        return self.get_channel_by_name("inbox")

    def get_voice_channel(self) -> discord.TextChannel | None:
        """Get voice memo channel by name"""
        return self.get_channel_by_name("voice")

    def get_files_channel(self) -> discord.TextChannel | None:
        """Get file uploads channel by name"""
        return self.get_channel_by_name("files")

    def get_expenses_channel(self) -> discord.TextChannel | None:
        """Get expenses channel by name"""
        return self.get_channel_by_name("money")

    def get_tasks_channel(self) -> discord.TextChannel | None:
        """Get tasks channel by name"""
        return self.get_channel_by_name("tasks")

    def get_notifications_channel(self) -> discord.TextChannel | None:
        """Get notifications channel by name"""
        return self.get_channel_by_name("notifications")

    def get_commands_channel(self) -> discord.TextChannel | None:
        """Get commands channel by name"""
        return self.get_channel_by_name("commands")

    def get_daily_review_channel(self) -> discord.TextChannel | None:
        """Get daily review channel by name"""
        return self.get_channel_by_name("productivity-reviews")

    def get_finance_analytics_channel(self) -> discord.TextChannel | None:
        """Get finance analytics channel by name"""
        return self.get_channel_by_name("finance-reports")

    def is_monitored_channel_by_name(self, channel_name: str) -> bool:
        """Check if a channel is being monitored by the bot (by name)"""
        channel = self.get_channel_by_name(channel_name)
        return channel is not None and self.is_monitored_channel(channel.id)

    def get_all_monitored_channel_names(self) -> list[str]:
        """Get all monitored channel names"""
        from ..config import get_settings

        settings = get_settings()

        return list(settings.get_channel_name_mapping().values())

    def _discover_channels_by_names(self) -> bool:
        """Discover and configure channels by searching for standard names"""
        if not self.bot:
            self.logger.error("Bot not set, cannot discover channels")
            return False

        from ..config import get_settings

        settings = get_settings()
        guild = self.bot.get_guild(settings.discord_guild_id)
        if not guild:
            guild = self.bot.guilds[0] if self.bot.guilds else None

        if not guild:
            self.logger.error("No guild available for channel discovery")
            return False

        discovered_channels = {}
        discovered_count = 0

        # Try to discover all supported channels
        all_channels = settings.get_all_supported_channel_names()
        required_names = settings.get_required_channel_names()

        for channel_name in all_channels:
            discord_channel = self._find_channel_by_name(guild, channel_name)
            if discord_channel:
                # Determine category and create channel info
                category = self._get_category_for_channel_name(channel_name)

                channel_info = ChannelInfo(
                    id=discord_channel.id,
                    name=discord_channel.name,
                    category=category,
                    description=f"{channel_name.replace('-', ' ').title()} channel",
                )

                discovered_channels[discord_channel.id] = channel_info
                discovered_count += 1

                self.logger.info(
                    "Discovered channel",
                    channel_name=channel_name,
                    channel_id=discord_channel.id,
                    category=category.value,
                )
            elif channel_name in required_names:
                self.logger.warning(
                    "Required channel not found",
                    channel_name=channel_name,
                    suggestion=f"Create a channel named '{channel_name}' in your Discord server",
                )

        # Update channels dict
        self.channels = discovered_channels

        # Check if we found the minimum required channels
        required_found = sum(
            1 for name in required_names if self.get_channel_by_name(name) is not None
        )

        if required_found >= len(required_names):
            self.logger.info(
                "Channel discovery completed successfully",
                discovered_count=discovered_count,
                required_found=required_found,
                total_supported=len(all_channels),
            )
            return True
        else:
            self.logger.error(
                "Missing required channels",
                required_found=required_found,
                required_total=len(required_names),
                missing_channels=[
                    name
                    for name in required_names
                    if not self.get_channel_by_name(name)
                ],
            )
            return False

    def get_channel_setup_status(self) -> dict[str, Any]:
        """Get status of channel setup for diagnostics"""
        from ..config import get_settings

        settings = get_settings()

        required_names = settings.get_required_channel_names()
        optional_names = settings.get_optional_channel_names()

        found_required = []
        missing_required = []
        found_optional = []
        missing_optional = []

        for name in required_names:
            if self.get_channel_by_name(name):
                found_required.append(name)
            else:
                missing_required.append(name)

        for name in optional_names:
            if self.get_channel_by_name(name):
                found_optional.append(name)
            else:
                missing_optional.append(name)

        return {
            "total_channels_found": len(self.channels),
            "required_channels_found": len(found_required),
            "required_channels_missing": missing_required,
            "optional_channels_found": len(found_optional),
            "optional_channels_missing": missing_optional,
            "setup_complete": len(missing_required) == 0,
        }

    def suggest_channel_setup(self) -> dict[str, Any]:
        """Provide suggestions for easy channel setup"""
        from ..config import get_settings

        settings = get_settings()

        required_names = settings.get_required_channel_names()
        optional_names = settings.get_optional_channel_names()

        missing_required = []
        missing_optional = []

        for name in required_names:
            if not self.get_channel_by_name(name):
                missing_required.append(
                    {
                        "name": name,
                        "description": self._get_channel_description(name),
                        "required": True,
                    }
                )

        for name in optional_names:
            if not self.get_channel_by_name(name):
                missing_optional.append(
                    {
                        "name": name,
                        "description": self._get_channel_description(name),
                        "required": False,
                    }
                )

        all_missing = missing_required + missing_optional

        return {
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "setup_commands": self._generate_setup_commands(all_missing),
        }

    def _get_category_for_channel_name(self, channel_name: str) -> ChannelCategory:
        """Determine channel category based on channel name"""
        if channel_name in ["inbox", "voice", "files", "quick-notes"]:
            return ChannelCategory.CAPTURE
        elif channel_name in ["money", "finance-reports", "income", "subscriptions"]:
            return ChannelCategory.FINANCE
        elif channel_name in [
            "tasks",
            "productivity-reviews",
            "activity-log",
            "daily-tasks",
            "projects",
            "weekly-reviews",
            "goal-tracking",
        ]:
            return ChannelCategory.PRODUCTIVITY
        elif channel_name in [
            "health-activities",
            "health-sleep",
            "health-wellness",
            "health-analytics",
        ]:
            return ChannelCategory.HEALTH
        elif channel_name in ["notifications", "commands", "logs"]:
            return ChannelCategory.SYSTEM
        else:
            return ChannelCategory.UNKNOWN

    def _get_channel_description(self, channel_name: str) -> str:
        """Get user-friendly description for channel name"""
        descriptions = {
            "inbox": "Main memo and message processing",
            "voice": "Voice memo uploads and processing",
            "files": "File attachment handling",
            "money": "Financial transaction tracking",
            "tasks": "Task and productivity management",
            "notifications": "System alerts and feedback",
            "commands": "Bot command execution",
            "finance-reports": "Financial analytics and reports",
            "productivity-reviews": "Daily productivity summaries",
        }
        return descriptions.get(
            channel_name, f"Channel for {channel_name} functionality"
        )

    def _generate_setup_commands(self, missing_channels: list) -> list[str]:
        """Generate Discord commands to create missing channels"""
        commands = []

        if missing_channels:
            commands.append("# Create these channels in your Discord server:")
            for channel in missing_channels:
                priority = "🔴 REQUIRED" if channel["required"] else "🟡 OPTIONAL"
                commands.append(
                    f"# {priority}: #{channel['name']} - {channel['description']}"
                )

        commands.append("")
        commands.append("# After creating channels, restart the bot or run:")
        commands.append("# /rescan-channels (if command is available)")

        return commands
