"""Statistics and analytics commands."""

from datetime import datetime
from typing import Any

import discord
import structlog
from discord import app_commands
from discord.ext import commands

from ..mixins.command_base import CommandMixin

logger = structlog.get_logger(__name__)


class StatsCommands(commands.Cog, CommandMixin):
    """Commands for displaying various statistics."""

    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.startup_time = datetime.now()

    @app_commands.command(name="bot", description="ボットの統計情報を表示")
    async def stats_bot_command(self, interaction: discord.Interaction) -> None:
        """Display bot statistics."""
        try:
            await self.defer_if_needed(interaction)

            # Calculate uptime
            uptime = self._get_uptime()

            # Get basic bot stats
            guild_count = len(self.bot.guilds)
            user_count = sum(
                guild.member_count for guild in self.bot.guilds if guild.member_count
            )

            # Memory usage (if available)
            try:
                import psutil

                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_text = f"{memory_mb:.1f} MB"
            except ImportError:
                memory_text = "利用不可"

            fields = [
                ("アップタイム", uptime, True),
                ("サーバー数", str(guild_count), True),
                ("ユーザー数", str(user_count), True),
                ("メモリ使用量", memory_text, True),
                ("Python バージョン", self._get_python_version(), True),
                ("Discord.py バージョン", discord.__version__, True),
            ]

            await self.send_success_response(
                interaction,
                "ボット統計情報",
                fields=fields,
                color=discord.Color.blue(),
                followup=True,
            )

        except Exception as e:
            logger.error("Failed to get bot stats", error=str(e))
            await self.send_error_response(
                interaction, "統計情報の取得に失敗しました。", followup=True
            )

    @app_commands.command(
        name="obsidian", description="Obsidian vault の統計情報を表示"
    )
    async def obsidian_stats_command(self, interaction: discord.Interaction) -> None:
        """Display Obsidian vault statistics."""
        try:
            await self.defer_if_needed(interaction)

            # Try to get Obsidian stats from the bot's components
            obsidian_stats = await self._get_obsidian_stats()

            if not obsidian_stats:
                await self.send_error_response(
                    interaction,
                    "Obsidian の統計情報を取得できませんでした。",
                    followup=True,
                )
                return

            fields = [
                ("総ノート数", str(obsidian_stats.get("total_notes", 0)), True),
                ("今日作成", str(obsidian_stats.get("notes_today", 0)), True),
                ("今週作成", str(obsidian_stats.get("notes_this_week", 0)), True),
                ("総文字数", f"{obsidian_stats.get('total_characters', 0):,}", True),
                (
                    "平均ノートサイズ",
                    f"{obsidian_stats.get('avg_note_size', 0):.0f} 文字",
                    True,
                ),
                ("最終更新", obsidian_stats.get("last_updated", "不明"), True),
            ]

            await self.send_success_response(
                interaction,
                "Obsidian Vault 統計",
                fields=fields,
                color=discord.Color.purple(),
                followup=True,
            )

        except Exception as e:
            logger.error("Failed to get Obsidian stats", error=str(e))
            await self.send_error_response(
                interaction, "Obsidian 統計情報の取得に失敗しました。", followup=True
            )

    @app_commands.command(name="finance", description="家計管理統計情報を表示")
    async def finance_stats_command(self, interaction: discord.Interaction) -> None:
        """Display finance statistics."""
        try:
            await self.defer_if_needed(interaction)

            # Try to get finance stats
            finance_stats = await self._get_finance_stats()

            if not finance_stats:
                await self.send_error_response(
                    interaction, "家計統計情報を取得できませんでした。", followup=True
                )
                return

            fields = [
                ("今月の支出", f"¥{finance_stats.get('monthly_expenses', 0):,}", True),
                (
                    "定期購入",
                    f"¥{finance_stats.get('monthly_subscriptions', 0):,}/月",
                    True,
                ),
                ("今年の支出", f"¥{finance_stats.get('yearly_expenses', 0):,}", True),
                (
                    "アクティブ定期購入",
                    f"{finance_stats.get('active_subscriptions', 0)}件",
                    True,
                ),
                ("最大カテゴリ", finance_stats.get("top_category", "不明"), True),
                ("最終記録", finance_stats.get("last_expense_date", "不明"), True),
            ]

            await self.send_success_response(
                interaction,
                "家計管理統計",
                fields=fields,
                color=discord.Color.green(),
                followup=True,
            )

        except Exception as e:
            logger.error("Failed to get finance stats", error=str(e))
            await self.send_error_response(
                interaction, "家計統計情報の取得に失敗しました。", followup=True
            )

    @app_commands.command(name="tasks", description="タスク管理統計情報を表示")
    async def task_stats_command(self, interaction: discord.Interaction) -> None:
        """Display task management statistics."""
        try:
            await self.defer_if_needed(interaction)

            # Try to get task stats
            task_stats = await self._get_task_stats()

            if not task_stats:
                await self.send_error_response(
                    interaction, "タスク統計情報を取得できませんでした。", followup=True
                )
                return

            fields = [
                ("アクティブタスク", str(task_stats.get("active_tasks", 0)), True),
                (
                    "完了タスク（今月）",
                    str(task_stats.get("completed_this_month", 0)),
                    True,
                ),
                ("遅延タスク", str(task_stats.get("overdue_tasks", 0)), True),
                ("完了率", f"{task_stats.get('completion_rate', 0):.1f}%", True),
                (
                    "平均完了時間",
                    f"{task_stats.get('avg_completion_days', 0):.1f}日",
                    True,
                ),
                ("最終更新", task_stats.get("last_updated", "不明"), True),
            ]

            await self.send_success_response(
                interaction,
                "タスク管理統計",
                fields=fields,
                color=discord.Color.orange(),
                followup=True,
            )

        except Exception as e:
            logger.error("Failed to get task stats", error=str(e))
            await self.send_error_response(
                interaction, "タスク統計情報の取得に失敗しました。", followup=True
            )

    def _get_uptime(self) -> str:
        """Calculate bot uptime."""
        uptime_delta = datetime.now() - self.startup_time
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            return f"{days}日 {hours}時間 {minutes}分"
        elif hours > 0:
            return f"{hours}時間 {minutes}分"
        else:
            return f"{minutes}分"

    def _get_python_version(self) -> str:
        """Get Python version."""
        import sys

        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    async def _get_obsidian_stats(self) -> dict[str, Any] | None:
        """Get Obsidian vault statistics."""
        try:
            # This would integrate with the actual Obsidian file manager
            # For now, return placeholder data
            return {
                "total_notes": 0,
                "notes_today": 0,
                "notes_this_week": 0,
                "total_characters": 0,
                "avg_note_size": 0,
                "last_updated": "未取得",
            }
        except Exception as e:
            logger.error("Failed to get Obsidian stats", error=str(e))
            return None

    async def _get_finance_stats(self) -> dict[str, Any] | None:
        """Get finance statistics."""
        try:
            # This would integrate with the actual finance manager
            # For now, return placeholder data
            return {
                "monthly_expenses": 0,
                "monthly_subscriptions": 0,
                "yearly_expenses": 0,
                "active_subscriptions": 0,
                "top_category": "未取得",
                "last_expense_date": "未取得",
            }
        except Exception as e:
            logger.error("Failed to get finance stats", error=str(e))
            return None

    async def _get_task_stats(self) -> dict[str, Any] | None:
        """Get task management statistics."""
        try:
            # This would integrate with the actual task manager
            # For now, return placeholder data
            return {
                "active_tasks": 0,
                "completed_this_month": 0,
                "overdue_tasks": 0,
                "completion_rate": 0.0,
                "avg_completion_days": 0.0,
                "last_updated": "未取得",
            }
        except Exception as e:
            logger.error("Failed to get task stats", error=str(e))
            return None
