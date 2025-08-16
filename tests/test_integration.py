#!/usr/bin/env python3
"""
包括的な統合テスト - Discord-Obsidian Memo Bot

全機能の統合フローをテストし、システム全体の動作を確認する
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from src.ai.models import (
    AIProcessingResult,
    CategoryResult,
    ProcessingCategory,
    SummaryResult,
    TagResult,
)

# テスト対象のモジュールをインポート
from src.bot.client import DiscordBot
from src.bot.handlers import MessageHandler
from src.config import get_settings
from src.security.access_logger import AccessLogger, SecurityEventType


class MockMessage:
    """Discord メッセージのモック"""

    def __init__(self, content: str, author_id: int = 123, channel_id: int = 12345):
        self.id = 123456789
        self.content = content
        self.author = MagicMock(spec=discord.Member)
        self.author.configure_mock(id=author_id)
        self.author.mention = f"<@{author_id}>"
        self.author.bot = False  # Fix: Ensure message is not from bot
        self.channel = MagicMock()
        self.channel.id = channel_id
        self.channel.name = "test-channel"
        self.attachments = []
        self.created_at = datetime.now()
        self.flags = MagicMock(spec=discord.MessageFlags)
        self.flags.crossposted = False
        self.type = discord.MessageType.default
        self.pinned = False  # 追加
        self.tts = False  # 追加
        self.guild = MagicMock(name="mock_guild")  # 追加
        self.guild.name = "Test Guild"  # 追加
        self.guild.id = 123456789  # 追加
        self.reference = None  # 追加
        self.embeds = []  # 追加
        self.reactions = []  # 追加
        self.mentions = []  # 追加
        self.role_mentions = []  # 追加
        self.channel_mentions = []  # 追加
        self.mention_everyone = False  # 追加
        self.stickers = []  # 追加
        self.edited_at = None  # 追加


class MockDiscordChannel:
    """Discord チャンネルのモック"""

    def __init__(self, channel_id: int, name: str):
        self.id = channel_id
        self.name = name
        self.send = AsyncMock()


@pytest.mark.asyncio
class TestCompleteMessageProcessingFlow:
    """完全なメッセージ処理フローのテスト"""

    async def test_end_to_end_message_processing(self):
        """エンドツーエンドのメッセージ処理テスト"""
        print("=== エンドツーエンドメッセージ処理テスト ===")

        # テスト用の一時ディレクトリ
        with tempfile.TemporaryDirectory() as temp_dir:
            # モックの設定
            mock_channel_config = MagicMock()
            mock_channel_config.get_channel_category.return_value = "INBOX"
            mock_channel_config.is_monitored_channel.return_value = (
                True  # Fix: Ensure channel is monitored
            )

            # Channel info mock setup
            mock_channel_info = MagicMock()
            mock_channel_info.name = "test-channel"
            mock_channel_info.id = 12345
            from src.bot.channel_config import ChannelCategory

            mock_channel_info.category = ChannelCategory.CAPTURE
            mock_channel_info.description = "Test channel"
            mock_channel_config.get_channel_info.return_value = mock_channel_info

            # AI処理をモック
            with patch(
                "src.ai.mock_processor.MockAIProcessor.process_text"
            ) as mock_process_text:
                # テストメッセージの作成
                test_message = MockMessage(
                    content="今日は素晴らしい一日でした。新しいプロジェクトのアイデアが浮かびました。",
                    author_id=123,  # 修正
                    channel_id=12345,
                )

                mock_ai_result_instance = AIProcessingResult(
                    message_id=test_message.id,
                    processed_at=datetime.now(),
                    summary=SummaryResult(
                        summary="新しいプロジェクトアイデアについて",
                        processing_time_ms=100,
                        model_used="mock-gemini-pro",
                    ),
                    tags=TagResult(
                        tags=["アイデア", "プロジェクト"],
                        processing_time_ms=50,
                        model_used="mock-gemini-pro",
                    ),
                    category=CategoryResult(
                        category=ProcessingCategory.PROJECT,
                        confidence_score=0.95,
                        processing_time_ms=70,
                        model_used="mock-gemini-pro",
                    ),
                    total_processing_time_ms=1500,
                )
                mock_process_text.return_value = mock_ai_result_instance

                # Obsidianファイル作成をモック
                with patch("src.bot.handlers.ObsidianFileManager") as mock_obsidian:
                    mock_obsidian_instance = AsyncMock()
                    # vault_path を設定
                    mock_obsidian_instance.vault_path = Path(temp_dir)
                    mock_obsidian_instance.create_note.return_value = {
                        "success": True,
                        "file_path": Path(temp_dir) / "test_note.md",
                        "note_title": "新しいプロジェクトアイデア",
                    }
                    mock_obsidian.return_value = mock_obsidian_instance

                    # メッセージハンドラーの初期化をモックのスコープ内に移動
                    handler = MessageHandler(mock_channel_config)

                    # メッセージ処理の実行
                    result = await handler.process_message(test_message)

                    # 結果の検証
                    assert result is not None
                    assert result.get("metadata") is not None
                    assert result.get("ai_processing") is not None
                    assert result.get("channel_info") is not None
                    assert result.get("processing_timestamp") is not None

                    # AI処理が呼ばれたことを確認
                    mock_process_text.assert_called_once()

                    # Obsidianファイル作成が呼ばれたことを確認
                    mock_obsidian_instance.save_note.assert_called_once()

        print("✓ エンドツーエンドメッセージ処理が正常に動作")

    async def test_api_limit_handling(self):
        """API制限到達時の処理テスト"""
        print("=== API制限処理テスト ===")

        mock_channel_config = MagicMock()
        mock_channel_config.is_monitored_channel.return_value = True
        # Channel info mock setup
        mock_channel_info = MagicMock()
        mock_channel_info.name = "test-channel"
        mock_channel_info.id = 12345
        from src.bot.channel_config import ChannelCategory

        mock_channel_info.category = ChannelCategory.CAPTURE
        mock_channel_info.description = "Test channel"
        mock_channel_config.get_channel_info.return_value = mock_channel_info

        handler = MessageHandler(mock_channel_config)

        test_message = MockMessage("テストメッセージ", author_id=123)

        # APIエラーをシミュレート
        with patch("src.ai.processor.AIProcessor") as mock_ai_processor:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.process_text.side_effect = Exception("API quota exceeded")
            mock_ai_processor.return_value = mock_ai_instance

            # エラーハンドリングのテスト
            result = await handler.process_message(test_message)

            # フォールバック処理の確認
            assert result is not None
            assert result.get("metadata") is not None
            # AI処理が失敗した場合、ai_processingはNoneになる
            assert result.get("ai_processing") is None

        print("✓ API制限エラーハンドリングが正常に動作")


@pytest.mark.asyncio
class TestSecurityIntegration:
    """セキュリティ機能の統合テスト"""

    async def test_access_logging_integration(self):
        """アクセスログ機能の統合テスト"""
        print("=== アクセスログ統合テスト ===")

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as temp_file:
            logger = AccessLogger(Path(temp_file.name))

            # セキュリティイベントのログ
            from src.security.access_logger import SecurityEvent

            event = SecurityEvent(
                event_type=SecurityEventType.COMMAND_EXECUTION,
                user_id="test_user",
                channel_id="123",
                action="help",
                success=True,
            )

            await logger.log_event(event)

            # ログファイルの確認
            with open(temp_file.name) as f:
                log_line = f.readline()
                log_data = json.loads(log_line)

                assert log_data["event_type"] == "command_execution"
                assert log_data["user_id"] == "test_user"
                assert log_data["action"] == "help"
                assert log_data["success"]

            # ファイルクリーンアップ
            os.unlink(temp_file.name)

        print("✓ アクセスログ機能が正常に動作")

    async def test_suspicious_activity_detection(self):
        """不審な活動検知テスト"""
        print("=== 不審活動検知テスト ===")

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as temp_file:
            logger = AccessLogger(Path(temp_file.name))

            # 大量の失敗イベントを生成
            from src.security.access_logger import SecurityEvent

            user_id = "suspicious_user"
            for i in range(6):  # 閾値(5)を超える失敗
                event = SecurityEvent(
                    event_type=SecurityEventType.COMMAND_EXECUTION,
                    user_id=user_id,
                    action=f"failed_command_{i}",
                    success=False,
                )
                await logger.log_event(event)

            # 不審活動フラグの確認
            assert logger.is_user_suspicious(user_id)

            # セキュリティレポートの生成
            report = await logger.get_security_report(hours=1)
            assert report["suspicious_activities"] > 0

            # ファイルクリーンアップ
            os.unlink(temp_file.name)

        print("✓ 不審活動検知が正常に動作")


@pytest.mark.asyncio
class TestMonitoringIntegration:
    """監視システムの統合テスト"""

    async def test_system_metrics_collection(self):
        """システムメトリクス収集テスト"""
        print("=== システムメトリクス統合テスト ===")

        from src.bot.client import SystemMetrics

        metrics = SystemMetrics()

        # メトリクスの記録
        metrics.record_message_processed()
        metrics.record_ai_request(True, 1500)
        metrics.record_file_created()

        # ヘルスステータスの取得
        health = metrics.get_system_health_status()

        assert health["total_messages_processed"] == 1
        assert health["ai_success_rate"] == 100.0
        assert health["files_created"] == 1
        assert "performance_score" in health

        print("✓ システムメトリクス収集が正常に動作")

    async def test_api_usage_monitoring(self):
        """API使用量監視テスト"""
        print("=== API使用量監視テスト ===")

        from src.bot.client import APIUsageMonitor

        monitor = APIUsageMonitor()

        # API使用量の記録
        monitor.track_gemini_usage(1000, True)
        monitor.track_speech_usage(2.5, True)

        # ダッシュボードデータの取得
        dashboard = monitor.get_usage_dashboard()

        assert dashboard["gemini_api"]["requests_used"] == 1
        assert dashboard["gemini_api"]["tokens_processed"] == 1000
        assert dashboard["speech_api"]["minutes_used"] == 2.5

        # 使用量レポートのエクスポート
        report = monitor.export_usage_report()
        assert "cost_estimation" in report["summary"]

        print("✓ API使用量監視が正常に動作")


@pytest.mark.asyncio
class TestFullSystemIntegration:
    """システム全体の統合テスト"""

    async def test_bot_initialization_flow(self):
        """ボット初期化フローの統合テスト"""
        print("=== ボット初期化統合テスト ===")

        # 設定の確認
        settings = get_settings()
        assert settings is not None

        # モック環境でのボット初期化テスト
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "test",
                "ENABLE_MOCK_MODE": "true",
                "DISCORD_BOT_TOKEN": "test_token",
                "DISCORD_GUILD_ID": "123456789",
                "GEMINI_API_KEY": "test_gemini_key",
                "OBSIDIAN_VAULT_PATH": "/tmp/test_vault",
            },
        ):
            settings.enable_mock_mode = True

            # テスト用のObsidianディレクトリ作成
            Path("/tmp/test_vault").mkdir(exist_ok=True)

            # DiscordBotの初期化（mockモード）
            bot = DiscordBot()

            assert bot is not None
            assert bot.system_metrics is not None
            assert bot.api_usage_monitor is not None
            assert bot.notification_system is not None

        print("✓ ボット初期化フローが正常に動作")

    async def test_health_check_endpoints(self):
        """ヘルスチェックエンドポイントのテスト"""
        print("=== ヘルスチェック統合テスト ===")

        from src.health_server import HealthServer

        # モックボットインスタンス
        mock_bot = MagicMock()
        mock_bot.is_ready = True
        mock_bot._start_time = datetime.now()
        mock_bot.client.guilds = []

        # ヘルスサーバーの作成（実際の起動はしない）
        health_server = HealthServer(bot_instance=mock_bot, port=8080)

        assert health_server.bot_instance == mock_bot
        assert health_server.port == 8080

        print("✓ ヘルスチェック機能が正常に初期化")


async def run_integration_tests():
    """全ての統合テストを実行"""
    print("Discord-Obsidian Memo Bot 統合テストを開始します...\n")

    try:
        # メッセージ処理フローテスト
        message_tests = TestCompleteMessageProcessingFlow()
        await message_tests.test_end_to_end_message_processing()
        await message_tests.test_api_limit_handling()
        print()

        # セキュリティ統合テスト
        security_tests = TestSecurityIntegration()
        await security_tests.test_access_logging_integration()
        await security_tests.test_suspicious_activity_detection()
        print()

        # 監視統合テスト
        monitoring_tests = TestMonitoringIntegration()
        await monitoring_tests.test_system_metrics_collection()
        await monitoring_tests.test_api_usage_monitoring()
        print()

        # システム全体統合テスト
        system_tests = TestFullSystemIntegration()
        await system_tests.test_bot_initialization_flow()
        await system_tests.test_health_check_endpoints()
        print()

        print("🎉 全ての統合テストが正常に完了しました！")
        print("\n統合テスト結果:")
        print("✓ メッセージ処理フロー - 正常動作")
        print("✓ API制限エラーハンドリング - 正常動作")
        print("✓ セキュリティアクセスログ - 正常動作")
        print("✓ 不審活動検知 - 正常動作")
        print("✓ システムメトリクス収集 - 正常動作")
        print("✓ API使用量監視 - 正常動作")
        print("✓ ボット初期化フロー - 正常動作")
        print("✓ ヘルスチェック機能 - 正常動作")

        return True

    except Exception as e:
        print(f"❌ 統合テストエラー: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    exit(0 if success else 1)
