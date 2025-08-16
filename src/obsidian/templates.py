"""
Obsidian note templates
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from ..ai.models import AIProcessingResult
from ..utils.mixins import LoggerMixin
from .models import (
    FolderMapping,
    NoteFilename,
    NoteFrontmatter,
    NoteStatus,
    ObsidianNote,
    VaultFolder,
)


class NoteTemplate(ABC, LoggerMixin):
    """ノートテンプレートの基底クラス"""

    @abstractmethod
    def generate_note(self, *args: Any, **kwargs: Any) -> ObsidianNote:
        """ノートを生成する抽象メソッド"""

    @abstractmethod
    def generate_frontmatter(self, *args: Any, **kwargs: Any) -> NoteFrontmatter:
        """フロントマターを生成する抽象メソッド"""

    @abstractmethod
    def generate_content(self, *args: Any, **kwargs: Any) -> str:
        """コンテンツを生成する抽象メソッド"""


class MessageNoteTemplate(NoteTemplate):
    """Discordメッセージ用ノートテンプレート"""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.logger.info("Message note template initialized")

    def generate_note(
        self,
        message_data: dict[str, Any],
        ai_result: AIProcessingResult | None = None,
        vault_folder: VaultFolder | None = None,
    ) -> ObsidianNote:
        """
        Discordメッセージからノートを生成

        Args:
            message_data: メッセージメタデータ
            ai_result: AI処理結果
            vault_folder: 保存先フォルダ（指定されない場合は自動決定）

        Returns:
            生成されたObsidianNote
        """

        # メッセージ情報の抽出
        metadata = message_data.get("metadata", {})
        metadata.get("basic", {})
        content_info = metadata.get("content", {})
        timing_info = metadata.get("timing", {})
        message_data.get("channel_info", {})

        # AI処理結果の抽出
        ai_summary = None
        ai_category = None

        if ai_result:
            if ai_result.summary:
                ai_summary = ai_result.summary.summary
            if ai_result.tags:
                pass
            if ai_result.category:
                ai_category = ai_result.category.category.value

        # タイムスタンプの処理
        created_at = datetime.fromisoformat(
            timing_info.get("created_at", {}).get("iso", datetime.now().isoformat())
        )

        # フォルダの決定
        if not vault_folder:
            if ai_result and ai_result.category:
                vault_folder = FolderMapping.get_folder_for_category(
                    ai_result.category.category.value
                )
            else:
                # デフォルトで受信箱に送る
                vault_folder = VaultFolder.INBOX

        # ファイル名の生成
        title = self._extract_title_from_content(
            content_info.get("raw_content", ""), ai_summary
        )
        filename = NoteFilename.generate_message_note_filename(
            timestamp=created_at, category=ai_category, title=title
        )

        # ファイルパス
        file_path = self.vault_path / vault_folder.value / filename

        # フロントマターの生成
        frontmatter = self.generate_frontmatter(
            message_data=message_data,
            ai_result=ai_result,
            vault_folder=vault_folder,
            created_at=created_at,
        )

        # コンテンツの生成
        content = self.generate_content(message_data=message_data, ai_result=ai_result)

        return ObsidianNote(
            filename=filename,
            file_path=file_path,
            frontmatter=frontmatter,
            content=content,
            created_at=created_at,
            modified_at=datetime.now(),
        )

    def generate_frontmatter(
        self,
        message_data: dict[str, Any],
        ai_result: AIProcessingResult | None = None,
        vault_folder: VaultFolder = VaultFolder.INBOX,
        created_at: datetime | None = None,
    ) -> NoteFrontmatter:
        """フロントマターを生成"""

        metadata = message_data.get("metadata", {})
        basic_info = metadata.get("basic", {})
        metadata.get("content", {})
        timing_info = metadata.get("timing", {})
        channel_info = message_data.get("channel_info", {})
        author_info = basic_info.get("author", {})
        discord_channel = basic_info.get("channel", {})
        guild_info = basic_info.get("guild", {})

        if not created_at:
            created_at = datetime.now()

        # AI処理結果の抽出
        ai_processed = ai_result is not None
        ai_processing_time = ai_result.total_processing_time_ms if ai_result else None
        ai_summary = (
            ai_result.summary.summary if ai_result and ai_result.summary else None
        )
        ai_tags = ai_result.tags.tags if ai_result and ai_result.tags else []
        ai_category = (
            ai_result.category.category.value
            if ai_result and ai_result.category
            else None
        )
        ai_confidence = (
            ai_result.category.confidence_score
            if ai_result and ai_result.category
            else None
        )

        # タグの生成
        tags = ["discord", "auto-generated"]
        if ai_category:
            tags.append(ai_category.lower())
        if channel_info.get("category"):
            tags.append(channel_info["category"].lower())

        return NoteFrontmatter(
            # Discord情報
            discord_message_id=basic_info.get("id"),
            discord_channel=discord_channel.get("name"),
            discord_channel_id=discord_channel.get("id"),
            discord_author=(
                f"{author_info.get('name')}#{author_info.get('discriminator')}"
                if author_info.get("discriminator") != "0"
                else author_info.get("name")
            ),
            discord_author_id=author_info.get("id"),
            discord_timestamp=timing_info.get("created_at", {}).get("iso"),
            discord_guild=guild_info.get("name") if guild_info else None,
            # AI処理結果
            ai_processed=ai_processed,
            ai_processing_time=ai_processing_time,
            ai_summary=ai_summary,
            ai_tags=ai_tags,
            ai_category=ai_category,
            ai_confidence=ai_confidence,
            # Obsidian管理情報
            created=created_at.isoformat(),
            modified=datetime.now().isoformat(),
            status=NoteStatus.ACTIVE,
            obsidian_folder=vault_folder.value,
            source_type="discord_message",
            # メタデータ
            tags=tags,
            aliases=[],
            cssclass="discord-note",
        )

    def generate_content(
        self,
        message_data: dict[str, Any],
        ai_result: AIProcessingResult | None = None,
    ) -> str:
        """Markdownコンテンツを生成"""

        metadata = message_data.get("metadata", {})
        basic_info = metadata.get("basic", {})
        content_info = metadata.get("content", {})
        timing_info = metadata.get("timing", {})
        attachments = metadata.get("attachments", [])
        author_info = basic_info.get("author", {})
        discord_channel = basic_info.get("channel", {})

        # タイトルの生成
        title = self._extract_title_from_content(
            content_info.get("raw_content", ""),
            ai_result.summary.summary if ai_result and ai_result.summary else None,
        )

        content_parts = [f"# {title}", ""]

        # AI要約セクション
        if ai_result and ai_result.summary:
            content_parts.extend(["## 📝 要約", ai_result.summary.summary, ""])

            # キーポイントがある場合
            if ai_result.summary.key_points:
                content_parts.extend(["### 主要ポイント", ""])
                for point in ai_result.summary.key_points:
                    content_parts.append(f"- {point}")
                content_parts.append("")

        # 元メッセージセクション
        raw_content = content_info.get("raw_content", "")
        if raw_content:
            content_parts.extend(["## 💬 元メッセージ", "```", raw_content, "```", ""])

        # タグセクション
        if ai_result and ai_result.tags and ai_result.tags.tags:
            content_parts.extend(["## 🏷️ タグ", " ".join(ai_result.tags.tags), ""])

        # 分類セクション
        if ai_result and ai_result.category:
            content_parts.extend(
                [
                    "## 📂 分類",
                    f"- **カテゴリ**: {ai_result.category.category.value}",
                    f"- **信頼度**: {ai_result.category.confidence_score:.2f}",
                    "",
                ]
            )

            if ai_result.category.reasoning:
                content_parts.extend(
                    [f"- **根拠**: {ai_result.category.reasoning}", ""]
                )

        # 添付ファイルセクション
        if attachments:
            content_parts.extend(["## 📎 添付ファイル", ""])

            for attachment in attachments:
                filename = attachment.get("filename", "Unknown")
                size = attachment.get("size", 0)
                file_type = attachment.get("file_category", "other")

                size_str = self._format_file_size(size)
                content_parts.append(f"- **{filename}** ({size_str}, {file_type})")

            content_parts.append("")

        # リンクセクション
        message_id = basic_info.get("id")
        channel_id = discord_channel.get("id")
        guild_id = (
            basic_info.get("guild", {}).get("id") if basic_info.get("guild") else None
        )

        content_parts.extend(["## 🔗 関連リンク", ""])

        if message_id and channel_id and guild_id:
            discord_link = (
                f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
            )
            content_parts.append(f"- [Discord Message]({discord_link})")

        if discord_channel.get("name"):
            content_parts.append(f"- **チャンネル**: #{discord_channel['name']}")

        content_parts.append("")

        # メタデータセクション
        created_time = timing_info.get("created_at", {}).get("iso", "")
        if created_time:
            created_dt = datetime.fromisoformat(created_time.replace("Z", "+00:00"))
            formatted_time = created_dt.strftime("%Y年%m月%d日 %H:%M:%S")
        else:
            formatted_time = "不明"

        processing_time = ai_result.total_processing_time_ms if ai_result else None

        content_parts.extend(
            [
                "## 📊 メタデータ",
                f"- **作成者**: {author_info.get('name', 'Unknown')}",
                f"- **作成日時**: {formatted_time}",
            ]
        )

        if processing_time:
            content_parts.append(f"- **AI処理時間**: {processing_time}ms")

        content_parts.extend(
            [
                "",
                "---",
                "*このノートはDiscord-Obsidian Memo Botによって自動生成されました*",
            ]
        )

        return "\n".join(content_parts)

    def _extract_title_from_content(
        self, content: str, ai_summary: str | None = None
    ) -> str:
        """コンテンツからタイトルを抽出"""

        # AI要約がある場合はそれを基にタイトル生成
        if ai_summary:
            # 要約の最初の行をタイトルとして使用
            first_line = ai_summary.split("\n")[0].strip()
            if first_line:
                # 不要な記号を除去
                title = first_line.lstrip("・-*").strip()
                if len(title) > 5:  # 十分な長さがある場合
                    return title[:50]  # 最大50文字

        # コンテンツから抽出
        if content:
            # 改行や余分な空白を除去
            clean_content = content.strip()
            if clean_content:
                # 最初の行または最初の50文字を使用
                first_line = clean_content.split("\n")[0].strip()
                if first_line:
                    return first_line[:50]

        # デフォルトタイトル
        return "Discord Memo"

    def _format_file_size(self, size_bytes: int) -> str:
        """ファイルサイズをフォーマット"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"


class DailyNoteTemplate(NoteTemplate):
    """日次ノート用テンプレート"""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.logger.info("Daily note template initialized")

    def generate_note(
        self, date: datetime, daily_stats: dict[str, Any] | None = None
    ) -> ObsidianNote:
        """
        日次ノートを生成

        Args:
            date: 対象日
            daily_stats: 日次統計情報

        Returns:
            生成されたObsidianNote
        """

        # ファイル名とパス
        filename = NoteFilename.generate_daily_note_filename(date)
        year = date.strftime("%Y")
        month = date.strftime("%m-%B")
        file_path = (
            self.vault_path / VaultFolder.DAILY_NOTES.value / year / month / filename
        )

        # フロントマターとコンテンツの生成
        frontmatter = self.generate_frontmatter(date=date, daily_stats=daily_stats)
        content = self.generate_content(date=date, daily_stats=daily_stats)

        return ObsidianNote(
            filename=filename,
            file_path=file_path,
            frontmatter=frontmatter,
            content=content,
            created_at=date,
            modified_at=datetime.now(),
        )

    def generate_frontmatter(
        self, date: datetime, daily_stats: dict[str, Any] | None = None
    ) -> NoteFrontmatter:
        """日次ノートのフロントマターを生成"""

        stats = daily_stats or {}

        return NoteFrontmatter(
            # 基本情報
            created=date.isoformat(),
            modified=datetime.now().isoformat(),
            status=NoteStatus.ACTIVE,
            obsidian_folder=VaultFolder.DAILY_NOTES.value,
            source_type="daily_note",
            # 統計情報
            total_messages=stats.get("total_messages", 0),
            processed_messages=stats.get("processed_messages", 0),
            ai_processing_time_total=stats.get("ai_processing_time_total", 0),
            categories=stats.get("categories", {}),
            # メタデータ
            tags=["daily", "auto-generated"],
            aliases=[],
            cssclass="daily-note",
        )

    def generate_content(
        self, date: datetime, daily_stats: dict[str, Any] | None = None
    ) -> str:
        """日次ノートのコンテンツを生成"""

        stats = daily_stats or {}
        date_str = date.strftime("%Y年%m月%d日")

        content_parts = [f"# Daily Note - {date_str}", ""]

        # 統計情報セクション
        total_messages = stats.get("total_messages", 0)
        processed_messages = stats.get("processed_messages", 0)
        ai_time_total = stats.get("ai_processing_time_total", 0)

        content_parts.extend(
            [
                "## 📊 今日の統計",
                f"- **総メッセージ数**: {total_messages}",
                f"- **AI処理済み**: {processed_messages}",
                f"- **処理時間合計**: {ai_time_total:,}ms",
                "",
            ]
        )

        # カテゴリ別統計
        categories = stats.get("categories", {})
        if categories:
            content_parts.extend(["## 📝 カテゴリ別統計", ""])

            category_names = {
                "work": "仕事",
                "learning": "学習",
                "life": "生活",
                "ideas": "アイデア",
                "projects": "プロジェクト",
                "other": "その他",
            }

            for category, count in categories.items():
                category_jp = category_names.get(category, category)
                content_parts.append(f"- **{category_jp}**: {count}件")

            content_parts.append("")

        # 今日のメモセクション
        content_parts.extend(["## 📝 今日のメモ", ""])

        # カテゴリ別にセクションを作成
        for category, count in categories.items():
            if count > 0:
                category_names = {
                    "work": "仕事",
                    "learning": "学習",
                    "life": "生活",
                    "ideas": "アイデア",
                    "projects": "プロジェクト",
                    "other": "その他",
                }
                category_jp = category_names.get(category, category)
                content_parts.extend(
                    [
                        f"### {category_jp} ({count}件)",
                        f"- *{category_jp}関連のメモがここに表示されます*",
                        "",
                    ]
                )

        # タグセクション
        tags = stats.get("tags", [])
        if tags:
            content_parts.extend(["## 🏷️ 今日のタグ", ""])

            # タグを頻度順にソート
            if isinstance(tags, list):
                tag_str = " ".join(tags[:20])  # 最大20個
            else:
                # tags が辞書の場合（タグ: 回数）
                sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[
                    :20
                ]
                tag_str = " ".join([f"{tag}({count})" for tag, count in sorted_tags])

            content_parts.extend([tag_str, ""])

        # 添付ファイルセクション
        attachments = stats.get("attachments", [])
        if attachments:
            content_parts.extend(["## 📎 今日の添付ファイル", ""])

            for attachment in attachments[:10]:  # 最大10個
                content_parts.append(f"- {attachment}")

            content_parts.append("")

        # フッター
        content_parts.extend(["---", "*このノートは毎日自動更新されます*"])

        return "\n".join(content_parts)
