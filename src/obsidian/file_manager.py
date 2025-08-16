"""
Obsidian vault file management system
"""

import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
import yaml

from ..config.settings import get_settings
from ..utils.mixins import LoggerMixin
from .models import (
    FileOperation,
    NoteStatus,
    ObsidianNote,
    OperationType,
    VaultFolder,
    VaultStats,
)


class ObsidianFileManager(LoggerMixin):
    """Obsidian vault file management system"""

    def __init__(self, vault_path: Path | None = None):
        """
        Initialize Obsidian file manager

        Args:
            vault_path: Path to Obsidian vault (defaults to settings)
        """
        settings = get_settings()
        self.vault_path = vault_path or settings.obsidian_vault_path

        # 操作履歴
        self.operation_history: list[FileOperation] = []

        # キャッシュ
        self._folder_cache: set[Path] = set()
        self._stats_cache: VaultStats | None = None
        self._stats_cache_time: datetime | None = None

        self.logger.info(
            "Obsidian file manager initialized", vault_path=str(self.vault_path)
        )

    async def initialize_vault(self) -> bool:
        """
        Vault構造を初期化

        Returns:
            初期化成功可否
        """
        try:
            # Vaultディレクトリの作成
            self.vault_path.mkdir(parents=True, exist_ok=True)

            # 必要なフォルダ構造を作成
            await self._ensure_vault_structure()

            # テンプレートファイルの作成
            await self._create_template_files()

            self.logger.info("Vault structure initialized successfully")
            return True

        except Exception as e:
            self.logger.error(
                "Failed to initialize vault structure", error=str(e), exc_info=True
            )
            return False

    async def save_note(self, note: ObsidianNote, overwrite: bool = False) -> bool:
        """
        ノートをファイルとして保存

        Args:
            note: 保存するノート
            overwrite: 既存ファイルの上書き許可

        Returns:
            保存成功可否
        """
        try:
            # ディレクトリの確保
            note.file_path.parent.mkdir(parents=True, exist_ok=True)

            # ファイル存在チェック
            if note.file_path.exists() and not overwrite:
                self.logger.warning(
                    "File already exists",
                    file_path=str(note.file_path),
                    overwrite=overwrite,
                )
                return False

            # Markdownコンテンツの生成
            markdown_content = note.to_markdown()

            # ファイル保存
            async with aiofiles.open(note.file_path, "w", encoding="utf-8") as f:
                await f.write(markdown_content)

            # 操作記録
            operation = FileOperation(
                operation_type=OperationType.CREATE,
                file_path=note.file_path,
                success=True,
                metadata={
                    "note_title": note.title,
                    "category": note.category_from_filename,
                    "size_bytes": len(markdown_content.encode("utf-8")),
                },
            )
            self.operation_history.append(operation)

            # キャッシュの無効化
            self._invalidate_stats_cache()

            self.logger.info(
                "Note saved successfully",
                file_path=str(note.file_path),
                title=note.title,
                size_bytes=len(markdown_content.encode("utf-8")),
            )

            return True

        except Exception as e:
            # エラー記録
            operation = FileOperation(
                operation_type=OperationType.CREATE,
                file_path=note.file_path,
                success=False,
                error_message=str(e),
            )
            self.operation_history.append(operation)

            self.logger.error(
                "Failed to save note",
                file_path=str(note.file_path),
                error=str(e),
                exc_info=True,
            )

            return False

    async def load_note(self, file_path: Path) -> ObsidianNote | None:
        """
        ファイルからノートを読み込み

        Args:
            file_path: ファイルパス

        Returns:
            読み込まれたノート（失敗時はNone）
        """
        try:
            if not file_path.exists() or not file_path.is_file():
                self.logger.warning("File not found", file_path=str(file_path))
                return None

            # ファイル読み込み
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()

            # フロントマターとコンテンツの分離
            frontmatter_data, markdown_content = self._parse_markdown_file(content)

            # ファイル情報の取得
            stat = file_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime)
            modified_at = datetime.fromtimestamp(stat.st_mtime)

            # NoteFrontmatterオブジェクトの作成
            from .models import NoteFrontmatter

            frontmatter = NoteFrontmatter(**frontmatter_data)

            note = ObsidianNote(
                filename=file_path.name,
                file_path=file_path,
                frontmatter=frontmatter,
                content=markdown_content,
                created_at=created_at,
                modified_at=modified_at,
            )

            self.logger.debug("Note loaded successfully", file_path=str(file_path))
            return note

        except Exception as e:
            self.logger.error(
                "Failed to load note",
                file_path=str(file_path),
                error=str(e),
                exc_info=True,
            )
            return None

    async def update_note(self, note: ObsidianNote) -> bool:
        """
        既存ノートを更新

        Args:
            note: 更新するノート

        Returns:
            更新成功可否
        """
        try:
            # modified時刻を更新
            note.modified_at = datetime.now()
            note.frontmatter.modified = note.modified_at.isoformat()

            # 保存実行
            success = await self.save_note(note, overwrite=True)

            if success:
                # 操作記録を更新に変更
                if self.operation_history:
                    self.operation_history[-1].operation_type = OperationType.UPDATE

                self.logger.info(
                    "Note updated successfully", file_path=str(note.file_path)
                )

            return success

        except Exception as e:
            self.logger.error(
                "Failed to update note",
                file_path=str(note.file_path),
                error=str(e),
                exc_info=True,
            )
            return False

    async def delete_note(self, file_path: Path, to_archive: bool = True) -> bool:
        """
        ノートを削除またはアーカイブ

        Args:
            file_path: 削除するファイルパス
            to_archive: アーカイブするかどうか

        Returns:
            削除成功可否
        """
        try:
            if not file_path.exists():
                self.logger.warning(
                    "File not found for deletion", file_path=str(file_path)
                )
                return False

            success = False
            operation_type = (
                OperationType.ARCHIVE if to_archive else OperationType.DELETE
            )

            if to_archive:
                # アーカイブフォルダに移動
                archive_folder = self.vault_path / VaultFolder.ARCHIVE.value
                archive_folder.mkdir(parents=True, exist_ok=True)

                # アーカイブファイル名の生成
                timestamp = datetime.now().strftime("%Y%m%d%H%M")
                archived_filename = f"{timestamp}_archived_{file_path.name}"
                archive_path = archive_folder / archived_filename

                # ファイル移動
                shutil.move(str(file_path), str(archive_path))

                self.logger.info(
                    "Note archived successfully",
                    original_path=str(file_path),
                    archive_path=str(archive_path),
                )
                success = True

            else:
                # 完全削除
                file_path.unlink()

                self.logger.info("Note deleted successfully", file_path=str(file_path))
                success = True

            # 操作記録
            operation = FileOperation(
                operation_type=operation_type, file_path=file_path, success=success
            )
            self.operation_history.append(operation)

            # キャッシュの無効化
            self._invalidate_stats_cache()

            return success

        except Exception as e:
            # エラー記録
            operation = FileOperation(
                operation_type=operation_type,
                file_path=file_path,
                success=False,
                error_message=str(e),
            )
            self.operation_history.append(operation)

            self.logger.error(
                "Failed to delete/archive note",
                file_path=str(file_path),
                to_archive=to_archive,
                error=str(e),
                exc_info=True,
            )

            return False

    async def search_notes(
        self,
        query: str | None = None,
        folder: VaultFolder | None = None,
        status: NoteStatus | None = None,
        tags: list[str] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
    ) -> list[ObsidianNote]:
        """
        ノート検索

        Args:
            query: 検索クエリ
            folder: フォルダ指定
            status: ステータス指定
            tags: タグ指定
            date_from: 開始日
            date_to: 終了日
            limit: 結果上限

        Returns:
            検索結果のノートリスト
        """
        try:
            results: list[ObsidianNote] = []
            search_path = self.vault_path

            # フォルダ指定がある場合
            if folder:
                search_path = self.vault_path / folder.value
                if not search_path.exists():
                    return []

            # .mdファイルを再帰的に検索
            for md_file in search_path.rglob("*.md"):
                if len(results) >= limit:
                    break

                # テンプレートフォルダは除外
                if VaultFolder.TEMPLATES.value in str(
                    md_file.relative_to(self.vault_path)
                ):
                    continue

                note = await self.load_note(md_file)
                if not note:
                    continue

                # フィルタリング
                if not self._matches_search_criteria(
                    note, query, status, tags, date_from, date_to
                ):
                    continue

                results.append(note)

            # 作成日時で逆順ソート
            results.sort(key=lambda n: n.created_at, reverse=True)

            self.logger.debug(
                "Note search completed",
                query=query,
                results_count=len(results),
                limit=limit,
            )

            return results

        except Exception as e:
            self.logger.error(
                "Failed to search notes", query=query, error=str(e), exc_info=True
            )
            return []

    async def get_vault_stats(self, force_refresh: bool = False) -> VaultStats:
        """
        Vault統計情報を取得

        Args:
            force_refresh: 強制リフレッシュ

        Returns:
            Vault統計情報
        """
        try:
            # キャッシュチェック（5分間有効）
            if (
                not force_refresh
                and self._stats_cache
                and self._stats_cache_time
                and (datetime.now() - self._stats_cache_time).seconds < 300
            ):
                return self._stats_cache

            stats = VaultStats()

            # .mdファイルを再帰的に検索
            for md_file in self.vault_path.rglob("*.md"):
                # テンプレートフォルダは除外
                if VaultFolder.TEMPLATES.value in str(
                    md_file.relative_to(self.vault_path)
                ):
                    continue

                # 基本統計
                stats.total_notes += 1
                stats.total_size_bytes += md_file.stat().st_size

                # フォルダ別統計
                relative_path = md_file.relative_to(self.vault_path)
                folder_name = (
                    str(relative_path.parts[0]) if relative_path.parts else "root"
                )
                stats.notes_by_folder[folder_name] = (
                    stats.notes_by_folder.get(folder_name, 0) + 1
                )

                # 日付別統計
                created_time = datetime.fromtimestamp(md_file.stat().st_ctime)
                today = datetime.now().date()
                created_date = created_time.date()

                if created_date == today:
                    stats.notes_created_today += 1

                if (today - created_date).days <= 7:
                    stats.notes_created_this_week += 1

                if (
                    created_date.month == today.month
                    and created_date.year == today.year
                ):
                    stats.notes_created_this_month += 1

            # ノート詳細統計（重い処理なので一部のみ）
            recent_notes = await self.search_notes(limit=100)

            for note in recent_notes:
                # ステータス別統計
                status_name = note.frontmatter.status.value
                stats.notes_by_status[status_name] = (
                    stats.notes_by_status.get(status_name, 0) + 1
                )

                # カテゴリ別統計
                if note.frontmatter.ai_category:
                    category = note.frontmatter.ai_category
                    stats.notes_by_category[category] = (
                        stats.notes_by_category.get(category, 0) + 1
                    )

                # AI処理統計
                if note.frontmatter.ai_processed:
                    stats.ai_processed_notes += 1
                    if note.frontmatter.ai_processing_time:
                        stats.total_ai_processing_time += (
                            note.frontmatter.ai_processing_time
                        )

                # タグ統計
                for tag in note.frontmatter.ai_tags + note.frontmatter.tags:
                    clean_tag = tag.lstrip("#")
                    stats.most_common_tags[clean_tag] = (
                        stats.most_common_tags.get(clean_tag, 0) + 1
                    )

            # 平均AI処理時間
            if stats.ai_processed_notes > 0:
                stats.average_ai_processing_time = (
                    stats.total_ai_processing_time / stats.ai_processed_notes
                )

            # タグを頻度順にソート（上位20個）
            sorted_tags = sorted(
                stats.most_common_tags.items(), key=lambda x: x[1], reverse=True
            )[:20]
            stats.most_common_tags = dict(sorted_tags)

            stats.last_updated = datetime.now()

            # キャッシュ更新
            self._stats_cache = stats
            self._stats_cache_time = datetime.now()

            self.logger.info(
                "Vault stats collected",
                total_notes=stats.total_notes,
                total_size_mb=stats.total_size_bytes / (1024 * 1024),
                ai_processed=stats.ai_processed_notes,
            )

            return stats

        except Exception as e:
            self.logger.error(
                "Failed to collect vault stats", error=str(e), exc_info=True
            )
            return VaultStats()

    async def backup_vault(self, backup_path: Path) -> bool:
        """
        Vaultのバックアップを作成

        Args:
            backup_path: バックアップ先パス

        Returns:
            バックアップ成功可否
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = backup_path / f"obsidian_vault_backup_{timestamp}"

            # ディレクトリコピー
            await asyncio.to_thread(shutil.copytree, self.vault_path, backup_dir)

            self.logger.info(
                "Vault backup completed",
                backup_path=str(backup_dir),
                vault_path=str(self.vault_path),
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to backup vault",
                backup_path=str(backup_path),
                error=str(e),
                exc_info=True,
            )
            return False

    def get_operation_history(self, limit: int = 50) -> list[FileOperation]:
        """操作履歴を取得"""
        return self.operation_history[-limit:]

    def clear_operation_history(self) -> None:
        """操作履歴をクリア"""
        self.operation_history.clear()
        self.logger.info("Operation history cleared")

    async def _ensure_vault_structure(self) -> None:
        """Vault構造を確保"""
        folders_to_create = [
            VaultFolder.INBOX,
            VaultFolder.DAILY_NOTES,
            VaultFolder.AREAS,
            VaultFolder.RESOURCES,
            VaultFolder.ARCHIVE,
            VaultFolder.TEMPLATES,
            VaultFolder.ATTACHMENTS,
            VaultFolder.WORK,
            VaultFolder.LEARNING,
            VaultFolder.PROJECTS,
            VaultFolder.LIFE,
            VaultFolder.IDEAS,
            VaultFolder.FINANCE,
            VaultFolder.PRODUCTIVITY,
            VaultFolder.IMAGES,
            VaultFolder.AUDIO,
            VaultFolder.DOCUMENTS,
            VaultFolder.OTHER_FILES,
        ]

        for folder in folders_to_create:
            folder_path = self.vault_path / folder.value
            folder_path.mkdir(parents=True, exist_ok=True)
            self._folder_cache.add(folder_path)

        # 年月フォルダの作成（現在年の前後1年）
        current_year = datetime.now().year
        for year in range(current_year - 1, current_year + 2):
            year_folder = self.vault_path / VaultFolder.DAILY_NOTES.value / str(year)
            year_folder.mkdir(parents=True, exist_ok=True)

            # 月フォルダの作成
            for month in range(1, 13):
                month_name = datetime(year, month, 1).strftime("%m-%B")
                month_folder = year_folder / month_name
                month_folder.mkdir(parents=True, exist_ok=True)

    async def _create_template_files(self) -> None:
        """テンプレートファイルを作成"""
        templates_dir = self.vault_path / VaultFolder.TEMPLATES.value

        # メッセージノートテンプレート
        message_template_content = """# {{title}}

## 📝 要約
{{ai_summary}}

## 💬 元メッセージ
```
{{original_content}}
```

## 🏷️ タグ
{{ai_tags}}

## 📂 分類
- **カテゴリ**: {{ai_category}}
- **信頼度**: {{ai_confidence}}

## 📎 添付ファイル
{{attachments}}

## 🔗 関連リンク
- [Discord Message]({{discord_link}})
- **チャンネル**: #{{channel_name}}

## 📊 メタデータ
- **作成者**: {{author_name}}
- **作成日時**: {{created_time}}
- **AI処理時間**: {{processing_time}}ms

---
*このノートはDiscord-Obsidian Memo Botによって自動生成されました*"""

        message_template_path = templates_dir / "message_note_template.md"
        if not message_template_path.exists():
            async with aiofiles.open(message_template_path, "w", encoding="utf-8") as f:
                await f.write(message_template_content)

        # 日次ノートテンプレート
        daily_template_content = """# Daily Note - {{date}}

## 📊 今日の統計
- **総メッセージ数**: {{total_messages}}
- **AI処理済み**: {{processed_messages}}
- **処理時間合計**: {{ai_time_total}}ms

## 📝 今日のメモ

### 仕事 ({{work_count}}件)
{{work_notes}}

### 学習 ({{learning_count}}件)
{{learning_notes}}

### 生活 ({{life_count}}件)
{{life_notes}}

### アイデア ({{ideas_count}}件)
{{ideas_notes}}

## 🏷️ 今日のタグ
{{daily_tags}}

## 📎 添付ファイル
{{daily_attachments}}

---
*このノートは毎日自動更新されます*"""

        daily_template_path = templates_dir / "daily_note_template.md"
        if not daily_template_path.exists():
            async with aiofiles.open(daily_template_path, "w", encoding="utf-8") as f:
                await f.write(daily_template_content)

    def _parse_markdown_file(self, content: str) -> tuple[dict[str, Any], str]:
        """Markdownファイルからフロントマターとコンテンツを分離"""

        frontmatter_data: dict[str, Any] = {}
        markdown_content = content

        # フロントマターの検出
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                try:
                    frontmatter_data = yaml.safe_load(parts[1]) or {}
                    markdown_content = parts[2]
                except yaml.YAMLError as e:
                    self.logger.warning(
                        "Failed to parse YAML frontmatter", error=str(e)
                    )

        return frontmatter_data, markdown_content

    def _matches_search_criteria(
        self,
        note: ObsidianNote,
        query: str | None,
        status: NoteStatus | None,
        tags: list[str] | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> bool:
        """検索条件にマッチするかチェック"""

        # ステータスフィルタ
        if status and note.frontmatter.status != status:
            return False

        # 日付フィルタ
        if date_from and note.created_at < date_from:
            return False

        if date_to and note.created_at > date_to:
            return False

        # タグフィルタ
        if tags:
            note_tags = set(
                note.frontmatter.tags
                + [tag.lstrip("#") for tag in note.frontmatter.ai_tags]
            )
            if not any(tag in note_tags for tag in tags):
                return False

        # クエリフィルタ（タイトル、コンテンツ、タグ、要約を検索）
        if query:
            query_lower = query.lower()
            searchable_text = " ".join(
                [
                    note.title.lower(),
                    note.content.lower(),
                    " ".join(note.frontmatter.tags),
                    " ".join(note.frontmatter.ai_tags),
                    note.frontmatter.ai_summary or "",
                ]
            )

            if query_lower not in searchable_text:
                return False

        return True

    def _invalidate_stats_cache(self) -> None:
        """統計キャッシュを無効化"""
        self._stats_cache = None
        self._stats_cache_time = None
