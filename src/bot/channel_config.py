"""
Channel configuration and categorization for Discord bot
"""

from dataclasses import dataclass
from enum import Enum

import discord

from ..config import settings
from ..utils import LoggerMixin


class ChannelCategory(Enum):
    """Channel categories for organizing different types of content"""

    CAPTURE = "capture"
    FINANCE = "finance"
    PRODUCTIVITY = "productivity"
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
        """Set the Discord bot instance for channel lookups."""
        self.bot = bot

    def _load_channel_config(self) -> dict[int, ChannelInfo]:
        """Load channel configuration from settings"""
        channels = {}

        # Capture channels
        channels[settings.channel_inbox] = ChannelInfo(
            id=settings.channel_inbox,
            name="inbox",
            category=ChannelCategory.CAPTURE,
            description="General memo and idea capture",
        )

        channels[settings.channel_voice] = ChannelInfo(
            id=settings.channel_voice,
            name="voice",
            category=ChannelCategory.CAPTURE,
            description="Voice memo processing",
        )

        channels[settings.channel_files] = ChannelInfo(
            id=settings.channel_files,
            name="files",
            category=ChannelCategory.CAPTURE,
            description="File attachment processing",
        )

        # Finance channels
        channels[settings.channel_money] = ChannelInfo(
            id=settings.channel_money,
            name="money",
            category=ChannelCategory.FINANCE,
            description="Income and expense tracking",
        )

        channels[settings.channel_finance_reports] = ChannelInfo(
            id=settings.channel_finance_reports,
            name="finance-reports",
            category=ChannelCategory.FINANCE,
            description="Financial reports and statistics",
        )

        # Productivity channels
        channels[settings.channel_tasks] = ChannelInfo(
            id=settings.channel_tasks,
            name="tasks",
            category=ChannelCategory.PRODUCTIVITY,
            description="Task and schedule management",
        )

        channels[settings.channel_productivity_reviews] = ChannelInfo(
            id=settings.channel_productivity_reviews,
            name="reviews",
            category=ChannelCategory.PRODUCTIVITY,
            description="Productivity reviews and analysis",
        )

        # System channels
        channels[settings.channel_notifications] = ChannelInfo(
            id=settings.channel_notifications,
            name="notifications",
            category=ChannelCategory.SYSTEM,
            description="System notifications and alerts",
        )

        channels[settings.channel_commands] = ChannelInfo(
            id=settings.channel_commands,
            name="commands",
            category=ChannelCategory.SYSTEM,
            description="Bot command execution",
        )

        # Activity log and daily tasks channels (optional)
        if settings.channel_activity_log:
            channels[settings.channel_activity_log] = ChannelInfo(
                id=settings.channel_activity_log,
                name="activity-log",
                category=ChannelCategory.PRODUCTIVITY,
                description="Daily activity log entries",
            )

        if settings.channel_daily_tasks:
            channels[settings.channel_daily_tasks] = ChannelInfo(
                id=settings.channel_daily_tasks,
                name="daily-tasks",
                category=ChannelCategory.PRODUCTIVITY,
                description="Daily task management",
            )

        return channels

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

    def get_finance_money_channel(self) -> discord.TextChannel | None:
        """Get finance money channel if exists."""
        if not self.bot:
            return None
        channel = self.bot.get_channel(settings.channel_money)
        return channel if isinstance(channel, discord.TextChannel) else None

    def get_finance_expenses_channel(self) -> discord.TextChannel | None:
        """Get finance expenses channel if exists."""
        if not self.bot or not hasattr(settings, "channel_expenses"):
            return None
        channel = self.bot.get_channel(getattr(settings, "channel_expenses", None))
        return channel if isinstance(channel, discord.TextChannel) else None

    def get_finance_income_channel(self) -> discord.TextChannel | None:
        """Get finance income channel if exists."""
        if not self.bot or not hasattr(settings, "channel_income"):
            return None
        channel = self.bot.get_channel(getattr(settings, "channel_income", None))
        return channel if isinstance(channel, discord.TextChannel) else None
