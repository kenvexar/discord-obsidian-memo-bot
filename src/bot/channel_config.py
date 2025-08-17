"""
Channel configuration and categorization for Discord bot
"""

from dataclasses import dataclass
from enum import Enum

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
        """Set the Discord bot instance for channel lookups."""
        self.bot = bot

    def _load_channel_config(self) -> dict[int, ChannelInfo]:
        """Load channel configuration from settings"""
        from ..config import get_settings

        settings = get_settings()
        channels = {}

        # Capture channels (improved categorization)
        channels[settings.channel_inbox] = ChannelInfo(
            id=settings.channel_inbox,
            name="memo-inbox",
            category=ChannelCategory.CAPTURE,
            description="General memo and idea capture",
        )

        channels[settings.channel_voice] = ChannelInfo(
            id=settings.channel_voice,
            name="voice-memo",
            category=ChannelCategory.CAPTURE,
            description="Voice memo processing",
        )

        channels[settings.channel_files] = ChannelInfo(
            id=settings.channel_files,
            name="file-uploads",
            category=ChannelCategory.CAPTURE,
            description="File attachment processing",
        )

        # Add quick notes channel if configured
        if hasattr(settings, "channel_quick_notes") and settings.channel_quick_notes:
            channels[settings.channel_quick_notes] = ChannelInfo(
                id=settings.channel_quick_notes,
                name="quick-notes",
                category=ChannelCategory.CAPTURE,
                description="Quick notes without AI processing",
            )

        # Finance channels (enhanced structure)
        channels[settings.channel_money] = ChannelInfo(
            id=settings.channel_money,
            name="expenses",
            category=ChannelCategory.FINANCE,
            description="Expense tracking",
        )

        # Add enhanced finance channels if configured
        if hasattr(settings, "channel_income") and settings.channel_income:
            channels[settings.channel_income] = ChannelInfo(
                id=settings.channel_income,
                name="income",
                category=ChannelCategory.FINANCE,
                description="Income tracking",
            )

        if (
            hasattr(settings, "channel_subscriptions")
            and settings.channel_subscriptions
        ):
            channels[settings.channel_subscriptions] = ChannelInfo(
                id=settings.channel_subscriptions,
                name="subscriptions",
                category=ChannelCategory.FINANCE,
                description="Subscription management",
            )

        channels[settings.channel_finance_reports] = ChannelInfo(
            id=settings.channel_finance_reports,
            name="finance-analytics",
            category=ChannelCategory.FINANCE,
            description="Financial reports and statistics",
        )

        # Productivity channels (enhanced structure)
        channels[settings.channel_tasks] = ChannelInfo(
            id=settings.channel_tasks,
            name="tasks",
            category=ChannelCategory.PRODUCTIVITY,
            description="Task management",
        )

        # Add projects channel if configured
        if hasattr(settings, "channel_projects") and settings.channel_projects:
            channels[settings.channel_projects] = ChannelInfo(
                id=settings.channel_projects,
                name="projects",
                category=ChannelCategory.PRODUCTIVITY,
                description="Project management",
            )

        channels[settings.channel_productivity_reviews] = ChannelInfo(
            id=settings.channel_productivity_reviews,
            name="daily-review",
            category=ChannelCategory.PRODUCTIVITY,
            description="Daily productivity reviews",
        )

        # Add weekly review channel if configured
        if (
            hasattr(settings, "channel_weekly_reviews")
            and settings.channel_weekly_reviews
        ):
            channels[settings.channel_weekly_reviews] = ChannelInfo(
                id=settings.channel_weekly_reviews,
                name="weekly-review",
                category=ChannelCategory.PRODUCTIVITY,
                description="Weekly productivity reviews",
            )

        # Add goal tracking channel if configured
        if (
            hasattr(settings, "channel_goal_tracking")
            and settings.channel_goal_tracking
        ):
            channels[settings.channel_goal_tracking] = ChannelInfo(
                id=settings.channel_goal_tracking,
                name="goal-tracking",
                category=ChannelCategory.PRODUCTIVITY,
                description="Goal tracking and management",
            )

        # Health channels (new category)
        if (
            hasattr(settings, "channel_health_activities")
            and settings.channel_health_activities
        ):
            channels[settings.channel_health_activities] = ChannelInfo(
                id=settings.channel_health_activities,
                name="activities",
                category=ChannelCategory.HEALTH,
                description="Activity and exercise tracking",
            )

        if hasattr(settings, "channel_health_sleep") and settings.channel_health_sleep:
            channels[settings.channel_health_sleep] = ChannelInfo(
                id=settings.channel_health_sleep,
                name="sleep",
                category=ChannelCategory.HEALTH,
                description="Sleep tracking and analysis",
            )

        if (
            hasattr(settings, "channel_health_wellness")
            and settings.channel_health_wellness
        ):
            channels[settings.channel_health_wellness] = ChannelInfo(
                id=settings.channel_health_wellness,
                name="wellness",
                category=ChannelCategory.HEALTH,
                description="General wellness and health tracking",
            )

        if (
            hasattr(settings, "channel_health_analytics")
            and settings.channel_health_analytics
        ):
            channels[settings.channel_health_analytics] = ChannelInfo(
                id=settings.channel_health_analytics,
                name="health-analytics",
                category=ChannelCategory.HEALTH,
                description="Health data analysis and reports",
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

        # Add system logs channel if configured
        if hasattr(settings, "channel_logs") and settings.channel_logs:
            channels[settings.channel_logs] = ChannelInfo(
                id=settings.channel_logs,
                name="logs",
                category=ChannelCategory.SYSTEM,
                description="System logs and debugging",
            )

        # Legacy channels (maintain backward compatibility)
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

    def get_health_channels(self) -> set[int]:
        """Get all health channel IDs"""
        return self.get_channels_by_category(ChannelCategory.HEALTH)

    def get_finance_money_channel(self) -> discord.TextChannel | None:
        """Get finance money channel if exists."""
        if not self.bot:
            return None
        from ..config import get_settings

        settings = get_settings()
        channel = self.bot.get_channel(settings.channel_money)
        return channel if isinstance(channel, discord.TextChannel) else None

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
