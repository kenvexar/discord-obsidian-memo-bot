"""
Mock Discord client for development and testing
"""

import asyncio
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..utils import LoggerMixin


@dataclass
class MockMessage:
    """Mock Discord message"""

    id: int
    content: str
    author_id: int
    author_name: str
    channel_id: int
    guild_id: int
    timestamp: datetime
    attachments: list[dict[str, Any]]

    @property
    def clean_content(self) -> str:
        return self.content

    @property
    def author(self) -> "MockUser":
        return MockUser(self.author_id, self.author_name)

    @property
    def channel(self) -> "MockChannel":
        """Mock channel property for compatibility"""
        return MockChannel(self.channel_id, f"channel_{self.channel_id}", self.guild_id)

    @property
    def type(self) -> str:
        """Mock message type property"""
        return "default"

    @property
    def guild(self) -> "MockGuild":
        """Mock guild property"""
        return MockGuild(self.guild_id, "Test Guild", 5)

    @property
    def created_at(self) -> datetime:
        """Mock created_at property"""
        return self.timestamp

    @property
    def flags(self) -> Any:
        """Mock flags property"""

        class MockFlags:
            def __iter__(self) -> Iterator[Any]:
                return iter([])

        return MockFlags()

    @property
    def pinned(self) -> bool:
        """Mock pinned property"""
        return False


@dataclass
class MockUser:
    """Mock Discord user"""

    id: int
    name: str
    discriminator: str = "0000"

    @property
    def bot(self) -> bool:
        return self.name.endswith("_bot")


@dataclass
class MockChannel:
    """Mock Discord channel"""

    id: int
    name: str
    guild_id: int


@dataclass
class MockGuild:
    """Mock Discord guild"""

    id: int
    name: str
    member_count: int


class MockDiscordBot(LoggerMixin):
    """Mock Discord bot for testing without real Discord connection"""

    def __init__(self) -> None:
        self.is_ready = False
        self._start_time = datetime.now()
        self.guild = MockGuild(id=123456789, name="Test Guild", member_count=5)
        self.user = MockUser(id=98765, name="MockBot", discriminator="0001")
        self.guilds = [self.guild]
        self._event_handlers: dict[str, Callable[..., Any]] = {}

        # Mock channels based on configuration
        self.channels = {
            123456789: MockChannel(123456789, "inbox", 123456789),
            123456790: MockChannel(123456790, "voice", 123456789),
            123456791: MockChannel(123456791, "files", 123456789),
            123456792: MockChannel(123456792, "money", 123456789),
            123456793: MockChannel(123456793, "finance-reports", 123456789),
            123456794: MockChannel(123456794, "tasks", 123456789),
            123456795: MockChannel(123456795, "productivity-reviews", 123456789),
            123456796: MockChannel(123456796, "notifications", 123456789),
            123456797: MockChannel(123456797, "commands", 123456789),
            123456798: MockChannel(123456798, "activity-log", 123456789),
            123456799: MockChannel(123456799, "daily-tasks", 123456789),
        }

        self.message_handlers: list[Callable[..., Any]] = []
        self.ready_handlers: list[Callable[..., Any]] = []
        self.error_handlers: list[Callable[..., Any]] = []

        self.logger.info("Mock Discord bot initialized")

    async def start(self, token: str) -> None:
        """Mock bot start"""
        self.logger.info("Starting mock Discord bot", token_length=len(token))

        # Simulate connection delay
        await asyncio.sleep(0.5)

        # Call ready handlers
        for handler in self.ready_handlers:
            try:
                await handler()
            except Exception as e:
                self.logger.error("Error in ready handler", error=str(e))

        self.is_ready = True
        self.logger.info("Mock Discord bot started successfully")

        # Simulate some messages for testing
        await self._simulate_messages()

    async def close(self) -> None:
        """Mock bot stop"""
        self.logger.info("Stopping mock Discord bot")
        self.is_ready = False

    def get_guild(self, guild_id: int) -> MockGuild | None:
        """Get mock guild"""
        if guild_id == self.guild.id:
            return self.guild
        return None

    def get_channel(self, channel_id: int) -> MockChannel | None:
        """Get mock channel"""
        return self.channels.get(channel_id)

    async def send_message(self, channel_id: int, content: str) -> None:
        """Mock send message"""
        channel = self.get_channel(channel_id)
        if channel:
            self.logger.info(
                "Mock message sent",
                channel_name=channel.name,
                content_length=len(content),
            )
        else:
            self.logger.warning("Mock channel not found", channel_id=channel_id)

    def event(self, handler: Any) -> Any:
        """Register event handler (decorator)"""
        self._event_handlers[handler.__name__] = handler
        return handler

    def on_ready(self, handler: Any) -> Any:
        """Register ready handler"""
        self.ready_handlers.append(handler)
        return handler

    def on_message(self, handler: Any) -> Any:
        """Register message handler"""
        self.message_handlers.append(handler)
        return handler

    def on_error(self, handler: Any) -> Any:
        """Register error handler"""
        self.error_handlers.append(handler)
        return handler

    async def process_commands(self, message: MockMessage) -> None:
        """Mock command processing"""
        if message.content.startswith("/"):
            self.logger.debug(
                "Mock command processed", command=message.content.split()[0]
            )

    async def _simulate_messages(self) -> None:
        """Simulate incoming messages for testing"""
        await asyncio.sleep(1.0)  # Wait for setup to complete

        # Sample test messages
        test_messages = [
            {
                "content": "これはテストメッセージです。AIで要約してください。",
                "channel_id": 123456789,  # inbox
                "author": "test_user",
            },
            {
                "content": "今日のタスク: プロジェクトの進捗確認, 資料作成, チームミーティング",
                "channel_id": 123456799,  # daily-tasks
                "author": "test_user",
            },
            {
                "content": "💡 新しいアイデア: ユーザー体験を向上させるための機能改善案",
                "channel_id": 123456789,  # inbox
                "author": "test_user",
            },
        ]

        message_id = 1000
        for msg_data in test_messages:
            message = MockMessage(
                id=message_id,
                content=str(msg_data["content"]),
                author_id=12345,
                author_name=str(msg_data["author"]),
                channel_id=int(msg_data["channel_id"])
                if isinstance(msg_data["channel_id"], str | int)
                else 0,
                guild_id=self.guild.id,
                timestamp=datetime.now(),
                attachments=[],
            )

            # Process message through handlers
            for handler in self.message_handlers:
                try:
                    await handler(message)
                except Exception as e:
                    self.logger.error(
                        "Error in message handler",
                        message_id=message_id,
                        error=str(e),
                        exc_info=True,
                    )

            message_id += 1
            await asyncio.sleep(2.0)  # Delay between messages

        self.logger.info("Mock message simulation completed")
