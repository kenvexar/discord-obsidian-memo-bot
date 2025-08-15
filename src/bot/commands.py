"""
Discord bot commands implementation
"""

from datetime import datetime

import discord
from discord.ext import commands

from ..ai import AIProcessor, ProcessingSettings
from ..ai.note_analyzer import AdvancedNoteAnalyzer
from ..config import settings
from ..obsidian import (
    DailyNoteIntegration,
    MetadataManager,
    ObsidianFileManager,
    TemplateEngine,
    VaultOrganizer,
)
from ..utils import LoggerMixin
from .channel_config import ChannelConfig


class BasicCommands(commands.Cog, LoggerMixin):
    """Basic bot commands"""

    def __init__(self, bot: commands.Bot, channel_config: ChannelConfig) -> None:
        self.bot = bot
        self.channel_config = channel_config
        self.logger.info("Basic commands initialized")

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context) -> None:
        """Display help information"""
        embed = discord.Embed(
            title="🤖 Discord-Obsidian Memo Bot",
            description="統合ライフログ・ナレッジマネジメントシステム",
            color=0x5865F2,
        )

        embed.add_field(
            name="📝 基本コマンド",
            value=(
                "`/help` - このヘルプを表示\n"
                "`/status` - システム状態確認\n"
                "`/search [キーワード]` - Vault内検索\n"
                "`/stats` - 統計情報表示\n"
                "`/random_note` - ランダムノート表示"
            ),
            inline=False,
        )

        embed.add_field(
            name="🤖 AI処理コマンド",
            value=(
                "`/ai_test [テキスト]` - AI処理のテスト実行\n"
                "`/ai_stats` - AI処理統計の表示\n"
                "`/ai_health` - AIシステムヘルスチェック\n"
                "`/search_notes [キーワード]` - セマンティック検索"
            ),
            inline=False,
        )

        embed.add_field(
            name="📚 Obsidian管理コマンド",
            value=(
                "`/vault_stats` - Vault統計情報の表示\n"
                "`/vault_search [キーワード]` - ノート検索\n"
                "`/vault_organize [true/false]` - Vault組織化\n"
                "`/vault_report` - 詳細レポート生成"
            ),
            inline=False,
        )

        embed.add_field(
            name="📅 デイリーノート管理コマンド",
            value=(
                "`/daily_note [YYYY-MM-DD]` - デイリーノート作成\n"
                "`/activity_log [内容]` - Activity Log追加\n"
                "`/daily_task [タスク内容]` - Daily Task追加"
            ),
            inline=False,
        )

        embed.add_field(
            name="📝 テンプレート管理コマンド",
            value=(
                "`/list_templates` - 利用可能なテンプレート一覧\n"
                "`/create_from_template [template] [content]` - テンプレートからノート作成\n"
                "`/create_default_templates` - デフォルトテンプレート作成"
            ),
            inline=False,
        )

        embed.add_field(
            name="⚙️ システム管理コマンド",
            value=(
                "`/config [category] [key] [value]` - 設定管理\n"
                "`/backup [type]` - バックアップ実行\n"
                "`/review [type]` - レビュー実行\n"
                "`/system_health` - システム健康状態"
            ),
            inline=False,
        )

        embed.add_field(
            name="📋 監視チャンネル",
            value=(
                f"📥 受信箱: <#{settings.channel_inbox}>\n"
                f"🎤 音声: <#{settings.channel_voice}>\n"
                f"📎 ファイル: <#{settings.channel_files}>\n"
                f"💰 家計: <#{settings.channel_money}>\n"
                f"📋 タスク: <#{settings.channel_tasks}>"
            ),
            inline=False,
        )

        embed.set_footer(
            text="このボットはDiscordメッセージを自動的にObsidianに保存し、AI処理で整理します。"
        )

        await ctx.send(embed=embed)

        self.logger.info("Help command executed", user=str(ctx.author))

    @commands.command(name="status")
    async def status_command(self, ctx: commands.Context) -> None:
        """Display system status"""
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ ギルド情報を取得できませんでした。")
            return

        # Check channel accessibility
        accessible_channels = 0
        total_channels = len(self.channel_config.channels)

        for channel_id in self.channel_config.channels:
            channel = guild.get_channel(channel_id)
            if channel:
                accessible_channels += 1

        embed = discord.Embed(
            title="🔍 システム状態",
            color=0x00FF00 if accessible_channels == total_channels else 0xFFFF00,
        )

        embed.add_field(
            name="📊 基本情報",
            value=(
                f"**ボット状態**: ✅ オンライン\n"
                f"**ギルド**: {guild.name}\n"
                f"**メンバー数**: {guild.member_count}\n"
                f"**レイテンシ**: {round(self.bot.latency * 1000)}ms"
            ),
            inline=False,
        )

        embed.add_field(
            name="📡 チャンネル監視",
            value=(
                f"**監視チャンネル**: {accessible_channels}/{total_channels}\n"
                f"**キャプチャ**: {len(self.channel_config.get_capture_channels())}\n"
                f"**家計管理**: {len(self.channel_config.get_finance_channels())}\n"
                f"**生産性**: {len(self.channel_config.get_productivity_channels())}"
            ),
            inline=False,
        )

        embed.add_field(
            name="🔧 設定",
            value=(
                f"**環境**: {settings.environment}\n"
                f"**ログレベル**: {settings.log_level}\n"
                f"**Obsidian Vault**: 設定済み"
            ),
            inline=False,
        )

        await ctx.send(embed=embed)

        self.logger.info("Status command executed", user=str(ctx.author))

    @commands.command(name="search")
    async def search_command(
        self, ctx: commands.Context, *, query: str | None = None
    ) -> None:
        """Search in Obsidian vault"""
        if not query:
            await ctx.send(
                "❌ 検索キーワードを指定してください。\n使用方法: `/search [キーワード]`"
            )
            return

        try:
            # ObsidianFileManagerを初期化
            from ..obsidian import ObsidianFileManager

            obsidian_manager = ObsidianFileManager()

            # ノート検索を実行
            search_results = await obsidian_manager.search_notes(query=query, limit=10)

            embed = discord.Embed(
                title="🔍 検索結果",
                description=f"キーワード: `{query}`",
                color=0x5865F2,
            )

            if search_results:
                # 結果を表示（最大10件）
                results_text = ""
                for i, note in enumerate(search_results[:10], 1):
                    # ファイル名からタイムスタンプを除去してタイトルを作成
                    title = note.title or note.file_path.stem
                    if len(title) > 50:
                        title = title[:47] + "..."

                    # 作成日時をフォーマット
                    created_str = note.created_at.strftime("%Y-%m-%d %H:%M")

                    results_text += f"**{i}.** [{title}]({note.file_path.name})\n"
                    results_text += f"   📅 {created_str}"
                    if note.tags:
                        tags_str = " ".join([f"#{tag}" for tag in note.tags[:3]])
                        results_text += f" | 🏷️ {tags_str}"
                    results_text += "\n\n"

                embed.add_field(
                    name=f"📝 検索結果 ({len(search_results)}件)",
                    value=results_text,
                    inline=False,
                )

                if len(search_results) > 10:
                    embed.add_field(
                        name="ℹ️ 注意",
                        value=f"さらに{len(search_results) - 10}件の結果があります。",
                        inline=False,
                    )
            else:
                embed.add_field(
                    name="📝 結果",
                    value="🔍 該当するノートが見つかりませんでした。",
                    inline=False,
                )

            # 検索のヒントを追加
            embed.add_field(
                name="💡 検索のヒント",
                value="• 部分一致で検索されます\n• タグや内容も検索対象に含まれます\n• 複数のキーワードはスペースで区切ってください",
                inline=False,
            )

            await ctx.send(embed=embed)

            self.logger.info(
                "Search command executed",
                user=str(ctx.author),
                query=query,
                results_count=len(search_results),
            )

        except Exception as e:
            embed = discord.Embed(
                title="❌ エラー",
                description="検索中にエラーが発生しました。",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)

            self.logger.error(
                "Search command error", user=str(ctx.author), query=query, error=str(e)
            )

    @commands.command(name="stats")
    async def stats_command(self, ctx: commands.Context) -> None:
        """Display comprehensive statistics"""
        try:
            # 統計情報を並行して取得
            obsidian_stats_task = self._get_obsidian_stats()
            finance_stats_task = self._get_finance_stats()
            task_stats_task = self._get_task_stats()

            # 並行実行
            import asyncio

            obsidian_stats, finance_stats, task_stats = await asyncio.gather(
                obsidian_stats_task, finance_stats_task, task_stats_task
            )

            embed = discord.Embed(
                title="📊 システム統計情報", color=0x5865F2, timestamp=datetime.now()
            )

            # Obsidian統計
            if obsidian_stats:
                stats_text = (
                    f"📝 **総ノート数**: {obsidian_stats['total_notes']}件\n"
                    f"💾 **総サイズ**: {obsidian_stats['total_size_mb']:.1f}MB\n"
                    f"🤖 **AI処理済み**: {obsidian_stats['ai_processed']}件\n"
                    f"📅 **今日作成**: {obsidian_stats['created_today']}件\n"
                    f"📈 **今週作成**: {obsidian_stats['created_week']}件"
                )
                if obsidian_stats.get("top_tags"):
                    tags_text = " ".join(
                        [f"#{tag}" for tag in obsidian_stats["top_tags"][:5]]
                    )
                    stats_text += f"\n🏷️ **人気タグ**: {tags_text}"

                embed.add_field(name="📚 Obsidian統計", value=stats_text, inline=False)

            # 家計統計
            if finance_stats:
                finance_text = (
                    f"💰 **総収支**: ¥{finance_stats['net_balance']:,.0f}\n"
                    f"📥 **総収入**: ¥{finance_stats['total_income']:,.0f}\n"
                    f"📤 **総支出**: ¥{finance_stats['total_expenses']:,.0f}\n"
                    f"🔄 **定期購入数**: {finance_stats['total_subscriptions']}件\n"
                    f"⚠️ **支払い予定**: {finance_stats['upcoming_payments']}件"
                )
                embed.add_field(name="💰 家計統計", value=finance_text, inline=False)

            # タスク統計
            if task_stats:
                task_text = (
                    f"✅ **完了タスク**: {task_stats['completed']}件\n"
                    f"🔄 **進行中**: {task_stats['in_progress']}件\n"
                    f"⏳ **未着手**: {task_stats['todo']}件\n"
                    f"🎯 **完了率**: {task_stats['completion_rate']:.1f}%\n"
                    f"📋 **総スケジュール**: {task_stats['total_schedules']}件"
                )
                embed.add_field(name="📋 タスク統計", value=task_text, inline=False)

            # システム情報
            system_text = (
                f"🤖 **Bot稼働時間**: {self._get_uptime()}\n"
                f"🔧 **バージョン**: 0.1.0\n"
                f"📡 **接続状態**: {'✅ 正常' if self.bot.is_ready else '❌ 切断'}"
            )
            embed.add_field(name="⚙️ システム情報", value=system_text, inline=False)

            embed.set_footer(text="最終更新")

            await ctx.send(embed=embed)

            self.logger.info("Stats command executed", user=str(ctx.author))

        except Exception as e:
            embed = discord.Embed(
                title="❌ エラー",
                description="統計情報の取得中にエラーが発生しました。",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)

            self.logger.error(
                "Stats command error", user=str(ctx.author), error=str(e), exc_info=True
            )

    async def _get_obsidian_stats(self):
        """Obsidian統計情報を取得"""
        try:
            from ..obsidian import ObsidianFileManager

            obsidian_manager = ObsidianFileManager()
            vault_stats = await obsidian_manager.get_vault_stats()

            return {
                "total_notes": vault_stats.total_notes,
                "total_size_mb": vault_stats.total_size_bytes / (1024 * 1024),
                "ai_processed": vault_stats.ai_processed_notes,
                "created_today": vault_stats.notes_created_today,
                "created_week": vault_stats.notes_created_this_week,
                "top_tags": list(vault_stats.most_common_tags.keys())[:5],
            }
        except Exception as e:
            self.logger.warning("Failed to get Obsidian stats", error=str(e))
            return None

    async def _get_finance_stats(self):
        """家計統計情報を取得"""
        try:
            from ..finance import ExpenseManager, SubscriptionManager
            from ..obsidian import ObsidianFileManager

            obsidian_manager = ObsidianFileManager()
            subscription_manager = SubscriptionManager(obsidian_manager)
            expense_manager = ExpenseManager(obsidian_manager)

            # 基本統計
            subscriptions = await subscription_manager.get_all_subscriptions()
            upcoming = await subscription_manager.get_upcoming_payments()

            # 今月の収支（簡易版）
            from datetime import date

            today = date.today()
            start_of_month = date(today.year, today.month, 1)

            total_income = await expense_manager.get_total_income(start_of_month, today)
            total_expenses = await expense_manager.get_total_expenses(
                start_of_month, today
            )

            return {
                "total_subscriptions": len(subscriptions),
                "upcoming_payments": len(upcoming),
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_balance": total_income - total_expenses,
            }
        except Exception as e:
            self.logger.warning("Failed to get finance stats", error=str(e))
            return None

    async def _get_task_stats(self):
        """タスク統計情報を取得"""
        try:
            from ..obsidian import ObsidianFileManager
            from ..tasks import ScheduleManager, TaskManager

            obsidian_manager = ObsidianFileManager()
            task_manager = TaskManager(obsidian_manager)
            schedule_manager = ScheduleManager(obsidian_manager)

            # タスク統計
            all_tasks = await task_manager.get_all_tasks()
            completed = len([t for t in all_tasks if t.status.value == "completed"])
            in_progress = len([t for t in all_tasks if t.status.value == "in_progress"])
            todo = len([t for t in all_tasks if t.status.value == "todo"])

            completion_rate = (completed / len(all_tasks) * 100) if all_tasks else 0

            # スケジュール統計
            all_schedules = await schedule_manager.get_all_schedules()

            return {
                "completed": completed,
                "in_progress": in_progress,
                "todo": todo,
                "completion_rate": completion_rate,
                "total_schedules": len(all_schedules),
            }
        except Exception as e:
            self.logger.warning("Failed to get task stats", error=str(e))
            return None

    def _get_uptime(self):
        """Bot稼働時間を取得"""
        try:
            if hasattr(self.bot, "_start_time"):
                uptime_delta = datetime.now() - self.bot._start_time
                hours = uptime_delta.total_seconds() // 3600
                minutes = (uptime_delta.total_seconds() % 3600) // 60
                return f"{int(hours)}時間{int(minutes)}分"
            return "不明"
        except Exception:
            return "不明"

    @commands.command(name="random_note")
    async def random_note_command(self, ctx: commands.Context) -> None:
        """Display random note from vault"""
        try:
            import random

            from ..obsidian import ObsidianFileManager

            obsidian_manager = ObsidianFileManager()

            # 全ノートを取得
            all_notes = await obsidian_manager.search_notes(limit=1000)

            if not all_notes:
                embed = discord.Embed(
                    title="🎲 ランダムノート",
                    description="📝 Vaultにノートが見つかりませんでした。",
                    color=0xFF9500,
                )
                await ctx.send(embed=embed)
                return

            # ランダムに1つ選択
            random_note = random.choice(all_notes)

            embed = discord.Embed(title="🎲 ランダムノート", color=0x5865F2)

            # ノートタイトル
            title = random_note.title or random_note.file_path.stem
            if len(title) > 100:
                title = title[:97] + "..."

            embed.add_field(name="📝 タイトル", value=f"**{title}**", inline=False)

            # ノート情報
            created_str = random_note.created_at.strftime("%Y-%m-%d %H:%M")
            info_text = f"📅 作成: {created_str}\n"

            if random_note.frontmatter.ai_category:
                info_text += f"🏷️ カテゴリ: {random_note.frontmatter.ai_category}\n"

            if random_note.frontmatter.status:
                status_emojis = {"active": "✅", "archived": "📦", "draft": "📝"}
                status_emoji = status_emojis.get(
                    random_note.frontmatter.status.value, "📄"
                )
                info_text += f"{status_emoji} ステータス: {random_note.frontmatter.status.value}\n"

            # ファイルパス情報
            relative_path = random_note.file_path.relative_to(
                obsidian_manager.vault_path
            )
            info_text += f"📁 パス: `{relative_path}`"

            embed.add_field(name="ℹ️ 詳細情報", value=info_text, inline=False)

            # ノート内容のプレビュー
            if random_note.content:
                # マークダウンを簡略化してプレビュー
                preview = (
                    random_note.content.replace("#", "")
                    .replace("*", "")
                    .replace("_", "")
                )
                # 長すぎる場合は切り詰め
                if len(preview) > 300:
                    preview = preview[:297] + "..."

                embed.add_field(
                    name="👁️ プレビュー", value=f"```\n{preview}\n```", inline=False
                )

            # タグがある場合
            all_tags = random_note.frontmatter.tags + random_note.frontmatter.ai_tags
            if all_tags:
                tags_text = " ".join([f"#{tag.lstrip('#')}" for tag in all_tags[:8]])
                embed.add_field(name="🏷️ タグ", value=tags_text, inline=False)

            # AI処理情報
            if random_note.frontmatter.ai_processed:
                ai_text = "🤖 AI処理済み"
                if (
                    random_note.frontmatter.ai_confidence
                    and random_note.frontmatter.ai_confidence > 0
                ):
                    ai_text += f" (信頼度: {random_note.frontmatter.ai_confidence:.2f})"
                embed.add_field(name="🧠 AI情報", value=ai_text, inline=False)

            # フッター
            embed.set_footer(text=f"総ノート数: {len(all_notes)}件から選択")

            await ctx.send(embed=embed)

            self.logger.info(
                "Random note command executed",
                user=str(ctx.author),
                note_title=title,
                total_notes=len(all_notes),
            )

        except Exception as e:
            embed = discord.Embed(
                title="❌ エラー",
                description="ランダムノートの取得中にエラーが発生しました。",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)

            self.logger.error(
                "Random note command error",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="config")
    @commands.has_permissions(administrator=True)
    async def config_command(
        self, ctx: commands.Context, action: str = None, *, args: str = None
    ) -> None:
        """動的設定管理コマンド (管理者のみ)"""
        if not hasattr(self.bot, "config_manager"):
            embed = discord.Embed(
                title="❌ エラー",
                description="設定管理システムが利用できません。",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)
            return

        config_manager = self.bot.config_manager

        try:
            if not action:
                # 設定概要を表示
                summary = config_manager.get_config_summary()

                embed = discord.Embed(
                    title="⚙️ 設定管理システム",
                    description="システム設定の概要",
                    color=0x5865F2,
                )

                embed.add_field(
                    name="📊 統計情報",
                    value=(
                        f"システム設定カテゴリ: {summary.get('total_categories', 0)}\n"
                        f"ユーザー設定数: {summary.get('user_config_count', 0)}\n"
                        f"今日の変更数: {summary.get('config_changes_today', 0)}"
                    ),
                    inline=False,
                )

                if summary.get("last_updated"):
                    embed.add_field(
                        name="🕒 最終更新", value=summary["last_updated"], inline=False
                    )

                embed.add_field(
                    name="💡 使用方法",
                    value=(
                        "`/config show` - すべての設定を表示\n"
                        "`/config set category.key value` - 設定を変更\n"
                        "`/config get category.key` - 特定の設定を取得\n"
                        "`/config history` - 変更履歴を表示\n"
                        "`/config validate_api api_name api_key` - APIキー検証"
                    ),
                    inline=False,
                )

                await ctx.send(embed=embed)

            elif action == "show":
                # すべての設定を表示
                await self._show_all_configs(ctx, config_manager)

            elif action == "set" and args:
                # 設定を変更
                await self._set_config(ctx, config_manager, args)

            elif action == "get" and args:
                # 特定の設定を取得
                await self._get_config(ctx, config_manager, args)

            elif action == "history":
                # 変更履歴を表示
                await self._show_config_history(ctx, config_manager)

            elif action == "validate_api" and args:
                # APIキー検証
                await self._validate_api_key(ctx, config_manager, args)

            else:
                embed = discord.Embed(
                    title="❌ 無効なアクション",
                    description=f"アクション '{action}' は認識されません。",
                    color=0xFF0000,
                )
                await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ エラー",
                description=f"設定コマンドの実行中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)

            self.logger.error(
                "Config command error",
                action=action,
                args=args,
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    async def _show_all_configs(self, ctx, config_manager):
        """すべての設定を表示"""
        embed = discord.Embed(title="⚙️ システム設定一覧", color=0x5865F2)

        # デフォルト設定をベースに現在の設定を表示
        for category_name, default_configs in config_manager.default_configs.items():
            config_text = ""
            for key, default_value in default_configs.items():
                current_value = await config_manager.get_config(
                    config_manager.ConfigCategory(category_name), key
                )
                status = "✅" if current_value == default_value else "🔧"
                config_text += f"{status} `{key}`: {current_value}\n"

            if config_text:
                embed.add_field(
                    name=f"📁 {category_name.upper()}", value=config_text, inline=False
                )

        await ctx.send(embed=embed)

    async def _set_config(self, ctx, config_manager, args):
        """設定を変更"""
        try:
            parts = args.split(" ", 1)
            if len(parts) != 2:
                raise ValueError("使用方法: /config set category.key value")

            config_path, value = parts
            if "." not in config_path:
                raise ValueError("設定パスは 'category.key' の形式で指定してください")

            category_name, key = config_path.split(".", 1)

            # 値の型変換
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "", 1).isdigit():
                value = float(value)

            # 設定更新
            success = await config_manager.set_config(
                config_manager.ConfigCategory(category_name),
                key,
                value,
                requester=str(ctx.author),
            )

            if success:
                embed = discord.Embed(
                    title="✅ 設定更新完了",
                    description=f"`{category_name}.{key}` を `{value}` に設定しました。",
                    color=0x00FF00,
                )
            else:
                embed = discord.Embed(
                    title="❌ 設定更新失敗",
                    description="設定の更新に失敗しました。",
                    color=0xFF0000,
                )

            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ エラー",
                description=f"設定変更中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)

    async def _get_config(self, ctx, config_manager, args):
        """特定の設定を取得"""
        try:
            if "." not in args:
                raise ValueError("設定パスは 'category.key' の形式で指定してください")

            category_name, key = args.split(".", 1)

            value = await config_manager.get_config(
                config_manager.ConfigCategory(category_name), key
            )

            embed = discord.Embed(title="⚙️ 設定値", color=0x5865F2)

            embed.add_field(
                name=f"📍 {category_name}.{key}", value=f"`{value}`", inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ エラー",
                description=f"設定取得中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)

    async def _show_config_history(self, ctx, config_manager):
        """設定変更履歴を表示"""
        history = config_manager.get_config_history(limit=10)

        if not history:
            embed = discord.Embed(
                title="📋 設定変更履歴",
                description="設定変更の履歴がありません。",
                color=0x5865F2,
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title="📋 設定変更履歴 (最新10件)", color=0x5865F2)

        for i, record in enumerate(history[:10], 1):
            timestamp = record["timestamp"]
            change_text = (
                f"**変更者**: {record.get('requester', '不明')}\n"
                f"**カテゴリ**: {record['category']}\n"
                f"**キー**: {record['key']}\n"
                f"**変更**: `{record['old_value']}` → `{record['new_value']}`"
            )

            embed.add_field(name=f"{i}. {timestamp}", value=change_text, inline=False)

        await ctx.send(embed=embed)

    async def _validate_api_key(self, ctx, config_manager, args):
        """APIキーを検証"""
        try:
            parts = args.split(" ", 1)
            if len(parts) != 2:
                raise ValueError("使用方法: /config validate_api api_name api_key")

            api_name, api_key = parts

            # 検証処理の実行
            embed = discord.Embed(
                title="🔍 APIキー検証中...",
                description=f"{api_name} APIキーを検証しています。",
                color=0xFF9500,
            )
            message = await ctx.send(embed=embed)

            validation_result = await config_manager.validate_api_key(api_name, api_key)

            if validation_result["valid"]:
                embed = discord.Embed(
                    title="✅ APIキー検証成功",
                    description=f"{api_name} APIキーは有効です。",
                    color=0x00FF00,
                )

                if validation_result["details"]:
                    details_text = "\n".join(
                        [
                            f"**{k}**: {v}"
                            for k, v in validation_result["details"].items()
                        ]
                    )
                    embed.add_field(name="詳細情報", value=details_text, inline=False)
            else:
                embed = discord.Embed(
                    title="❌ APIキー検証失敗",
                    description=f"{api_name} APIキーは無効です。",
                    color=0xFF0000,
                )

                if validation_result["error"]:
                    embed.add_field(
                        name="エラー詳細",
                        value=validation_result["error"][:500],
                        inline=False,
                    )

            await message.edit(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ エラー",
                description=f"APIキー検証中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )
            await ctx.send(embed=embed)


class AICommands(commands.Cog, LoggerMixin):
    """AI processing commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        # AI処理システムの初期化
        processing_settings = ProcessingSettings(
            min_text_length=10,
            max_text_length=2000,
            enable_summary=True,
            enable_tags=True,
            enable_categorization=True,
        )

        try:
            self.ai_processor = AIProcessor(settings=processing_settings)
            # 高度なノート分析システムの初期化
            obsidian_manager = ObsidianFileManager()
            self.note_analyzer = AdvancedNoteAnalyzer(
                obsidian_file_manager=obsidian_manager, ai_processor=self.ai_processor
            )
            self.logger.info("AI commands initialized with processor and note analyzer")
        except Exception as e:
            self.ai_processor = None
            self.note_analyzer = None
            self.logger.error("Failed to initialize AI systems", error=str(e))

    @commands.command(name="ai_test")
    async def ai_test_command(
        self, ctx: commands.Context, *, text: str | None = None
    ) -> None:
        """Test AI processing functionality"""
        if not self.ai_processor:
            await ctx.send(
                "❌ AI処理システムが利用できません。設定を確認してください。"
            )
            return

        if not text:
            await ctx.send(
                "❌ 処理するテキストを指定してください。\n使用方法: `/ai_test [テキスト]`"
            )
            return

        # 処理中メッセージを送信
        processing_msg = await ctx.send("🤖 AI処理を実行中...")

        try:
            # AI処理を実行
            result = await self.ai_processor.process_text(
                text=text, message_id=ctx.message.id
            )

            # 結果をembed形式で表示
            embed = discord.Embed(
                title="🤖 AI処理結果", color=0x00FF00 if not result.errors else 0xFF0000
            )

            # 処理時間
            embed.add_field(
                name="⏱️ 処理時間",
                value=f"{result.total_processing_time_ms}ms",
                inline=True,
            )

            # キャッシュヒット
            embed.add_field(
                name="💾 キャッシュ",
                value="ヒット" if result.cache_hit else "ミス",
                inline=True,
            )

            # 要約結果
            if result.summary:
                summary_text = result.summary.summary
                if len(summary_text) > 1000:
                    summary_text = summary_text[:1000] + "..."

                embed.add_field(name="📝 要約", value=summary_text, inline=False)

            # タグ結果
            if result.tags and result.tags.tags:
                tags_text = ", ".join(result.tags.tags[:10])
                embed.add_field(name="🏷️ タグ", value=tags_text, inline=False)

            # カテゴリ結果
            if result.category:
                confidence = result.category.confidence_score
                category_text = (
                    f"{result.category.category.value} (信頼度: {confidence:.2f})"
                )
                embed.add_field(name="📂 カテゴリ", value=category_text, inline=True)

            # エラーがある場合
            if result.errors:
                embed.add_field(
                    name="❌ エラー", value="\n".join(result.errors[:3]), inline=False
                )

            # 元のメッセージを更新
            await processing_msg.edit(content=None, embed=embed)

            self.logger.info(
                "AI test command executed",
                user=str(ctx.author),
                text_length=len(text),
                has_errors=bool(result.errors),
                processing_time=result.total_processing_time_ms,
            )

        except Exception as e:
            embed = discord.Embed(
                title="❌ AI処理エラー",
                description=f"処理中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "AI test command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="ai_stats")
    async def ai_stats_command(self, ctx: commands.Context) -> None:
        """Display AI processing statistics"""
        if not self.ai_processor:
            await ctx.send("❌ AI処理システムが利用できません。")
            return

        try:
            stats = self.ai_processor.get_stats()
            cache_info = self.ai_processor.get_cache_info()

            embed = discord.Embed(title="📊 AI処理統計", color=0x5865F2)

            # 基本統計
            success_rate = (
                stats.successful_requests / max(stats.total_requests, 1)
            ) * 100
            embed.add_field(
                name="📈 処理統計",
                value=(
                    f"**総リクエスト**: {stats.total_requests}\n"
                    f"**成功**: {stats.successful_requests}\n"
                    f"**失敗**: {stats.failed_requests}\n"
                    f"**成功率**: {success_rate:.1f}%"
                ),
                inline=True,
            )

            # パフォーマンス
            embed.add_field(
                name="⚡ パフォーマンス",
                value=(
                    f"**平均処理時間**: {stats.average_processing_time_ms:.0f}ms\n"
                    f"**総処理時間**: {stats.total_processing_time_ms:,}ms\n"
                    f"**API呼び出し**: {stats.api_calls_made}\n"
                    f"**トークン使用**: {stats.total_tokens_used:,}"
                ),
                inline=True,
            )

            # キャッシュ
            cache_hit_rate = (stats.cache_hits / max(stats.total_requests, 1)) * 100
            embed.add_field(
                name="💾 キャッシュ",
                value=(
                    f"**ヒット**: {stats.cache_hits}\n"
                    f"**ミス**: {stats.cache_misses}\n"
                    f"**ヒット率**: {cache_hit_rate:.1f}%\n"
                    f"**エントリ数**: {cache_info['total_entries']}"
                ),
                inline=True,
            )

            # エラー統計
            if stats.error_counts:
                error_text = "\n".join(
                    [
                        f"**{error}**: {count}"
                        for error, count in list(stats.error_counts.items())[:5]
                    ]
                )
                embed.add_field(
                    name="❌ エラー統計", value=error_text or "なし", inline=False
                )

            embed.set_footer(
                text=f"最終更新: {stats.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            await ctx.send(embed=embed)

            self.logger.info("AI stats command executed", user=str(ctx.author))

        except Exception as e:
            await ctx.send(f"❌ 統計情報の取得に失敗しました: {str(e)}")

            self.logger.error(
                "AI stats command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="ai_health")
    async def ai_health_command(self, ctx: commands.Context) -> None:
        """Check AI system health"""
        if not self.ai_processor:
            await ctx.send("❌ AI処理システムが利用できません。")
            return

        # ヘルスチェック実行中メッセージ
        checking_msg = await ctx.send("🔍 AI システムヘルスチェック実行中...")

        try:
            health_status = await self.ai_processor.health_check()

            if health_status["status"] == "healthy":
                embed = discord.Embed(title="✅ AI システム正常", color=0x00FF00)

                embed.add_field(
                    name="📊 詳細",
                    value=(
                        f"**応答時間**: {health_status.get('response_time_ms', 'N/A')}ms\n"
                        f"**モデル**: {health_status.get('model', 'N/A')}\n"
                        f"**キャッシュエントリ**: {health_status.get('cache_entries', 0)}\n"
                        f"**キューサイズ**: {health_status.get('queue_size', 0)}"
                    ),
                    inline=False,
                )

                if "total_requests" in health_status:
                    success_rate = health_status.get("success_rate", 0) * 100
                    embed.add_field(
                        name="📈 統計",
                        value=(
                            f"**総リクエスト**: {health_status['total_requests']}\n"
                            f"**成功率**: {success_rate:.1f}%"
                        ),
                        inline=True,
                    )

            else:
                embed = discord.Embed(
                    title="❌ AI システム異常",
                    description=f"エラー: {health_status.get('error', '不明なエラー')}",
                    color=0xFF0000,
                )

                embed.add_field(
                    name="📊 詳細",
                    value=f"**モデル**: {health_status.get('model', 'N/A')}",
                    inline=False,
                )

            await checking_msg.edit(content=None, embed=embed)

            self.logger.info(
                "AI health command executed",
                user=str(ctx.author),
                status=health_status["status"],
            )

        except Exception as e:
            embed = discord.Embed(
                title="❌ ヘルスチェック失敗",
                description=f"ヘルスチェック実行中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await checking_msg.edit(content=None, embed=embed)

            self.logger.error(
                "AI health command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="search_notes")
    async def search_notes_command(
        self, ctx: commands.Context, *, query: str | None = None
    ) -> None:
        """Semantic search for related notes"""
        if not self.note_analyzer:
            await ctx.send(
                "❌ ノート分析システムが利用できません。設定を確認してください。"
            )
            return

        if not query:
            await ctx.send(
                "❌ 検索クエリを指定してください。\n使用方法: `/search_notes [キーワード]`"
            )
            return

        # 処理中メッセージを送信
        processing_msg = await ctx.send(f"🔍 '{query}' でセマンティック検索を実行中...")

        try:
            # セマンティック検索を実行
            results = await self.note_analyzer.search_related_notes(
                query=query, limit=10, min_similarity=0.1
            )

            embed = discord.Embed(
                title=f"🔍 セマンティック検索結果: '{query}'",
                description=f"{len(results)}件の関連ノートが見つかりました",
                color=0x2196F3,
            )

            if results:
                # 上位5件を表示
                for i, result in enumerate(results[:5], 1):
                    similarity_percent = result["similarity_score"] * 100
                    preview = result["content_preview"]
                    if len(preview) > 100:
                        preview = preview[:100] + "..."

                    # ファイルパスを簡潔に表示
                    file_path = result["file_path"]
                    if "/" in file_path:
                        display_path = file_path.split("/")[-1]  # ファイル名のみ
                    else:
                        display_path = file_path

                    embed.add_field(
                        name=f"{i}. {result['title']} (類似度: {similarity_percent:.1f}%)",
                        value=(f"📄 `{display_path}`\n📝 {preview}"),
                        inline=False,
                    )

                if len(results) > 5:
                    embed.add_field(
                        name="📋 その他",
                        value=f"他に{len(results) - 5}件の関連ノートがあります。",
                        inline=False,
                    )

                # 検索結果の統計情報
                if results:
                    avg_similarity = sum(r["similarity_score"] for r in results) / len(
                        results
                    )
                    best_match = max(results, key=lambda x: x["similarity_score"])

                    embed.add_field(
                        name="📊 検索統計",
                        value=(
                            f"**平均類似度**: {avg_similarity * 100:.1f}%\n"
                            f"**最高マッチ**: {best_match['similarity_score'] * 100:.1f}%"
                        ),
                        inline=True,
                    )

            else:
                embed.add_field(
                    name="📭 結果なし",
                    value=(
                        "指定されたクエリに関連するノートが見つかりませんでした。\n"
                        "• より一般的なキーワードを試してください\n"
                        "• ベクトルインデックスが構築されているか確認してください"
                    ),
                    inline=False,
                )

            # 元のメッセージを更新
            await processing_msg.edit(content=None, embed=embed)

            self.logger.info(
                "Semantic search command executed",
                user=str(ctx.author),
                query=query,
                results_count=len(results),
            )

        except Exception as e:
            embed = discord.Embed(
                title="❌ セマンティック検索エラー",
                description=f"検索中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "Search notes command failed",
                user=str(ctx.author),
                query=query,
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="rebuild_index")
    async def rebuild_index_command(
        self, ctx: commands.Context, force: str = "false"
    ) -> None:
        """Rebuild vector search index"""
        if not self.note_analyzer:
            await ctx.send("❌ ノート分析システムが利用できません。")
            return

        # force パラメータの解析
        is_force = force.lower() in ["true", "yes", "1", "force"]

        # 処理中メッセージ
        mode_text = "強制再構築" if is_force else "インクリメンタル構築"
        processing_msg = await ctx.send(f"🔄 ベクトルインデックスを{mode_text}中...")

        try:
            # インデックス再構築
            result = await self.note_analyzer.rebuild_vector_index(force=is_force)

            if result["success"]:
                embed = discord.Embed(
                    title="✅ ベクトルインデックス再構築完了", color=0x4CAF50
                )

                stats = result.get("stats", {})
                embed.add_field(
                    name="📊 構築結果",
                    value=(
                        f"**処理時間**: {result['duration_seconds']:.1f}秒\n"
                        f"**総埋め込み数**: {stats.get('total_embeddings', 0):,}\n"
                        f"**最終更新**: {stats.get('last_updated', 'N/A')[:19] if stats.get('last_updated') else 'N/A'}"
                    ),
                    inline=False,
                )

                embed.add_field(
                    name="💡 次のステップ",
                    value="セマンティック検索が利用可能になりました。`/search_notes [キーワード]` で検索してください。",
                    inline=False,
                )
            else:
                embed = discord.Embed(
                    title="❌ インデックス再構築エラー",
                    description=f"エラー: {result.get('error', '不明なエラー')}",
                    color=0xFF0000,
                )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.info(
                "Vector index rebuild command executed",
                user=str(ctx.author),
                force=is_force,
                success=result["success"],
                duration=result.get("duration_seconds", 0),
            )

        except Exception as e:
            embed = discord.Embed(
                title="❌ インデックス再構築失敗",
                description=f"再構築中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "Rebuild index command failed",
                user=str(ctx.author),
                force=is_force,
                error=str(e),
                exc_info=True,
            )


class ObsidianCommands(commands.Cog, LoggerMixin):
    """Obsidian vault management commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        try:
            self.obsidian_manager = ObsidianFileManager()
            self.vault_organizer = VaultOrganizer(self.obsidian_manager)
            self.metadata_manager = MetadataManager(self.obsidian_manager)
            self.logger.info("Obsidian commands initialized")
        except Exception as e:
            self.obsidian_manager = None
            self.vault_organizer = None
            self.metadata_manager = None
            self.logger.error("Failed to initialize Obsidian commands", error=str(e))

    @commands.command(name="vault_stats")
    async def vault_stats_command(self, ctx: commands.Context) -> None:
        """Display Obsidian vault statistics"""
        if not self.obsidian_manager:
            await ctx.send("❌ Obsidian管理システムが利用できません。")
            return

        # 処理中メッセージ
        processing_msg = await ctx.send("📊 Vault統計を収集中...")

        try:
            stats = await self.obsidian_manager.get_vault_stats()

            embed = discord.Embed(title="📊 Obsidian Vault統計", color=0x9C27B0)

            # 基本統計
            embed.add_field(
                name="📁 基本情報",
                value=(
                    f"**総ノート数**: {stats.total_notes:,}\n"
                    f"**Vaultサイズ**: {stats.total_size_bytes / (1024 * 1024):.1f}MB\n"
                    f"**AI処理済み**: {stats.ai_processed_notes:,}\n"
                    f"**平均処理時間**: {stats.average_ai_processing_time:.0f}ms"
                ),
                inline=True,
            )

            # 期間別統計
            embed.add_field(
                name="📅 作成統計",
                value=(
                    f"**今日**: {stats.notes_created_today}\n"
                    f"**今週**: {stats.notes_created_this_week}\n"
                    f"**今月**: {stats.notes_created_this_month}"
                ),
                inline=True,
            )

            # フォルダ別統計
            if stats.notes_by_folder:
                folder_text = "\n".join(
                    [
                        f"**{folder}**: {count}"
                        for folder, count in list(stats.notes_by_folder.items())[:5]
                    ]
                )
                embed.add_field(name="📂 フォルダ別", value=folder_text, inline=True)

            # カテゴリ別統計
            if stats.notes_by_category:
                category_text = "\n".join(
                    [
                        f"**{category}**: {count}"
                        for category, count in list(stats.notes_by_category.items())[:5]
                    ]
                )
                embed.add_field(name="🏷️ カテゴリ別", value=category_text, inline=True)

            # 人気タグ
            if stats.most_common_tags:
                tags_text = "\n".join(
                    [
                        f"**{tag}**: {count}"
                        for tag, count in list(stats.most_common_tags.items())[:5]
                    ]
                )
                embed.add_field(name="🔖 人気タグ", value=tags_text, inline=True)

            embed.set_footer(
                text=f"最終更新: {stats.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.info("Vault stats command executed", user=str(ctx.author))

        except Exception as e:
            embed = discord.Embed(
                title="❌ 統計取得エラー",
                description=f"統計情報の取得に失敗しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "Vault stats command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="vault_organize")
    async def vault_organize_command(
        self, ctx: commands.Context, dry_run: str = "true"
    ) -> None:
        """Organize vault structure"""
        if not self.vault_organizer:
            await ctx.send("❌ Vault組織化システムが利用できません。")
            return

        # dry_runパラメータの解析
        is_dry_run = dry_run.lower() in ["true", "yes", "1", "dry"]

        # 処理中メッセージ
        mode_text = "プレビュー" if is_dry_run else "実行"
        processing_msg = await ctx.send(f"🔄 Vault組織化を{mode_text}中...")

        try:
            results = await self.vault_organizer.optimize_vault_structure(
                dry_run=is_dry_run
            )

            embed = discord.Embed(
                title=f"🔄 Vault組織化結果 ({'プレビュー' if is_dry_run else '実行'})",
                color=0x4CAF50 if not is_dry_run else 0xFF9800,
            )

            # 組織化結果
            organization = results.get("organization", {})
            embed.add_field(
                name="📂 ノート整理",
                value=(
                    f"**処理済み**: {organization.get('processed', 0)}\n"
                    f"**移動済み**: {organization.get('moved', 0)}\n"
                    f"**エラー**: {organization.get('errors', 0)}"
                ),
                inline=True,
            )

            # アーカイブ結果
            archival = results.get("archival", {})
            embed.add_field(
                name="📦 アーカイブ",
                value=(
                    f"**処理済み**: {archival.get('processed', 0)}\n"
                    f"**アーカイブ済み**: {archival.get('archived', 0)}\n"
                    f"**エラー**: {archival.get('errors', 0)}"
                ),
                inline=True,
            )

            # クリーンアップ結果
            cleanup = results.get("cleanup", {})
            embed.add_field(
                name="🧹 クリーンアップ",
                value=(
                    f"**処理済み**: {cleanup.get('processed', 0)}\n"
                    f"**削除済み**: {cleanup.get('removed', 0)}\n"
                    f"**エラー**: {cleanup.get('errors', 0)}"
                ),
                inline=True,
            )

            # 日次ノート
            daily_notes = results.get("daily_notes_created", 0)
            embed.add_field(
                name="📅 日次ノート", value=f"**作成済み**: {daily_notes}", inline=True
            )

            if is_dry_run:
                embed.add_field(
                    name="💡 次のステップ",
                    value="実際に組織化を実行するには `/vault_organize false` を実行してください。",
                    inline=False,
                )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.info(
                "Vault organize command executed",
                user=str(ctx.author),
                dry_run=is_dry_run,
                moved=organization.get("moved", 0),
                archived=archival.get("archived", 0),
            )

        except Exception as e:
            embed = discord.Embed(
                title="❌ 組織化エラー",
                description=f"Vault組織化中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "Vault organize command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="vault_search")
    async def vault_search_command(
        self, ctx: commands.Context, *, query: str | None = None
    ) -> None:
        """Search notes in Obsidian vault"""
        if not self.obsidian_manager:
            await ctx.send("❌ Obsidian管理システムが利用できません。")
            return

        if not query:
            await ctx.send(
                "❌ 検索キーワードを指定してください。\n使用方法: `/vault_search [キーワード]`"
            )
            return

        # 処理中メッセージ
        processing_msg = await ctx.send(f"🔍 '{query}' を検索中...")

        try:
            # ノート検索
            notes = await self.obsidian_manager.search_notes(query=query, limit=10)

            embed = discord.Embed(
                title=f"🔍 検索結果: '{query}'",
                description=f"{len(notes)}件のノートが見つかりました",
                color=0x2196F3,
            )

            if notes:
                for i, note in enumerate(notes[:5], 1):  # 最大5件表示
                    # パスを相対パスに変換
                    relative_path = str(
                        note.file_path.relative_to(self.obsidian_manager.vault_path)
                    )

                    # カテゴリと作成日
                    category = note.frontmatter.ai_category or "未分類"
                    created_date = note.created_at.strftime("%Y-%m-%d")

                    embed.add_field(
                        name=f"{i}. {note.title}",
                        value=(
                            f"**カテゴリ**: {category}\n"
                            f"**作成日**: {created_date}\n"
                            f"**パス**: `{relative_path}`"
                        ),
                        inline=False,
                    )

                if len(notes) > 5:
                    embed.add_field(
                        name="📋 その他",
                        value=f"他に{len(notes) - 5}件のノートがあります。",
                        inline=False,
                    )
            else:
                embed.add_field(
                    name="📭 結果なし",
                    value="指定されたキーワードに一致するノートが見つかりませんでした。",
                    inline=False,
                )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.info(
                "Vault search command executed",
                user=str(ctx.author),
                query=query,
                results_count=len(notes),
            )

        except Exception as e:
            embed = discord.Embed(
                title="❌ 検索エラー",
                description=f"検索中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "Vault search command failed",
                user=str(ctx.author),
                query=query,
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="vault_report")
    async def vault_report_command(self, ctx: commands.Context) -> None:
        """Generate comprehensive vault metadata report"""
        if not self.metadata_manager:
            await ctx.send("❌ メタデータ管理システムが利用できません。")
            return

        # 処理中メッセージ
        processing_msg = await ctx.send("📊 包括的なVaultレポートを生成中...")

        try:
            report = await self.metadata_manager.generate_metadata_report()

            embed = discord.Embed(title="📊 Vault詳細レポート", color=0x673AB7)

            # Vault概要
            overview = report.get("vault_overview", {})
            embed.add_field(
                name="📁 Vault概要",
                value=(
                    f"**総ノート数**: {overview.get('total_notes', 0):,}\n"
                    f"**総サイズ**: {overview.get('total_size_mb', 0):.1f}MB\n"
                    f"**AI処理済み**: {overview.get('ai_processed_notes', 0):,}\n"
                    f"**平均処理時間**: {overview.get('average_ai_processing_time', 0):.0f}ms"
                ),
                inline=True,
            )

            # 作成傾向
            trends = report.get("creation_trends", {})
            embed.add_field(
                name="📈 作成傾向",
                value=(
                    f"**今日**: {trends.get('notes_created_today', 0)}\n"
                    f"**今週**: {trends.get('notes_created_this_week', 0)}\n"
                    f"**今月**: {trends.get('notes_created_this_month', 0)}"
                ),
                inline=True,
            )

            # タグインサイト
            tag_insights = report.get("tag_insights", {})
            embed.add_field(
                name="🏷️ タグ統計",
                value=(
                    f"**総タグ数**: {tag_insights.get('total_tags', 0):,}\n"
                    f"**ユニークタグ**: {tag_insights.get('unique_tags', 0):,}\n"
                    f"**タグカバレッジ**: {tag_insights.get('tag_coverage', 0):.1f}%\n"
                    f"**孤立タグ**: {tag_insights.get('orphaned_tags_count', 0)}"
                ),
                inline=True,
            )

            # レコメンデーション
            recommendations = report.get("recommendations", [])
            if recommendations:
                rec_text = "\n".join(
                    [f"• {rec['message'][:60]}..." for rec in recommendations[:3]]
                )
                embed.add_field(name="💡 推奨事項", value=rec_text, inline=False)

            embed.set_footer(
                text=f"レポート生成: {report.get('generated_at', datetime.now().isoformat())[:19]}"
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.info("Vault report command executed", user=str(ctx.author))

        except Exception as e:
            embed = discord.Embed(
                title="❌ レポート生成エラー",
                description=f"レポート生成中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "Vault report command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )


class DailyNoteCommands(commands.Cog, LoggerMixin):
    """Daily note management commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        try:
            self.obsidian_manager = ObsidianFileManager()
            self.daily_integration = DailyNoteIntegration(self.obsidian_manager)
            self.logger.info("Daily note commands initialized")
        except Exception as e:
            self.obsidian_manager = None
            self.daily_integration = None
            self.logger.error("Failed to initialize daily note commands", error=str(e))

    @commands.command(name="daily_note")
    async def create_daily_note_command(
        self, ctx: commands.Context, date_str: str | None = None
    ) -> None:
        """Create or update daily note for specified date"""
        if not self.daily_integration:
            await ctx.send("❌ デイリーノート機能が利用できません。")
            return

        # 処理中メッセージ
        processing_msg = await ctx.send("📅 デイリーノートを作成中...")

        try:
            # 日付の解析
            target_date = datetime.now()
            if date_str:
                try:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    await processing_msg.edit(
                        content="❌ 日付フォーマットが正しくありません。YYYY-MM-DD形式で入力してください。"
                    )
                    return

            # デイリーノートを作成
            daily_note = await self.daily_integration.create_daily_note_if_not_exists(
                target_date
            )

            if daily_note:
                embed = discord.Embed(title="📅 デイリーノート作成完了", color=0x4CAF50)

                embed.add_field(
                    name="📁 作成されたノート",
                    value=f"**日付**: {target_date.strftime('%Y年%m月%d日')}\n**ファイル名**: {daily_note.filename}",
                    inline=False,
                )

                embed.add_field(
                    name="📊 セクション",
                    value="• 📋 Activity Log\n• ✅ Daily Tasks\n• その他の日次統計情報",
                    inline=False,
                )

                await processing_msg.edit(content=None, embed=embed)

                self.logger.info(
                    "Daily note created via command",
                    user=str(ctx.author),
                    date=target_date.strftime("%Y-%m-%d"),
                )
            else:
                await processing_msg.edit(
                    content="❌ デイリーノートの作成に失敗しました。"
                )

        except Exception as e:
            embed = discord.Embed(
                title="❌ デイリーノート作成エラー",
                description=f"エラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "Daily note creation command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="activity_log")
    async def add_activity_log_command(
        self, ctx: commands.Context, *, activity: str
    ) -> None:
        """Add activity log entry to today's daily note"""
        if not self.daily_integration:
            await ctx.send("❌ デイリーノート機能が利用できません。")
            return

        try:
            # メッセージデータを構築
            message_data = {
                "metadata": {
                    "content": {"raw_content": activity.strip()},
                    "timing": {"created_at": {"iso": datetime.now().isoformat()}},
                }
            }

            # Activity logエントリを追加
            success = await self.daily_integration.add_activity_log_entry(message_data)

            if success:
                embed = discord.Embed(
                    title="📋 Activity Log追加完了",
                    description="アクティビティが今日のデイリーノートに追加されました。",
                    color=0x4CAF50,
                )

                embed.add_field(
                    name="📝 追加された内容", value=f"```{activity}```", inline=False
                )

                await ctx.send(embed=embed)

                self.logger.info(
                    "Activity log entry added via command",
                    user=str(ctx.author),
                    activity_length=len(activity),
                )
            else:
                await ctx.send("❌ Activity logの追加に失敗しました。")

        except Exception as e:
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

            self.logger.error(
                "Activity log command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="daily_task")
    async def add_daily_task_command(self, ctx: commands.Context, *, task: str) -> None:
        """Add task to today's daily note"""
        if not self.daily_integration:
            await ctx.send("❌ デイリーノート機能が利用できません。")
            return

        try:
            # メッセージデータを構築
            message_data = {
                "metadata": {
                    "content": {"raw_content": task.strip()},
                    "timing": {"created_at": {"iso": datetime.now().isoformat()}},
                }
            }

            # Daily taskエントリを追加
            success = await self.daily_integration.add_daily_task_entry(message_data)

            if success:
                embed = discord.Embed(
                    title="✅ Daily Task追加完了",
                    description="タスクが今日のデイリーノートに追加されました。",
                    color=0x4CAF50,
                )

                embed.add_field(
                    name="📋 追加されたタスク", value=f"```{task}```", inline=False
                )

                await ctx.send(embed=embed)

                self.logger.info(
                    "Daily task entry added via command",
                    user=str(ctx.author),
                    task_length=len(task),
                )
            else:
                await ctx.send("❌ Daily taskの追加に失敗しました。")

        except Exception as e:
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

            self.logger.error(
                "Daily task command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )


class SystemCommands(commands.Cog, LoggerMixin):
    """System management commands"""

    def __init__(self, bot: commands.Bot, channel_config: ChannelConfig) -> None:
        self.bot = bot
        self.channel_config = channel_config
        self.logger.info("System commands initialized")

    @commands.command(name="config")
    async def config_command(
        self,
        ctx: commands.Context,
        category: str | None = None,
        key: str | None = None,
        *,
        value: str | None = None,
    ) -> None:
        """Manage system configuration"""
        # Get config manager from bot instance
        config_manager = getattr(ctx.bot, "_cogs", {}).get("DiscordBot", {})
        if hasattr(ctx.bot, "_parent") and hasattr(ctx.bot._parent, "config_manager"):
            config_manager = ctx.bot._parent.config_manager
        else:
            await ctx.send("❌ 設定管理システムが利用できません。")
            return

        if not category:
            # 設定カテゴリ一覧表示
            embed = discord.Embed(title="⚙️ 設定管理", color=0x607D8B)
            embed.add_field(
                name="📂 利用可能なカテゴリ",
                value=(
                    "• `channels` - チャンネル設定\n"
                    "• `ai_processing` - AI処理設定\n"
                    "• `notifications` - 通知設定\n"
                    "• `reminders` - リマインダー設定\n"
                    "• `file_management` - ファイル管理設定\n"
                    "• `security` - セキュリティ設定"
                ),
                inline=False,
            )
            embed.add_field(
                name="💡 使用方法",
                value="`/config [category] [key] [value]` - 設定値を変更",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        if not key:
            # カテゴリ内の設定一覧表示
            config_manager.get_config_summary()
            embed = discord.Embed(
                title=f"⚙️ 設定カテゴリ: {category}",
                description="カテゴリ内の設定項目を表示します。",
                color=0x607D8B,
            )
            await ctx.send(embed=embed)
            return

        if value is None:
            # 現在の設定値を取得
            from .config_manager import ConfigCategory

            try:
                cat_enum = ConfigCategory(category)
                current_value = await config_manager.get_config(
                    cat_enum, key, str(ctx.author.id)
                )
                embed = discord.Embed(
                    title=f"⚙️ 設定値: {category}.{key}",
                    description=f"現在の値: `{current_value}`",
                    color=0x607D8B,
                )
                await ctx.send(embed=embed)
            except ValueError:
                await ctx.send(f"❌ 無効なカテゴリ: {category}")
            return

        # 設定値を更新
        try:
            from .config_manager import ConfigCategory, ConfigLevel

            cat_enum = ConfigCategory(category)

            # 値の型変換
            parsed_value = value
            if value.lower() in ["true", "false"]:
                parsed_value = value.lower() == "true"
            elif value.isdigit():
                parsed_value = int(value)
            elif "." in value and value.replace(".", "").isdigit():
                parsed_value = float(value)

            success = await config_manager.set_config(
                cat_enum,
                key,
                parsed_value,
                str(ctx.author.id),
                ConfigLevel.USER,
                str(ctx.author),
            )

            if success:
                embed = discord.Embed(
                    title="✅ 設定更新完了",
                    description=f"`{category}.{key}` を `{parsed_value}` に更新しました。",
                    color=0x4CAF50,
                )
            else:
                embed = discord.Embed(
                    title="❌ 設定更新失敗",
                    description="設定の更新に失敗しました。",
                    color=0xFF0000,
                )

            await ctx.send(embed=embed)

        except ValueError:
            await ctx.send(f"❌ 無効なカテゴリ: {category}")
        except Exception as e:
            await ctx.send(f"❌ 設定更新エラー: {str(e)}")

    @commands.command(name="backup")
    async def backup_command(
        self, ctx: commands.Context, backup_type: str = "full"
    ) -> None:
        """Execute system backup"""
        # Get backup system from bot instance
        backup_system = getattr(ctx.bot, "_parent", {})
        if hasattr(backup_system, "backup_system"):
            backup_system = backup_system.backup_system
        else:
            await ctx.send("❌ バックアップシステムが利用できません。")
            return

        processing_msg = await ctx.send(f"💾 {backup_type} バックアップを実行中...")

        try:
            from .backup_system import BackupType

            # バックアップタイプの変換
            backup_type_enum = BackupType.FULL
            if backup_type.lower() == "incremental":
                backup_type_enum = BackupType.INCREMENTAL
            elif backup_type.lower() == "obsidian":
                backup_type_enum = BackupType.OBSIDIAN_ONLY
            elif backup_type.lower() == "config":
                backup_type_enum = BackupType.CONFIG_ONLY

            result = await backup_system.run_backup(backup_type_enum)

            if result.get("status") == "success":
                embed = discord.Embed(title="✅ バックアップ完了", color=0x4CAF50)
                embed.add_field(
                    name="📊 結果",
                    value=(
                        f"**ファイル数**: {result.get('files_backed_up', 0)}\n"
                        f"**サイズ**: {result.get('total_size_mb', 0)}MB\n"
                        f"**所要時間**: {result.get('duration_seconds', 0):.1f}秒"
                    ),
                    inline=False,
                )
            else:
                embed = discord.Embed(
                    title="⚠️ バックアップ完了（エラー有）", color=0xFF9800
                )
                if result.get("errors"):
                    embed.add_field(
                        name="エラー",
                        value="\n".join(result["errors"][:3]),
                        inline=False,
                    )

            await processing_msg.edit(content=None, embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ バックアップエラー",
                description=f"バックアップ中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )
            await processing_msg.edit(content=None, embed=embed)

    @commands.command(name="review")
    async def review_command(
        self, ctx: commands.Context, review_type: str = "weekly"
    ) -> None:
        """Execute system review"""
        # Get review system from bot instance
        review_system = getattr(ctx.bot, "_parent", {})
        if hasattr(review_system, "review_system"):
            review_system = review_system.review_system
        else:
            await ctx.send("❌ レビューシステムが利用できません。")
            return

        processing_msg = await ctx.send(f"📊 {review_type} レビューを実行中...")

        try:
            if review_type.lower() == "weekly":
                result = await review_system.run_weekly_unorganized_review()
            elif review_type.lower() == "monthly":
                result = await review_system.run_monthly_summary()
            elif review_type.lower() == "longterm":
                result = await review_system.run_long_term_notes_check()
            else:
                await processing_msg.edit(
                    content="❌ 無効なレビュータイプ: weekly, monthly, longterm"
                )
                return

            if result.get("status") == "completed":
                embed = discord.Embed(title="📊 レビュー完了", color=0x4CAF50)

                if "unorganized_count" in result:
                    embed.add_field(
                        name="📝 未整理メモ",
                        value=f"{result['unorganized_count']}件",
                        inline=True,
                    )
                if "notes_count" in result:
                    embed.add_field(
                        name="📋 分析対象",
                        value=f"{result['notes_count']}件",
                        inline=True,
                    )

            else:
                embed = discord.Embed(title="ℹ️ レビュー結果", color=0x5865F2)
                embed.add_field(
                    name="状態", value=result.get("status", "不明"), inline=False
                )

            await processing_msg.edit(content=None, embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ レビューエラー",
                description=f"レビュー中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )
            await processing_msg.edit(content=None, embed=embed)

    @commands.command(name="system_health")
    async def system_health_command(self, ctx: commands.Context) -> None:
        """Check system health status"""
        # Get notification system from bot instance
        notification_system = getattr(ctx.bot, "_parent", {})
        if hasattr(notification_system, "notification_system"):
            notification_system = notification_system.notification_system
        else:
            await ctx.send("❌ システムヘルス機能が利用できません。")
            return

        processing_msg = await ctx.send("🔍 システム健康状態を確認中...")

        try:
            health_status = await notification_system.get_system_health_status()

            embed = discord.Embed(title="🔍 システム健康状態", color=0x4CAF50)

            embed.add_field(
                name="🌐 Discord接続",
                value=health_status.get("discord_status", "不明"),
                inline=True,
            )

            embed.add_field(
                name="⏱️ システム稼働時間",
                value=health_status.get("system_uptime", "不明"),
                inline=True,
            )

            embed.add_field(
                name="📊 最近の統計 (1時間)",
                value=(
                    f"エラー: {health_status.get('recent_errors', 0)}件\n"
                    f"警告: {health_status.get('recent_warnings', 0)}件"
                ),
                inline=True,
            )

            embed.add_field(
                name="📝 総通知数",
                value=f"{health_status.get('total_notifications', 0)}件",
                inline=True,
            )

            # 健康状態に応じて色を変更
            if health_status.get("recent_errors", 0) > 10:
                embed.color = 0xFF0000  # Red
            elif (
                health_status.get("recent_errors", 0) > 0
                or health_status.get("recent_warnings", 0) > 5
            ):
                embed.color = 0xFF9800  # Orange

            await processing_msg.edit(content=None, embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ ヘルスチェックエラー",
                description=f"システム健康状態の確認中にエラーが発生しました: {str(e)}",
                color=0xFF0000,
            )
            await processing_msg.edit(content=None, embed=embed)


class TemplateCommands(commands.Cog, LoggerMixin):
    """Template system management commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        try:
            self.obsidian_manager = ObsidianFileManager()
            self.template_engine = TemplateEngine(self.obsidian_manager.vault_path)
            self.logger.info("Template commands initialized")
        except Exception as e:
            self.obsidian_manager = None
            self.template_engine = None
            self.logger.error("Failed to initialize template commands", error=str(e))

    @commands.command(name="list_templates")
    async def list_templates_command(self, ctx: commands.Context) -> None:
        """List available templates"""
        if not self.template_engine:
            await ctx.send("❌ テンプレートシステムが利用できません。")
            return

        try:
            templates = await self.template_engine.list_available_templates()

            if not templates:
                await ctx.send("📝 利用可能なテンプレートがありません。")
                return

            embed = discord.Embed(title="📋 利用可能なテンプレート", color=0x4CAF50)

            template_list = "\n".join(f"• `{template}`" for template in templates)
            embed.add_field(
                name="🔧 テンプレート一覧", value=template_list, inline=False
            )

            embed.add_field(
                name="💡 使用方法",
                value="`/create_from_template [template_name] [content]` - テンプレートからノート作成",
                inline=False,
            )

            await ctx.send(embed=embed)

            self.logger.info(
                "Template list command executed",
                user=str(ctx.author),
                template_count=len(templates),
            )

        except Exception as e:
            await ctx.send(f"❌ エラーが発生しました: {str(e)}")

            self.logger.error(
                "List templates command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="create_from_template")
    async def create_from_template_command(
        self,
        ctx: commands.Context,
        template_name: str,
        *,
        content: str | None = None,
    ) -> None:
        """Create note from template"""
        if not self.template_engine:
            await ctx.send("❌ テンプレートシステムが利用できません。")
            return

        # 処理中メッセージ
        processing_msg = await ctx.send(
            f"📝 `{template_name}` テンプレートからノートを作成中..."
        )

        try:
            # 利用可能なテンプレートの確認
            available_templates = await self.template_engine.list_available_templates()
            if template_name not in available_templates:
                await processing_msg.edit(
                    content=f"❌ テンプレート `{template_name}` が見つかりません。\n"
                    f"利用可能なテンプレート: {', '.join(available_templates)}"
                )
                return

            # メッセージデータを構築
            message_data = {
                "metadata": {
                    "basic": {
                        "id": ctx.message.id,
                        "author": {
                            "display_name": ctx.author.display_name,
                            "username": ctx.author.name,
                        },
                        "channel": {
                            "id": ctx.channel.id,
                            "name": (
                                ctx.channel.name
                                if hasattr(ctx.channel, "name")
                                else "DM"
                            ),
                        },
                    },
                    "content": {"raw_content": content or ""},
                    "timing": {"created_at": {"iso": datetime.now().isoformat()}},
                    "attachments": [],
                }
            }

            # テンプレートからノートを生成
            note = await self.template_engine.generate_note_from_template(
                template_name, message_data
            )

            if note:
                # ノートを保存
                success = await self.obsidian_manager.save_note(note)

                if success:
                    embed = discord.Embed(
                        title="📝 テンプレートからノート作成完了", color=0x4CAF50
                    )

                    embed.add_field(
                        name="🔧 使用テンプレート",
                        value=f"`{template_name}`",
                        inline=True,
                    )

                    embed.add_field(
                        name="📁 作成されたノート",
                        value=f"`{note.filename}`",
                        inline=True,
                    )

                    if content:
                        embed.add_field(
                            name="📝 入力内容",
                            value=f"```{content[:200]}{'...' if len(content) > 200 else ''}```",
                            inline=False,
                        )

                    await processing_msg.edit(content=None, embed=embed)

                    self.logger.info(
                        "Note created from template via command",
                        user=str(ctx.author),
                        template=template_name,
                        filename=note.filename,
                    )
                else:
                    await processing_msg.edit(content="❌ ノートの保存に失敗しました。")
            else:
                await processing_msg.edit(
                    content="❌ テンプレートからのノート作成に失敗しました。"
                )

        except Exception as e:
            embed = discord.Embed(
                title="❌ テンプレート処理エラー",
                description=f"エラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "Create from template command failed",
                user=str(ctx.author),
                template=template_name,
                error=str(e),
                exc_info=True,
            )

    @commands.command(name="create_default_templates")
    async def create_default_templates_command(self, ctx: commands.Context) -> None:
        """Create default templates"""
        if not self.template_engine:
            await ctx.send("❌ テンプレートシステムが利用できません。")
            return

        # 処理中メッセージ
        processing_msg = await ctx.send("🔧 デフォルトテンプレートを作成中...")

        try:
            success = await self.template_engine.create_default_templates()

            if success:
                available_templates = (
                    await self.template_engine.list_available_templates()
                )

                embed = discord.Embed(
                    title="✅ デフォルトテンプレート作成完了", color=0x4CAF50
                )

                embed.add_field(
                    name="📋 作成されたテンプレート",
                    value="\n".join(
                        f"• `{template}`" for template in available_templates
                    ),
                    inline=False,
                )

                embed.add_field(
                    name="📁 保存場所",
                    value="`99_Meta/Templates/` フォルダ",
                    inline=False,
                )

                embed.add_field(
                    name="💡 使用方法",
                    value="`/create_from_template [template_name]` でテンプレートを使用",
                    inline=False,
                )

                await processing_msg.edit(content=None, embed=embed)

                self.logger.info(
                    "Default templates created via command",
                    user=str(ctx.author),
                    template_count=len(available_templates),
                )
            else:
                await processing_msg.edit(
                    content="❌ デフォルトテンプレートの作成に失敗しました。"
                )

        except Exception as e:
            embed = discord.Embed(
                title="❌ テンプレート作成エラー",
                description=f"エラーが発生しました: {str(e)}",
                color=0xFF0000,
            )

            await processing_msg.edit(content=None, embed=embed)

            self.logger.error(
                "Create default templates command failed",
                user=str(ctx.author),
                error=str(e),
                exc_info=True,
            )


async def setup_commands(bot: commands.Bot, channel_config: ChannelConfig) -> None:
    """Setup bot commands"""
    await bot.add_cog(BasicCommands(bot, channel_config))
    await bot.add_cog(AICommands(bot))
    await bot.add_cog(ObsidianCommands(bot))
    await bot.add_cog(DailyNoteCommands(bot))
    await bot.add_cog(TemplateCommands(bot))
    await bot.add_cog(SystemCommands(bot, channel_config))
