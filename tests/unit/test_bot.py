"""Test Discord bot functionality"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest

# Set up test environment variables before importing modules
os.environ.update(
    {
        "DISCORD_BOT_TOKEN": "test_token",
        "DISCORD_GUILD_ID": "123456789",
        "GEMINI_API_KEY": "test_api_key",
        "OBSIDIAN_VAULT_PATH": "/tmp/test_vault",
        "CHANNEL_INBOX": "111111111",
        "CHANNEL_VOICE": "222222222",
        "CHANNEL_FILES": "333333333",
        "CHANNEL_MONEY": "444444444",
        "CHANNEL_FINANCE_REPORTS": "555555555",
        "CHANNEL_TASKS": "666666666",
        "CHANNEL_PRODUCTIVITY_REVIEWS": "777777777",
        "CHANNEL_NOTIFICATIONS": "888888888",
        "CHANNEL_COMMANDS": "999999999",
    }
)

from src.bot.channel_config import ChannelCategory, ChannelConfig
from src.bot.handlers import MessageHandler


class TestChannelConfig:
    """Test channel configuration"""

    def test_channel_config_initialization(self):
        """Test channel config loads correctly"""
        config = ChannelConfig()

        assert len(config.channels) > 0
        assert config.is_monitored_channel(
            config.channels[list(config.channels.keys())[0]].id
        )

    def test_get_channels_by_category(self):
        """Test getting channels by category with mocked settings"""
        # settingsをモックしてテスト用のチャンネルIDを設定
        with patch("src.bot.channel_config.settings") as mock_settings:
            # CAPTUREカテゴリのチャンネル
            mock_settings.channel_inbox = 111111111
            mock_settings.channel_voice = 222222222
            mock_settings.channel_files = 333333333

            # FINANCEカテゴリのチャンネル
            mock_settings.channel_money = 444444444
            mock_settings.channel_finance_reports = 555555555

            # PRODUCTIVITYカテゴリのチャンネル
            mock_settings.channel_tasks = 666666666
            mock_settings.channel_productivity_reviews = 777777777

            # SYSTEMカテゴリのチャンネル
            mock_settings.channel_notifications = 888888888
            mock_settings.channel_commands = 999999999

            # OptionalチャンネルはNoneに設定
            mock_settings.channel_activity_log = None
            mock_settings.channel_daily_tasks = None

            # モックされたsettingsでChannelConfigを作成
            config = ChannelConfig()

            capture_channels = config.get_capture_channels()
            finance_channels = config.get_finance_channels()

            assert (
                len(capture_channels) > 0
            ), f"capture_channels is empty: {capture_channels}"
            assert (
                len(finance_channels) > 0
            ), f"finance_channels is empty: {finance_channels}"
            assert capture_channels.isdisjoint(
                finance_channels
            ), "Capture and finance channels should not overlap"

            # 具体的なチャンネルIDを確認
            expected_capture = {111111111, 222222222, 333333333}
            expected_finance = {444444444, 555555555}

            assert capture_channels == expected_capture
            assert finance_channels == expected_finance


class TestMessageHandler:
    """Test message handler functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.channel_config = ChannelConfig()
        self.handler = MessageHandler(self.channel_config)

    @pytest.mark.asyncio
    async def test_bot_message_ignored(self):
        """Test that bot messages are ignored"""
        # Create mock bot message
        mock_message = Mock(spec=discord.Message)
        mock_message.author.bot = True

        result = await self.handler.process_message(mock_message)
        assert result is None

    @pytest.mark.asyncio
    async def test_unmonitored_channel_ignored(self):
        """Test that unmonitored channels are ignored"""
        # Create mock message from unmonitored channel
        mock_message = Mock(spec=discord.Message)
        mock_message.author.bot = False
        mock_message.channel.id = 999999999  # Invalid channel ID

        # Test early return when channel is not monitored
        with patch.object(
            self.channel_config, "is_monitored_channel", return_value=False
        ):
            result = await self.handler.process_message(mock_message)
            assert result is None

    @pytest.mark.asyncio
    async def test_valid_message_processing(self):
        """Test processing of valid messages"""
        # Get a valid channel ID
        valid_channel_id = list(self.channel_config.channels.keys())[0]
        channel_info = self.channel_config.get_channel_info(valid_channel_id)

        # Create a more complete mock message
        mock_message = Mock(spec=discord.Message)
        mock_message.id = 123456789
        mock_message.content = "Test message"
        mock_message.author.bot = False
        mock_message.author.id = 987654321
        mock_message.author.display_name = "Test User"
        mock_message.author.name = "testuser"
        mock_message.author.discriminator = "1234"
        mock_message.author.avatar = None
        mock_message.author.mention = "<@987654321>"
        mock_message.channel.id = valid_channel_id
        mock_message.channel.name = "test-channel"
        mock_message.channel.type = discord.ChannelType.text
        mock_message.channel.category = None
        mock_message.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_message.edited_at = None
        mock_message.guild.id = 111111111
        mock_message.guild.name = "Test Guild"
        mock_message.attachments = []
        mock_message.embeds = []
        mock_message.mentions = []
        mock_message.role_mentions = []
        mock_message.channel_mentions = []
        mock_message.reactions = []
        mock_message.stickers = []
        mock_message.reference = None
        mock_message.type = discord.MessageType.default
        mock_message.flags = discord.MessageFlags()
        mock_message.pinned = False
        mock_message.tts = False
        mock_message.mention_everyone = False

        # Mock the routing method to avoid actual processing
        self.handler._route_message_by_category = AsyncMock()

        result = await self.handler.process_message(mock_message)

        assert result is not None
        assert "metadata" in result
        assert "channel_info" in result
        assert result["channel_info"]["name"] == channel_info.name
        assert result["channel_info"]["category"] == channel_info.category.value

        # Check metadata structure
        metadata = result["metadata"]
        assert "basic" in metadata
        assert "content" in metadata
        assert "attachments" in metadata
        assert "references" in metadata
        assert "discord_features" in metadata
        assert "timing" in metadata

        # Verify routing was called
        self.handler._route_message_by_category.assert_called_once()
